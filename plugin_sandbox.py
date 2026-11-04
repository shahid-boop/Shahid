"""Docker-isolated execution for untrusted third-party Python plugins.

Requires Docker Desktop with Linux containers. No host folders, network,
Linux capabilities, or writable container root are exposed to the plugin.
The Docker daemon remains part of the trusted computing base.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any


class PluginSandboxError(RuntimeError):
    pass


class DockerPluginSandbox:
    def __init__(
        self,
        image: str = "python:3.12-alpine",
        timeout_seconds: int = 8,
        memory_limit: str = "128m",
        cpu_limit: str = "0.50",
        max_output_bytes: int = 64_000,
    ) -> None:
        if not image or timeout_seconds < 1 or timeout_seconds > 60:
            raise ValueError("Invalid sandbox image or timeout.")
        self.image = image
        self.timeout_seconds = timeout_seconds
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.max_output_bytes = max_output_bytes

    @staticmethod
    def available() -> bool:
        docker = shutil.which("docker")
        if not docker:
            return False
        try:
            result = subprocess.run(
                [docker, "info", "--format", "{{.ServerVersion}}"],
                capture_output=True, text=True, timeout=3, check=False,
            )
            return result.returncode == 0 and bool(result.stdout.strip())
        except (OSError, subprocess.TimeoutExpired):
            return False

    def run(self, source: str, payload: dict[str, Any] | None = None) -> Any:
        if not isinstance(source, str) or not source.strip() or len(source) > 64_000:
            raise ValueError("Plugin source must contain 1-64000 characters.")
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            raise TypeError("Plugin payload must be a JSON object.")
        docker = shutil.which("docker")
        if not docker:
            raise PluginSandboxError("Docker CLI not found. Install Docker Desktop and enable Linux containers.")

        # The plugin source is data on stdin, not interpolated into the shell/CLI command.
        envelope = json.dumps({"source": source, "payload": payload}, ensure_ascii=False)
        runner = (
            "import json,sys\n"
            "d=json.load(sys.stdin)\n"
            "ns={'__name__':'__plugin__'}\n"
            "exec(compile(d['source'],'<sandbox-plugin>','exec'),ns,ns)\n"
            "fn=ns.get('run')\n"
            "if not callable(fn): raise RuntimeError('Plugin must define run(payload)')\n"
            "result=fn(d['payload'])\n"
            "print(json.dumps({'ok':True,'result':result},ensure_ascii=False,default=str))\n"
        )
        command = [
            docker, "run", "--rm", "-i",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--pids-limit=32",
            f"--memory={self.memory_limit}",
            f"--cpus={self.cpu_limit}",
            "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=8m",
            "--user=65534:65534",
            self.image, "python", "-I", "-c", runner,
        ]
        try:
            completed = subprocess.run(
                command, input=envelope, capture_output=True, text=True,
                timeout=self.timeout_seconds, check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise PluginSandboxError("Plugin exceeded its execution time limit.") from exc
        except OSError as exc:
            raise PluginSandboxError(f"Could not start Docker sandbox: {exc}") from exc

        output = completed.stdout[-self.max_output_bytes:]
        if completed.returncode != 0:
            detail = completed.stderr[-4000:].strip()
            raise PluginSandboxError(detail or f"Sandbox exited with code {completed.returncode}.")
        try:
            result = json.loads(output.strip().splitlines()[-1])
        except (ValueError, IndexError) as exc:
            raise PluginSandboxError("Plugin returned invalid or oversized JSON output.") from exc
        if not result.get("ok"):
            raise PluginSandboxError("Plugin execution failed.")
        return result.get("result")
