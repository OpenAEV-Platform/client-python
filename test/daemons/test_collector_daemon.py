import unittest
from unittest.mock import mock_open, patch

from pyoaev.configuration import Configuration
from pyoaev.daemons import CollectorDaemon
from pyoaev.daemons.collector_daemon import (
    DEFAULT_PERIOD_SECONDS,
    DEFAULT_PLATFORM_TAG_COLOR,
)


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

    @patch("pyoaev.apis.SecurityPlatformManager.upsert")
    @patch("pyoaev.apis.TagManager.upsert")
    @patch("pyoaev.apis.DocumentManager.upsert")
    @patch("pyoaev.apis.CollectorManager.create")
    @patch("builtins.open", new_callable=mock_open, read_data="data")
    @patch("pyoaev.utils.PingAlive.start")
    def test_security_platform_upsert_carries_description_and_tags(
        self,
        mock_ping_alive,
        mock_open_local,
        mock_collector_create,
        mock_document_upsert,
        mock_tag_upsert,
        mock_security_platform_upsert,
    ):
        mock_ping_alive.return_value = None
        mock_collector_create.return_value = {}
        mock_document_upsert.return_value = {"document_id": "doc id"}
        mock_tag_upsert.side_effect = [{"tag_id": "tag-1"}, {"tag_id": "tag-2"}]
        mock_security_platform_upsert.return_value = {"asset_id": "sp id"}
        config = Configuration(
            config_hints={
                "openaev_url": {"data": "fake"},
                "openaev_token": {"data": "fake"},
                "collector_id": {"data": "fake id"},
                "collector_name": {"data": "Fake EDR"},
                "collector_platform": {"data": "EDR"},
                "collector_platform_description": {"data": "A fake EDR platform."},
                # Padded name: list values must be stripped like string ones.
                "collector_platform_tags": {"data": ["edr", " fake-vendor "]},
            }
        )
        collector = CollectorDaemon(configuration=config, collector_type="test")

        collector._setup()

        payload = mock_security_platform_upsert.call_args.args[0]
        self.assertEqual(payload["asset_description"], "A fake EDR platform.")
        self.assertEqual(payload["asset_tags"], ["tag-1", "tag-2"])
        self.assertEqual(mock_tag_upsert.call_count, 2)
        self.assertEqual(mock_tag_upsert.call_args_list[0].args[0]["tag_name"], "edr")
        self.assertEqual(
            mock_tag_upsert.call_args_list[1].args[0]["tag_name"], "fake-vendor"
        )
        self.assertEqual(
            mock_tag_upsert.call_args_list[0].args[0]["tag_color"],
            DEFAULT_PLATFORM_TAG_COLOR,
        )

    @patch("pyoaev.apis.SecurityPlatformManager.upsert")
    @patch("pyoaev.apis.TagManager.upsert")
    @patch("pyoaev.apis.DocumentManager.upsert")
    @patch("pyoaev.apis.CollectorManager.create")
    @patch("builtins.open", new_callable=mock_open, read_data="data")
    @patch("pyoaev.utils.PingAlive.start")
    def test_security_platform_tags_accept_comma_separated_string(
        self,
        mock_ping_alive,
        mock_open_local,
        mock_collector_create,
        mock_document_upsert,
        mock_tag_upsert,
        mock_security_platform_upsert,
    ):
        mock_ping_alive.return_value = None
        mock_collector_create.return_value = {}
        mock_document_upsert.return_value = {"document_id": "doc id"}
        mock_tag_upsert.side_effect = [{"tag_id": "tag-1"}, {"tag_id": "tag-2"}]
        mock_security_platform_upsert.return_value = {"asset_id": "sp id"}
        config = Configuration(
            config_hints={
                "openaev_url": {"data": "fake"},
                "openaev_token": {"data": "fake"},
                "collector_id": {"data": "fake id"},
                "collector_name": {"data": "Fake SIEM"},
                "collector_platform": {"data": "SIEM"},
                "collector_platform_tags": {"data": "siem, fake-vendor"},
            }
        )
        collector = CollectorDaemon(configuration=config, collector_type="test")

        collector._setup()

        payload = mock_security_platform_upsert.call_args.args[0]
        self.assertNotIn("asset_description", payload)
        self.assertEqual(payload["asset_tags"], ["tag-1", "tag-2"])

    @patch("pyoaev.apis.SecurityPlatformManager.upsert")
    @patch("pyoaev.apis.TagManager.upsert")
    @patch("pyoaev.apis.DocumentManager.upsert")
    @patch("pyoaev.apis.CollectorManager.create")
    @patch("builtins.open", new_callable=mock_open, read_data="data")
    @patch("pyoaev.utils.PingAlive.start")
    def test_security_platform_upsert_without_description_and_tags_is_unchanged(
        self,
        mock_ping_alive,
        mock_open_local,
        mock_collector_create,
        mock_document_upsert,
        mock_tag_upsert,
        mock_security_platform_upsert,
    ):
        mock_ping_alive.return_value = None
        mock_collector_create.return_value = {}
        mock_document_upsert.return_value = {"document_id": "doc id"}
        mock_security_platform_upsert.return_value = {"asset_id": "sp id"}
        config = Configuration(
            config_hints={
                "openaev_url": {"data": "fake"},
                "openaev_token": {"data": "fake"},
                "collector_id": {"data": "fake id"},
                "collector_name": {"data": "Fake XDR"},
                "collector_platform": {"data": "XDR"},
            }
        )
        collector = CollectorDaemon(configuration=config, collector_type="test")

        collector._setup()

        payload = mock_security_platform_upsert.call_args.args[0]
        self.assertNotIn("asset_description", payload)
        self.assertNotIn("asset_tags", payload)
        mock_tag_upsert.assert_not_called()


if __name__ == "__main__":
    unittest.main()
