"""Entegrasyon bağlayıcıları (ADIM 10). Yeni bağlayıcı: modülde CONNECTOR tanımla, aşağıdaki listeye ekle."""
from typing import Dict

from app.integrations.base import Connector
from app.integrations import edge, git_hosting, mail, mcp, odoo, telegram, trello, web_source

REGISTRY: Dict[str, Connector] = {c.code: c for c in (odoo.CONNECTOR, trello.CONNECTOR, git_hosting.GITHUB, git_hosting.GITEA,
                                                      telegram.CONNECTOR, mcp.CONNECTOR, edge.CONNECTOR,
                                                      mail.CONNECTOR, web_source.CONNECTOR)}  # #740


def get(code: str) -> Connector:
    return REGISTRY[code]
