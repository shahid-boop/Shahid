"""Application entry point for Shahid Assistant."""
from __future__ import annotations

import argparse
import json

from assistant_runtime import AssistantRuntime
from config_manager import load_config
from memory_manager import MemoryManager
from provider_registry import build_engine_pipeline
from skills.registry import build_skill_loader


def build_runtime(config: dict) -> AssistantRuntime:
    return AssistantRuntime(
        engines=build_engine_pipeline(config),
        memory=MemoryManager(),
        provider_name=config.get("engine", "openai_compatible"),
        skills=build_skill_loader(),
        system_prompt=config.get(
            "system_prompt",
            "You are Shahid Assistant, a helpful Windows desktop AI assistant.",
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Shahid Assistant")
    parser.add_argument("--ui", action="store_true", help="Launch the desktop chat HUD")
    parser.add_argument("--server", action="store_true", help="Launch the local dashboard API")
    args = parser.parse_args()

    config = load_config()
    runtime = build_runtime(config)
    print(f"{config['assistant_name']} starting...")

    if args.server:
        from server import serve
        serve(
            status_provider=lambda: {
                "name": config["assistant_name"],
                "engine": config.get("engine", "openai_compatible"),
                "providers": runtime.engines.available_providers(),
                "skills": [item["name"] for item in runtime.skills.list_skills()],
                "status": "ready",
            },
            chat_handler=runtime.respond,
        )
        return

    if args.ui:
        from speech.voice_controller import WindowsVoiceController
        from ui import launch
        voice = WindowsVoiceController(
            sample_rate=int(config.get("voice_sample_rate", 16000)),
            seconds=int(config.get("voice_record_seconds", 6)),
        )
        launch(runtime.respond, voice)
        return

    print("CLI mode. Type /help for commands, /exit to quit.")
    while True:
        try:
            message = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if message.lower() in {"/exit", "/quit"}:
            break
        if message == "/help":
            print("/skills — list skills\n/skill NAME JSON — run a skill explicitly\n/exit — quit")
            continue
        if message == "/skills":
            print(json.dumps(runtime.skills.list_skills(), indent=2))
            continue
        if message.startswith("/skill "):
            try:
                _, name, raw = message.split(" ", 2)
                arguments = json.loads(raw)
                if not isinstance(arguments, dict):
                    raise ValueError("Skill arguments must be a JSON object.")
                print(json.dumps(runtime.run_skill(name, **arguments), indent=2, default=str))
            except Exception as exc:
                print(f"Skill error> {exc}")
            continue
        if not message:
            continue
        try:
            print(f"Assistant> {runtime.respond(message)}")
        except Exception as exc:
            print(f"Error> {exc}")


if __name__ == "__main__":
    main()
