from unittest import TestCase
from unittest.mock import MagicMock

from tasks.create_index import create_gazettes_index


class CreateIndexTaskTests(TestCase):
    def test_gazettes_index_maps_raw_text_file_as_keyword(self):
        index = MagicMock()

        create_gazettes_index(index)

        body = index.create_index.call_args.kwargs["body"]
        properties = body["mappings"]["properties"]

        self.assertEqual(properties["file_raw_txt"], {"type": "keyword"})
