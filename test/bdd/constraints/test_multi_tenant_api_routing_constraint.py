import pytest

from pyoaev import OpenAEV


@pytest.mark.parametrize(
    "base_url, input_path, expected",
    [
        (
            "base_url",
            "path",
            "base_url/api/path",
        ),
        (
            "base_url/",
            "/path",
            "base_url/api/path",
        ),
        (
            "base_url//",
            "//path",
            "base_url/api/path",
        ),
    ],
    ids=[
        "clean-base-url-and-relative-path",
        "base-url-trailing-slash",
        "base-url-double-slash-and-path-double-slash",
    ],
)
def test_url_normalization(base_url, input_path, expected):
    client = OpenAEV(
        url=base_url,
        token="token",
        tenant_id=None,
    )
    result = client._build_url(input_path)
    assert result == expected
