"""Minimal plugin registry.

Plugins are registered explicitly; this loader does not import arbitrary files
or execute untrusted code from a directory.
"""
from __future__ import annotations

from typing import Any, Callable


class PluginLoader:
    def __init__(self) -> None:
        self._plugins: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, handler: Callable[..., Any]) -> None:
        if not name.strip() or not callable(handler):
            raise ValueError("A plugin needs a name and a callable handler.")
        self._plugins[name] = handler

    def list_plugins(self) -> list[str]:
        return sorted(self._plugins)

    def call(self, name: str, **arguments: Any) -> Any:
        try:
            handler = self._plugins[name]
        except KeyError as exc:
            raise LookupError(f"Unknown plugin: {name}") from exc
        return handler(**arguments)
