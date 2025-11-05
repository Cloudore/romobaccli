"""Minimal Home Assistant core stubs for the RoboVac logger."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

from .config_entries import ConfigEntries


@dataclass
class _StubBus:
    """Simplified event bus placeholder."""

    def async_listen_once(self, _event_type: str, _listener: Callable[..., Coroutine[Any, Any, None]]) -> None:
        raise NotImplementedError


@dataclass
class HomeAssistant:
    """Tiny subset of Home Assistant's core object."""

    data: dict[str, Any] = field(default_factory=dict)
    config_entries: ConfigEntries = field(default_factory=ConfigEntries)
    bus: _StubBus = field(default_factory=_StubBus)
