import unittest
from unittest.mock import MagicMock, patch

import pyoaev.utils as module


class TestUtils(unittest.TestCase):
    def test_get_content_type(self):
        self.assertEqual(
            module.get_content_type("application/json; charset=utf-8"),
            "application/json",
        )

    def test_response_content_returns_iterator_when_requested(self):
        response = MagicMock()
        response.iter_content.return_value = iter([b"a", b"b"])

        iterator = module.response_content(
            response,
            streamed=False,
            action=None,
            chunk_size=10,
            iterator=True,
        )

        self.assertEqual(list(iterator), [b"a", b"b"])

    def test_response_content_returns_raw_content_when_not_streamed(self):
        response = MagicMock()
        response.content = b"payload"

        data = module.response_content(
            response,
            streamed=False,
            action=None,
            chunk_size=10,
            iterator=False,
        )

        self.assertEqual(data, b"payload")

    def test_response_content_streamed_uses_action_for_non_empty_chunks(self):
        response = MagicMock()
        response.iter_content.return_value = [b"one", b"", b"two"]
        action = MagicMock()

        returned = module.response_content(
            response,
            streamed=True,
            action=action,
            chunk_size=10,
            iterator=False,
        )

        self.assertIsNone(returned)
        action.assert_any_call(b"one")
        action.assert_any_call(b"two")
        self.assertEqual(action.call_count, 2)

    def test_response_content_streamed_defaults_to_stdout_stream(self):
        response = MagicMock()
        response.iter_content.return_value = [b"visible"]

        with patch("builtins.print") as mock_print:
            module.response_content(
                response,
                streamed=True,
                action=None,
                chunk_size=10,
                iterator=False,
            )

        mock_print.assert_called_once_with(b"visible")

    def test_pingalive_ping_uses_injector_branch(self):
        api = MagicMock()
        logger = MagicMock()
        ping_alive = module.PingAlive(
            api=api, config={"id": 1}, logger=logger, ping_type="injector"
        )
        ping_alive.exit_event.is_set = MagicMock(side_effect=[False, True])
        ping_alive.exit_event.wait = MagicMock()

        ping_alive.ping()

        api.injector.create.assert_called_once_with({"id": 1}, False)
        ping_alive.exit_event.wait.assert_called_once_with(40)

    def test_pingalive_ping_uses_collector_branch_and_logs_errors(self):
        api = MagicMock()
        api.collector.create.side_effect = Exception("boom")
        logger = MagicMock()
        ping_alive = module.PingAlive(
            api=api, config={}, logger=logger, ping_type="collector"
        )
        ping_alive.exit_event.is_set = MagicMock(side_effect=[False, True])
        ping_alive.exit_event.wait = MagicMock()

        ping_alive.ping()

        logger.error.assert_called_once()
        ping_alive.exit_event.wait.assert_called_once_with(40)

    def test_pingalive_run_and_stop(self):
        ping_alive = module.PingAlive(
            api=MagicMock(), config={}, logger=MagicMock(), ping_type="collector"
        )
        ping_alive.ping = MagicMock()

        ping_alive.run()
        ping_alive.stop()

        ping_alive.logger.info.assert_any_call(
            "Starting PingAlive thread", {"tenant_id": str(ping_alive.tenant_id)}
        )
        ping_alive.logger.info.assert_any_call(
            "Preparing PingAlive for clean shutdown",
            {"tenant_id": str(ping_alive.tenant_id)},
        )
        self.assertTrue(ping_alive.exit_event.is_set())


if __name__ == "__main__":
    unittest.main()
