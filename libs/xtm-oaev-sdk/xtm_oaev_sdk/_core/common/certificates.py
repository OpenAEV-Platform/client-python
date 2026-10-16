"""Certificates: load files or in-memory PEM data into SSL contexts.

Thanks to https://bugs.python.org/issue16487 it is not possible to load
in-memory PEM data into an SSL context: it is written to a temporary file first.
"""

import os
import ssl
import tempfile

__all__ = ["Certificates"]


class Certificates:
    """Implements ``CertificatesPort``."""

    # As cert must be written in files to be loaded in ssl context
    # Creates a temporary file in the most secure manner possible
    def data_to_temp_file(self, data: str) -> str:
        # The file is readable and writable only by the creating user ID.
        # If the operating system uses permission bits to indicate whether a
        # file is executable, the file is executable by no one. The file
        # descriptor is not inherited by children of this process.
        file_descriptor, file_path = tempfile.mkstemp()
        with os.fdopen(file_descriptor, "w") as open_file:
            open_file.write(data)
            open_file.close()
        return file_path

    def is_memory_certificate(self, certificate: str) -> bool:
        return certificate.startswith("-----BEGIN")

    def ssl_cert_chain(
        self,
        ssl_context: ssl.SSLContext,
        cert_data: str | None,
        key_data: str | None,
        passphrase: str | None,
    ) -> None:
        if cert_data is None:
            return

        cert_file_path = None
        key_file_path = None

        # Cert loading
        if self.is_memory_certificate(cert_data):
            cert_file_path = self.data_to_temp_file(cert_data)
        cert = cert_file_path if cert_file_path is not None else cert_data

        # Key loading
        if key_data is not None and self.is_memory_certificate(key_data):
            key_file_path = self.data_to_temp_file(key_data)
        key = key_file_path if key_file_path is not None else key_data

        # Load cert
        ssl_context.load_cert_chain(cert, key, passphrase)
        # Remove temp files
        if cert_file_path is not None:
            os.unlink(cert_file_path)
        if key_file_path is not None:
            os.unlink(key_file_path)

    def ssl_verify_locations(
        self, ssl_context: ssl.SSLContext, certdata: str | None
    ) -> None:
        if certdata is None:
            return

        if self.is_memory_certificate(certdata):
            ssl_context.load_verify_locations(cadata=certdata)
        else:
            ssl_context.load_verify_locations(cafile=certdata)
