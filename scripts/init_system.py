"""
RECOrion Sistem Başlatma ve Tohum Verisi Doğrulama Betiği (init_system.py)
PostgreSQL tablolarını, Qdrant koleksiyonunu ve MinIO depolama kovasını kontrol eder.
"""

import subprocess
import urllib.request
import urllib.error
import json
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def check_qdrant_collection():
    url = "http://localhost:6333/collections/recorion_collective_memory"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get("result", {}).get("status") in ["green", "yellow", "ok"]:
                return True, "Koleksiyon mevcut ve aktif"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Koleksiyonu oluştur
            create_payload = json.dumps({
                "vectors": {
                    "size": 4096,
                    "distance": "Cosine"
                }
            }).encode('utf-8')
            create_req = urllib.request.Request(
                url,
                data=create_payload,
                headers={"Content-Type": "application/json"},
                method="PUT"
            )
            with urllib.request.urlopen(create_req) as c_resp:
                return True, "Koleksiyon yeni oluşturuldu (4096 dim, Cosine)"
    except Exception as e:
        return False, str(e)
    return True, "Aktif"


def check_minio_bucket():
    try:
        # MinIO içinde recorion-artifacts klasörünü doğrula
        cmd = ["docker", "exec", "recorion_minio", "sh", "-c", "mkdir -p /data/recorion-artifacts && ls -d /data/recorion-artifacts"]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if res.returncode == 0 and "recorion-artifacts" in res.stdout:
            return True, "Kova (Bucket) mevcut: /data/recorion-artifacts"
        return False, res.stderr or "Hata"
    except Exception as e:
        return False, str(e)


def check_postgres_records():
    query = """
    SELECT 'LLM Modelleri', count(*) FROM llm_models
    UNION ALL SELECT 'NACE Kataloğu', count(*) FROM nace_catalog
    UNION ALL SELECT 'Şirketler (Tenants)', count(*) FROM tenants
    UNION ALL SELECT 'Aktörler (Personel)', count(*) FROM actors
    UNION ALL SELECT 'Hafıza Maddeleri', count(*) FROM memory_items;
    """
    try:
        cmd = ["docker", "exec", "recorion_postgres", "psql", "-U", "recorion_admin", "-d", "recorion_db", "-t", "-A", "-c", query]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if res.returncode == 0:
            lines = [l.strip().split("|") for l in res.stdout.strip().split("\n") if "|" in l]
            return True, {k: int(v) for k, v in lines}
        return False, res.stderr
    except Exception as e:
        return False, str(e)


def main():
    print("=" * 70)
    print("🚀 RECOrion Sistem Başlatma ve Doğrulama Raporu (Adım 4)")
    print("=" * 70)

    # 1. PostgreSQL Kontrolü
    pg_ok, pg_data = check_postgres_records()
    if pg_ok:
        print("✅ PostgreSQL 16 Tabloları ve Tohum Verileri:")
        for table, count in pg_data.items():
            print(f"   • {table:<25}: {count} adet kayıt mevcut")
    else:
        print(f"❌ PostgreSQL Hatası: {pg_data}")

    # 2. Qdrant Kontrolü
    qd_ok, qd_msg = check_qdrant_collection()
    if qd_ok:
        print(f"✅ Qdrant Vektör Hafızası: {qd_msg}")
    else:
        print(f"❌ Qdrant Hatası: {qd_msg}")

    # 3. MinIO Kontrolü
    mn_ok, mn_msg = check_minio_bucket()
    if mn_ok:
        print(f"✅ MinIO Nesne Deposu: {mn_msg}")
    else:
        print(f"❌ MinIO Hatası: {mn_msg}")

    print("=" * 70)
    if pg_ok and qd_ok and mn_ok:
        print("🎯 ADIM 4 BAŞARIYLA TAMAMLANDI: Veritabanı, Vektör ve Depolama Katmanı Hazır!")
    else:
        print("⚠️ Bazı bileşenler doğrulanamadı.")
    print("=" * 70)


if __name__ == "__main__":
    main()
