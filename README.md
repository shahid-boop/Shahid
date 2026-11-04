# Shahid Assistant

A modular desktop assistant following the supplied architecture diagram.

## Architecture modules

- `main.py` — application/runtime entry point.
- `config_manager.py` — local configuration with safe defaults.
- `memory_manager.py` — persistent local memory store.
- `engine_pipeline.py` — provider-neutral engine contract and dispatcher.

The planned next layers are the provider implementations (LLM, speech input/output),
user interfaces (dashboard and HUD), skills/control modules, live conversation,
plugin loading, proactive/background monitoring, and computer/file controls.

## Run the foundation

Requires Python 3.10 or newer. No third-party packages are required for this stage.

```bash
python main.py
python -m unittest discover -s tests
```

Configuration and memory are created under `data/` when first saved. Do not put API
keys or other secrets in the JSON configuration file; use environment variables for
credentials when provider integrations are added.

## Current scope

This is the first foundation milestone only. External AI providers, voice services,
HUD/dashboard UI, automation and operating-system controls are not implemented yet.
