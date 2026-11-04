"""Run on the target Windows 11 PC to verify local devices and credentials."""
from __future__ import annotations

import json
import os
import platform
import sys
from datetime import datetime, timezone


def main() -> int:
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python": sys.version,
        "checks": {},
    }
    if platform.system() != "Windows":
        report["checks"]["windows_11"] = {"ok": False, "detail": "Run this script on Windows 11."}
    else:
        report["checks"]["windows_11"] = {"ok": platform.release() == "11" or int(platform.version().split(".")[-1]) >= 22000, "detail": platform.version()}

    try:
        import sounddevice as sd
        devices = sd.query_devices()
        inputs = [{"name": d["name"], "channels": d["max_input_channels"]}
                  for d in devices if d["max_input_channels"] > 0]
        outputs = [{"name": d["name"], "channels": d["max_output_channels"]}
                   for d in devices if d["max_output_channels"] > 0]
        report["checks"]["audio_devices"] = {
            "ok": bool(inputs and outputs), "inputs": inputs, "outputs": outputs,
        }
        if inputs:
            try:
                sd.check_input_settings(device=None, channels=1, dtype="int16")
                report["checks"]["microphone_stream"] = {"ok": True, "detail": "Default input format accepted."}
            except Exception as exc:
                report["checks"]["microphone_stream"] = {"ok": False, "detail": str(exc)}
        else:
            report["checks"]["microphone_stream"] = {"ok": False, "detail": "No input device detected."}
    except Exception as exc:
        report["checks"]["audio_devices"] = {"ok": False, "detail": str(exc)}

    try:
        import cv2
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        ok, frame = camera.read()
        camera.release()
        report["checks"]["camera"] = {
            "ok": bool(ok and frame is not None),
            "detail": "Frame captured." if ok else "No frame from default camera.",
        }
    except Exception as exc:
        report["checks"]["camera"] = {"ok": False, "detail": str(exc)}

    credentials = bool(os.getenv("OPENAI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    report["checks"]["provider_credentials"] = {"ok": credentials, "detail": "At least one provider key is configured." if credentials else "Set OPENAI_API_KEY or GOOGLE_API_KEY in the environment."}
    report["checks"]["docker_sandbox"] = {"ok": False, "detail": "Not checked by this diagnostic; run docker info."}
    try:
        import shutil
        import subprocess
        docker = shutil.which("docker")
        if docker:
            result = subprocess.run([docker, "info", "--format", "{{.ServerVersion}}"],
                                    capture_output=True, text=True, timeout=5)
            report["checks"]["docker_sandbox"] = {
                "ok": result.returncode == 0,
                "detail": result.stdout.strip() if result.returncode == 0 else result.stderr.strip(),
            }
    except Exception as exc:
        report["checks"]["docker_sandbox"] = {"ok": False, "detail": str(exc)}

    print(json.dumps(report, indent=2))
    return 0 if all(item.get("ok") for item in report["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
