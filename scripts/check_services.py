"""
RECOrion Çekirdek Altyapı Servisleri Doğrulama Betiği
Standart Python kütüphaneleri (socket, urllib) ile tüm Docker servislerinin erişilebilirliğini ve sağlık durumunu test eder.
"""

import socket
import urllib.request
import urllib.error
import sys
import time

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

SERVICES = [
    {
        "name": "PostgreSQL 16 (pgvector)",
        "type": "tcp",
        "host": "localhost",
        "port": 5432,
        "desc": "Dark DB - İlişkisel Veritabanı"
    },
    {
        "name": "Qdrant (Vektör DB)",
        "type": "http",
        "url": "http://localhost:6333/healthz",
        "desc": "2 Kademeli Kolektif Hafıza"
    },
    {
        "name": "Redis 7",
        "type": "redis",
        "host": "localhost",
        "port": 6379,
        "desc": "Streams & Canlı Düşünce Akışı"
    },
    {
        "name": "MinIO S3",
        "type": "http",
        "url": "http://localhost:9000/minio/health/live",
        "desc": "Artifact & Dosya Deposu"
    },
    {
        "name": "Gitea",
        "type": "http",
        "url": "http://localhost:3000/",
        "desc": "Yerel Git Sunucusu"
    },
    {
        "name": "Temporal Server (gRPC)",
        "type": "tcp",
        "host": "localhost",
        "port": 7233,
        "desc": "Dayanıklı İş Akışı Motoru"
    },
    {
        "name": "Temporal Web UI",
        "type": "http",
        "url": "http://localhost:8233/",
        "desc": "İş Akışı Görsel Paneli"
    }
]


def test_tcp(host, port, timeout=3):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, "Port açık ve dinliyor"
    except Exception as e:
        return False, str(e)


def test_http(url, timeout=4):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RECOrion-HealthChecker"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status in [200, 301, 302]:
                return True, f"HTTP {response.status} OK"
            return False, f"Beklenmeyen HTTP durumu: {response.status}"
    except urllib.error.HTTPError as e:
        if e.code in [200, 301, 302]:
            return True, f"HTTP {e.code}"
        return False, f"HTTP {e.code} - {e.reason}"
    except Exception as e:
        return False, str(e)


def test_redis(host, port, timeout=3):
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.sendall(b"PING\r\n")
        resp = s.recv(1024)
        s.close()
        if b"+PONG" in resp:
            return True, "PONG yanıtı alındı"
        return False, f"Beklenmeyen yanıt: {resp}"
    except Exception as e:
        return False, str(e)


def check_all():
    print("=" * 70)
    print("🔍 RECOrion Çekirdek Servisleri Sağlık Kontrolü")
    print("=" * 70)
    
    all_ok = True
    for s in SERVICES:
        name = s["name"]
        stype = s["type"]
        desc = s["desc"]
        
        if stype == "tcp":
            ok, msg = test_tcp(s["host"], s["port"])
        elif stype == "http":
            ok, msg = test_http(s["url"])
        elif stype == "redis":
            ok, msg = test_redis(s["host"], s["port"])
        else:
            ok, msg = False, "Bilinmeyen tip"
            
        status_icon = "✅ BAŞARILI" if ok else "❌ BAĞLANILAMADI"
        print(f"{status_icon} | {name:<26} | {desc:<30} | {msg}")
        if not ok:
            all_ok = False
            
    print("=" * 70)
    if all_ok:
        print("🎉 Tüm altyapı servisleri sağlıklı ve çalışıyor!")
    else:
        print("⚠️ Bazı servisler henüz hazır değil veya ayağa kalkmamış.")
    print("=" * 70)
    return all_ok


if __name__ == "__main__":
    check_all()
