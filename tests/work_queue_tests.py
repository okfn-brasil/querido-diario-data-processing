import os
from datetime import date, datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch

import fakeredis
import psycopg2
from requests.exceptions import ConnectionError as RequestsConnectionError

# celery_app lê o broker ao ser importado; nos testes o Redis é o fakeredis
os.environ.setdefault("QUEUE_BROKER_URL", "redis://localhost:6379/0")

from data_extraction import TextExtractorInterface, UnsupportedFileTypeError
from main.__main__ import enqueue_extraction_pipeline, themes_from_queue_pipeline
from work_queue import redis_keys, tasks
from work_queue.celery_app import app

CHECKSUM = "972aca2e-1174-11eb-b2d5-a86daaca905e"


def gazette_data(processed=False):
    return {
        "id": 1,
        "source_text": "",
        "date": date(2026, 10, 9),
        "edition_number": "26827",
        "is_extra_edition": False,
        "power": "executive",
        "file_checksum": CHECKSUM,
        "file_path": f"3299999/2026-10-09/{CHECKSUM}.pdf",
        "file_url": "https://ioes.dio.es.gov.br/portal/edicoes/download/11542",
        "scraped_at": datetime.now(),
        "created_at": datetime.now(),
        "territory_id": "3299999",
        "processed": processed,
        "territory_name": "Governo do Estado do Espírito Santo",
        "state_code": "ES",
    }


class FakeIndex:
    """Índice em memória: indexar com o mesmo document_id sobrescreve"""

    def __init__(self):
        self.documents = {}

    def index_document(self, document, document_id=None, refresh=False):
        self.documents[document_id] = document


@patch.dict("os.environ", {"QUERIDO_DIARIO_FILES_ENDPOINT": "http://test.com"})
class WorkQueueTaskTests(TestCase):
    def setUp(self):
        app.conf.task_always_eager = True
        self.redis = fakeredis.FakeRedis(decode_responses=True)
        patcher = patch.object(redis_keys, "_client", self.redis)
        patcher.start()
        self.addCleanup(patcher.stop)

        self.database = MagicMock()
        self.index = FakeIndex()
        self.text_extractor = MagicMock(spec=TextExtractorInterface)
        self.text_extractor.extract_text.return_value = "decreto"
        self.text_extractor.is_zip.return_value = False
        self.storage = MagicMock()
        tasks.deps.clear()
        tasks.deps.update(
            database=self.database,
            storage=self.storage,
            index=self.index,
            text_extractor=self.text_extractor,
            territories=[],
        )
        self.addCleanup(tasks.deps.clear)

        self.gazette = gazette_data()
        patcher = patch.object(
            tasks, "get_gazette_by_id", side_effect=lambda *_: dict(self.gazette)
        )
        self.get_gazette_by_id = patcher.start()
        self.addCleanup(patcher.stop)

    def dead_letters(self):
        return self.redis.llen(redis_keys.DEAD_LETTER_KEY)

    def enqueued_key(self):
        return redis_keys.ENQUEUED_KEY.format(1)

    @patch("main.__main__.run_task")
    @patch("main.__main__.create_index_interface")
    @patch("main.__main__.create_database_interface")
    def test_enqueue_same_gazette_twice_sends_one_message(self, _db, _index, run_task):
        run_task.side_effect = lambda name, *_: (
            [gazette_data()] if name == "get_gazettes_to_be_processed" else None
        )
        with patch.object(tasks.extract_gazette, "delay") as delay:
            enqueue_extraction_pipeline()
            enqueue_extraction_pipeline()
        delay.assert_called_once_with(1)

    def test_process_same_gazette_twice_indexes_one_document(self):
        # Reentrega da mensagem antes de o diário ser marcado como processado
        tasks.extract_gazette.apply(args=(1,)).get()
        tasks.extract_gazette.apply(args=(1,)).get()
        self.assertEqual(self.text_extractor.extract_text.call_count, 2)
        self.assertEqual(list(self.index.documents), [CHECKSUM])
        self.assertEqual(self.dead_letters(), 0)

    def test_processed_gazette_does_not_call_tika(self):
        self.gazette["processed"] = True
        self.redis.set(self.enqueued_key(), 1)
        tasks.extract_gazette.apply(args=(1,)).get()
        self.text_extractor.extract_text.assert_not_called()
        self.assertEqual(self.index.documents, {})
        self.assertFalse(self.redis.exists(self.enqueued_key()))

    def test_unsupported_file_goes_to_dlq_without_retry(self):
        with patch.object(
            tasks,
            "try_process_gazette_file",
            side_effect=UnsupportedFileTypeError("application/zip"),
        ) as process:
            tasks.extract_gazette.apply(args=(1,))
        process.assert_called_once()
        self.assertEqual(self.dead_letters(), 1)
        self.assertIn("unsupported", self.redis.lindex(redis_keys.DEAD_LETTER_KEY, 0))
        # Sem TTL: o produtor não reenfileira o diário enquanto ele estiver na DLQ
        self.assertEqual(self.redis.ttl(self.enqueued_key()), -1)

    def test_transient_error_retries_then_goes_to_dlq(self):
        with patch.object(
            tasks,
            "try_process_gazette_file",
            side_effect=RequestsConnectionError("Tika indisponível"),
        ) as process:
            tasks.extract_gazette.apply(args=(1,))
        # 1 tentativa + max_retries (5)
        self.assertEqual(process.call_count, 6)
        self.assertEqual(self.dead_letters(), 1)

    def test_success_marks_checksums_for_themes(self):
        tasks.extract_gazette.apply(args=(1,)).get()
        self.assertEqual(self.redis.smembers(redis_keys.THEMES_PENDING_KEY), {CHECKSUM})
        self.assertFalse(self.redis.exists(self.enqueued_key()))

    def test_lost_database_connection_is_reopened_and_retried(self):
        broken = MagicMock()
        healthy = MagicMock()
        tasks.deps["database"] = broken
        self.get_gazette_by_id.side_effect = lambda database, _: (
            (_ for _ in ()).throw(psycopg2.OperationalError("server closed"))
            if database is broken
            else dict(self.gazette)
        )
        with patch.object(tasks, "create_database_interface", return_value=healthy):
            tasks.extract_gazette.apply(args=(1,)).get()
        broken.close.assert_called_once()
        self.assertIs(tasks.deps["database"], healthy)
        self.assertEqual(list(self.index.documents), [CHECKSUM])
        self.assertEqual(self.dead_letters(), 0)

    def test_aborted_transaction_discards_connection(self):
        self.get_gazette_by_id.side_effect = psycopg2.errors.InFailedSqlTransaction(
            "current transaction is aborted"
        )
        tasks.extract_gazette.apply(args=(1,))
        self.database.close.assert_called_once()
        self.assertNotIn("database", tasks.deps)
        self.assertEqual(self.dead_letters(), 1)


@patch("main.__main__.create_index_interface")
class ThemesFromQueueTests(TestCase):
    def setUp(self):
        self.redis = fakeredis.FakeRedis(decode_responses=True)
        patcher = patch.object(redis_keys, "_client", self.redis)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.redis.sadd(redis_keys.THEMES_PENDING_KEY, "a", "b")

    def pending(self):
        return self.redis.smembers(redis_keys.THEMES_PENDING_KEY)

    @patch("main.__main__.run_task")
    def test_batch_is_removed_after_all_themes(self, run_task, _index):
        run_task.side_effect = lambda name, *_: (
            [{"index": "educacao"}] if name == "get_themes" else []
        )
        themes_from_queue_pipeline()
        self.assertEqual(self.pending(), set())

    @patch("main.__main__.run_task")
    def test_batch_stays_pending_when_themes_fail(self, run_task, _index):
        def fail_on_rerank(name, *_):
            if name == "get_themes":
                return [{"index": "educacao"}]
            if name == "embedding_rerank_excerpts":
                raise MemoryError("BERT")
            return []

        run_task.side_effect = fail_on_rerank
        with self.assertRaises(MemoryError):
            themes_from_queue_pipeline()
        self.assertEqual(self.pending(), {"a", "b"})
