import threading
import time
import unittest

from desktop.live_audio_controller import LiveAudioController


class LiveAudioControllerTests(unittest.TestCase):
    def test_declined_start_does_not_call_runner(self):
        calls = []
        controller = LiveAudioController("test-key", runner=lambda *a, **k: calls.append(True))
        self.assertFalse(controller.start(approved=False))
        self.assertEqual(calls, [])

    def test_start_requires_api_key(self):
        controller = LiveAudioController("")
        with self.assertRaises(ValueError):
            controller.start(approved=True)

    def test_start_and_stop_are_cooperative(self):
        started = threading.Event()
        finished = threading.Event()
        states = []

        def runner(_api_key, *, stop_event, on_transcript):
            started.set()
            self.assertIsNone(on_transcript)
            while not stop_event.wait(0.01):
                pass
            finished.set()

        controller = LiveAudioController(
            "test-key", runner=runner, on_state=lambda *args: states.append(args)
        )
        self.assertTrue(controller.start(approved=True))
        self.assertTrue(started.wait(1))
        controller.stop()
        self.assertTrue(finished.wait(1))
        deadline = time.monotonic() + 1
        while controller.running and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertFalse(controller.running)
        self.assertIn(("stopped",), states)


if __name__ == "__main__":
    unittest.main()
