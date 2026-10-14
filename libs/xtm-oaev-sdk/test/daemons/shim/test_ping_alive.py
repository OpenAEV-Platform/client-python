import unittest
from unittest.mock import MagicMock

import pyoaev.utils as module


class TestPingAlive(unittest.TestCase):
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
