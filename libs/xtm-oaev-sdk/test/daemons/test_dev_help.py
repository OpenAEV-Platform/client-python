"""Tests for the help of the dev options and the parser the role SDKs extend.

Feature: Help on the dev options
  "--dev --help" (or "--dev -h") asks for the dev options and what each one is for.
  Without --dev, -h stays the daemon's own. The SDK only knows the options common to
  every daemon: an injector or a collector SDK adds its own options to the dev parser,
  and its help then lists the common options next to the role's.
"""

import argparse
from typing import Any, Callable

import pytest
import xtm_oaev_sdk as sdk

COMMON_OPTIONS = ("--dev", "-h", "--out", "--record", "--replay")
ROLE_OPTIONS = (
    "--inject",
    "--emit",
    "--dump-contracts",
    "--list-contracts",
    "--new-inject",
    "--expectations",
    "--once",
)


def _given_dev_options_reader() -> Callable[..., Any]:
    """Given the SDK exposes the daemon dev options"""
    return sdk.dev_options


def _given_dev_help() -> Callable[[], str]:
    """Given the SDK exposes the help of the dev options"""
    helper = getattr(sdk, "dev_help", None)
    assert helper is not None, "Expected xtm_oaev_sdk.dev_help on public surface"
    return helper


def _given_dev_argument_parser() -> Callable[..., argparse.ArgumentParser]:
    """Given the SDK exposes the dev parser a role extends"""
    builder = getattr(sdk, "dev_argument_parser", None)
    assert (
        builder is not None
    ), "Expected xtm_oaev_sdk.dev_argument_parser on public surface"
    return builder


def _given_command_line(*args: str) -> list[str]:
    """Given a daemon command line with "<args>" """
    return list(args)


def _given_role_parser(
    builder: Callable[..., argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Given a role adds an "injector options" group with --inject to the dev parser"""
    parser = builder(description="Injector dev mode.", epilog="Injector exit codes.")
    group = parser.add_argument_group("injector options")
    group.add_argument("--inject", metavar="PATH", help="the inject message to run")
    return parser


def _when_reading_dev_options(reader: Callable[..., Any], argv: list[str]) -> Any:
    """When the dev options are read"""
    return reader(argv)


def _when_reading_the_help(helper: Callable[[], str]) -> str:
    """When the help of the dev options is read"""
    return helper()


def _when_parsing(parser: argparse.ArgumentParser, argv: list[str]) -> Any:
    """When the role parses the command line"""
    args, _ = parser.parse_known_args(argv)
    return args


def _then_help_is_asked(options: Any, asked: bool) -> None:
    """Then the dev help is <asked>"""
    assert options.help is asked


def _then_help_groups(text: str, heading: str, *options: str) -> None:
    """Then the help section "<heading>" lists exactly <options>"""
    section = text.split(f"{heading}:", 1)[1].split("\n\n", 1)[0]
    listed = tuple(
        token.rstrip(",")
        for line in section.splitlines()
        for token in line.split()
        if token.startswith("-") and line.lstrip().startswith(token)
    )
    assert listed == options, f"Expected {options} under {heading}, got {listed}"


def _then_help_names_no_role_option(text: str) -> None:
    """Then the help names no injector nor collector option"""
    named = [option for option in ROLE_OPTIONS if option in text]
    assert named == [], f"Expected no role option in the common help, got {named}"


def _then_help_says(text: str, *phrases: str) -> None:
    """Then the help says "<phrases>" """
    for phrase in phrases:
        assert phrase in text, f"Expected {phrase!r} in {text!r}"


def _then_role_option_is(args: Any, value: Any) -> None:
    """Then the role's --inject is <value>"""
    assert args.inject == value


@pytest.mark.parametrize("flag", ["--help", "-h"])
def test_dev_help_is_asked_with_dev(flag: str) -> None:
    """It asks for the dev help when --dev comes with -h or --help.

    Scenario Outline: The dev help is asked with --dev
      Given the SDK exposes the daemon dev options
      And a daemon command line with "--dev <flag>"
      When the dev options are read
      Then the dev help is True

      Examples:
        | flag   |
        | --help |
        | -h     |
    """
    reader = _given_dev_options_reader()
    argv = _given_command_line("--dev", flag)
    options = _when_reading_dev_options(reader, argv)
    _then_help_is_asked(options, True)


def test_dev_help_lists_only_the_common_options() -> None:
    """It lists the options common to every daemon, and no role option.

    Scenario: The dev help lists only the common options
      Given the SDK exposes the help of the dev options
      When the help of the dev options is read
      Then the help section "common options" lists exactly --dev, -h, --out, --record and --replay
      And the help names no injector nor collector option
    """
    helper = _given_dev_help()
    text = _when_reading_the_help(helper)
    _then_help_groups(text, "common options", *COMMON_OPTIONS)
    _then_help_names_no_role_option(text)


def test_a_role_extends_the_dev_parser_with_its_own_options() -> None:
    """It lets a role add its options and lists them next to the common ones.

    Scenario: A role extends the dev parser with its own options
      Given the SDK exposes the dev parser a role extends
      And a role adds an "injector options" group with --inject to the dev parser
      When the help of the dev options is read
      Then the help section "common options" lists exactly --dev, -h, --out, --record and --replay
      And the help section "injector options" lists exactly --inject
      And the help says "Injector dev mode." and "Injector exit codes."
    """
    builder = _given_dev_argument_parser()
    parser = _given_role_parser(builder)
    text = _when_reading_the_help(parser.format_help)
    _then_help_groups(text, "common options", *COMMON_OPTIONS)
    _then_help_groups(text, "injector options", "--inject")
    _then_help_says(text, "Injector dev mode.", "Injector exit codes.")


@pytest.mark.parametrize(
    ("argv", "value"),
    [
        (["--dev", "--inject", "inject.json"], "inject.json"),
        (["--dev", "--inj", "inject.json"], None),
        (["--dev", "--nmap-ports", "22"], None),
    ],
    ids=["full name", "abbreviation", "daemon's own flag"],
)
def test_a_role_parser_reads_its_options_only_under_their_full_name(
    argv: list[str], value: Any
) -> None:
    """It reads a role option only under its full name and leaves foreign flags alone.

    Scenario Outline: A role parser reads its options only under their full name
      Given the SDK exposes the dev parser a role extends
      And a role adds an "injector options" group with --inject to the dev parser
      When the role parses the command line "<argv>"
      Then the role's --inject is <value>

      Examples:
        | argv                          | value       |
        | --dev --inject inject.json    | inject.json |
        | --dev --inj inject.json       | None        |
        | --dev --nmap-ports 22         | None        |
    """
    builder = _given_dev_argument_parser()
    parser = _given_role_parser(builder)
    args = _when_parsing(parser, argv)
    _then_role_option_is(args, value)


# ---- Constraints identified ----


@pytest.mark.parametrize("flag", ["--help", "-h"])
def test_help_without_dev_stays_the_daemon_s_own(flag: str) -> None:
    """It leaves -h and --help to the daemon when --dev is absent.

    Scenario Outline: Help without --dev stays the daemon's own
      Given the SDK exposes the daemon dev options
      And a daemon command line with "<flag>"
      When the dev options are read
      Then the dev help is False

      Examples:
        | flag   |
        | --help |
        | -h     |
    """
    reader = _given_dev_options_reader()
    argv = _given_command_line(flag)
    options = _when_reading_dev_options(reader, argv)
    _then_help_is_asked(options, False)
