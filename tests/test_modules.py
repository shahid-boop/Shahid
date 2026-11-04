import tempfile
import unittest
from pathlib import Path

from skills.loader import SkillLoader
from skills.reminders import ReminderSkill
from skills.file_controller import FileControlSkill
from skills.file_processor import FileProcessingSkill


class ModuleTests(unittest.TestCase):
    def test_reminder_requires_timezone_and_persists(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = ReminderSkill(Path(tmp) / "reminders.json")
            with self.assertRaises(ValueError):
                skill.run(action="add", text="test", due_at="2026-12-01T10:00:00")
            skill.run(action="add", text="test", due_at="2026-12-01T10:00:00+00:00")
            self.assertEqual(skill.run(action="list")[0]["text"], "test")

    def test_file_control_creates_but_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = FileControlSkill(Path(tmp))
            skill.run(action="create", path="note.txt", content="hello")
            with self.assertRaises(FileExistsError):
                skill.run(action="create", path="note.txt", content="again")
            with self.assertRaises(PermissionError):
                skill.run(action="create", path="../outside.txt", content="no")

    def test_file_processor_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = FileProcessingSkill(Path(tmp))
            with self.assertRaises(PermissionError):
                skill.run(path="../outside.txt")

    def test_skill_loader_requires_registration(self):
        loader = SkillLoader()
        with self.assertRaises(LookupError):
            loader.run("missing")


if __name__ == "__main__":
    unittest.main()
