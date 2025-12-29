"""
Logging estruturado para monitoramento de conexões com Tika e OpenSearch

Fornece funções para registrar chamadas, respostas e erros de forma estruturada,
facilitando a análise de problemas de conexão e performance.
"""

import json
import logging
import time
from datetime import date, datetime
from functools import wraps
from typing import Dict, Optional


def date_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


# Configuração de logging estruturado
def setup_structured_logging(level: int = logging.INFO) -> None:
    """
    Configura logging estruturado com formato JSON para melhor análise
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


class ConnectionMonitor:
    """
    Monitor de conexões que rastreia estatísticas de chamadas
    """

    def __init__(self):
        self.stats = {
            "tika": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_duration_ms": 0,
                "errors": {},
            },
            "opensearch": {
                "total_operations": 0,
                "successful_operations": 0,
                "failed_operations": 0,
                "total_duration_ms": 0,
                "errors": {},
            },
        }

    def record_tika_request(
        self, success: bool, duration_ms: float, error_type: Optional[str] = None
    ):
        """Registra estatísticas de uma requisição ao Tika"""
        self.stats["tika"]["total_requests"] += 1
        self.stats["tika"]["total_duration_ms"] += duration_ms

        if success:
            self.stats["tika"]["successful_requests"] += 1
        else:
            self.stats["tika"]["failed_requests"] += 1
            if error_type:
                self.stats["tika"]["errors"][error_type] = (
                    self.stats["tika"]["errors"].get(error_type, 0) + 1
                )

    def record_opensearch_operation(
        self, success: bool, duration_ms: float, error_type: Optional[str] = None
    ):
        """Registra estatísticas de uma operação no OpenSearch"""
        self.stats["opensearch"]["total_operations"] += 1
        self.stats["opensearch"]["total_duration_ms"] += duration_ms

        if success:
            self.stats["opensearch"]["successful_operations"] += 1
        else:
            self.stats["opensearch"]["failed_operations"] += 1
            if error_type:
                self.stats["opensearch"]["errors"][error_type] = (
                    self.stats["opensearch"]["errors"].get(error_type, 0) + 1
                )

    def get_stats(self) -> Dict:
        """Retorna estatísticas agregadas"""
        return self.stats

    def print_summary(self):
        """Imprime resumo das estatísticas"""
        print("\n=== RESUMO DE CONEXÕES ===")
        print("\nApache Tika:")
        print(f"  Total de requisições: {self.stats['tika']['total_requests']}")
        print(f"  Bem-sucedidas: {self.stats['tika']['successful_requests']}")
        print(f"  Falhas: {self.stats['tika']['failed_requests']}")
        if self.stats["tika"]["total_requests"] > 0:
            avg_duration = (
                self.stats["tika"]["total_duration_ms"]
                / self.stats["tika"]["total_requests"]
            )
            print(f"  Duração média: {avg_duration:.2f}ms")
        if self.stats["tika"]["errors"]:
            print(f"  Tipos de erro: {self.stats['tika']['errors']}")

        print("\nOpenSearch:")
        print(f"  Total de operações: {self.stats['opensearch']['total_operations']}")
        print(f"  Bem-sucedidas: {self.stats['opensearch']['successful_operations']}")
        print(f"  Falhas: {self.stats['opensearch']['failed_operations']}")
        if self.stats["opensearch"]["total_operations"] > 0:
            avg_duration = (
                self.stats["opensearch"]["total_duration_ms"]
                / self.stats["opensearch"]["total_operations"]
            )
            print(f"  Duração média: {avg_duration:.2f}ms")
        if self.stats["opensearch"]["errors"]:
            print(f"  Tipos de erro: {self.stats['opensearch']['errors']}")


# Monitor global (singleton)
_global_monitor = ConnectionMonitor()


def get_monitor() -> ConnectionMonitor:
    """Retorna a instância global do monitor"""
    return _global_monitor


# Funções de logging estruturado para Tika
def log_tika_request(
    filepath: str, file_size: int, content_type: str, url: str
) -> None:
    """
    Registra uma requisição ao servidor Tika

    Args:
        filepath: Caminho do arquivo sendo processado
        file_size: Tamanho do arquivo em bytes
        content_type: Tipo MIME do arquivo
        url: URL do servidor Tika
    """
    logger = logging.getLogger("tika.request")
    logger.info(
        "TIKA_REQUEST",
        extra={
            "event_type": "tika_request",
            "filepath": filepath,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / 1024 / 1024, 2),
            "content_type": content_type,
            "tika_url": url,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


def log_tika_response(
    filepath: str, duration_ms: float, response_size: int, status_code: int
) -> None:
    """
    Registra a resposta bem-sucedida do servidor Tika

    Args:
        filepath: Caminho do arquivo processado
        duration_ms: Duração da requisição em milissegundos
        response_size: Tamanho da resposta em bytes
        status_code: Código de status HTTP
    """
    logger = logging.getLogger("tika.response")
    logger.info(
        "TIKA_RESPONSE",
        extra={
            "event_type": "tika_response",
            "filepath": filepath,
            "duration_ms": round(duration_ms, 2),
            "response_size_bytes": response_size,
            "response_size_kb": round(response_size / 1024, 2),
            "status_code": status_code,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    # Registra no monitor
    _global_monitor.record_tika_request(success=True, duration_ms=duration_ms)


def log_tika_error(
    filepath: str,
    error_type: str,
    error_message: str,
    duration_ms: float,
    file_size: Optional[int] = None,
    status_code: Optional[int] = None,
) -> None:
    """
    Registra um erro na comunicação com o servidor Tika

    Args:
        filepath: Caminho do arquivo que causou o erro
        error_type: Tipo da exceção (ex: ChunkedEncodingError, ConnectionError)
        error_message: Mensagem de erro detalhada
        duration_ms: Duração até o erro em milissegundos
        file_size: Tamanho do arquivo (se disponível)
        status_code: Código de status HTTP (se disponível)
    """
    logger = logging.getLogger("tika.error")

    error_data = {
        "event_type": "tika_error",
        "filepath": filepath,
        "error_type": error_type,
        "error_message": error_message,
        "duration_ms": round(duration_ms, 2),
        "timestamp": datetime.utcnow().isoformat(),
    }

    if file_size is not None:
        error_data["file_size_bytes"] = file_size
        error_data["file_size_mb"] = round(file_size / 1024 / 1024, 2)

    if status_code is not None:
        error_data["status_code"] = status_code

    logger.error("TIKA_ERROR", extra=error_data)

    # Registra no monitor
    _global_monitor.record_tika_request(
        success=False, duration_ms=duration_ms, error_type=error_type
    )


# Funções de logging estruturado para OpenSearch
def log_opensearch_operation(
    operation: str,
    index_name: str,
    duration_ms: float,
    document_id: Optional[str] = None,
    success: bool = True,
    document_size: Optional[int] = None,
) -> None:
    """
    Registra uma operação no OpenSearch

    Args:
        operation: Tipo de operação (index, search, bulk, etc.)
        index_name: Nome do índice
        duration_ms: Duração da operação em milissegundos
        document_id: ID do documento (se aplicável)
        success: Se a operação foi bem-sucedida
        document_size: Tamanho do documento em bytes (se aplicável)
    """
    logger = logging.getLogger("opensearch.operation")

    log_data = {
        "event_type": "opensearch_operation",
        "operation": operation,
        "index_name": index_name,
        "duration_ms": round(duration_ms, 2),
        "success": success,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if document_id:
        log_data["document_id"] = document_id

    if document_size is not None:
        log_data["document_size_bytes"] = document_size
        log_data["document_size_kb"] = round(document_size / 1024, 2)

    if success:
        logger.info("OPENSEARCH_OPERATION", extra=log_data)
    else:
        logger.warning("OPENSEARCH_OPERATION_FAILED", extra=log_data)

    # Registra no monitor
    _global_monitor.record_opensearch_operation(
        success=success, duration_ms=duration_ms
    )


def log_opensearch_error(
    operation: str,
    index_name: str,
    error_type: str,
    error_message: str,
    duration_ms: float,
    document_id: Optional[str] = None,
    document_size: Optional[int] = None,
) -> None:
    """
    Registra um erro em operação do OpenSearch

    Args:
        operation: Tipo de operação que falhou
        index_name: Nome do índice
        error_type: Tipo da exceção
        error_message: Mensagem de erro detalhada
        duration_ms: Duração até o erro em milissegundos
        document_id: ID do documento (se aplicável)
        document_size: Tamanho do documento (se aplicável)
    """
    logger = logging.getLogger("opensearch.error")

    error_data = {
        "event_type": "opensearch_error",
        "operation": operation,
        "index_name": index_name,
        "error_type": error_type,
        "error_message": error_message,
        "duration_ms": round(duration_ms, 2),
        "timestamp": datetime.utcnow().isoformat(),
    }

    if document_id:
        error_data["document_id"] = document_id

    if document_size is not None:
        error_data["document_size_bytes"] = document_size
        error_data["document_size_mb"] = round(document_size / 1024 / 1024, 2)

    logger.error("OPENSEARCH_ERROR", extra=error_data)

    # Registra no monitor
    _global_monitor.record_opensearch_operation(
        success=False, duration_ms=duration_ms, error_type=error_type
    )


# Decorators para instrumentação automática
def monitor_tika_call(func):
    """
    Decorator para monitorar automaticamente chamadas ao Tika
    """

    @wraps(func)
    def wrapper(self, filepath: str) -> str:
        import os

        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        content_type = (
            self._get_file_type(filepath)
            if hasattr(self, "_get_file_type")
            else "unknown"
        )
        url = self._url if hasattr(self, "_url") else "unknown"

        log_tika_request(filepath, file_size, content_type, url)

        start_time = time.time()
        try:
            result = func(self, filepath)
            duration_ms = (time.time() - start_time) * 1000

            response_size = len(result) if result else 0
            log_tika_response(filepath, duration_ms, response_size, 200)

            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_type = type(e).__name__
            error_message = str(e)

            log_tika_error(filepath, error_type, error_message, duration_ms, file_size)
            raise

    return wrapper


def monitor_opensearch_call(operation: str):
    """
    Decorator para monitorar automaticamente operações no OpenSearch
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            index_name = kwargs.get(
                "index",
                self._default_index if hasattr(self, "_default_index") else "unknown",
            )
            document_id = kwargs.get("document_id") or kwargs.get("id")

            start_time = time.time()
            try:
                result = func(self, *args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                # Tenta calcular tamanho do documento
                document_size = None
                if "document" in kwargs or "body" in kwargs:
                    doc = kwargs.get("document") or kwargs.get("body")
                    if doc:
                        document_size = len(json.dumps(doc, default=date_serializer))

                log_opensearch_operation(
                    operation,
                    index_name,
                    duration_ms,
                    document_id,
                    success=True,
                    document_size=document_size,
                )

                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                error_type = type(e).__name__
                error_message = str(e)

                log_opensearch_error(
                    operation,
                    index_name,
                    error_type,
                    error_message,
                    duration_ms,
                    document_id,
                )
                raise

        return wrapper

    return decorator
