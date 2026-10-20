"""
Platform departman ve unvan kataloğunun başlangıç verisini yükler (app/seed/catalog/*.json).

Yalnızca eksik kayıtlar eklenir: aynı kodlu departman veya unvan varsa dokunulmaz, böylece
Süper Admin'in katalogda yaptığı düzenlemeler ve sildiği (pasife aldığı) kayıtlar korunur.
Biçim: app/seed/catalog/README.md
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CatalogDepartment, JobTitle, Profession, Sector

logger = logging.getLogger("recorion.catalog")

SEED_DIR = Path(__file__).resolve().parent.parent / "seed" / "catalog"


def seed_files(directory: Path = SEED_DIR) -> List[Path]:
    files = sorted(directory.glob("sector_*.json"))
    general = directory / "general.json"
    return ([general] if general.exists() else []) + files  # genel departmanlar önce


async def load_catalog(db: AsyncSession, directory: Path = SEED_DIR) -> Dict[str, int]:
    sectors = set((await db.execute(select(Sector.code))).scalars())
    professions = set((await db.execute(select(Profession.code))).scalars())
    departments = {d.code: d for d in (await db.execute(select(CatalogDepartment))).scalars()}
    title_codes = set((await db.execute(select(JobTitle.code).where(JobTitle.tenant_id.is_(None)))).scalars())
    added = {"departments": 0, "titles": 0, "skipped_files": 0}

    def valid_professions(codes, sector_code: Optional[str]) -> List[str]:
        return [c for c in (codes or []) if c in professions and (not sector_code or c.startswith(f"{sector_code}."))]

    for path in seed_files(directory):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.error("Katalog dosyası okunamadı (%s): %s", path.name, exc)
            added["skipped_files"] += 1
            continue
        scope = data.get("scope") or "GENERAL"
        sector_code = data.get("sector_code") if scope == "SECTOR" else None
        if sector_code and sector_code not in sectors:
            logger.error("Katalog dosyasındaki sektör bulunamadı (%s): %s", path.name, sector_code)
            added["skipped_files"] += 1
            continue

        for order, item in enumerate(data.get("departments") or []):
            code = str(item.get("code") or "").strip().upper()
            if not code:
                continue
            dept = departments.get(code)
            if dept is None:
                if scope == "SECTOR" and code.startswith("GEN_"):
                    logger.warning("Genel departman bulunamadı, unvanlar atlandı (%s): %s", path.name, code)
                    continue
                dept = CatalogDepartment(
                    code=code, name=item["name"].strip(), description=item.get("description"),
                    scope="SECTOR" if sector_code else "GENERAL", sector_code=sector_code,
                    profession_codes=valid_professions(item.get("professions"), sector_code), sort_order=order,
                )
                db.add(dept)
                await db.flush()
                departments[code] = dept
                added["departments"] += 1

            for t in item.get("titles") or []:
                t_code = str(t.get("code") or "").strip().upper()
                if not t_code or t_code in title_codes:
                    continue
                db.add(JobTitle(
                    tenant_id=None, code=t_code, title=t["title"].strip(), category=dept.name,
                    description=t.get("description"), base_role_prompt=t["role_prompt"].strip(),
                    required_skills=t.get("skills") or [], responsibilities=t.get("responsibilities") or [],
                    kpis=t.get("kpis") or [], seniority=t.get("seniority"),
                    recommended_model_code=t.get("recommended_model_code"), autonomy_level=t.get("autonomy_level") or "L1",
                    catalog_department_id=dept.id, scope="SECTOR" if sector_code else "GENERAL", sector_code=sector_code,
                    profession_codes=valid_professions(t.get("professions"), sector_code),
                    source="CATALOG", ai_review_status="PLATFORM", is_active=True,
                ))
                title_codes.add(t_code)
                added["titles"] += 1
    await db.commit()
    return added
