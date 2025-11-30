import json
import os
import time
from datetime import date, datetime
from functools import wraps
from typing import Dict, Iterable, List, Union

import opensearchpy

from .interfaces import IndexInterface
from monitoring import log_opensearch_operation, log_opensearch_error


def date_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def retry_with_exponential_backoff(max_retries=3, initial_delay=1.0, backoff_factor=2.0):
    """
    Decorator to retry operations with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        backoff_factor: Multiplier for delay between retries (default: 2.0)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        raise last_exception
            
            raise last_exception
        
        return wrapper
    return decorator


class OpenSearchInterface(IndexInterface):
    def __init__(
        self,
        hosts: List,
        user: str,
        password: str,
        timeout: int = 60,
        default_index: str = "",
    ):
        self._search_engine = opensearchpy.OpenSearch(
            hosts=hosts,
            http_auth=(user, password),
            timeout=timeout,
            max_retries=3,
            retry_on_timeout=True,
        )
        self._timeout = timeout
        self._default_index = default_index

    def index_exists(self, index_name: str) -> bool:
        return self._search_engine.indices.exists(index=index_name)

    def is_valid_index_name(self, index_name: str) -> bool:
        return isinstance(index_name, str) and len(index_name) > 0

    def get_index_name(self, index_name: str) -> str:
        if self.is_valid_index_name(index_name):
            return index_name
        if self._default_index == "":
            raise Exception("Index name not defined")
        return self._default_index

    @retry_with_exponential_backoff(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def create_index(self, index_name: str = "", body: Dict = {}) -> None:
        index_name = self.get_index_name(index_name)
        if self.index_exists(index_name):
            return
        self._search_engine.indices.create(
            index=index_name,
            body=body,
            timeout=self._timeout,
        )

    @retry_with_exponential_backoff(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def refresh_index(self, index_name: str = "") -> None:
        index_name = self.get_index_name(index_name)
        if self.index_exists(index_name):
            return
        self._search_engine.indices.refresh(
            index=index_name,
        )

    def index_document(
        self,
        document: Dict,
        document_id: Union[str, None] = None,
        index: str = "",
        refresh: bool = False,
    ) -> None:
        index = self.get_index_name(index)
        
        start_time = time.time()
        delay = 1.0
        last_exception = None
        
        for attempt in range(4):  # 3 retries + 1 initial attempt
            try:
                self._search_engine.index(
                    index=index, body=document, id=document_id, refresh=refresh, request_timeout=self._timeout
                )
                duration_ms = (time.time() - start_time) * 1000
                
                # Log operação bem-sucedida
                document_size = len(json.dumps(document, default=date_serializer))
                log_opensearch_operation(
                    'index',
                    index,
                    duration_ms,
                    document_id=document_id,
                    success=True,
                    document_size=document_size
                )
                return
            except Exception as e:
                last_exception = e
                
                if attempt < 3:  # Still have retries left
                    time.sleep(delay)
                    delay *= 2.0
                else:  # Last attempt failed
                    duration_ms = (time.time() - start_time) * 1000
                    error_type = type(e).__name__
                    error_message = str(e)
                    
                    # Log erro
                    try:
                        document_size = len(json.dumps(document, default=date_serializer))
                    except:
                        document_size = None
                    
                    log_opensearch_error(
                        'index',
                        index,
                        error_type,
                        error_message,
                        duration_ms,
                        document_id=document_id,
                        document_size=document_size
                    )
                    raise

    def search(self, query: Dict, index: str = "") -> Dict:
        index = self.get_index_name(index)
        
        start_time = time.time()
        try:
            result = self._search_engine.search(index=index, body=query, request_timeout=60)
            duration_ms = (time.time() - start_time) * 1000
            
            # Log operação bem-sucedida
            log_opensearch_operation('search', index, duration_ms, success=True)
            
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_type = type(e).__name__
            error_message = str(e)
            
            # Log erro
            log_opensearch_error('search', index, error_type, error_message, duration_ms)
            raise

    def analyze(self, text: str, field: str, index: str = "") -> Dict:
        index = self.get_index_name(index)
        result = self._search_engine.indices.analyze(
            body={"text": text, "field": field}, index=index
        )
        return result

    def paginated_search(
        self, query: Dict, index: str = "", keep_alive: str = "5m"
    ) -> Iterable[Dict]:
        index = self.get_index_name(index)
        result = self._search_engine.search(
            index=index, body=query, scroll=keep_alive, request_timeout=120
        )

        if len(result["hits"]["hits"]) == 0:
            return

        scroll_id = None
        while len(result["hits"]["hits"]) > 0:
            yield result

            if scroll_id is not None and scroll_id != result["_scroll_id"]:
                self._search_engine.clear_scroll(scroll_id=scroll_id)

            scroll_id = result["_scroll_id"]
            result = self._search_engine.scroll(
                scroll_id=scroll_id, scroll=keep_alive, request_timeout=120
            )

        self._search_engine.clear_scroll(scroll_id=scroll_id)


def get_opensearch_host():
    return os.environ["OPENSEARCH_HOST"]


def get_opensearch_index():
    return os.environ["OPENSEARCH_INDEX"]


def get_opensearch_user():
    return os.environ["OPENSEARCH_USER"]


def get_opensearch_password():
    return os.environ["OPENSEARCH_PASSWORD"]


def create_index_interface() -> IndexInterface:
    hosts = get_opensearch_host()
    if not isinstance(hosts, str) or len(hosts) == 0:
        raise Exception("Missing index hosts")
    default_index_name = get_opensearch_index()
    if not isinstance(default_index_name, str) or len(default_index_name) == 0:
        raise Exception("Invalid index name")
    return OpenSearchInterface(
        [hosts],
        get_opensearch_user(),
        get_opensearch_password(),
        default_index=default_index_name,
    )
