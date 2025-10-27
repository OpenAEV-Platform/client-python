import unittest
from unittest.mock import mock_open, patch

from pyoaev.configuration import Configuration
from pyoaev.daemons import CollectorDaemon
from pyoaev.daemons.collector_daemon import DEFAULT_PERIOD_SECONDS


class TestCollectorDaemon(unittest.TestCase):
    @patch("pyoaev.apis.DocumentManager.upsert")
    @patch("pyoaev.apis.CollectorManager.create")
    @patch("builtins.open", new_callable=mock_open, read_data="data")
    @patch("pyoaev.utils.PingAlive.start")
    def test_when_no_period_config_provided_set_default_period(
        self,
        mock_ping_alive,
        mock_open_local,
        mock_collector_create,
        mock_document_upsert,
    ):
        mock_ping_alive.return_value = None
        mock_collector_create.return_value = {}
        mock_document_upsert.return_value = {}
        config = Configuration(
            config_hints={
                "openaev_url": {"data": "fake"},
                "openaev_token": {"data": "fake"},
                "collector_id": {"data": "fake id"},
            }
        )
        collector = CollectorDaemon(configuration=config, collector_type="test")

        collector._setup()

        self.assertEqual(config.get("collector_period"), DEFAULT_PERIOD_SECONDS)


if __name__ == "__main__":
    unittest.main()
