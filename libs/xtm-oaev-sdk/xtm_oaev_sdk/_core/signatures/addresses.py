"""Container addresses: the source IPs of network execution signatures."""

import logging
import os
import socket
import subprocess

__all__ = ["ContainerAddressResolver"]


class ContainerAddressResolver:
    """Implements ``ContainerAddressPort``."""

    def resolve_ipv4(self, logger: logging.Logger) -> str | None:
        env_ip = os.environ.get("CONTAINER_IP")
        if env_ip:
            return env_ip

        try:
            ip = socket.gethostbyname(socket.gethostname())
            if ip and ip != "127.0.0.1":
                return ip
        except (socket.gaierror, OSError):
            pass

        try:
            result = subprocess.run(
                ["hostname", "-i"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                ip = result.stdout.strip().split()[0]
                if ip and ip != "127.0.0.1":
                    return ip
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            pass

        logger.warning("Could not resolve container IP; returning 'unknown'")
        return None

    def resolve_ipv6(self) -> str | None:
        try:
            infos = socket.getaddrinfo(
                socket.gethostname(), None, socket.AF_INET6, socket.SOCK_STREAM
            )
            for info in infos:
                addr = info[4][0]
                if (
                    isinstance(addr, str)
                    and addr
                    and not addr.startswith("::1")
                    and not addr.startswith("fe80")
                ):
                    return addr
        except (socket.gaierror, OSError):
            pass
        return None
