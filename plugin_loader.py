"""Explicit trusted plugin registry.

Third-party code is never discovered or imported from disk. Handlers run
in-process and therefore must be trusted; this is not an OS sandbox.
"""
from __future__ import annotations

import re
from typing import Any, Callable


class PluginLoader:
    def __init__(self) -> None:
        self._plugins: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, handler: Callable[..., Any]) -> None:
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", name):
            raise ValueError("Plugin names must match [a-z][a-z0-9_]{0,63}.")
        if not callable(handler):
            raise ValueError("Plugin handler must be callable.")
        if name in self._plugins:
            raise ValueError(f"Plugin '{name}' is already registered.")
        self._plugins[name] = handler

    def list_plugins(self) -> list[str]:
        return sorted(self._plugins)

    def call(self, name: str, **arguments: Any) -> Any:
        try:
            handler = self._plugins[name]
        except KeyError as exc:
            raise LookupError(f"Unknown trusted plugin: {name}") from exc
        return handler(**arguments)
