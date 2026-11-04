"""Local plugin catalog with Ed25519 manifest verification and safe archive extraction.

This is a secure local marketplace core, not a hosted public marketplace or publisher service.
"""
from __future__ import annotations
import hashlib, json, zipfile
from pathlib import Path, PurePosixPath

class PluginError(RuntimeError): pass

def verify_manifest(manifest: dict, public_key_hex: str) -> bool:
    signature=manifest.get("signature")
    if not isinstance(signature,str): raise PluginError("Manifest signature is missing.")
    payload={k:v for k,v in manifest.items() if k!="signature"}
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex)).verify(bytes.fromhex(signature),canonical)
        return True
    except ImportError as exc: raise PluginError("Install cryptography to verify marketplace signatures.") from exc
    except Exception as exc: raise PluginError("Plugin signature verification failed.") from exc

def install_archive(archive: str | Path, destination: str | Path, expected_sha256: str, manifest: dict, public_key_hex: str) -> dict:
    verify_manifest(manifest, public_key_hex)
    path=Path(archive); digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest.lower()!=expected_sha256.lower(): raise PluginError("Archive SHA-256 does not match signed catalog entry.")
    target=Path(destination).resolve(); target.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path) as zf:
        members=zf.infolist()
        if len(members)>200: raise PluginError("Plugin archive contains too many files.")
        for member in members:
            name=PurePosixPath(member.filename)
            if name.is_absolute() or ".." in name.parts or member.is_dir() and not name.parts:
                raise PluginError("Unsafe archive path.")
            resolved=(target / Path(*name.parts)).resolve()
            if target not in resolved.parents and resolved != target: raise PluginError("Archive path escapes plugin directory.")
            if member.file_size>2_000_000: raise PluginError("Plugin file exceeds 2 MB.")
        zf.extractall(target)
    return {"installed":manifest.get("name"),"version":manifest.get("version"),"directory":str(target),"files":len(members)}
