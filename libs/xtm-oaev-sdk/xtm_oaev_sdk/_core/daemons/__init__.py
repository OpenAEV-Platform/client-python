"""Daemon runtime shared by collectors and injectors."""

from .base_daemon import BaseDaemon
from .ping_alive import PingAlive

__all__ = ["BaseDaemon", "PingAlive"]
