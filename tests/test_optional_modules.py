import unittest
from unittest.mock import patch
from gemini import GeminiEngine, GeminiError
from config_manager import Settings
from skills.registry import SkillRegistry
from skills.windows_tools import register_windows_skills, launch_app, open_website, system_info

class GeminiTests(unittest.TestCase):
    def test_missing_key_fails_clearly(self):
        engine = GeminiEngine(Settings(google_api_key=""))
        with self.assertRaisesRegex(GeminiError, "GOOGLE_API_KEY"):
            engine.chat([{"role":"user","content":"hello"}])

class WindowsSkillTests(unittest.TestCase):
    def test_registers_only_explicit_safe_skills(self):
        registry = SkillRegistry()
        register_windows_skills(registry)
        self.assertEqual(registry.names(), ["launch_app", "open_website", "system_info"])
        self.assertIn("python", system_info())

    def test_rejects_unlisted_application(self):
        with self.assertRaises(ValueError):
            launch_app({"name":"powershell"})

    def test_rejects_non_http_url(self):
        with self.assertRaises(ValueError):
            open_website({"url":"file:///C:/Windows/win.ini"})

if __name__ == "__main__":
    unittest.main()
