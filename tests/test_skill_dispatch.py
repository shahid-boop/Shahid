import unittest

from desktop.skill_dispatch import dispatch_skill


class FakeRegistry:
    def __init__(self):
        self.called = None

    def run(self, name, payload):
        self.called = (name, payload)
        return {"ok": True, "name": name}


class SkillDispatchTests(unittest.TestCase):
    def test_sensitive_action_requires_approval(self):
        registry = FakeRegistry()
        with self.assertRaises(PermissionError):
            dispatch_skill(registry, "capture_camera", {})
        self.assertIsNone(registry.called)

    def test_confirmation_flag_is_added_only_after_approval(self):
        registry = FakeRegistry()
        result = dispatch_skill(registry, "capture_camera", {"output": "camera.jpg"}, approved=True)
        self.assertTrue(result["ok"])
        self.assertEqual(registry.called[0], "capture_camera")
        self.assertTrue(registry.called[1]["confirm"])
        self.assertEqual(registry.called[1]["output"], "camera.jpg")

    def test_non_sensitive_allowlisted_action_does_not_need_approval(self):
        registry = FakeRegistry()
        dispatch_skill(registry, "system_info", {})
        self.assertEqual(registry.called, ("system_info", {}))

    def test_payload_must_be_an_object(self):
        with self.assertRaises(TypeError):
            dispatch_skill(FakeRegistry(), "system_info", ["not", "an", "object"])


if __name__ == "__main__":
    unittest.main()
