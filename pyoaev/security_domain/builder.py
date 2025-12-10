from pyoaev.security_domain.types import SecurityDomains, SecurityDomainsKeyWords


class SecurityDomainBuilder:

    def _find_in_keywords(self, keywords, search):
        return any(keyword.lower() in search.lower() for keyword in keywords.value)

    # Define the domain by item
    def get_associated_security_domains(self, name):
        domains = []
        domains.append(SecurityDomains.ENDPOINT.value)

        if self._find_in_keywords(SecurityDomainsKeyWords.NETWORK, name):
            domains.append(SecurityDomains.NETWORK.value)
        if self._find_in_keywords(SecurityDomainsKeyWords.WEB_APP, name):
            domains.append(SecurityDomains.WEB_APP.value)
        if self._find_in_keywords(SecurityDomainsKeyWords.EMAIL_INFILTRATION, name):
            domains.append(SecurityDomains.EMAIL_INFILTRATION.value)
        if self._find_in_keywords(SecurityDomainsKeyWords.DATA_EXFILTRATION, name):
            domains.append(SecurityDomains.DATA_EXFILTRATION.value)
        if self._find_in_keywords(SecurityDomainsKeyWords.URL_FILTERING, name):
            domains.append(SecurityDomains.URL_FILTERING.value)
        if self._find_in_keywords(SecurityDomainsKeyWords.CLOUD, name):
            domains.append(SecurityDomains.CLOUD.value)

        return domains
