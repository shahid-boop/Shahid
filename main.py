"""Application entry point for Shahid Assistant."""
from __future__ import annotations

import argparse
import asyncio
import json

from dotenv import load_dotenv

load_dotenv()

from assistant_runtime import AssistantRuntime
from config_manager import load_config
from memory_manager import MemoryManager
from provider_registry import build_engine_pipeline
from skills.registry import build_skill_loader
from plugin_loader import PluginLoader


def build_runtime(config: dict) -> AssistantRuntime:
    skills = build_skill_loader()
    plugins = PluginLoader()
    for name in ("system_monitor", "web_search", "reminders", "proactive_checks"):
        plugins.register(name, lambda _name=name, **arguments: skills.run(_name, **arguments))
    return AssistantRuntime(
        engines=build_engine_pipeline(config),
        memory=MemoryManager(),
        provider_name=config.get("engine", "openai_compatible"),
        skills=skills,
        plugins=plugins,
        system_prompt=config.get(
            "system_prompt",
            "You are Shahid Assistant, a helpful Windows desktop AI assistant.",
        ),
    )



async def run_gemini_live_cli(config: dict) -> None:
    from speech.gemini_live import GeminiLiveClient

    client = GeminiLiveClient(
        model=config.get("gemini_live_model") or None,
        system_instruction=config.get(
            "system_prompt",
            "You are Shahid Assistant, a helpful Windows desktop AI assistant.",
        ),
    )
    await client.connect(response_modalities=("TEXT",))
    print("Gemini Live text session ready. Type /exit to disconnect.")
    try:
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
                answer = await client.text_turn(message)
                print(f"Gemini Live> {answer or '[No text returned]'}")
            except Exception as exc:
                print(f"Gemini Live error> {exc}")
    finally:
        await client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Shahid Assistant")
    parser.add_argument("--ui", action="store_true", help="Launch the desktop chat HUD")
    parser.add_argument("--server", action="store_true", help="Launch the local dashboard API")
    parser.add_argument("--settings", action="store_true", help="Open assistant settings")
    parser.add_argument("--reminders", action="store_true", help="Enable reminder notifications")
    parser.add_argument("--monitor", action="store_true", help="Enable opt-in background health monitoring")
    parser.add_argument("--gemini-live", action="store_true", help="Start a Gemini Live text session")
    args = parser.parse_args()

    if args.settings:
        from settings_ui import SettingsWindow
        SettingsWindow().run()
        return

    config = load_config()
    if args.gemini_live:
        asyncio.run(run_gemini_live_cli(config))
        return
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
        launch(runtime.respond, voice, config)
        return

    scheduler = None
    monitor = None
    if args.monitor:
        from skills.background_monitoring import BackgroundMonitoring
        monitor = BackgroundMonitoring(
            interval_seconds=int(config.get("monitor_interval_seconds", 300)),
            on_result=lambda result: print(f"Health monitor> {json.dumps(result, default=str)}"),
        )
        monitor.start()
        print("Background health monitoring enabled.")
    if args.reminders:
        from skills.reminder_scheduler import ReminderScheduler
        scheduler = ReminderScheduler()
        scheduler.start()
        print("Reminder notifications enabled.")

    print("CLI mode. Type /help for commands, /exit to quit.")
    try:
        while True:
            try:
                message = input("You> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if message.lower() in {"/exit", "/quit"}:
                break
            if message == "/help":
                print("/skills — list skills\n/skill NAME JSON — run a skill explicitly\n/plugins — list trusted plugins\n/plugin NAME JSON — run a trusted plugin\n/exit — quit")
                continue
            if message == "/skills":
                print(json.dumps(runtime.skills.list_skills(), indent=2))
                continue
            if message == "/plugins":
                print(json.dumps(runtime.plugins.list_plugins(), indent=2))
                continue
            if message.startswith("/plugin "):
                try:
                    _, name, raw = message.split(" ", 2)
                    arguments = json.loads(raw)
                    if not isinstance(arguments, dict):
                        raise ValueError("Plugin arguments must be a JSON object.")
                    print(json.dumps(runtime.run_plugin(name, **arguments), indent=2, default=str))
                except Exception as exc:
                    print(f"Plugin error> {exc}")
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
    finally:
        if scheduler is not None:
            scheduler.stop()
        if monitor is not None:
            monitor.stop()


if __name__ == "__main__":
    main()
