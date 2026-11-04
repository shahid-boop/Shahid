"""Application entry point for Shahid Assistant."""
from __future__ import annotations

import argparse

from assistant_runtime import AssistantRuntime
from config_manager import load_config
from engine_pipeline import EnginePipeline
from memory_manager import MemoryManager
from provider_registry import build_engine_pipeline


def build_runtime(config: dict) -> AssistantRuntime:
    engines: EnginePipeline = build_engine_pipeline(config)
    return AssistantRuntime(
        engines=engines,
        memory=MemoryManager(),
        provider_name=config.get("engine", "openai_compatible"),
        system_prompt=config.get(
            "system_prompt",
            "You are Shahid Assistant, a helpful desktop AI assistant.",
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Shahid Assistant")
    parser.add_argument("--ui", action="store_true", help="Launch the desktop HUD")
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
                "status": "ready",
            },
            chat_handler=runtime.respond,
        )
        return

    if args.ui:
        from ui import launch
        launch(runtime.respond)
        return

    print("CLI mode. Type /exit to quit.")
    while True:
        try:
            message = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if message.lower() in {"/exit", "/quit"}:
            break
        if not message:
            continue
        try:
            print(f"Assistant> {runtime.respond(message)}")
        except Exception as exc:
            print(f"Error> {exc}")


if __name__ == "__main__":
    main()
