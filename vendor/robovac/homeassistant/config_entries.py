"""Minimal Home Assistant config entry stubs for the RoboVac logger."""
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Iterable


class _StubConfigEntryState:
    """Placeholder state object mimicking Home Assistant's ConfigEntryState."""

    @property
    def recoverable(self) -> bool:
        return True


@dataclass
class ConfigEntry:
    """Simplified stand-in for Home Assistant's ConfigEntry.

    The real Home Assistant runtime provides many more attributes and coroutine
    helpers. The logger never instantiates ConfigEntry objects, so the stub only
    exists so the vendored integration can import its type hints without the
    heavy dependency.
    """

    entry_id: str = "stub"
    data: dict[str, Any] | None = None
    options: dict[str, Any] | None = None

    @property
    def state(self) -> _StubConfigEntryState:
        return _StubConfigEntryState()

    def async_on_unload(self, _callback: Callable[..., Any]) -> None:
        """Placeholder for the on-unload helper in real ConfigEntry objects."""
        raise NotImplementedError

    def add_update_listener(self, _listener: Callable[..., Awaitable[None]]) -> Callable[[], None]:
        """Placeholder for the update-listener helper in real ConfigEntry objects."""
        raise NotImplementedError


class ConfigEntries:
    """Namespace placeholder matching hass.config_entries in the real app."""

    def async_entries(self, _domain: str) -> Iterable[ConfigEntry]:
        raise NotImplementedError

    def async_update_entry(self, *_: Any, **__: Any) -> None:
        raise NotImplementedError

    async def async_forward_entry_setups(self, *_: Any, **__: Any) -> None:
        raise NotImplementedError

    async def async_reload(self, *_: Any, **__: Any) -> None:
        raise NotImplementedError

    async def async_unload_platforms(self, *_: Any, **__: Any) -> bool:
        raise NotImplementedError
