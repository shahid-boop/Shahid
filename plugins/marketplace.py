"""Signed local plugin package installer; activation remains a separate reviewed step."""
from __future__ import annotations
import hashlib, json, zipfile
from pathlib import Path, PurePosixPath
class PluginError(RuntimeError): pass

def verify_manifest(manifest, public_key_hex):
    if not isinstance(manifest,dict): raise PluginError("Manifest must be an object")
    signature=manifest.get("signature")
    if not isinstance(signature,str): raise PluginError("Manifest signature is missing")
    payload={k:v for k,v in manifest.items() if k!="signature"}
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex)).verify(bytes.fromhex(signature),canonical)
        return True
    except ImportError as exc: raise PluginError("Install cryptography from requirements-live.txt") from exc
    except Exception as exc: raise PluginError("Plugin signature verification failed") from exc

def install_archive(archive,destination,expected_sha256,manifest,public_key_hex):
    verify_manifest(manifest,public_key_hex)
    if not all(manifest.get(k) for k in ("id","version","entrypoint")): raise PluginError("Manifest requires id, version and entrypoint")
    path=Path(archive)
    if not path.is_file(): raise PluginError("Plugin archive does not exist")
    if hashlib.sha256(path.read_bytes()).hexdigest().lower()!=str(expected_sha256).lower(): raise PluginError("Archive SHA-256 mismatch")
    target=Path(destination).resolve()
    with zipfile.ZipFile(path) as zf:
        members=zf.infolist()
        if len(members)>200: raise PluginError("Plugin archive contains too many files")
        total=0
        for member in members:
            name=PurePosixPath(member.filename); mode=(member.external_attr>>16)&0xFFFF
            if name.is_absolute() or ".." in name.parts or not name.parts or (mode&0o170000)==0o120000:
                raise PluginError("Unsafe archive path or symlink")
            resolved=(target/Path(*name.parts)).resolve()
            if target not in resolved.parents and resolved!=target: raise PluginError("Archive path escapes plugin directory")
            if member.file_size>2_000_000: raise PluginError("Plugin file exceeds 2 MB")
            total+=member.file_size
            if total>10_000_000: raise PluginError("Plugin package exceeds 10 MB")
        if manifest["entrypoint"] not in {m.filename for m in members}: raise PluginError("Manifest entrypoint missing from archive")
        target.mkdir(parents=True,exist_ok=True); zf.extractall(target)
    return {"installed":manifest.get("name",manifest["id"]),"id":manifest["id"],"version":manifest["version"],"directory":str(target),"files":len(members),"activation":"manual_review_required"}
