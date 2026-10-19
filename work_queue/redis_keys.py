"""
Chaves auxiliares da fila no Redis (o mesmo do broker do Celery)

- qd:enqueued:{id}   diário já enfileirado; impede que o produtor o enfileire de
                     novo enquanto ele ainda está na fila
- qd:extraction:dead DLQ: diários que falharam de vez, com o erro
- qd:themes:pending  checksums dos documentos indexados que ainda precisam
                     passar pelos excertos temáticos

DLQ e qd:enqueued:{id}: ao ir para a DLQ, a chave do diário perde o TTL e fica
até alguém reprocessá-lo. Como o diário continua `processed=false`, se a chave
expirasse o produtor o reenfileiraria e ele voltaria à DLQ a cada 6 h. Para
reprocessar um diário da DLQ: tirá-lo de qd:extraction:dead, apagar
qd:enqueued:{id} e deixar o produtor reenfileirá-lo na próxima execução.
"""

import json
import os
import time
from typing import Iterable, List, Optional

import redis

ENQUEUED_KEY = "qd:enqueued:{}"
DEAD_LETTER_KEY = "qd:extraction:dead"
THEMES_PENDING_KEY = "qd:themes:pending"

# Maior que o tempo esperado de espera na fila; se expirar com o diário ainda
# na fila, o pior caso é ele ser processado duas vezes (o que é idempotente)
ENQUEUED_TTL_SECONDS = 6 * 3600

_client: Optional[redis.Redis] = None


def get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            os.environ["QUEUE_BROKER_URL"], decode_responses=True
        )
    return _client


def try_mark_enqueued(gazette_id: int) -> bool:
    """Marca o diário como enfileirado; False se ele já estava na fila"""
    return bool(
        get_client().set(
            ENQUEUED_KEY.format(gazette_id), 1, nx=True, ex=ENQUEUED_TTL_SECONDS
        )
    )


def release_enqueued(gazette_id: int) -> None:
    get_client().delete(ENQUEUED_KEY.format(gazette_id))


def send_to_dlq(gazette_id: int, error: str) -> None:
    entry = json.dumps({"id": gazette_id, "error": error, "ts": time.time()})
    pipeline = get_client().pipeline()
    pipeline.lpush(DEAD_LETTER_KEY, entry)
    # Sem EX: a chave fica enquanto o diário estiver na DLQ (ver docstring)
    pipeline.set(ENQUEUED_KEY.format(gazette_id), 1)
    pipeline.execute()


def mark_for_themes(checksums: Iterable[str]) -> None:
    checksums = list(checksums)
    if checksums:
        get_client().sadd(THEMES_PENDING_KEY, *checksums)


def pop_themes_batch(n: int) -> List[str]:
    return get_client().spop(THEMES_PENDING_KEY, n) or []
