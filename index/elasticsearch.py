from typing import Dict, Iterable, List, Union
import os

import elasticsearch

from tasks import IndexInterface


class ElasticSearchInterface(IndexInterface):
    def __init__(self, hosts: List, user: str, password: str, timeout: str = "30s", default_index: str = ""):
        self._es = elasticsearch.Elasticsearch(hosts=hosts, http_auth=(user, password))
        self._timeout = timeout
        self._default_index = default_index

    def index_exists(self, index_name: str) -> bool:
        return self._es.indices.exists(index=index_name)

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
        self._es.indices.create(
            index=index_name,
            body=body,
            timeout=self._timeout,
        )

    def refresh_index(self, index_name: str = "") -> None:
        index_name = self.get_index_name(index_name)
        if self.index_exists(index_name):
            return
        self._es.indices.refresh(
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
        self._es.index(index=index, body=document, id=document_id, refresh=refresh)

    def search(self, query: Dict, index: str = "") -> Dict:
        index = self.get_index_name(index)
        result = self._es.search(index=index, body=query, request_timeout=60)
        return result

    def analyze(self, text: str, field: str, index: str = "") -> Dict:
        index = self.get_index_name(index)
        result = self._es.indices.analyze(body={"text": text, "field":field}, index=index)
        return result

    def paginated_search(
        self, query: Dict, index: str = "", keep_alive: str = "5m"
    ) -> Iterable[Dict]:
        index = self.get_index_name(index)
        result = self._es.search(
            index=index, body=query, scroll=keep_alive, request_timeout=120
        )

        if len(result["hits"]["hits"]) == 0:
            return

        while len(result["hits"]["hits"]) > 0:
            yield result
            scroll_id = result["_scroll_id"]
            result = self._es.scroll(
                scroll_id=scroll_id, scroll=keep_alive, request_timeout=120
            )

        self._es.clear_scroll(scroll_id=scroll_id)


def get_elasticsearch_host():
    return os.environ["ELASTICSEARCH_HOST"]

def get_elasticsearch_index():
    return os.environ["ELASTICSEARCH_INDEX"]

def get_elasticsearch_user():
    return os.environ["ELASTICSEARCH_USER"]

def get_elasticsearch_password():
    return os.environ["ELASTICSEARCH_PASSWORD"]

def create_index_interface() -> IndexInterface:
    hosts = get_elasticsearch_host()
    if not isinstance(hosts, str) or len(hosts) == 0:
        raise Exception("Missing index hosts")
    default_index_name = get_elasticsearch_index()
    if not isinstance(default_index_name, str) or len(default_index_name) == 0:
        raise Exception("Invalid index name")
    return ElasticSearchInterface([hosts], get_elasticsearch_user(), get_elasticsearch_password(), default_index=default_index_name)
