from pyoaev.security_domain.types import SecurityDomainsKeyWords, SecurityDomains

class SecurityDomainBuilder:

    def _find_in_keywords(self, keywords, search):
        return any(keyword.lower() in search.lower() for keyword in keywords.value)

    # Define the domain by item
    def get_associated_security_domains(self, name, description):
        domains = []

        if self._find_in_keywords(SecurityDomainsKeyWords.ENDPOINT, name) or self._find_in_keywords(SecurityDomainsKeyWords.ENDPOINT, description):
            domains.append(SecurityDomains.ENDPOINT.value)
        if self._find_in_keywords(SecurityDomainsKeyWords.NETWORK, name) or self._find_in_keywords(SecurityDomainsKeyWords.NETWORK, description):
            domains.append(SecurityDomains.NETWORK.value)
        if self._find_in_keywords(SecurityDomainsKeyWords.WEB_APP, name) or self._find_in_keywords(SecurityDomainsKeyWords.WEB_APP, description):
            domains.append(SecurityDomains.WEB_APP.value)
        if self._find_in_keywords(SecurityDomainsKeyWords.EMAIL_INFILTRATION, name) or self._find_in_keywords(SecurityDomainsKeyWords.EMAIL_INFILTRATION, description):
            domains.append(SecurityDomains.EMAIL_INFILTRATION.value)
        if self._find_in_keywords(SecurityDomainsKeyWords.DATA_EXFILTRATION, name) or self._find_in_keywords(SecurityDomainsKeyWords.DATA_EXFILTRATION, description):
            domains.append(SecurityDomains.DATA_EXFILTRATION.value)
        if self._find_in_keywords(SecurityDomainsKeyWords.URL_FILTERING, name) or self._find_in_keywords(SecurityDomainsKeyWords.URL_FILTERING, description):
            domains.append(SecurityDomains.URL_FILTERING.value)
        if self._find_in_keywords(SecurityDomainsKeyWords.CLOUD, name) or self._find_in_keywords(SecurityDomainsKeyWords.CLOUD, description):
            domains.append(SecurityDomains.CLOUD.value)

        if 0 == len(domains):
            domains.append(SecurityDomains.ENDPOINT.value)

        return domains