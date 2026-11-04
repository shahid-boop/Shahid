import tempfile
import unittest
from pathlib import Path
from config_manager import Settings
from memory_manager import MemoryManager
from skills.registry import SkillRegistry

class MemoryTests(unittest.TestCase):
    def test_persists_and_bounds_history(self):
        with tempfile.TemporaryDirectory() as temp:
            memory = MemoryManager(Path(temp) / "history.json", max_messages=2)
            memory.append("user", "one")
            memory.append("assistant", "two")
            memory.append("user", "three")
            self.assertEqual([m["content"] for m in memory.get_messages()], ["two", "three"])

    def test_clear_conversation(self):
        with tempfile.TemporaryDirectory() as temp:
            memory = MemoryManager(Path(temp) / "history.json")
            memory.append("user", "hello")
            memory.clear()
            self.assertEqual(memory.get_messages(), [])

class ConfigTests(unittest.TestCase):
    def test_dashboard_host_is_forced_to_loopback(self):
        import os
        old = os.environ.get("APP_HOST")
        os.environ["APP_HOST"] = "0.0.0.0"
        try:
            self.assertEqual(Settings.load().host, "127.0.0.1")
        finally:
            if old is None:
                os.environ.pop("APP_HOST", None)
            else:
                os.environ["APP_HOST"] = old

class RegistryTests(unittest.TestCase):
    def test_only_registered_skills_run(self):
        registry = SkillRegistry()
        registry.register("echo", lambda payload: {"value": payload.get("value")})
        self.assertEqual(registry.run("echo", {"value": 3}), {"value": 3})
        with self.assertRaises(KeyError):
            registry.run("not_registered")

if __name__ == "__main__":
    unittest.main()
