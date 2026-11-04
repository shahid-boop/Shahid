import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from monitoring.topic_monitor import TopicMonitor
from skills.registry import SkillRegistry
from skills.advanced_tools import register_advanced_skills
from realtime.gemini_live import GeminiLiveSession, GeminiLiveUnavailable
from vision.capture import capture_screen

class RemainingDiagramTests(unittest.TestCase):
    def test_topic_monitor_persists_seen_items(self):
        xml=b'<rss><channel><item><title>Python update</title><link>https://example.org/1</link></item></channel></rss>'
        class Response:
            def __enter__(self): return self
            def __exit__(self,*a): pass
            def read(self,n): return xml
        with tempfile.TemporaryDirectory() as d:
            state=Path(d)/"seen.json"; hits=[]
            with patch("urllib.request.urlopen",return_value=Response()):
                m=TopicMonitor(["https://example.org/rss"],["python"],hits.append,state_path=state)
                self.assertEqual(len(m.check_once()),1)
            m2=TopicMonitor(["https://example.org/rss"],["python"],hits.append,state_path=state)
            with patch("urllib.request.urlopen",return_value=Response()):
                self.assertEqual(m2.check_once(),[])
            self.assertEqual(len(hits),1)
    def test_advanced_skills_are_registered_without_optional_imports(self):
        r=SkillRegistry(); register_advanced_skills(r)
        self.assertIn("capture_screen",r.names())
        self.assertIn("start_topic_monitor",r.names())
        self.assertIn("install_signed_plugin",r.names())
    def test_gemini_live_requires_key_before_optional_sdk(self):
        with self.assertRaises(GeminiLiveUnavailable): GeminiLiveSession("")
    def test_screen_capture_validates_monitor_before_dependency(self):
        with self.assertRaises(ValueError): capture_screen("x.png",-1)

if __name__=="__main__": unittest.main()
