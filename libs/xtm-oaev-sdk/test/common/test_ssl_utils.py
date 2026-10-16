"""Tests for the SSL helpers."""

import os
from typing import Any
from unittest.mock import MagicMock

import xtm_oaev_sdk as sdk

PEM_CERT = "-----BEGIN CERTIFICATE-----\nAAAA\n-----END CERTIFICATE-----\n"
PEM_KEY = "-----BEGIN PRIVATE KEY-----\nBBBB\n-----END PRIVATE KEY-----\n"


def _given_ssl_context() -> MagicMock:
    return MagicMock()


def _given_recording_context(recorded: dict[str, Any]) -> MagicMock:
    def _record(cert: str, key: str | None, passphrase: str | None) -> None:
        recorded["cert"] = cert
        recorded["key"] = key
        recorded["passphrase"] = passphrase
        with open(cert) as handle:
            recorded["cert_content"] = handle.read()

    context = MagicMock()
    context.load_cert_chain.side_effect = _record
    return context


def test_data_to_temp_file_writes_content_owner_only() -> None:
    """It writes the data to a new file readable only by its owner."""
    path = sdk.data_to_temp_file("secret")
    try:
        with open(path) as handle:
            assert handle.read() == "secret"
        assert os.stat(path).st_mode & 0o077 == 0
    finally:
        os.unlink(path)


def test_is_memory_certificate_detects_pem_data() -> None:
    """It distinguishes in-memory PEM data from a file path."""
    assert sdk.is_memory_certificate(PEM_CERT) is True
    assert sdk.is_memory_certificate("/etc/ssl/cert.pem") is False


def test_ssl_verify_locations_ignores_none() -> None:
    """It leaves the context untouched without CA data."""
    context = _given_ssl_context()
    sdk.ssl_verify_locations(context, None)
    context.load_verify_locations.assert_not_called()


def test_ssl_verify_locations_loads_memory_ca_as_cadata() -> None:
    """It loads in-memory CA data through cadata."""
    context = _given_ssl_context()
    sdk.ssl_verify_locations(context, PEM_CERT)
    context.load_verify_locations.assert_called_once_with(cadata=PEM_CERT)


def test_ssl_verify_locations_loads_ca_path_as_cafile() -> None:
    """It loads a CA path through cafile."""
    context = _given_ssl_context()
    sdk.ssl_verify_locations(context, "/etc/ssl/ca.pem")
    context.load_verify_locations.assert_called_once_with(cafile="/etc/ssl/ca.pem")


def test_ssl_cert_chain_ignores_missing_certificate() -> None:
    """It does nothing without certificate data."""
    context = _given_ssl_context()
    sdk.ssl_cert_chain(context, None, PEM_KEY, None)
    context.load_cert_chain.assert_not_called()


def test_ssl_cert_chain_passes_paths_through() -> None:
    """It loads certificate and key paths as given."""
    context = _given_ssl_context()
    sdk.ssl_cert_chain(context, "/tmp/cert.pem", "/tmp/key.pem", "pass")
    context.load_cert_chain.assert_called_once_with(
        "/tmp/cert.pem", "/tmp/key.pem", "pass"
    )


def test_ssl_cert_chain_bridges_memory_pem_through_removed_temp_files() -> None:
    """It writes in-memory PEM data to temp files, loads them, then removes them."""
    recorded: dict[str, Any] = {}
    context = _given_recording_context(recorded)
    sdk.ssl_cert_chain(context, PEM_CERT, PEM_KEY, "pass")
    assert recorded["cert_content"] == PEM_CERT
    assert recorded["passphrase"] == "pass"
    assert not os.path.exists(recorded["cert"])
    assert not os.path.exists(recorded["key"])
