import tempfile, unittest
from pathlib import Path
from providers.registry import ProviderRegistry
from skills.agent_tasks import TaskStore
from skills.reminders import ReminderStore
from skills.proactive_checks import run_checks
class AddedFeatureTests(unittest.TestCase):
    def test_reminder_storage(self):
        with tempfile.TemporaryDirectory() as d:
            s=ReminderStore(Path(d)/"r.json"); item=s.add("Call home"); self.assertTrue(s.complete(item["id"])["done"])
    def test_task_storage(self):
        with tempfile.TemporaryDirectory() as d:
            s=TaskStore(Path(d)/"t.json"); item=s.add("Review"); self.assertEqual(s.complete(item["id"])["status"],"completed")
    def test_provider_registry(self):
        class Fake:
            def chat(self,messages): return "ok"
        r=ProviderRegistry(); r.register("fake",Fake()); self.assertEqual(r.get("fake").chat([]),"ok")
        with self.assertRaises(KeyError): r.get("missing")
    def test_on_demand_checks(self): self.assertIn("checks",run_checks())
if __name__=="__main__": unittest.main()
