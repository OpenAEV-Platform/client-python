"""Tests for the dev command-line options common to collector and injector daemons.

Feature: Daemon dev options
  Collector and injector daemons can run without the platform ("dev mode").
  Every daemon reads its dev options from its command line, dev or not,
  so the dev options must never act on anything that is not theirs.
"""

import io
import sys
from contextlib import redirect_stdout
from typing import Any, Callable, NamedTuple
from unittest.mock import MagicMock

import pytest
import xtm_oaev_sdk as sdk

PROGRAM = "openaev-collector"
SCHEMA = '{"title": "collector configuration"}'


class Reading(NamedTuple):
    options: Any
    exit_code: Any
    output: str


class Start(NamedTuple):
    exit_code: Any
    output: str


def _given_dev_options_reader() -> Callable[..., Any]:
    """Given the SDK exposes the daemon dev options"""
    reader = getattr(sdk, "dev_options", None)
    assert (
        reader is not None
    ), "Expected xtm_oaev_sdk.dev_options to exist on public surface"
    return reader


def _given_command_line(*args: str) -> list[str]:
    """Given a daemon command line with "<args>" """
    return list(args)


def _given_command_line_with_every_common_dev_flag() -> list[str]:
    """Given a daemon command line with:
    | flag     | value            |
    | --dev    |                  |
    | --out    | run.json         |
    | --record | shodan.tape.json |
    """
    return _given_command_line(
        "--dev", "--out", "run.json", "--record", "shodan.tape.json"
    )


def _given_process_command_line(monkeypatch: pytest.MonkeyPatch, *args: str) -> None:
    """Given the process command line contains "<args>" """
    monkeypatch.setattr(sys, "argv", [PROGRAM, *args])


def _given_configuration() -> sdk.Configuration:
    """Given a daemon configuration"""
    return sdk.Configuration(
        config_hints={
            "log_level": {"data": "info"},
            "name": {"data": "whoami collector"},
            "collector_id": {"data": "whoami-collector"},
        }
    )


def _given_configuration_schema(
    monkeypatch: pytest.MonkeyPatch, configuration: sdk.Configuration
) -> None:
    """Given the daemon configuration has a schema"""
    monkeypatch.setattr(configuration, "schema", lambda: SCHEMA)


def _given_daemon_with_callback(
    configuration: sdk.Configuration,
) -> tuple[sdk.BaseDaemon, MagicMock, MagicMock]:
    """Given a daemon with a callback"""
    setup, main_loop = MagicMock(), MagicMock()

    class WhoamiCollector(sdk.BaseDaemon):
        def _setup(self):
            setup()

        def _start_loop(self):
            main_loop()

    daemon = WhoamiCollector(
        configuration=configuration,
        callback=MagicMock(),
        logger=MagicMock(),
        api_client=MagicMock(),
    )
    return daemon, setup, main_loop


def _when_reading_dev_options(
    reader: Callable[..., Any], argv: list[str] | None
) -> Reading:
    """When the dev options are read"""
    output = io.StringIO()
    try:
        with redirect_stdout(output):
            options = reader(argv) if argv is not None else reader()
    except SystemExit as exit_:
        return Reading(None, exit_.code, output.getvalue())
    return Reading(options, None, output.getvalue())


def _when_turning_dev_mode_off(options: Any) -> Exception | None:
    """When someone tries to turn dev mode off on those options"""
    try:
        options.enabled = False
    except Exception as err:  # pylint: disable=broad-except
        return err
    return None


def _when_starting_daemon(daemon: sdk.BaseDaemon) -> Start:
    """When the daemon is started"""
    output = io.StringIO()
    try:
        with redirect_stdout(output):
            daemon.start()
    except SystemExit as exit_:
        return Start(exit_.code, output.getvalue())
    return Start(None, output.getvalue())


def _then_reading_did_not_exit(reading: Reading) -> None:
    """Then reading the dev options does not exit"""
    assert (
        reading.exit_code is None
    ), f"Expected reading the dev options not to exit, exited with {reading.exit_code}"


def _then_nothing_was_printed(reading: Reading) -> None:
    """Then nothing is printed"""
    assert reading.output == "", f"Expected no output, got {reading.output!r}"


def _then_dev_mode_is_enabled(options: Any) -> None:
    """Then dev mode is enabled"""
    assert options.enabled is True


def _then_dev_mode_is_disabled(options: Any) -> None:
    """Then dev mode is disabled"""
    assert options.enabled is False


def _then_output_destination_is(options: Any, destination: str | None) -> None:
    """Then the output destination is "<destination>" """
    assert options.out == destination


def _then_tapes_are(options: Any, record: str | None, replay: str | None) -> None:
    """Then the tape to record is "<record>" and the tape to replay is "<replay>" """
    assert (options.record, options.replay) == (record, replay)


def _then_options_hold_only_the_common_fields(options: Any) -> None:
    """Then the options hold only the fields common to every daemon"""
    assert set(vars(options)) == {"enabled", "out", "record", "replay", "help"}


def _then_change_was_refused(error: Exception | None) -> None:
    """Then the change is refused"""
    assert isinstance(
        error, (AttributeError, TypeError, ValueError)
    ), f"Expected the change to be refused, got {error!r}"


def _then_option_is_unset(options: Any, option: str) -> None:
    """Then the <option> is not set"""
    assert getattr(options, option) is None


def _then_daemon_did_not_exit(start: Start) -> None:
    """Then the daemon does not exit"""
    assert (
        start.exit_code is None
    ), f"Expected the daemon not to exit, exited with {start.exit_code}"


def _then_schema_was_printed(start: Start, schema: str) -> None:
    """Then the configuration schema is printed"""
    assert start.output == f"{schema}\n"


def _then_ran_once(step: MagicMock) -> None:
    """Then its <step> runs once"""
    step.assert_called_once()


def _then_did_not_run(step: MagicMock) -> None:
    """Then its <step> does not run"""
    step.assert_not_called()


def test_dev_mode_is_off_when_no_dev_flag_is_given() -> None:
    """It reports dev mode as disabled when no dev flag is given.

    Scenario: Dev mode is off when no dev flag is given
      Given the SDK exposes the daemon dev options
      And a daemon command line without any dev flag
      When the dev options are read
      Then dev mode is disabled
      And the output destination is "None"
      And the tape to record is "None" and the tape to replay is "None"
    """
    reader = _given_dev_options_reader()
    argv = _given_command_line()
    reading = _when_reading_dev_options(reader, argv)
    _then_dev_mode_is_disabled(reading.options)
    _then_output_destination_is(reading.options, None)
    _then_tapes_are(reading.options, None, None)


def test_every_common_dev_flag_given_on_the_command_line_is_exposed() -> None:
    """It exposes every common dev flag given on the command line.

    Scenario: Every common dev flag given on the command line is exposed
      Given the SDK exposes the daemon dev options
      And a daemon command line with:
        | flag     | value            |
        | --dev    |                  |
        | --out    | run.json         |
        | --record | shodan.tape.json |
      When the dev options are read
      Then dev mode is enabled
      And the output destination is "run.json"
      And the tape to record is "shodan.tape.json" and the tape to replay is "None"
    """
    reader = _given_dev_options_reader()
    argv = _given_command_line_with_every_common_dev_flag()
    reading = _when_reading_dev_options(reader, argv)
    _then_dev_mode_is_enabled(reading.options)
    _then_output_destination_is(reading.options, "run.json")
    _then_tapes_are(reading.options, "shodan.tape.json", None)


def test_replay_names_its_tape() -> None:
    """It exposes the tape to replay.

    Scenario: --replay names its tape
      Given the SDK exposes the daemon dev options
      And a daemon command line with "--dev --replay shodan.tape.json"
      When the dev options are read
      Then the tape to record is "None" and the tape to replay is "shodan.tape.json"
    """
    reader = _given_dev_options_reader()
    argv = _given_command_line("--dev", "--replay", "shodan.tape.json")
    reading = _when_reading_dev_options(reader, argv)
    _then_tapes_are(reading.options, None, "shodan.tape.json")


def test_common_options_carry_no_injector_nor_collector_option() -> None:
    """It keeps the common options free of any injector or collector option.

    Scenario: The common dev options carry no role option
      Given the SDK exposes the daemon dev options
      And a daemon command line with "--dev --inject inject.json --expectations - --once"
      When the dev options are read
      Then reading the dev options does not exit
      And the options hold only the fields common to every daemon
    """
    reader = _given_dev_options_reader()
    argv = _given_command_line(
        "--dev", "--inject", "inject.json", "--expectations", "-", "--once"
    )
    reading = _when_reading_dev_options(reader, argv)
    _then_reading_did_not_exit(reading)
    _then_options_hold_only_the_common_fields(reading.options)


def test_flags_owned_by_a_daemon_are_ignored() -> None:
    """It ignores the command-line flags that belong to the daemon itself.

    Scenario: Flags owned by a daemon are ignored
      Given the SDK exposes the daemon dev options
      And a daemon command line with "--dev --nmap-ports 22,443"
      When the dev options are read
      Then reading the dev options does not exit
      And dev mode is enabled
    """
    reader = _given_dev_options_reader()
    argv = _given_command_line("--dev", "--nmap-ports", "22,443")
    reading = _when_reading_dev_options(reader, argv)
    _then_reading_did_not_exit(reading)
    _then_dev_mode_is_enabled(reading.options)


def test_dev_options_cannot_be_modified_once_read() -> None:
    """It refuses to turn dev mode off on dev options already read.

    Scenario: Dev options cannot be modified once read
      Given the SDK exposes the daemon dev options
      And a daemon command line with "--dev"
      When the dev options are read
      And someone tries to turn dev mode off on those options
      Then the change is refused
      And dev mode is enabled
    """
    reader = _given_dev_options_reader()
    argv = _given_command_line("--dev")
    reading = _when_reading_dev_options(reader, argv)
    error = _when_turning_dev_mode_off(reading.options)
    _then_change_was_refused(error)
    _then_dev_mode_is_enabled(reading.options)


def test_daemon_starts_when_dev_flags_are_on_its_command_line(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """It sets the daemon up and starts its main loop once despite dev flags.

    Scenario: A daemon starts when dev flags are on its command line
      Given a daemon configuration
      And a daemon with a callback
      And the process command line contains "--dev --once"
      When the daemon is started
      Then the daemon does not exit
      And its setup runs once
      And its main loop runs once
    """
    configuration = _given_configuration()
    daemon, setup, main_loop = _given_daemon_with_callback(configuration)
    _given_process_command_line(monkeypatch, "--dev", "--once")
    start = _when_starting_daemon(daemon)
    _then_daemon_did_not_exit(start)
    _then_ran_once(setup)
    _then_ran_once(main_loop)


def test_configuration_schema_dump_still_wins_over_dev_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """It prints the configuration schema instead of starting, dev flags or not.

    Scenario: The configuration schema dump still wins over dev flags
      Given a daemon configuration
      And the daemon configuration has a schema
      And a daemon with a callback
      And the process command line contains "--dump-config-schema --dev"
      When the daemon is started
      Then the daemon does not exit
      And the configuration schema is printed
      And its setup does not run
    """
    configuration = _given_configuration()
    _given_configuration_schema(monkeypatch, configuration)
    daemon, setup, _ = _given_daemon_with_callback(configuration)
    _given_process_command_line(monkeypatch, "--dump-config-schema", "--dev")
    start = _when_starting_daemon(daemon)
    _then_daemon_did_not_exit(start)
    _then_schema_was_printed(start, SCHEMA)
    _then_did_not_run(setup)


# ---- Constraints identified ----


def test_dev_options_never_take_over_help() -> None:
    """It leaves -h to the daemon: dev options never print help nor exit.

    Scenario: Dev options never take over help
      Given the SDK exposes the daemon dev options
      And a daemon command line with "-h"
      When the dev options are read
      Then reading the dev options does not exit
      And nothing is printed
      And dev mode is disabled
    """
    reader = _given_dev_options_reader()
    argv = _given_command_line("-h")
    reading = _when_reading_dev_options(reader, argv)
    _then_reading_did_not_exit(reading)
    _then_nothing_was_printed(reading)
    _then_dev_mode_is_disabled(reading.options)


@pytest.mark.parametrize(
    ("abbreviation", "value", "option"),
    [
        ("--o", "run.json", "out"),
        ("--rec", "shodan.tape.json", "record"),
        ("--rep", "shodan.tape.json", "replay"),
    ],
    ids=["output destination", "tape to record", "tape to replay"],
)
def test_dev_options_are_read_only_under_their_full_name(
    abbreviation: str, value: str, option: str
) -> None:
    """It reads a dev option only under its full name, never an abbreviation.

    Scenario Outline: Dev options are read only under their full name
      Given the SDK exposes the daemon dev options
      And a daemon command line with "--dev <abbreviation> <value>"
      When the dev options are read
      Then the <option> is not set

      Examples:
        | abbreviation | value            | option             |
        | --o          | run.json         | output destination |
        | --rec        | shodan.tape.json | tape to record     |
        | --rep        | shodan.tape.json | tape to replay     |
    """
    reader = _given_dev_options_reader()
    argv = _given_command_line("--dev", abbreviation, value)
    reading = _when_reading_dev_options(reader, argv)
    _then_option_is_unset(reading.options, option)


def test_dev_options_default_to_the_process_command_line(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """It reads the process command line when no argument list is given.

    Scenario: Dev options default to the process command line
      Given the SDK exposes the daemon dev options
      And the process command line contains "--dev"
      When the dev options are read
      Then dev mode is enabled
    """
    reader = _given_dev_options_reader()
    _given_process_command_line(monkeypatch, "--dev")
    reading = _when_reading_dev_options(reader, None)
    _then_dev_mode_is_enabled(reading.options)
