import unittest

from main import build_registry


class DesktopRegistryTests(unittest.TestCase):
    def test_default_registry_exposes_reminders_and_diagram_tools(self):
        names = set(build_registry().names())
        expected = {
            "reminder_add", "reminder_list", "reminder_complete",
            "capture_screen", "capture_camera", "desktop_click", "desktop_type",
            "desktop_screenshot", "start_topic_monitor", "stop_topic_monitor",
            "install_signed_plugin", "list_windows_preferences",
            "set_windows_preference", "lookup_installed_app",
            "web_search", "system_status", "list_workspace_files",
            "read_workspace_file", "write_workspace_file",
        }
        self.assertTrue(expected.issubset(names), sorted(expected - names))


if __name__ == "__main__":
    unittest.main()
