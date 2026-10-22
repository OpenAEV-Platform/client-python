"""Tests for the PingAlive heartbeat thread."""

import unittest
from unittest.mock import MagicMock

import xtm_oaev_sdk as sdk


class TestPingAlive(unittest.TestCase):
    def _given_ping(self, ping_type: str, api=None, config=None) -> sdk.PingAlive:
        ping = sdk.PingAlive(
            api=api or MagicMock(),
            config=config if config is not None else {},
            logger=MagicMock(),
            ping_type=ping_type,
        )
        ping.exit_event.is_set = MagicMock(side_effect=[False, True])
        ping.exit_event.wait = MagicMock()
        return ping

    def test_injector_ping_registers_the_injector_every_40_seconds(self):
        api = MagicMock()
        ping = self._given_ping("injector", api=api, config={"id": 1})

        ping.ping()

        api.injector.create.assert_called_once_with({"id": 1}, False)
        ping.exit_event.wait.assert_called_once_with(40)

    def test_collector_ping_logs_api_errors_and_keeps_going(self):
        api = MagicMock()
        api.collector.create.side_effect = Exception("boom")
        ping = self._given_ping("collector", api=api)

        ping.ping()

        ping.logger.error.assert_called_once()
        ping.exit_event.wait.assert_called_once_with(40)

    def test_tenant_id_comes_from_the_client(self):
        api = MagicMock()
        api.tenant_id = "tenant-1"

        ping = sdk.PingAlive(api=api, config={}, logger=MagicMock(), ping_type="x")

        self.assertEqual(ping.tenant_id, "tenant-1")

    def test_stop_sets_the_exit_event(self):
        ping = sdk.PingAlive(
            api=MagicMock(), config={}, logger=MagicMock(), ping_type="collector"
        )

        ping.stop()

        self.assertTrue(ping.exit_event.is_set())


if __name__ == "__main__":
    unittest.main()
