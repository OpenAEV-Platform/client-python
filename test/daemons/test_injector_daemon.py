import unittest
from unittest.mock import MagicMock, patch

from pyoaev.configuration import Configuration
from pyoaev.daemons import InjectorDaemon
from xtm_oaev_sdk import DaemonProtocol


class TestInjectorDaemonProtocol(unittest.TestCase):
    def test_injector_daemon_is_subclass_of_base_daemon(self):
        from pyoaev.daemons import BaseDaemon

        self.assertTrue(issubclass(InjectorDaemon, BaseDaemon))

    def test_injector_daemon_structurally_satisfies_daemon_protocol(self):
        self.assertTrue(issubclass(InjectorDaemon, DaemonProtocol))

    def test_injector_daemon_instance_satisfies_daemon_protocol(self):
        config = Configuration(
            config_hints={
                "openaev_url": {"data": "fake"},
                "openaev_token": {"data": "fake"},
            }
        )
        mock_api = MagicMock()
        daemon = InjectorDaemon(
            configuration=config,
            callback=lambda: None,
            api_client=mock_api,
        )
        self.assertIsInstance(daemon, DaemonProtocol)


class TestInjectorDaemonSetup(unittest.TestCase):
    @patch("pyoaev.utils.PingAlive.start")
    @patch("pyoaev.apis.InjectorManager.create")
    def test_setup_builds_config_dict_and_creates_injector(
        self,
        mock_injector_create,
        mock_ping_start,
    ):
        mock_injector_create.return_value = {"connection": {}, "listen": "q1"}
        mock_ping_start.return_value = None

        config = Configuration(
            config_hints={
                "openaev_url": {"data": "fake"},
                "openaev_token": {"data": "fake"},
                "injector_id": {"data": "test-id"},
                "injector_name": {"data": "test-injector"},
                "injector_type": {"data": "test-type"},
                "injector_contracts": {"data": "[]"},
            }
        )
        icon = MagicMock()
        daemon = InjectorDaemon(
            configuration=config,
            callback=lambda: None,
            icon=icon,
        )
        daemon._setup()

        self.assertEqual(daemon.config["injector_id"], "test-id")
        self.assertEqual(daemon.config["injector_name"], "test-injector")
        self.assertEqual(daemon.config["injector_type"], "test-type")
        self.assertIsNotNone(daemon.injector_config)
        mock_injector_create.assert_called_once()
        mock_ping_start.assert_called_once()

    @patch("pyoaev.utils.PingAlive.start")
    @patch("pyoaev.apis.InjectorManager.create")
    def test_setup_stores_ping_instance(
        self,
        mock_injector_create,
        mock_ping_start,
    ):
        mock_injector_create.return_value = {"connection": {}, "listen": "q1"}
        mock_ping_start.return_value = None

        config = Configuration(
            config_hints={
                "openaev_url": {"data": "fake"},
                "openaev_token": {"data": "fake"},
                "injector_id": {"data": "test-id"},
                "injector_name": {"data": "test-injector"},
                "injector_type": {"data": "test-type"},
            }
        )
        daemon = InjectorDaemon(
            configuration=config,
            callback=lambda: None,
            icon=MagicMock(),
        )
        daemon._setup()

        self.assertIsNotNone(daemon.ping)

    @patch("pyoaev.utils.PingAlive.start")
    @patch("pyoaev.apis.InjectorManager.create")
    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data=b"png")
    def test_setup_reads_icon_from_config_when_no_icon_handle(
        self,
        mock_open_file,
        mock_injector_create,
        mock_ping_start,
    ):
        mock_injector_create.return_value = {"connection": {}, "listen": "q1"}
        mock_ping_start.return_value = None

        config = Configuration(
            config_hints={
                "openaev_url": {"data": "fake"},
                "openaev_token": {"data": "fake"},
                "injector_id": {"data": "test-id"},
                "injector_name": {"data": "test-injector"},
                "injector_type": {"data": "test-type"},
                "injector_icon_filepath": {"data": "/path/to/icon.png"},
            }
        )
        daemon = InjectorDaemon(
            configuration=config,
            callback=lambda: None,
            # icon=None (default) — reads from config
        )
        daemon._setup()

        mock_open_file.assert_called_once_with("/path/to/icon.png", "rb")
        mock_injector_create.assert_called_once()


class TestInjectorDaemonStartLoop(unittest.TestCase):
    @patch("pyoaev.helpers.ListenQueue")
    def test_start_loop_creates_and_starts_listen_queue(self, mock_listen_queue_cls):
        mock_queue_instance = MagicMock()
        mock_listen_queue_cls.return_value = mock_queue_instance

        config = Configuration(
            config_hints={
                "openaev_url": {"data": "fake"},
                "openaev_token": {"data": "fake"},
            }
        )
        def callback(data):
            pass

        mock_api = MagicMock()
        daemon = InjectorDaemon(
            configuration=config,
            callback=callback,
            api_client=mock_api,
        )
        daemon.config = {"injector_id": "test"}
        daemon.injector_config = {"connection": {}, "listen": "q1"}

        daemon._start_loop()

        mock_listen_queue_cls.assert_called_once_with(
            daemon.config, daemon.injector_config, daemon.logger, callback
        )
        mock_queue_instance.start.assert_called_once()
        self.assertEqual(daemon.listen_queue, mock_queue_instance)


class TestDeprecatedInjectorHelper(unittest.TestCase):
    @patch("pyoaev.utils.PingAlive.start")
    @patch("pyoaev.apis.InjectorManager.create")
    def test_helper_emits_deprecation_warning(
        self,
        mock_injector_create,
        mock_ping_start,
    ):
        import warnings

        from pyoaev.helpers import OpenAEVConfigHelper, OpenAEVInjectorHelper

        mock_injector_create.return_value = {"connection": {}, "listen": "q1"}
        mock_ping_start.return_value = None

        config_obj = Configuration(
            config_hints={
                "openaev_url": {"data": "fake"},
                "openaev_token": {"data": "fake"},
                "injector_id": {"data": "test-id"},
                "injector_name": {"data": "test"},
                "injector_type": {"data": "test-type"},
                "injector_log_level": {"data": "error"},
            }
        )
        config = OpenAEVConfigHelper.from_configuration_object(config_obj)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            OpenAEVInjectorHelper(config, MagicMock())
            deprecation_warnings = [
                x for x in w if issubclass(x.category, DeprecationWarning)
            ]
            self.assertGreater(len(deprecation_warnings), 0)

    @patch("pyoaev.utils.PingAlive.start")
    @patch("pyoaev.apis.InjectorManager.create")
    def test_helper_exposes_legacy_attributes(
        self,
        mock_injector_create,
        mock_ping_start,
    ):
        import warnings

        from pyoaev.helpers import OpenAEVConfigHelper, OpenAEVInjectorHelper

        mock_injector_create.return_value = {"connection": {}, "listen": "q1"}
        mock_ping_start.return_value = None

        config_obj = Configuration(
            config_hints={
                "openaev_url": {"data": "fake"},
                "openaev_token": {"data": "fake"},
                "injector_id": {"data": "test-id"},
                "injector_name": {"data": "test"},
                "injector_type": {"data": "test-type"},
                "injector_log_level": {"data": "error"},
            }
        )
        config = OpenAEVConfigHelper.from_configuration_object(config_obj)

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            helper = OpenAEVInjectorHelper(config, MagicMock())

        self.assertIsNotNone(helper.api)
        self.assertIsNotNone(helper.injector_logger)
        self.assertIsInstance(helper.config, dict)
        self.assertIn("injector_id", helper.config)
        self.assertIsNotNone(helper.injector_config)
        self.assertIsNotNone(helper.ping)

    @patch("pyoaev.helpers.ListenQueue")
    @patch("pyoaev.utils.PingAlive.start")
    @patch("pyoaev.apis.InjectorManager.create")
    def test_helper_listen_starts_queue(
        self,
        mock_injector_create,
        mock_ping_start,
        mock_listen_queue_cls,
    ):
        import warnings

        from pyoaev.helpers import OpenAEVConfigHelper, OpenAEVInjectorHelper

        mock_injector_create.return_value = {"connection": {}, "listen": "q1"}
        mock_ping_start.return_value = None
        mock_queue = MagicMock()
        mock_listen_queue_cls.return_value = mock_queue

        config_obj = Configuration(
            config_hints={
                "openaev_url": {"data": "fake"},
                "openaev_token": {"data": "fake"},
                "injector_id": {"data": "test-id"},
                "injector_name": {"data": "test"},
                "injector_type": {"data": "test-type"},
                "injector_log_level": {"data": "error"},
            }
        )
        config = OpenAEVConfigHelper.from_configuration_object(config_obj)

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            helper = OpenAEVInjectorHelper(config, MagicMock())

        def callback(data):
            pass

        helper.listen(callback)

        mock_listen_queue_cls.assert_called_once()
        mock_queue.start.assert_called_once()


if __name__ == "__main__":
    unittest.main()
