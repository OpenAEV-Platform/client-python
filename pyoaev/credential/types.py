"""Credential reference types shared with the OpenAEV platform.

This enum is the Python mirror of the OpenAEV backend credential-type enum
used by credential secret references. Values must stay label-for-label in sync
with the platform so contracts can declare credential references without any
translation layer.
"""

from enum import Enum


class CredentialType(str, Enum):
    IDENTITY = "IDENTITY"
    CLOUD_AWS = "CLOUD_AWS"
    CLOUD_AZURE = "CLOUD_AZURE"
    CLOUD_GCP = "CLOUD_GCP"
