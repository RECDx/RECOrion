"""İSTEK #752 tıklama taraması: örnek uygulamada ölü düğme, JS hatası, ölü bağlantı ve README iddiası yakalanır.
Çalıştırma (Playwright'lı çalışma imajında):
  docker run --rm -v <repo>/sandbox:/s recorion-sandbox-runtime:2 python /s/tests/check_crawl.py"""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "runner"))
import smoke  # noqa: E402

work = tempfile.mkdtemp()
shutil.copytree(os.path.join(HERE, "crawl_app"), work, dirs_exist_ok=True)
smoke.WORK, smoke.OUT = work, os.path.join(work, ".rx-smoke.json")
smoke.main()
r = json.load(open(smoke.OUT, encoding="utf-8"))
checks = {c["name"]: c for c in r["checks"]}
cr = r["crawl"]
assert r["status"] == "FAILED", r["status"]
assert checks["Ana sayfa"]["ok"] is True
assert [d["label"] for d in cr["dead_buttons"]] == ["Kapat"], cr["dead_buttons"]  # Filtrele ve uyarı açan Bilgi canlı
assert [d["href"] for d in cr["dead_links"]] == ["/yok.html"], cr["dead_links"]  # dış bağlantı denenmez
assert len(cr["js_errors"]) == 1 and "undefinedFn" in cr["js_errors"][0]["error"]
assert {p["path"] for p in cr["pages"]} == {"/", "/detay.html"}
assert checks["Tıklama taraması"]["ok"] is False and "'Kapat'" in checks["Tıklama taraması"]["detail"]
assert r["doc_claims"]["missing"] == ["sol menü"] and checks["Belge iddiaları sayfada"]["ok"] is False
print("check_crawl: GEÇTİ")
