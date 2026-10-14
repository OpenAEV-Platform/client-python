"""Daemon runtime: the base daemon and its heartbeat, shared by the collector
and injector daemons. The API client is injected (``BaseClient``)."""

from xtm_oaev_sdk._core.daemons import BaseDaemon, PingAlive

__all__ = ["BaseDaemon", "PingAlive"]
