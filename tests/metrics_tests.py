from datetime import datetime, timedelta, timezone
from unittest import TestCase
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from data_extraction import UnsupportedFileTypeError
from monitoring.metrics import (
    REGISTRY,
    observe_gazette_processing,
    push_metrics_if_configured,
)
from tasks.gazette_text_extraction import extract_text_from_gazettes


def sample(name, **labels):
    return REGISTRY.get_sample_value(name, labels) or 0


class GazetteProcessingMetricsTests(TestCase):
    def processed(self, status, mode="cron"):
        return sample("qd_gazettes_processed_total", mode=mode, status=status)

    def latency_count(self, mode="cron"):
        return sample("qd_scrape_to_index_seconds_count", mode=mode)

    def latency_bucket(self, le, mode="cron"):
        return sample("qd_scrape_to_index_seconds_bucket", mode=mode, le=le)

    def duration_count(self, mode="cron"):
        return sample("qd_gazette_processing_seconds_count", mode=mode)

    @patch.dict("os.environ", {}, clear=True)
    def test_success_counts_ok_and_observes_latencies(self):
        ok, latency, duration = (
            self.processed("ok"),
            self.latency_count(),
            self.duration_count(),
        )
        up_to_30min, up_to_1h = self.latency_bucket("1800.0"), self.latency_bucket(
            "3600.0"
        )
        # scraped_at vem do banco em UTC, sem fuso
        scraped_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
            minutes=50
        )

        with observe_gazette_processing({"scraped_at": scraped_at}):
            pass

        self.assertEqual(self.processed("ok"), ok + 1)
        self.assertEqual(self.latency_count(), latency + 1)
        self.assertEqual(self.duration_count(), duration + 1)
        # 50 min cai no bucket de 1h, mas não no de 30 min
        self.assertEqual(self.latency_bucket("1800.0"), up_to_30min)
        self.assertEqual(self.latency_bucket("3600.0"), up_to_1h + 1)

    @patch.dict("os.environ", {"PIPELINE_MODE": "queue"})
    def test_mode_comes_from_environment(self):
        ok = self.processed("ok", mode="queue")

        with observe_gazette_processing({"scraped_at": datetime.now(timezone.utc)}):
            pass

        self.assertEqual(self.processed("ok", mode="queue"), ok + 1)

    @patch.dict("os.environ", {}, clear=True)
    def test_unsupported_file_counts_unsupported_without_latency(self):
        unsupported, latency = self.processed("unsupported"), self.latency_count()

        with self.assertRaises(UnsupportedFileTypeError):
            with observe_gazette_processing({"scraped_at": datetime.now()}):
                raise UnsupportedFileTypeError("application/zip")

        self.assertEqual(self.processed("unsupported"), unsupported + 1)
        self.assertEqual(self.latency_count(), latency)

    @patch.dict("os.environ", {}, clear=True)
    def test_failure_counts_error_without_latency(self):
        error, latency = self.processed("error"), self.latency_count()

        with self.assertRaises(RuntimeError):
            with observe_gazette_processing({"scraped_at": datetime.now()}):
                raise RuntimeError("boom")

        self.assertEqual(self.processed("error"), error + 1)
        self.assertEqual(self.latency_count(), latency)

    @patch.dict(
        "os.environ", {"QUERIDO_DIARIO_FILES_ENDPOINT": "http://test.com"}, clear=True
    )
    def test_missing_file_in_storage_counts_as_error(self):
        error, ok = self.processed("error"), self.processed("ok")
        storage = MagicMock()
        storage.get_file.side_effect = ClientError(
            {"Error": {"Code": "404"}}, "GetObject"
        )
        gazette = {
            "id": 1,
            "file_path": "sc_gaspar/2020-10-18/abc.pdf",
            "file_checksum": "abc",
            "scraped_at": datetime.now(),
        }

        ids = extract_text_from_gazettes(
            [gazette], [], MagicMock(), storage, MagicMock(), MagicMock()
        )

        self.assertEqual(ids, [])
        self.assertEqual(self.processed("error"), error + 1)
        self.assertEqual(self.processed("ok"), ok)


class PushgatewayTests(TestCase):
    @patch.dict("os.environ", {}, clear=True)
    @patch("monitoring.metrics.push_to_gateway")
    def test_does_not_push_without_url(self, push):
        self.assertFalse(push_metrics_if_configured())
        push.assert_not_called()

    @patch.dict("os.environ", {"PUSHGATEWAY_URL": "pushgateway:9091"})
    @patch("monitoring.metrics.push_to_gateway")
    def test_pushes_application_registry(self, push):
        self.assertTrue(push_metrics_if_configured())
        push.assert_called_once_with(
            "pushgateway:9091", job="data-processing", registry=REGISTRY
        )

    @patch.dict("os.environ", {"PUSHGATEWAY_URL": "pushgateway:9091"})
    @patch("monitoring.metrics.push_to_gateway", side_effect=OSError("refused"))
    def test_push_failure_does_not_raise(self, push):
        with self.assertLogs(level="WARNING"):
            self.assertFalse(push_metrics_if_configured())
