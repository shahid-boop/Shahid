import tempfile
import unittest
from pathlib import Path

from desktop.control import click_or_type
from monitoring.topic_monitor import TopicMonitor
from plugins.marketplace import PluginError, verify_manifest


class OptionalDiagramTests(unittest.TestCase):
    def test_marketplace_rejects_invalid_signature(self):
        manifest = {
            "id": "test-plugin",
            "version": "1.0.0",
            "entrypoint": "plugin.py",
            "signature": "00",
        }
        # This must fail closed whether the optional crypto package is installed or not.
        with self.assertRaises(PluginError):
            verify_manifest(manifest, "00" * 32)

    def test_topic_monitor_only_accepts_https_feeds(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                TopicMonitor(
                    feeds=["http://bad.example/feed"],
                    keywords=["test"],
                    callback=lambda item: None,
                    state_path=str(Path(directory) / "state.json"),
                )

    def test_desktop_control_rejects_unknown_action(self):
        with self.assertRaises(ValueError):
            click_or_type({"action": "shell", "command": "whoami"})


if __name__ == "__main__":
    unittest.main()
