import tempfile
import unittest
from pathlib import Path
from reminder_manager import ReminderManager
from skills.file_tools import read_file, write_file, list_files

class WorkspaceTests(unittest.TestCase):
    def test_write_read_and_list(self):
        import skills.file_tools as files
        with tempfile.TemporaryDirectory() as tmp:
            old = files.WORKSPACE
            files.WORKSPACE = Path(tmp)
            try:
                write_file({"path":"notes/today.txt","content":"hello"})
                self.assertEqual(read_file({"path":"notes/today.txt"})["content"], "hello")
                self.assertIn("notes/today.txt", list_files()["files"])
            finally:
                files.WORKSPACE = old

    def test_path_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            read_file({"path":"../../outside.txt"})

class ReminderTests(unittest.TestCase):
    def test_add_list_complete_persists(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reminders.json"
            manager = ReminderManager(path)
            item = manager.add("Call home")
            self.assertEqual(manager.list()[0]["text"], "Call home")
            manager.complete(item["id"])
            self.assertEqual(manager.list(), [])
            self.assertTrue(ReminderManager(path).list(include_done=True)[0]["done"])

    def test_timezone_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                ReminderManager(Path(tmp) / "r.json").add("Meeting", "2026-12-01T10:00:00")

if __name__ == "__main__":
    unittest.main()
