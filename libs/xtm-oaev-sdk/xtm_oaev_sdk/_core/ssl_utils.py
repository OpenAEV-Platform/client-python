"""SSL utility functions for OpenAEV SDK.

Loading certificates into an ``ssl.SSLContext``, including PEM data held in
memory (see https://bugs.python.org/issue16487).
"""

import os
import ssl
import tempfile

__all__ = [
    "data_to_temp_file",
    "is_memory_certificate",
    "ssl_cert_chain",
    "ssl_verify_locations",
]


# As cert must be written in files to be loaded in ssl context
# Creates a temporary file in the most secure manner possible
def data_to_temp_file(data: str) -> str:
    """Write data to a secure temporary file and return its path."""
    # The file is readable and writable only by the creating user ID.
    # If the operating system uses permission bits to indicate whether a
    # file is executable, the file is executable by no one. The file
    # descriptor is not inherited by children of this process.
    file_descriptor, file_path = tempfile.mkstemp()
    with os.fdopen(file_descriptor, "w") as open_file:
        open_file.write(data)
        open_file.close()
    return file_path


def is_memory_certificate(certificate: str) -> bool:
    """Return True if the certificate is PEM-encoded in memory (not a file path)."""
    return certificate.startswith("-----BEGIN")


def ssl_cert_chain(
    ssl_context: ssl.SSLContext,
    cert_data: str | None,
    key_data: str | None,
    passphrase: str | None,
) -> None:
    """Load a certificate chain into an SSL context, handling in-memory PEM data."""
    if cert_data is None:
        return

    cert_file_path = None
    key_file_path = None

    # Cert loading
    if is_memory_certificate(cert_data):
        cert_file_path = data_to_temp_file(cert_data)
    cert = cert_file_path if cert_file_path is not None else cert_data

    # Key loading
    if key_data is not None and is_memory_certificate(key_data):
        key_file_path = data_to_temp_file(key_data)
    key = key_file_path if key_file_path is not None else key_data

    # Load cert
    ssl_context.load_cert_chain(cert, key, passphrase)
    # Remove temp files
    if cert_file_path is not None:
        os.unlink(cert_file_path)
    if key_file_path is not None:
        os.unlink(key_file_path)


def ssl_verify_locations(ssl_context: ssl.SSLContext, certdata: str | None) -> None:
    """Load CA verification locations into an SSL context."""
    if certdata is None:
        return

    if is_memory_certificate(certdata):
        ssl_context.load_verify_locations(cadata=certdata)
    else:
        ssl_context.load_verify_locations(cafile=certdata)
