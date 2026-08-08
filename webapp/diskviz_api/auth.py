import hashlib
from fastapi import Request, HTTPException, Depends
from typing import Optional
from .config import settings

def _extract_token(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return request.query_params.get("token")

def require_token(require_write: bool = False):
    """Dependency factory. Usage: Depends(require_token(True))"""
    async def _dep(request: Request):
        token = _extract_token(request)
        if not token:
            raise HTTPException(401, "missing token")
        token_sha = hashlib.sha256(token.encode()).hexdigest()
        if token_sha == settings.write_token_sha256:
            return {"scope": "write", "token": token}
        if not require_write and token_sha == settings.read_token_sha256:
            return {"scope": "read", "token": token}
        raise HTTPException(401, "invalid or insufficient token")
    return _dep

def verify_confirm_token(confirm: str) -> bool:
    """Write operation二次确认: confirm should be SHA256 of write-token."""
    if not confirm:
        return False
    return confirm == settings.write_token_sha256
