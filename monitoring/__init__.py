"""
Módulo de monitoramento e logging estruturado para o projeto querido-diario-data-processing
"""

from .structured_logging import (
    ConnectionMonitor,
    get_monitor,
    log_opensearch_error,
    log_opensearch_operation,
    log_tika_error,
    log_tika_request,
    log_tika_response,
    monitor_opensearch_call,
    monitor_tika_call,
    setup_structured_logging,
)

__all__ = [
    "setup_structured_logging",
    "log_tika_request",
    "log_tika_response",
    "log_tika_error",
    "log_opensearch_operation",
    "log_opensearch_error",
    "ConnectionMonitor",
    "get_monitor",
    "monitor_tika_call",
    "monitor_opensearch_call",
]
