"""Shahid Assistant entry point for Windows 11."""
from __future__ import annotations
import argparse
import sys
from config_manager import Settings
from engine_pipeline import ChatEngine, ProviderError
from memory_manager import MemoryManager

def run_chat() -> int:
    settings = Settings.load()
    engine, memory = ChatEngine(settings), MemoryManager()
    print("Shahid Assistant CLI. Type /exit to quit, /clear to clear local conversation.")
    while True:
        try:
            text = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return 0
        if text.lower() in {"/exit", "/quit"}:
            return 0
        if text.lower() == "/clear":
            memory.clear()
            print("Local conversation cleared.")
            continue
        if not text:
            continue
        memory.append("user", text)
        messages = [{"role":"system","content":"You are Shahid Assistant, a helpful Windows desktop assistant. Be accurate and state limitations."}]
        messages.extend(memory.get_messages())
        try:
            reply = engine.chat(messages)
        except ProviderError as exc:
            print(f"\nShahid: {exc}")
            continue
        memory.append("assistant", reply)
        print(f"\nShahid: {reply}")

def main() -> int:
    parser = argparse.ArgumentParser(description="Shahid Assistant for Windows 11")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--server", action="store_true", help="Run localhost browser dashboard")
    mode.add_argument("--ui", action="store_true", help="Run desktop HUD")
    mode.add_argument("--chat", action="store_true", help="Run terminal chat")
    args = parser.parse_args()
    try:
        if args.server:
            from server import serve
            serve(Settings.load())
        elif args.ui:
            from ui import run_ui
            run_ui()
        else:
            return run_chat()
    except KeyboardInterrupt:
        return 0
    except OSError as exc:
        print(f"Startup error: {exc}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
