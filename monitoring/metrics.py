"""
Métricas Prometheus do pipeline de processamento

As mesmas séries servem ao baseline (CronJob, que envia ao Pushgateway no fim da
execução) e aos workers da fila (que expõem um endpoint HTTP raspado via
PodMonitor). O rótulo `mode` distingue os dois e vem de PIPELINE_MODE.
"""

import logging
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Histogram,
    push_to_gateway,
    start_http_server,
)

# Registry próprio para enviar ao Pushgateway só as métricas da aplicação, sem
# os coletores de processo/plataforma do registry padrão
REGISTRY = CollectorRegistry()

GAZETTES_PROCESSED = Counter(
    "qd_gazettes_processed_total",
    "Diários processados",
    ["mode", "status"],
    registry=REGISTRY,
)
PROCESSING_SECONDS = Histogram(
    "qd_gazette_processing_seconds",
    "Tempo de processamento por diário",
    ["mode"],
    buckets=(1, 2, 5, 10, 20, 40, 80, 160, 320),
    registry=REGISTRY,
)
SCRAPE_TO_INDEX_SECONDS = Histogram(
    "qd_scrape_to_index_seconds",
    "Latência coleta → indexado",
    ["mode"],
    buckets=(60, 300, 900, 1800, 3600, 7200, 14400, 43200, 86400),
    registry=REGISTRY,
)

STATUS_OK = "ok"
STATUS_UNSUPPORTED = "unsupported"
STATUS_ERROR = "error"

PUSHGATEWAY_JOB = "data-processing"
DEFAULT_METRICS_PORT = 9100


def get_pipeline_mode() -> str:
    return os.environ.get("PIPELINE_MODE", "cron")


def _seconds_since(moment: datetime) -> float:
    # scraped_at é gravado pelos raspadores em UTC, sem fuso
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - moment).total_seconds()


@contextmanager
def observe_gazette_processing(gazette: Dict[str, Any]):
    """
    Mede o processamento de um diário: duração, status e, em caso de sucesso,
    a latência entre a coleta (scraped_at) e a indexação.

    Uso:
        with observe_gazette_processing(gazette) as observation:
            ...
            observation["status"] = STATUS_UNSUPPORTED  # opcional

    Exceções levantadas no bloco contam como `error`, exceto
    UnsupportedFileTypeError, que conta como `unsupported`; em ambos os casos
    a exceção é propagada.
    """
    from data_extraction import UnsupportedFileTypeError

    mode = get_pipeline_mode()
    # Lido antes do bloco porque o diário é limpo da memória após o processamento
    scraped_at: Optional[datetime] = gazette.get("scraped_at")
    observation = {"status": STATUS_OK}
    start = time.perf_counter()
    try:
        yield observation
    except UnsupportedFileTypeError:
        observation["status"] = STATUS_UNSUPPORTED
        raise
    except Exception:
        observation["status"] = STATUS_ERROR
        raise
    finally:
        PROCESSING_SECONDS.labels(mode=mode).observe(time.perf_counter() - start)
        GAZETTES_PROCESSED.labels(mode=mode, status=observation["status"]).inc()
        if observation["status"] == STATUS_OK and isinstance(scraped_at, datetime):
            SCRAPE_TO_INDEX_SECONDS.labels(mode=mode).observe(
                _seconds_since(scraped_at)
            )


def push_metrics_if_configured() -> bool:
    """
    Envia as métricas ao Pushgateway quando PUSHGATEWAY_URL estiver definida.
    Processos batch (CronJob) não são raspados pelo Prometheus, então precisam
    empurrar as métricas no fim da execução. Falhas no envio não interrompem o
    pipeline.
    """
    url = os.environ.get("PUSHGATEWAY_URL")
    if not url:
        return False
    try:
        push_to_gateway(url, job=PUSHGATEWAY_JOB, registry=REGISTRY)
    except Exception as e:
        logging.warning(f"Falha ao enviar métricas ao Pushgateway ({url}): {e}")
        return False
    logging.info(f"Métricas enviadas ao Pushgateway ({url})")
    return True


def start_metrics_server(port: Optional[int] = None):
    """
    Expõe /metrics para processos de longa duração (workers da fila), raspados
    pelo Prometheus via PodMonitor.
    """
    port = port or int(os.environ.get("METRICS_PORT", DEFAULT_METRICS_PORT))
    start_http_server(port, registry=REGISTRY)
    logging.info(f"Servidor de métricas escutando na porta {port}")
