"""Assistant application entry point — foundation stage."""
from __future__ import annotations

from config_manager import load_config
from memory_manager import MemoryManager


def main() -> None:
    config = load_config()
    memory = MemoryManager()
    print(f"{config['assistant_name']} foundation is ready.")
    print(f"Configured engine: {config['engine']}")
    print(f"Stored memory items: {len(memory.recent(limit=100000))}")
    print("Provider connections and interactive UI are not configured yet.")


if __name__ == "__main__":
    main()
