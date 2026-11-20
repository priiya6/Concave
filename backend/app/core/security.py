import base64, hashlib, hmac, json, time
from fastapi import HTTPException
from .config import settings

def hash_password(password: str) -> str:
    salt = hashlib.sha256(settings.secret_key.encode()).digest()[:16]
    return base64.urlsafe_b64encode(salt).decode() + "." + hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000).hex()

def verify_password(password: str, encoded: str) -> bool:
    try:
        salt_b64, digest = encoded.split(".", 1)
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        return hmac.compare_digest(hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000).hex(), digest)
    except ValueError:
        return False

def create_token(user_id: int, role: str) -> str:
    payload = {"uid": user_id, "role": role, "exp": int(time.time()) + 43200}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    sig = hmac.new(settings.secret_key.encode(), raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=") + "." + base64.urlsafe_b64encode(sig).decode().rstrip("=")

def decode_token(token: str) -> dict:
    try:
        part, sig = token.split(".", 1)
        raw = base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))
        expected = hmac.new(settings.secret_key.encode(), raw, hashlib.sha256).digest()
        actual = base64.urlsafe_b64decode(sig + "=" * (-len(sig) % 4))
        data = json.loads(raw)
        if not hmac.compare_digest(actual, expected) or data["exp"] < time.time(): raise ValueError
        return data
    except Exception:
        raise HTTPException(401, detail={"code":"unauthorized","message":"Invalid or expired token"})

