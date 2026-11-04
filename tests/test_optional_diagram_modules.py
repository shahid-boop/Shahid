import json, tempfile, unittest
from pathlib import Path
from plugins.marketplace import PluginMarketplace
from monitoring.topic_monitor import TopicMonitor
from desktop.control import click_or_type

class OptionalDiagramTests(unittest.TestCase):
    def test_marketplace_rejects_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/"packages").mkdir()
            (root/"packages"/"x.py").write_text("def register_skills(r): pass")
            (root/"catalog.json").write_text(json.dumps([{"id":"x","file":"x.py","sha256":"bad"}]))
            store=PluginMarketplace(root/"catalog.json",root/"packages")
            with self.assertRaises(ValueError): store.install_local("x",object())
    def test_topic_monitor_only_accepts_https_feeds(self):
        with tempfile.TemporaryDirectory() as d:
            monitor=TopicMonitor(["http://bad.example/feed"],Path(d)/"state.json")
            self.assertEqual(monitor.check_once(["test"]),[])
    def test_desktop_control_rejects_unknown_action(self):
        with self.assertRaises(ValueError): click_or_type({"action":"shell","command":"whoami"})

if __name__ == "__main__": unittest.main()
