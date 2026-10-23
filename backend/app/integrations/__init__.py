"""Entegrasyon bağlayıcıları (ADIM 10). Yeni bağlayıcı: modülde CONNECTOR tanımla, aşağıdaki listeye ekle."""
from typing import Dict

from app.integrations.base import Connector
from app.integrations import git_hosting, odoo, telegram, trello

REGISTRY: Dict[str, Connector] = {c.code: c for c in (odoo.CONNECTOR, trello.CONNECTOR, git_hosting.GITHUB, git_hosting.GITEA,
                                                      telegram.CONNECTOR)}


def get(code: str) -> Connector:
    return REGISTRY[code]
