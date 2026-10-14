"""Network targets: raw injector targets into network injector configs."""

import ipaddress
from typing import Any

from xtm_oaev_sdk.seam.signatures import NetworkInjectorConfig

__all__ = ["NetworkTargets"]


class NetworkTargets:
    """Implements ``NetworkTargetsPort``."""

    def build_network_configs(
        self,
        targets: list[str | dict[str, Any] | NetworkInjectorConfig],
    ) -> list[NetworkInjectorConfig]:
        configs: list[NetworkInjectorConfig] = []
        for target in targets:
            if isinstance(target, NetworkInjectorConfig):
                configs.append(target)
            elif isinstance(target, dict):
                configs.append(NetworkInjectorConfig(**target))
            elif isinstance(target, str):
                configs.append(self._classify_network_target(target))
            else:
                raise TypeError(
                    f"unsupported network target type: {type(target).__name__}"
                )
        return configs

    def _classify_network_target(self, value: str) -> NetworkInjectorConfig:
        """Decide whether ``value`` is an IPv4, IPv6, or hostname and wrap it."""
        try:
            addr = ipaddress.ip_address(value)
        except ValueError:
            return NetworkInjectorConfig(target_hostname=value)
        if isinstance(addr, ipaddress.IPv4Address):
            return NetworkInjectorConfig(target_ipv4=value)
        return NetworkInjectorConfig(target_ipv6=value)
