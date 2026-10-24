"""
Toplantı kaydından proje taslağı (ADIM 11.3).

Akış (arka planda): ses/video dosyası → ffmpeg ile 16 kHz tek kanal WAV, CHUNK_SECONDS'lık parçalar (EVREN dosya boyutu
sınırı ~25 MB; 16 kHz'de 10 dk ≈ 19 MB) → her parça qwen3-asr ile yazıya (LLM geçidi; kayıt ve kredi) → KVKK maskeleme
(TCKN, IBAN, kart, e-posta, telefon) → Beyin AI proje taslağı (ad, açıklama, isterler, adımlar, riskler, açık sorular).
Ham ses SAKLANMAZ: geçici dosya işlem bitince (başarılı/başarısız) silinir. Kullanıcı taslağı düzeltip onaylayınca proje oluşur.
"""
import asyncio
import json
import logging
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.db.models import MeetingRecording
from app.db.session import AsyncSessionLocal
from app.services import llm_gateway
from app.services.documents import pii
from app.services.llm_gateway import LLMContext

logger = logging.getLogger("recorion.meetings")

WORK_DIR = Path(tempfile.gettempdir()) / "recorion_meetings"
MAX_BYTES = 300 * 1024 * 1024
MAX_SECONDS = 3 * 3600
MIN_SECONDS = 2
CHUNK_SECONDS = 600
MIN_TRANSCRIPT_CHARS = 40  # bundan kısa metinden proje taslağı çıkarılmaz (sessiz/anlamsız kayıt)
_tasks: set = set()

DRAFT_PROMPT = """Aşağıda bir iş toplantısının yazıya çevrilmiş metni var (kişisel veriler maskelendi; yazıya çevirmede küçük hatalar olabilir).
Bu toplantıdan bir proje (veya tek bir vaka ise Case) taslağı çıkar. Yalnızca toplantıda söylenenlere dayan; söylenmeyeni uydurma,
eksikleri "open_questions" altında sor. Yanıtın YALNIZCA şu JSON olsun:
{"name": "kısa proje adı", "kind": "PROJECT veya CASE", "description": "2-3 cümle amaç",
 "requirements": "madde madde isterler (kapsam, kısıtlar, onay noktaları, teslim tarihi)",
 "steps": [{"key": "S1", "title": "...", "description": "...", "job_title": "bu işi yapacak rol", "department": "...",
            "estimated_days": 2, "depends_on": [], "requires_approval": true}],
 "risks": ["..."], "participants": ["toplantıda adı geçen roller (ör. depo şefi)"], "open_questions": ["..."]}
En fazla 10 adım. Toplantı metni:
"""


def _run(cmd: List[str], timeout: int = 900) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def probe_seconds(path: Path) -> Optional[float]:
    """ffprobe ile süre; ses/video değilse None."""
    try:
        r = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)], 60)
        return float(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() not in ("", "N/A") else None
    except (ValueError, subprocess.TimeoutExpired, FileNotFoundError):
        return None


def split_audio(path: Path, out_dir: Path) -> List[Path]:
    """16 kHz tek kanal 16 bit WAV parçaları (yalnızca ses akışı; video atılır)."""
    r = _run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
              "-f", "segment", "-segment_time", str(CHUNK_SECONDS), "-reset_timestamps", "1", str(out_dir / "parca_%03d.wav")])
    if r.returncode != 0:
        raise ValueError("Ses dosyası çözülemedi; desteklenen bir ses/video biçimi yükleyin (mp3, m4a, wav, webm, mp4…).")
    return sorted(out_dir.glob("parca_*.wav"))


async def _update(rec_id: uuid.UUID, **values) -> None:
    async with AsyncSessionLocal() as db:
        rec = await db.get(MeetingRecording, rec_id)
        for k, v in values.items():
            setattr(rec, k, v)
        rec.updated_at = datetime.now(timezone.utc)
        await db.commit()


def _parse(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if "```" in text:
        text = text.split("```")[1].removeprefix("json").strip()
    return json.loads(text[text.find("{"): text.rfind("}") + 1])


async def make_draft(ctx: LLMContext, transcript: str) -> Dict[str, Any]:
    from app.services import project_planning as planning

    messages = [{"role": "system", "content": "Sen RECOrion'un Beyin AI'ısın; Türkçe, net ve dürüst çalışırsın."},
                {"role": "user", "content": DRAFT_PROMPT + transcript[:60000]}]
    raw = None
    for attempt in range(2):  # biçim bozuksa (ör. yoğunlukta yedek modelin yanıtı) bir kez "yalnızca JSON" diye yeniden iste
        result = await llm_gateway.chat(ctx, messages, temperature=0.2, max_tokens=3500, timeout=240, fallback=True)
        try:
            raw = _parse(result.content)
            break
        except (ValueError, json.JSONDecodeError):
            logger.warning("Toplantı taslağı JSON değil (deneme %s, %s)", attempt + 1, result.model_code)
            messages = messages + [{"role": "assistant", "content": (result.content or "")[:2000]},
                                   {"role": "user", "content": "Yanıtın geçerli JSON değildi. Açıklama yazmadan, yalnızca istenen JSON nesnesini ver."}]
    if raw is None:
        raise ValueError("Beyin AI toplantıdan taslak çıkaramadı (yanıt biçimi bozuk). Yeniden deneyin.")
    if isinstance(raw.get("requirements"), list):
        raw["requirements"] = "\n".join(f"- {str(x).lstrip('- ')}" for x in raw["requirements"])
    plan = planning.validate_plan({"summary": raw.get("description"), "steps": raw.get("steps") or [], "risks": raw.get("risks") or [],
                                   "questions": raw.get("open_questions") or []}, pool_ids=set(), human_ids=None)
    return {"name": str(raw.get("name") or "").strip()[:255] or "Toplantıdan proje", "kind": "CASE" if raw.get("kind") == "CASE" else "PROJECT",
            "description": str(raw.get("description") or "").strip()[:3000], "requirements": str(raw.get("requirements") or "").strip()[:8000],
            "participants": [str(p)[:120] for p in raw.get("participants") or []][:15], "plan": plan, "model": result.model_code}


async def process(rec_id: uuid.UUID, tenant_id: uuid.UUID, actor_id: Optional[uuid.UUID], src: Path) -> None:
    work = src.parent
    try:
        seconds = probe_seconds(src)
        if seconds is None:
            raise ValueError("Dosya ses veya video olarak okunamadı.")
        if seconds < MIN_SECONDS:
            raise ValueError("Kayıt çok kısa.")
        if seconds > MAX_SECONDS:
            raise ValueError(f"Kayıt en fazla {MAX_SECONDS // 3600} saat olabilir.")
        await _update(rec_id, duration_sec=round(seconds, 1), stage="Ses hazırlanıyor…")
        chunks = await asyncio.to_thread(split_audio, src, work)
        src.unlink(missing_ok=True)  # ham kayıt hemen silinir; yalnızca geçici parçalar kalır
        ctx = LLMContext(tenant_id=tenant_id, purpose="TRANSCRIPTION", actor_id=actor_id)
        parts = []
        for i, chunk in enumerate(chunks, 1):
            await _update(rec_id, stage=f"Yazıya çevriliyor ({i}/{len(chunks)})…")
            parts.append((await llm_gateway.transcribe(ctx, chunk.read_bytes(), chunk.name, "audio/wav", CHUNK_SECONDS)).strip())
            chunk.unlink(missing_ok=True)
        transcript = "\n".join(p for p in parts if p)
        masked, found = pii.mask(transcript)
        if len(masked.strip()) < MIN_TRANSCRIPT_CHARS:
            await _update(rec_id, status="FAILED", stage=None, transcript_masked=masked, pii=found,
                          error="Kayıtta anlaşılır konuşma bulunamadı; mikrofonu kontrol edip yeniden kaydedin.")
            return
        await _update(rec_id, transcript_masked=masked, pii=found, stage="Beyin AI proje taslağını hazırlıyor…")
        draft = await make_draft(LLMContext(tenant_id=tenant_id, purpose="BRAIN", actor_id=actor_id), masked)
        await _update(rec_id, status="READY", stage=None, draft=draft)
    except ValueError as exc:
        await _update(rec_id, status="FAILED", stage=None, error=str(exc))
    except llm_gateway.LLMError as exc:
        await _update(rec_id, status="FAILED", stage=None, error=str(exc))
    except Exception as exc:  # beklenmeyen: ayrıntı loga
        logger.exception("Toplantı kaydı işlenemedi (%s)", rec_id)
        await _update(rec_id, status="FAILED", stage=None, error=f"Kayıt işlenemedi ({exc.__class__.__name__}).")
    finally:
        shutil.rmtree(work, ignore_errors=True)  # ham ses ve parçalar diskte kalmaz


def start(rec_id: uuid.UUID, tenant_id: uuid.UUID, actor_id: Optional[uuid.UUID], src: Path) -> None:
    task = asyncio.get_running_loop().create_task(process(rec_id, tenant_id, actor_id, src))
    _tasks.add(task)  # referans tutulur, yoksa bitmeden çöpe gidebilir
    task.add_done_callback(_tasks.discard)


def out(rec: MeetingRecording, full: bool = False) -> Dict[str, Any]:
    d = {"id": str(rec.id), "title": rec.title, "source": rec.source, "status": rec.status, "stage": rec.stage,
         "duration_sec": float(rec.duration_sec) if rec.duration_sec is not None else None, "error": rec.error,
         "project_id": str(rec.project_id) if rec.project_id else None, "created_at": rec.created_at}
    if full:
        d.update(transcript=rec.transcript_masked, pii=rec.pii or {}, draft=rec.draft)
    return d
