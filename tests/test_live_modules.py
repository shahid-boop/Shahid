import hashlib, tempfile, unittest, zipfile
from pathlib import Path
from automation.desktop import click
from monitoring.topic_monitor import TopicMonitor
from plugins.marketplace import install_archive, PluginError
from windows.settings import list_settings, set_setting

class AdvancedFeatureTests(unittest.TestCase):
    def test_automation_requires_confirmation_before_import(self):
        with self.assertRaises(PermissionError): click(1,1)
    def test_windows_settings_are_allowlisted(self):
        self.assertIn("dark_app_mode", list_settings()["available"])
        with self.assertRaises(ValueError): set_setting("run_arbitrary_command", True, True)
    def test_topic_monitor_validates_https_and_interval(self):
        with self.assertRaises(ValueError): TopicMonitor(["http://bad"],["python"],lambda x:None)
        with self.assertRaises(ValueError): TopicMonitor(["https://example.com/rss"],["python"],lambda x:None,30)
    def test_marketplace_rejects_unsigned_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            archive=Path(d)/"p.zip"
            with zipfile.ZipFile(archive,"w") as z: z.writestr("plugin.py","x=1")
            digest=hashlib.sha256(archive.read_bytes()).hexdigest()
            with self.assertRaises(PluginError):
                install_archive(archive,Path(d)/"out",digest,{"name":"demo","version":"1.0"},"00"*32)

if __name__=="__main__": unittest.main()
