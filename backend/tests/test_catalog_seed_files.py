"""
Depodaki platform kataloğu dosyalarının (app/seed/catalog/*.json) biçim ve kapsam denetimi.
Biçim: app/seed/catalog/README.md
"""
import json
import re

import pytest

from app.services.catalog_seed import SEED_DIR, seed_files

CODE = re.compile(r"^[A-Z0-9_]{2,64}$")
SENIORITY = {"JUNIOR", "MID", "SENIOR", "LEAD", "MANAGER"}
MODELS = {"mimo-v2.6-pro", "deepseek-v4.1-flash", "deepseek-v4-flash", "gemma-4-31b", "qwen3-vl-30b"}
FILES = seed_files(SEED_DIR)


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_seed_files_exist():
    assert any(p.name == "general.json" for p in FILES)


@pytest.fixture(scope="module")
def catalog():
    return {p.name: _load(p) for p in FILES}


def test_codes_unique_across_files(catalog):
    dept_codes, title_codes = {}, {}
    for name, data in catalog.items():
        for d in data["departments"]:
            if not d["code"].startswith("GEN_") or name == "general.json":
                assert d["code"] not in dept_codes, f"{name}: {d['code']} tekrar ({dept_codes.get(d['code'])})"
                dept_codes[d["code"]] = name
            for t in d["titles"]:
                assert t["code"] not in title_codes, f"{name}: {t['code']} tekrar ({title_codes.get(t['code'])})"
                title_codes[t["code"]] = name
    general = {d["code"] for d in catalog["general.json"]["departments"]}
    for name, data in catalog.items():
        for d in data["departments"]:
            if d["code"].startswith("GEN_"):
                assert d["code"] in general, f"{name}: bilinmeyen genel departman {d['code']}"


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_file_structure(path, db):
    data = _load(path)
    sector = data.get("sector_code")
    assert data["scope"] == ("GENERAL" if path.name == "general.json" else "SECTOR")
    with db.cursor() as cur:
        cur.execute("SELECT code FROM professions WHERE sector_code = %s", (sector,))
        professions = {r[0] for r in cur.fetchall()}
    covered = {}
    for d in data["departments"]:
        assert CODE.match(d["code"]), d["code"]
        if not d["code"].startswith("GEN_") or path.name == "general.json":
            assert d.get("name"), d["code"]
            if sector:
                assert d["code"].startswith(f"{sector}_"), d["code"]
        for p in d.get("professions") or []:
            assert p in professions, f"{d['code']}: geçersiz meslek kodu {p}"
        for t in d["titles"]:
            where = f"{path.name}/{t['code']}"
            assert CODE.match(t["code"]) and t["code"].startswith(f"{sector}_" if sector else "GEN_"), where
            for field in ("title", "description", "role_prompt"):
                assert (t.get(field) or "").strip(), f"{where}: {field} boş"
            assert t["seniority"] in SENIORITY, where
            assert t["autonomy_level"] in {"L1", "L2"}, where
            assert t["recommended_model_code"] in MODELS, where
            assert 5 <= len(t["responsibilities"]) <= 7 and 5 <= len(t["skills"]) <= 8 and 3 <= len(t["kpis"]) <= 5, where
            words = len(t["role_prompt"].split())
            assert 150 <= words <= 300 and t["role_prompt"].startswith("Sen"), f"{where}: {words} kelime"
            for p in t.get("professions") or []:
                assert p in professions, f"{where}: geçersiz meslek kodu {p}"
                covered[p] = covered.get(p, 0) + 1
    if sector:
        missing = sorted(p for p in professions if covered.get(p, 0) < 2)
        assert not missing, f"{path.name}: 2'den az unvanla kapsanan meslek grupları: {missing}"
