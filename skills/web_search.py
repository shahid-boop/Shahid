"""Optional web search adapter for a configured HTTPS JSON search endpoint."""
import json, os
from urllib.parse import urlencode
from urllib.request import Request, urlopen
def web_search(payload=None):
    query=str((payload or {}).get("query","")).strip()
    if not query or len(query)>500: raise ValueError("query must be 1-500 characters.")
    endpoint=os.getenv("WEB_SEARCH_URL","").strip()
    if not endpoint.startswith("https://"): raise RuntimeError("Set WEB_SEARCH_URL to an HTTPS search API endpoint.")
    req=Request(endpoint+("&" if "?" in endpoint else "?")+urlencode({"q":query}),headers={"Accept":"application/json","User-Agent":"ShahidAssistant/1.0"})
    try:
        with urlopen(req,timeout=15) as response: data=json.loads(response.read(1_000_000).decode("utf-8"))
    except Exception as exc: raise RuntimeError(f"Search request failed: {exc}") from exc
    results=data.get("results",[]) if isinstance(data,dict) else []
    if not isinstance(results,list): raise RuntimeError("Search endpoint returned invalid results.")
    return {"query":query,"results":results[:10]}
def register_web_search_skill(registry): registry.register("web_search",web_search)
