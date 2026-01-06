from enum import Enum


class SecurityDomains(Enum):
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
    TABLE_TOP = {"domain_name": "Table Top", "domain_color": "#FFCC33"}
    TOCLASSIFY = {"domain_name": "To classify", "domain_color": "#FFFFFF"}
