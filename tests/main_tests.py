import os
import logging
from unittest import TestCase, expectedFailure
from unittest.mock import patch

from main import enable_debug_if_necessary, start_to_process_pending_gazettes


class MainModuleTests(TestCase):
    def check_if_some_log_message_has_text(self, text, logs):
        has_text = False
        for log in logs:
            if text in log:
                has_text = True
                break
        return has_text

    @patch.dict(
        "os.environ",
        {
            "DEBUG": "1",
        },
    )
    def test_run_with_debug_enabled(self):
        with self.assertLogs(level=logging.DEBUG) as logs:
            enable_debug_if_necessary()
            has_expected_text = self.check_if_some_log_message_has_text(
                "Debug enabled", logs.output
            )
            self.assertTrue(has_expected_text)

    @patch.dict(
        "os.environ",
        {"DEBUG": "0"},
    )
    def test_run_with_debug_disabled(self):
        with patch("logging.debug") as mock:
            enable_debug_if_necessary()
            mock.assert_not_called()

    def test_run_with_debug_not_defined(self):
        with patch("logging.debug") as mock:
            enable_debug_if_necessary()
            mock.assert_not_called()
