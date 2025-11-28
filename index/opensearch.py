import os
from typing import Dict, Iterable, List, Union

import opensearchpy

from .interfaces import IndexInterface


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
            hosts=hosts, http_auth=(user, password), timeout=timeout
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

    def create_index(self, index_name: str = "", body: Dict = {}) -> None:
        index_name = self.get_index_name(index_name)
        if self.index_exists(index_name):
            return
        self._search_engine.indices.create(
            index=index_name,
            body=body,
            timeout=self._timeout,
        )

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
        self._search_engine.index(
            index=index, body=document, id=document_id, refresh=refresh, request_timeout=self._timeout
        )

    def search(self, query: Dict, index: str = "") -> Dict:
        index = self.get_index_name(index)
        result = self._search_engine.search(index=index, body=query, request_timeout=60)
        return result

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
