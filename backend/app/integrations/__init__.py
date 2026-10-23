"""Entegrasyon bağlayıcıları (ADIM 10). Yeni bağlayıcı: modülde CONNECTOR tanımla, aşağıdaki listeye ekle."""
from typing import Dict

from app.integrations.base import Connector
from app.integrations import telegram

REGISTRY: Dict[str, Connector] = {c.code: c for c in (telegram.CONNECTOR,)}


def get(code: str) -> Connector:
    return REGISTRY[code]
