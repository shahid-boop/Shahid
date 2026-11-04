"""Explicit provider registry without dynamic imports."""
class ProviderRegistry:
    def __init__(self): self._providers={}
    def register(self,name,provider):
        key=str(name).strip().lower()
        if not key or not key.replace("-","").replace("_","").isalnum(): raise ValueError("Invalid provider name.")
        if key in self._providers: raise ValueError(f"Provider already registered: {key}")
        if not callable(getattr(provider,"chat",None)): raise TypeError("Provider must expose chat(messages).")
        self._providers[key]=provider
    def get(self,name):
        try: return self._providers[str(name).strip().lower()]
        except KeyError as exc: raise KeyError(f"Unknown provider: {name}") from exc
    def names(self): return sorted(self._providers)
