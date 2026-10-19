"""
Dış web adreslerine güvenli erişim (SSRF koruması).

Kullanıcının verdiği bir URL çekilmeden önce hedefin genel internette olduğu
doğrulanır. Yerel ağ, loopback, link-local, Docker iç servisleri (postgres,
redis, qdrant ...) ve özel IP aralıkları reddedilir. Yönlendirmeler elle
izlenir ve her adımda aynı kontrol tekrarlanır.
"""
import asyncio
import ipaddress
import socket
from typing import Dict, Optional
from urllib.parse import urljoin, urlparse

import httpx

MAX_REDIRECTS = 5


class UnsafeURLError(ValueError):
    """Hedef adres güvenli değil veya erişime kapalı."""


def _is_public_ip(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    return not (
        addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_multicast
        or addr.is_reserved or addr.is_unspecified
        or (addr.version == 6 and addr.ipv4_mapped is not None and not _is_public_ip(str(addr.ipv4_mapped)))
    )


async def assert_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeURLError("Yalnızca http ve https adreslerine izin verilir.")
    if not parsed.hostname:
        raise UnsafeURLError("Geçersiz adres.")
    if parsed.port not in (None, 80, 443):
        raise UnsafeURLError("Yalnızca standart web portlarına (80/443) izin verilir.")

    try:
        infos = await asyncio.get_running_loop().getaddrinfo(parsed.hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeURLError(f"Adres çözümlenemedi: {parsed.hostname}") from exc

    for info in infos:
        if not _is_public_ip(info[4][0]):
            raise UnsafeURLError("İç ağdaki veya özel IP adreslerine erişime izin verilmez.")


async def safe_request(
    method: str,
    url: str,
    *,
    timeout: float = 20.0,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, str]] = None,
) -> httpx.Response:
    """Her yönlendirmede hedefi yeniden doğrulayarak istek atar."""
    current = url
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False, headers=headers) as client:
        for _ in range(MAX_REDIRECTS + 1):
            await assert_public_url(current)
            resp = await client.request(method, current, data=data)
            if resp.is_redirect and "location" in resp.headers:
                current = urljoin(current, resp.headers["location"])
                method, data = "GET", None
                continue
            return resp
    raise UnsafeURLError("Çok fazla yönlendirme.")
