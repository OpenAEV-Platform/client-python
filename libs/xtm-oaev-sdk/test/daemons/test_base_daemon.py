"""Tests for the SDK BaseDaemon (API client injected)."""

import unittest
import unittest.mock

import xtm_oaev_sdk as sdk

TEST_DAEMON_CONFIGURATION = sdk.Configuration(
    config_hints={
        "log_level": {"data": "info"},
        "name": {"data": "my test daemon"},
        "collector_id": {"data": "collector-id"},
    }
)


class DaemonForTest(sdk.BaseDaemon):
    def _setup(self):
        pass

    def _start_loop(self):
        pass


def create_mock_daemon(callback: callable = None):
    mock_setup = unittest.mock.MagicMock()
    mock_start_loop = unittest.mock.MagicMock()
    inner_mock_func = unittest.mock.MagicMock()

    class MockDaemon(sdk.BaseDaemon):
        def _setup(self):
            mock_setup()

        def _start_loop(self):
            mock_start_loop()

        def bound_method(self):
            inner_mock_func()

    return (
        MockDaemon(
            configuration=TEST_DAEMON_CONFIGURATION,
            callback=callback,
            logger=unittest.mock.MagicMock(),
            api_client=unittest.mock.MagicMock(),
        ),
        mock_setup,
        mock_start_loop,
        inner_mock_func,
    )


@unittest.mock.patch("argparse.ArgumentParser")
class TestBaseDaemon(unittest.TestCase):
    def test_injected_api_client_is_used(self, _):
        client = unittest.mock.MagicMock()
        daemon = DaemonForTest(
            configuration=TEST_DAEMON_CONFIGURATION, api_client=client
        )

        self.assertIs(daemon.api, client)

    def test_without_api_client_ctor_raises(self, _):
        with self.assertRaises(sdk.OpenAEVError):
            DaemonForTest(configuration=TEST_DAEMON_CONFIGURATION)

    def test_without_api_client_subclass_hook_builds_it(self, _):
        client = unittest.mock.MagicMock()

        class HookedDaemon(DaemonForTest):
            def _create_default_api_client(self):
                return client

        daemon = HookedDaemon(configuration=TEST_DAEMON_CONFIGURATION)

        self.assertIs(daemon.api, client)

    def test_default_logger_is_named_from_configuration(self, _):
        daemon = DaemonForTest(
            configuration=TEST_DAEMON_CONFIGURATION,
            api_client=unittest.mock.MagicMock(),
        )

        self.assertIsInstance(daemon.logger, sdk.AppLogger)

    def test_get_id_reads_legacy_keys(self, _):
        daemon, *_ = create_mock_daemon()

        self.assertEqual(daemon.get_id(), "collector-id")

    def test_when_no_callback_daemon_cant_start(self, m_argparser):
        m_argparser.return_value.parse_args.return_value = unittest.mock.MagicMock(
            dump_config_schema=False
        )
        daemon, mock_setup, mock_start_loop, _ = create_mock_daemon()

        with self.assertRaises(sdk.OpenAEVError):
            daemon.start()

        mock_setup.assert_not_called()
        mock_start_loop.assert_not_called()

    def test_when_callback_daemon_can_start(self, m_argparser):
        m_argparser.return_value.parse_args.return_value = unittest.mock.MagicMock(
            dump_config_schema=False
        )
        daemon, mock_setup, mock_start_loop, _ = create_mock_daemon(lambda: None)

        daemon.start()

        mock_setup.assert_called_once()
        mock_start_loop.assert_called_once()

    def test_when_dump_config_schema_daemon_prints_schema_and_stops(self, m_argparser):
        m_argparser.return_value.parse_args.return_value = unittest.mock.MagicMock(
            dump_config_schema=True
        )
        daemon, mock_setup, mock_start_loop, _ = create_mock_daemon(lambda: None)

        with unittest.mock.patch.object(
            TEST_DAEMON_CONFIGURATION, "schema", return_value={}
        ), unittest.mock.patch("builtins.print") as mock_print:
            daemon.start()

        mock_print.assert_called_once_with({})
        mock_setup.assert_not_called()
        mock_start_loop.assert_not_called()

    def test_when_callback_is_bound_method_daemon_can_call(self, _):
        daemon, _, _, inner_mock_func = create_mock_daemon()
        daemon.set_callback(daemon.bound_method)

        daemon._try_callback()

        inner_mock_func.assert_called_once()

    def test_when_callback_is_func_with_collector_parameter_daemon_can_call(self, _):
        daemon, *_ = create_mock_daemon()
        inner_mock_func = unittest.mock.MagicMock()
        daemon.set_callback(lambda collector: inner_mock_func(collector))

        daemon._try_callback()

        inner_mock_func.assert_called_once_with(daemon)

    def test_when_callback_raises_daemon_logs_and_survives(self, _):
        daemon, *_ = create_mock_daemon()

        def failing():
            raise RuntimeError("boom")

        daemon.set_callback(failing)

        daemon._try_callback()

        daemon.logger.error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
