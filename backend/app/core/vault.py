"""
Entegrasyon kimlik kasası (ADIM 10.1): bağlantı şifreleri (API anahtarı, token, parola) AES-256-GCM ile şifrelenir.

- Anahtar RECORION_VAULT_KEY (.env, base64 32 bayt); DevOps adımında KMS'e taşınacak.
- Şifreli metin bağlantıya bağlanır (ek doğrulanmış veri = şirket + bağlantı kimliği): başka bir kayda kopyalanırsa çözülmez.
- Şifreler API yanıtında asla dönmez; yalnızca yazılabilir. Kayıtlarda ve hata iletilerinde gösterilmez.
"""
import base64
import json
import os
from typing import Any, Dict

from app.config import settings

PREFIX = "v1:"


class VaultError(Exception):
    pass


def _key() -> bytes:
    raw = settings.RECORION_VAULT_KEY
    if not raw:
        raise VaultError("Kimlik kasası anahtarı tanımlı değil (RECORION_VAULT_KEY).")
    try:
        key = base64.b64decode(raw)
    except ValueError as exc:
        raise VaultError("Kimlik kasası anahtarı geçersiz.") from exc
    if len(key) != 32:
        raise VaultError("Kimlik kasası anahtarı 32 bayt olmalı.")
    return key


def enabled() -> bool:
    try:
        _key()
        return True
    except VaultError:
        return False


def seal(secrets: Dict[str, Any], binding: str) -> str:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    nonce = os.urandom(12)
    ct = AESGCM(_key()).encrypt(nonce, json.dumps(secrets, ensure_ascii=False).encode("utf-8"), binding.encode("utf-8"))
    return PREFIX + base64.b64encode(nonce + ct).decode()


def unseal(token: str, binding: str) -> Dict[str, Any]:
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    if not token:
        return {}
    if not token.startswith(PREFIX):
        raise VaultError("Şifreli kayıt biçimi tanınmadı.")
    blob = base64.b64decode(token[len(PREFIX):])
    try:
        data = AESGCM(_key()).decrypt(blob[:12], blob[12:], binding.encode("utf-8"))
    except InvalidTag as exc:
        raise VaultError("Bağlantı şifreleri çözülemedi (anahtar değişmiş veya kayıt başka bağlantıya ait).") from exc
    return json.loads(data)


def mask(secrets: Dict[str, Any]) -> Dict[str, bool]:
    """Ekran için: hangi şifre alanı dolu (değer gösterilmez)."""
    return {k: bool(v) for k, v in (secrets or {}).items()}
