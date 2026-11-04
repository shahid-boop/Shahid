"""Shahid Assistant entry point for Windows 11."""
from __future__ import annotations
import argparse
import json
import sys
from config_manager import Settings
from engine_pipeline import ChatEngine, ProviderError
from memory_manager import MemoryManager
from reminder_manager import ReminderManager
from skills.registry import SkillRegistry
from skills.windows_tools import register_windows_skills
from skills.file_tools import register_file_skills
from skills.agent_tasks import register_task_skills
from skills.system_monitor import register_monitoring_skill
from skills.web_search import register_web_search_skill
from skills.proactive_checks import register_proactive_skills

SYSTEM_PROMPT = ("You are Shahid Assistant, a helpful Windows desktop assistant. "
                 "Be accurate, concise, and state limitations.")

def build_registry() -> SkillRegistry:
    registry = SkillRegistry()
    register_windows_skills(registry)
    register_file_skills(registry)
    register_task_skills(registry)
    register_monitoring_skill(registry)
    register_web_search_skill(registry)
    register_proactive_skills(registry)
    return registry

def run_chat(voice: bool = False) -> int:
    settings = Settings.load()
    engine, memory, skills, reminders = ChatEngine(settings), MemoryManager(), build_registry(), ReminderManager()
    speech = None
    if voice:
        try:
            from speech_engine import SpeechEngine
            speech = SpeechEngine()
        except (ImportError, RuntimeError) as exc:
            print(f"Voice unavailable: {exc}", file=sys.stderr)
            return 2
    print("Shahid Assistant. Commands: /exit, /clear, /skills, /reminders")
    if voice:
        print("Voice mode enabled (Urdu-Pakistan recognition requested). Say 'exit' to quit.")
    while True:
        try:
            if speech:
                print("\nListening...")
                user_text = speech.listen()
                if not user_text:
                    continue
                print(f"You: {user_text}")
            else:
                user_text = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return 0
        command = user_text.strip()
        if command.lower() in {"/exit", "/quit", "exit"}:
            return 0
        if command.lower() == "/clear":
            memory.clear()
            print("Local conversation cleared.")
            continue
        if command.lower() == "/skills":
            print("Available local tools:", ", ".join(skills.names()))
            continue
        if command.lower() == "/reminders":
            items = reminders.list()
            print(json.dumps(items, ensure_ascii=False, indent=2) if items else "No pending reminders.")
            continue
        if command.lower().startswith("/remind "):
            try:
                item = reminders.add(command[8:].strip())
                print("Reminder saved:", json.dumps(item, ensure_ascii=False))
            except ValueError as exc:
                print(f"Reminder error: {exc}")
            continue
        if command.lower().startswith("/run "):
            try:
                _, name, raw = command.split(" ", 2)
                result = skills.run(name, json.loads(raw))
                print("Tool result:", json.dumps(result, ensure_ascii=False))
            except (ValueError, KeyError, json.JSONDecodeError, TypeError) as exc:
                print(f"Tool error: {exc}")
            continue
        if not command:
            continue
        memory.append("user", command)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(memory.get_messages())
        try:
            reply = engine.chat(messages)
        except ProviderError as exc:
            reply = f"AI provider error: {exc}"
        memory.append("assistant", reply)
        print(f"\nShahid: {reply}")
        if speech:
            try:
                speech.speak(reply)
            except RuntimeError as exc:
                print(f"Speech output error: {exc}", file=sys.stderr)

def main() -> int:
    parser = argparse.ArgumentParser(description="Shahid Assistant for Windows 11")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--server", action="store_true", help="Run localhost browser dashboard")
    mode.add_argument("--ui", action="store_true", help="Run desktop HUD")
    mode.add_argument("--chat", action="store_true", help="Run terminal chat")
    mode.add_argument("--voice", action="store_true", help="Run optional microphone and speech mode")
    args = parser.parse_args()
    try:
        if args.server:
            from server import serve
            serve(Settings.load())
        elif args.ui:
            from ui import run_ui
            run_ui()
        else:
            return run_chat(voice=args.voice)
    except KeyboardInterrupt:
        return 0
    except OSError as exc:
        print(f"Startup error: {exc}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
