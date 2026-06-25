"""Security domain classification types.

Defines the taxonomy of security domains used to categorize signatures,
injections, and detection scenarios across the OpenAEV platform.

Each domain carries a display name and color for UI rendering.

Example:
    >>> from xtm_oaev_sdk import SecurityDomains
    >>> domain = SecurityDomains.ENDPOINT
    >>> domain.value["domain_name"]
    'Endpoint'
    >>> domain.value["domain_color"]
    '#389CFF'
"""

from enum import Enum

__all__ = ["SecurityDomains"]


class SecurityDomains(Enum):
    """Security domain classification for signatures and injections.

    Each member maps to a dict with:
        - ``domain_name``: Human-readable display name.
        - ``domain_color``: Hex color code for UI rendering.
    """

    ENDPOINT = {"domain_name": "Endpoint", "domain_color": "#389CFF"}
    NETWORK = {"domain_name": "Network", "domain_color": "#009933"}
    WEB_APP = {"domain_name": "Web App", "domain_color": "#FF9933"}
    EMAIL_INFILTRATION = {
        "domain_name": "E-mail Infiltration",
        "domain_color": "#FF6666",
    }
    DATA_EXFILTRATION = {"domain_name": "Data Exfiltration", "domain_color": "#9933CC"}
    URL_FILTERING = {"domain_name": "URL Filtering", "domain_color": "#66CCFF"}
    CLOUD = {"domain_name": "Cloud", "domain_color": "#9999CC"}
    TABLE_TOP = {"domain_name": "Tabletop", "domain_color": "#FFCC33"}
    TOCLASSIFY = {"domain_name": "To classify", "domain_color": "#FFFFFF"}
