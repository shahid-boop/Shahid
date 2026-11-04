import json
import tempfile
import unittest
from pathlib import Path

from config_manager import load_config, save_config
from engine_pipeline import EnginePipeline, EngineProvider
from memory_manager import MemoryManager


class EchoProvider(EngineProvider):
    name = "echo"

    def generate(self, prompt: str, **options) -> str:
        return prompt


class CoreTests(unittest.TestCase):
    def test_config_defaults_and_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            self.assertEqual(load_config(path)["engine"], "openai_compatible")
            save_config({"assistant_name": "Test"}, path)
            self.assertEqual(load_config(path)["assistant_name"], "Test")

    def test_memory_persists_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = MemoryManager(Path(tmp) / "memory.json")
            manager.add("hello")
            self.assertEqual(manager.recent()[0]["content"], "hello")

    def test_pipeline_dispatches_registered_provider(self):
        pipeline = EnginePipeline()
        pipeline.register(EchoProvider())
        self.assertEqual(pipeline.generate("echo", "hello"), "hello")


if __name__ == "__main__":
    unittest.main()
