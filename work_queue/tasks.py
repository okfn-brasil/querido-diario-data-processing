"""
Task de extração de um diário, consumida pelos workers da fila

A mensagem leva só o `gazette_id`: o Postgres continua sendo a fonte de verdade
e um reprocessamento sempre lê o estado atual do diário. A entrega do Celery é
at-least-once, o que é seguro porque o processamento é idempotente: o OpenSearch
indexa com `document_id=file_checksum` (sobrescreve, não duplica) e
`set_gazette_as_processed` é um UPDATE.
"""

import logging

from botocore.exceptions import ConnectionError as BotoConnectionError
from botocore.exceptions import HTTPClientError as BotoHTTPClientError
from celery import signals
from celery.exceptions import Reject
from opensearchpy.exceptions import ConnectionError as OpenSearchConnectionError
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout as RequestsTimeout

from data_extraction import UnsupportedFileTypeError, create_apache_tika_text_extraction
from database import create_database_interface
from index import create_index_interface
from monitoring.metrics import observe_gazette_processing, start_metrics_server
from storage import create_storage_interface
from tasks.gazette_text_extraction import (
    GazetteFileNotFoundError,
    try_process_gazette_file,
)
from tasks.list_gazettes_to_be_processed import get_gazette_by_id
from tasks.list_territories import get_territories
from work_queue import redis_keys
from work_queue.celery_app import app

deps = {}

# Erros que costumam se resolver sozinhos (serviço reiniciando, rede): tenta de
# novo com backoff. Qualquer outro erro vai direto para a DLQ
TRANSIENT_ERRORS = (
    ConnectionError,
    TimeoutError,
    RequestsConnectionError,
    RequestsTimeout,
    OpenSearchConnectionError,
    BotoConnectionError,
    BotoHTTPClientError,
)


@signals.worker_process_init.connect
def init_dependencies(**_):
    """
    Cria as conexões uma vez por processo filho do worker, e não no processo
    pai, para não compartilhar conexões entre processos após o fork.
    """
    deps["database"] = create_database_interface()
    deps["storage"] = create_storage_interface()
    deps["index"] = create_index_interface()
    deps["text_extractor"] = create_apache_tika_text_extraction()
    deps["territories"] = list(get_territories(deps["database"]))
    # No processo filho porque o prometheus_client não está em modo
    # multiprocess: as métricas só existem no processo que processa o diário.
    # Funciona com --concurrency=1; com mais filhos, as portas colidiriam
    start_metrics_server()


@app.task(
    bind=True,
    autoretry_for=TRANSIENT_ERRORS,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5,
)
def extract_gazette(self, gazette_id: int):
    gazette = get_gazette_by_id(deps["database"], gazette_id)
    if gazette is None or gazette["processed"]:
        # Idempotência: já processado (mensagem entregue de novo) ou removido
        logging.info(f"Diário {gazette_id} já processado ou inexistente")
        redis_keys.release_enqueued(gazette_id)
        return

    try:
        with observe_gazette_processing(gazette):
            document_ids = try_process_gazette_file(
                gazette,
                deps["territories"],
                deps["database"],
                deps["storage"],
                deps["index"],
                deps["text_extractor"],
            )
    except GazetteFileNotFoundError as e:
        # Não é transitório: não adianta tentar de novo
        redis_keys.send_to_dlq(gazette_id, f"not found: {e}")
        raise Reject(str(e), requeue=False)
    except UnsupportedFileTypeError as e:
        redis_keys.send_to_dlq(gazette_id, f"unsupported: {e}")
        raise Reject(str(e), requeue=False)

    redis_keys.mark_for_themes(document_ids)
    redis_keys.release_enqueued(gazette_id)


@signals.task_failure.connect(sender=extract_gazette)
def on_final_failure(
    sender=None, task_id=None, exception=None, args=None, kwargs=None, **_
):
    """
    Chamado quando a task falha de vez: estourou max_retries de um erro
    transitório ou ocorreu um erro não transitório. Os Reject acima não passam
    por aqui (já foram para a DLQ).
    """
    gazette_id = args[0] if args else (kwargs or {}).get("gazette_id")
    logging.error(f"Diário {gazette_id} enviado para a DLQ: {exception!r}")
    redis_keys.send_to_dlq(gazette_id, repr(exception))
