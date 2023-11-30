from datetime import date, datetime
from unittest import TestCase, expectedFailure
from unittest.mock import patch, MagicMock
import uuid

import opensearch

from index.opensearch import OpenSearchInterface, create_index_interface
from tasks import IndexInterface


class IndexInterfaceFactoryFunctionTests(TestCase):
    @patch.dict(
        "os.environ",
        {
            "OPENSEARCH_HOST": "127.0.0.1",
            "OPENSEARCH_INDEX": "index_name",
        },
    )
    def test_create_index_interface_factory_method_with_valid_arguments(self):
        interface = create_index_interface()
        self.assertIsInstance(interface, IndexInterface)
        self.assertEqual(interface._default_index, "index_name")

    @expectedFailure
    def test_index_interface_factory_method_failed_without_required_info(self):
        interface = create_index_interface()

    @patch.dict(
        "os.environ",
        {
            "OPENSEARCH_INDEX": "index_name",
        },
    )
    @expectedFailure
    def test_index_interface_factory_method_failed_with_no_hosts(self):
        interface = create_index_interface()

    @patch.dict(
        "os.environ",
        {
            "OPENSEARCH_HOST": "127.0.0.1",
        },
    )
    @expectedFailure
    def test_create_index_interface_factory_method_with_no_index(self):
        interface = create_index_interface()

    @patch.dict(
        "os.environ",
        {
            "OPENSEARCH_HOST": "127.0.0.1",
            "OPENSEARCH_INDEX": "",
        },
    )
    @expectedFailure
    def test_create_index_interface_factory_method_with_empty_index(self):
        interface = create_index_interface()

    @patch.dict(
        "os.environ",
        {
            "OPENSEARCH_HOST": "",
            "OPENSEARCH_INDEX": "index_name",
        },
    )
    @expectedFailure
    def test_create_index_interface_factory_method_with_empty_hosts(self):
        interface = create_index_interface()


class OpensearchBasicTests(TestCase):
    def setUp(self):
        document_checksum = str(uuid.uuid1())
        self.fake_document = {
            "source_text": "",
            "date": date.today(),
            "edition_number": "1",
            "is_extra_edition": False,
            "power": "executive",
            "file_checksum": document_checksum,
            "file_path": f"my/fake/path/gazette/{document_checksum}.pdf",
            "file_url": "www.querido-diario.org",
            "scraped_at": datetime.now(),
            "created_at": datetime.now(),
            "territory_id": "3550308",
            "processed": False,
            "state_code": "SC",
            "territory_name": "Gaspar",
        }

    def test_opensearch_should_implement_index_interface(self):
        self.assertIsInstance(OpenSearchInterface([]), IndexInterface)

    @patch("opensearch.Opensearch", autospec=True)
    def test_opensearch_connection(self, opensearch_mock):
        interface = OpenSearchInterface(["127.0.0.1"])
        opensearch_mock.assert_called_once_with(hosts=["127.0.0.1"])

    @patch("opensearch.Opensearch", autospec=True)
    def test_opensearch_index_creation_should_check_if_index_exists(
        self, opensearch_mock
    ):
        interface = OpenSearchInterface(["127.0.0.1"])
        interface.search_engine.indices = MagicMock()
        interface.search_engine.indices.exists = MagicMock()
        interface.create_index("querido-diario")
        interface.search_engine.indices.exists.assert_called_once_with(index="querido-diario")

    @patch("opensearch.Opensearch", autospec=True)
    def test_opensearch_index_creation_should_failed_when_no_index_is_provided(
        self, opensearch_mock
    ):
        interface = OpenSearchInterface(["127.0.0.1"])
        interface.search_engine.indices = MagicMock()
        interface.search_engine.indices.exists = MagicMock()
        with self.assertRaisesRegex(Exception, "Index name not defined"):
            interface.create_index()

    @patch("opensearch.Opensearch", autospec=True)
    def test_opensearch_index_creation_with_default_index_value(
        self, opensearch_mock
    ):
        interface = OpenSearchInterface(
            ["127.0.0.1"], default_index="querido-diario2"
        )
        interface.search_engine.indices = MagicMock()
        interface.search_engine.indices.exists = MagicMock()
        interface.create_index()
        interface.search_engine.indices.exists.assert_called_once_with(index="querido-diario2")

    @patch("opensearch.Opensearch", autospec=True)
    def test_opensearch_index_default_timeout_should_be_30s(
        self, opensearch_mock
    ):
        interface = OpenSearchInterface(["127.0.0.1"])
        interface.search_engine.indices = MagicMock()
        interface.search_engine.indices.exists = MagicMock(return_value=False)
        interface.search_engine.indices.create = MagicMock()
        interface.create_index("querido-diario")
        interface.search_engine.indices.create.assert_called_once_with(
            index="querido-diario",
            body={"mappings": {"properties": {"date": {"type": "date"}}}},
            timeout="30s",
        )

    @patch("opensearch.Opensearch", autospec=True)
    def test_opensearch_index_should_allow_change_default_timeout(
        self, opensearch_mock
    ):
        interface = OpenSearchInterface(["127.0.0.1"], timeout="2m")
        interface.search_engine.indices = MagicMock()
        interface.search_engine.indices.exists = MagicMock(return_value=False)
        interface.search_engine.indices.create = MagicMock()
        interface.create_index("querido-diario")
        interface.search_engine.indices.create.assert_called_once_with(
            index="querido-diario",
            body={"mappings": {"properties": {"date": {"type": "date"}}}},
            timeout="2m",
        )

    @patch("opensearch.Opensearch", autospec=True)
    def test_opensearch_index_creation_should_not_recreate_index_if_it_exists(
        self, opensearch_mock
    ):
        interface = OpenSearchInterface(["127.0.0.1"])
        interface.search_engine.indices = MagicMock()
        interface.search_engine.indices.exists = MagicMock(return_value=True)
        interface.search_engine.indices.create = MagicMock()
        interface.create_index("querido-diario")
        interface.search_engine.indices.exists.assert_called_once_with(index="querido-diario")
        interface.search_engine.indices.create.assert_not_called()

    @patch("opensearch.Opensearch", autospec=True)
    def test_opensearch_should_create_index_if_it_does_not_exists(
        self, opensearch_mock
    ):
        interface = OpenSearchInterface(["127.0.0.1"])
        interface.search_engine.indices = MagicMock()
        interface.search_engine.indices.exists = MagicMock(return_value=False)
        interface.search_engine.indices.create = MagicMock()
        interface.create_index("querido-diario")
        interface.search_engine.indices.exists.assert_called_once_with(index="querido-diario")
        interface.search_engine.indices.create.assert_called_once_with(
            index="querido-diario",
            body={"mappings": {"properties": {"date": {"type": "date"}}}},
            timeout="30s",
        )

    @patch("opensearch.Opensearch", autospec=True)
    def test_opensearch_should_create_index_with_default_value_with_function_has_no_arguments(
        self, opensearch_mock
    ):
        interface = OpenSearchInterface(
            ["127.0.0.1"], default_index="querido-diario2"
        )
        interface.search_engine.indices = MagicMock()
        interface.search_engine.indices.exists = MagicMock(return_value=False)
        interface.search_engine.indices.create = MagicMock()
        interface.create_index()
        interface.search_engine.indices.exists.assert_called_once_with(index="querido-diario2")
        interface.search_engine.indices.create.assert_called_once_with(
            index="querido-diario2",
            body={"mappings": {"properties": {"date": {"type": "date"}}}},
            timeout="30s",
        )

    @patch("opensearch.Opensearch", autospec=True)
    def test_upload_document_to_index(self, opensearch_mock):
        interface = OpenSearchInterface(["127.0.0.1"])
        document_checksum = str(uuid.uuid1())
        interface.index_document(self.fake_document, "querido-diario")
        interface.search_engine.index.assert_called_once_with(
            index="querido-diario",
            body=self.fake_document,
            id=self.fake_document["file_checksum"],
        )

    @patch("opensearch.Opensearch", autospec=True)
    def test_upload_document_to_index_using_default_index(self, opensearch_mock):
        interface = OpenSearchInterface(
            ["127.0.0.1"], default_index="querido-diario2"
        )
        document_checksum = str(uuid.uuid1())
        interface.index_document(self.fake_document)
        interface.search_engine.index.assert_called_once_with(
            index="querido-diario2",
            body=self.fake_document,
            id=self.fake_document["file_checksum"],
        )


class OpensearchIntegrationTests(TestCase):
    def setUp(self):
        document_checksum = str(uuid.uuid1())
        self.fake_document = {
            "source_text": "",
            "date": date.today(),
            "edition_number": "1",
            "is_extra_edition": False,
            "power": "executive",
            "file_checksum": document_checksum,
            "file_path": f"my/fake/path/gazette/{document_checksum}.pdf",
            "file_url": "www.querido-diario.org",
            "scraped_at": datetime.now(),
            "created_at": datetime.now(),
            "territory_id": "3550308",
            "processed": False,
            "state_code": "SC",
            "territory_name": "Gaspar",
        }
        self.search_engine = opensearch.Opensearch(hosts=["127.0.0.1"])

    def clean_index(self, index):
        self.search_engine.delete_by_query(
            index=index, body={"query": {"match_all": {}}}, timeout="5m"
        )
        self.search_engine.indices.refresh(index="querido-diario")

    def delete_index(self, index):
        self.search_engine.indices.delete(
            index="querido-diario", timeout="2m", ignore_unavailable=True
        )
        self.assertFalse(self.search_engine.indices.exists("querido-diario"))

    def test_index_creation(self):
        self.delete_index("querido-diario")

        interface = OpenSearchInterface(["127.0.0.1"], timeout="5m")
        interface.create_index("querido-diario")
        self.assertTrue(self.search_engine.indices.exists("querido-diario"))

    def test_index_document(self):
        self.clean_index("querido-diario")
        interface = OpenSearchInterface(["127.0.0.1"])
        interface.index_document(self.fake_document, "querido-diario")
        self.search_engine.indices.refresh(index="querido-diario")

        self.assertEqual(self.search_engine.count(index="querido-diario")["count"], 1)
        self.assertTrue(
            self.search_engine.exists(
                id=self.fake_document["file_checksum"], index="querido-diario"
            )
        )
        indexed_document = self.search_engine.get(
            index="querido-diario", id=self.fake_document["file_checksum"]
        )
        self.fake_document["date"] = self.fake_document["date"].strftime("%Y-%m-%d")
        self.fake_document["scraped_at"] = self.fake_document["scraped_at"].isoformat()
        self.fake_document["created_at"] = self.fake_document["created_at"].isoformat()
        self.assertEqual(indexed_document["_source"], self.fake_document)

    def test_index_document_twice(self):
        self.clean_index("querido-diario")
        interface = OpenSearchInterface(["127.0.0.1"])
        interface.index_document(self.fake_document, "querido-diario")
        interface.index_document(self.fake_document, "querido-diario")
        self.search_engine.indices.refresh(index="querido-diario")

        self.assertEqual(self.search_engine.count(index="querido-diario")["count"], 1)
        self.assertTrue(
            self.search_engine.exists(
                id=self.fake_document["file_checksum"], index="querido-diario"
            )
        )
        indexed_document = self.search_engine.get(
            index="querido-diario", id=self.fake_document["file_checksum"]
        )
        self.fake_document["date"] = self.fake_document["date"].strftime("%Y-%m-%d")
        self.fake_document["scraped_at"] = self.fake_document["scraped_at"].isoformat()
        self.fake_document["created_at"] = self.fake_document["created_at"].isoformat()
        self.assertEqual(indexed_document["_source"], self.fake_document)
