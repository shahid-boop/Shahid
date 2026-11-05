"""Shared policy for safely dispatching desktop skills from interactive UI surfaces."""
from __future__ import annotations

from typing import Any


# These operations can expose private data, change desktop state, or start background work.
# The UI must obtain a fresh, explicit confirmation for each invocation.
SENSITIVE_SKILLS = frozenset({
    "capture_screen",
    "capture_camera",
    "desktop_click",
    "desktop_type",
    "desktop_screenshot",
    "set_windows_preference",
    "install_signed_plugin",
    "start_topic_monitor",
    "listen_for_wake_word",
    "write_workspace_file",
    "task_complete",
    "reminder_complete",
})

# These existing handlers also enforce a confirm=True payload flag. Set it only
# after the UI has independently obtained approval.
CONFIRM_FLAG_SKILLS = frozenset({
    "capture_screen",
    "capture_camera",
    "desktop_click",
    "desktop_type",
    "desktop_screenshot",
    "set_windows_preference",
})


def dispatch_skill(
    registry: Any,
    name: str,
    payload: dict[str, Any] | None = None,
    *,
    approved: bool = False,
) -> dict[str, Any]:
    """Run one allowlisted skill, requiring explicit approval for sensitive work."""
    key = str(name).strip().lower()
    if not key:
        raise ValueError("Choose a skill to run.")
    if payload is not None and not isinstance(payload, dict):
        raise TypeError("Skill arguments must be a JSON object.")
    if key in SENSITIVE_SKILLS and not approved:
        raise PermissionError(f"{key} requires explicit confirmation in the desktop UI.")

    arguments = dict(payload or {})
    if key in CONFIRM_FLAG_SKILLS:
        arguments["confirm"] = True
    return registry.run(key, arguments)
