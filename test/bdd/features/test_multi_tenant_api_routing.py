from uuid import UUID

import pytest

from pyoaev import OpenAEV


@pytest.mark.parametrize(
    "tenant_id, path, expected",
    [
        (
            None,
            "/path",
            "base_url/api/path",
        ),
        (
            UUID("2cffad3a-0001-4078-b0e2-ef74274022c3"),
            "/path",
            "base_url/api/tenants/2cffad3a-0001-4078-b0e2-ef74274022c3/path",
        ),
        (
            None,
            "https://external.service/api/path",
            "https://external.service/api/path",
        ),
        (
            UUID("2cffad3a-0001-4078-b0e2-ef74274022c3"),
            "https://external.service/api/path",
            "https://external.service/api/path",
        ),
    ],
    ids=[
        "legacy-relative-path",
        "tenant-relative-path",
        "legacy-full-url-bypass",
        "tenant-full-url-bypass",
    ],
)
def test_build_url_behavior(tenant_id, path, expected):
    client = OpenAEV(
        "base_url",
        "token",
        tenant_id=tenant_id,
    )
    result = client._build_url(path)
    assert result == expected
