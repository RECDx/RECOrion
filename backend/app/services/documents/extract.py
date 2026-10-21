"""
Dokümanlardan metin ve görsel çıkarma. Taranmış PDF sayfaları ve görseller OCR ile okunur (paket izni gerekir).
Görseller (yüklenen resim dosyası ve Word/PowerPoint/PDF içindeki resimler) ayrıca toplanır; hat bunları
görsel-dil modeliyle açıklayıp öğrenilebilir metne çevirir.
Eski Office biçimleri (.doc, .ppt, .xls, .rtf, .odt ...) başsız LibreOffice ile güncel biçime çevrilir.
"""
import asyncio
import hashlib
import io
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Awaitable, Callable, List, Optional

TEXT_EXTS = {"txt", "csv", "md", "json", "xml", "log", "yaml", "yml", "html", "htm"}
IMAGE_EXTS = {"png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff"}
CONVERT = {"doc": "docx", "rtf": "docx", "odt": "docx", "ppt": "pptx", "odp": "pptx", "ods": "xlsx"}
SUPPORTED_EXTS = {"pdf", "docx", "xlsx", "xls", "pptx"} | TEXT_EXTS | IMAGE_EXTS | set(CONVERT)
MAX_OCR_PAGES = 40
SCANNED_PAGE_CHARS = 40  # bundan az metin içeren PDF sayfası taranmış sayılır
MAX_IMAGES = 8  # doküman başına açıklanacak en fazla görsel
MIN_IMAGE_SIDE = 140  # logo/ikon gibi küçük görseller atlanır
MIN_IMAGE_BYTES = 6 * 1024

OcrFn = Callable[[bytes], Awaitable[str]]


class ExtractionError(Exception):
    pass


@dataclass
class Extracted:
    text: str
    page_count: int = 0
    ocr_pages: int = 0
    images: List[bytes] = field(default_factory=list)  # PNG; görsel modelle açıklanacak


def _usable_images(blobs) -> List[bytes]:
    """Görselleri PNG'ye çevirir; küçükleri ve tekrarları atar."""
    from PIL import Image

    out, seen = [], set()
    for blob in blobs:
        if not blob or len(blob) < MIN_IMAGE_BYTES:
            continue
        digest = hashlib.sha1(blob).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        try:
            img = Image.open(io.BytesIO(blob))
            if min(img.size) < MIN_IMAGE_SIDE:
                continue
            img.thumbnail((1600, 1600))
            buf = io.BytesIO()
            img.convert("RGB").save(buf, "PNG")
            out.append(buf.getvalue())
        except Exception:  # okunamayan görsel (ör. WMF/EMF) atlanır
            continue
        if len(out) >= MAX_IMAGES:
            break
    return out


def _docx_images(data: bytes) -> List[bytes]:
    import docx

    d = docx.Document(io.BytesIO(data))
    return _usable_images(rel.target_part.blob for rel in d.part.rels.values() if "image" in rel.reltype)


def _pptx_images(data: bytes) -> List[bytes]:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    prs = Presentation(io.BytesIO(data))
    blobs = [shape.image.blob for slide in prs.slides for shape in slide.shapes
             if shape.shape_type == MSO_SHAPE_TYPE.PICTURE]
    return _usable_images(blobs)


def _pdf_images(data: bytes, pages: List[int]) -> List[bytes]:
    import pypdf

    reader = pypdf.PdfReader(io.BytesIO(data))
    blobs = []
    for n in pages:
        try:
            blobs.extend(img.data for img in reader.pages[n].images)
        except Exception:
            continue
    return _usable_images(blobs)


def _decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1254", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def _docx(data: bytes) -> str:
    import docx

    d = docx.Document(io.BytesIO(data))
    parts = [p.text.strip() for p in d.paragraphs if p.text.strip()]
    for table in d.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def _xlsx(data: bytes) -> str:
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True, read_only=True)
    sheets = []
    for ws in wb.worksheets:
        rows = [" | ".join(str(v).strip() for v in row if v is not None and str(v).strip()) for row in ws.iter_rows(values_only=True)]
        rows = [r for r in rows if r]
        if rows:
            sheets.append(f"--- Sayfa: {ws.title} ---\n" + "\n".join(rows))
    return "\n\n".join(sheets)


def _xls(data: bytes) -> str:
    import xlrd

    book = xlrd.open_workbook(file_contents=data)
    sheets = []
    for sh in book.sheets():
        rows = [" | ".join(str(v).strip() for v in sh.row_values(i) if str(v).strip()) for i in range(sh.nrows)]
        rows = [r for r in rows if r]
        if rows:
            sheets.append(f"--- Sayfa: {sh.name} ---\n" + "\n".join(rows))
    return "\n\n".join(sheets)


def _pptx(data: bytes) -> str:
    from pptx import Presentation

    prs = Presentation(io.BytesIO(data))
    slides = []
    for i, slide in enumerate(prs.slides, 1):
        texts = []
        for shape in slide.shapes:
            if getattr(shape, "has_text_frame", False) and shape.text_frame.text.strip():
                texts.append(shape.text_frame.text.strip())
            if getattr(shape, "has_table", False):
                for row in shape.table.rows:
                    cells = [c.text.strip() for c in row.cells if c.text.strip()]
                    if cells:
                        texts.append(" | ".join(cells))
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
            texts.append("Not: " + slide.notes_slide.notes_text_frame.text.strip())
        if texts:
            slides.append(f"--- Slayt {i} ---\n" + "\n".join(texts))
    return "\n\n".join(slides)


def _convert_legacy(data: bytes, ext: str) -> bytes:
    """LibreOffice ile eski biçimi güncel biçime çevirir."""
    target = CONVERT[ext]
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise ExtractionError(f".{ext} dosyaları için dönüştürücü bulunamadı; lütfen dosyayı .{target} olarak kaydedip yükleyin.")
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, f"kaynak.{ext}")
        with open(src, "wb") as f:
            f.write(data)
        try:
            subprocess.run([soffice, "--headless", "--norestore", f"-env:UserInstallation=file://{tmp}/profile",
                            "--convert-to", target, "--outdir", tmp, src],
                           check=True, capture_output=True, timeout=120)
        except (subprocess.SubprocessError, OSError) as exc:
            raise ExtractionError(f".{ext} dosyası dönüştürülemedi; dosyayı .{target} olarak kaydedip yükleyin.") from exc
        out = os.path.join(tmp, f"kaynak.{target}")
        if not os.path.exists(out):
            raise ExtractionError(f".{ext} dosyası dönüştürülemedi; dosyayı .{target} olarak kaydedip yükleyin.")
        with open(out, "rb") as f:
            return f.read()


def _render_pdf_pages(data: bytes, page_numbers: list) -> list:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(data)
    images = []
    for n in page_numbers:
        bitmap = pdf[n].render(scale=2).to_pil()
        buf = io.BytesIO()
        bitmap.convert("RGB").save(buf, "PNG")
        images.append(buf.getvalue())
    return images


def _to_png(data: bytes) -> bytes:
    from PIL import Image

    img = Image.open(io.BytesIO(data))
    img.thumbnail((2400, 2400))
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "PNG")
    return buf.getvalue()


async def extract(data: bytes, ext: str, ocr: Optional[OcrFn]) -> Extracted:
    """ocr verilmezse (paket izni yok) taranmış içerik için açıklayıcı hata verilir."""
    ext = ext.lower().lstrip(".")
    if ext not in SUPPORTED_EXTS:
        raise ExtractionError(f".{ext} biçimi desteklenmiyor.")
    try:
        if ext in CONVERT:
            data = await asyncio.to_thread(_convert_legacy, data, ext)
            ext = CONVERT[ext]
        if ext in TEXT_EXTS:
            return Extracted(_decode(data))
        if ext == "docx":
            return Extracted(await asyncio.to_thread(_docx, data), images=await asyncio.to_thread(_docx_images, data))
        if ext == "xlsx":
            return Extracted(await asyncio.to_thread(_xlsx, data))
        if ext == "xls":
            return Extracted(await asyncio.to_thread(_xls, data))
        if ext == "pptx":
            return Extracted(await asyncio.to_thread(_pptx, data), images=await asyncio.to_thread(_pptx_images, data))
        if ext in IMAGE_EXTS:
            if not ocr:
                raise ExtractionError("Görsellerden öğrenme (OCR ve görsel açıklama) paketinizde yer almıyor.")
            png = await asyncio.to_thread(_to_png, data)
            return Extracted(await ocr(png), page_count=1, ocr_pages=1, images=[png])
        if ext == "pdf":
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(data))
            pages = [(p.extract_text() or "").strip() for p in reader.pages]
            scanned = [i for i, t in enumerate(pages) if len(t) < SCANNED_PAGE_CHARS]
            if scanned and ocr:
                todo = scanned[:MAX_OCR_PAGES]
                for i, png in zip(todo, await asyncio.to_thread(_render_pdf_pages, data, todo)):
                    pages[i] = (await ocr(png)).strip()
            elif scanned and len(scanned) == len(pages):
                raise ExtractionError("Bu PDF taranmış görüntülerden oluşuyor; metin okumak (OCR) paketinizde yer almıyor.")
            text = "\n\n".join(f"--- Sayfa {i + 1} ---\n{t}" for i, t in enumerate(pages) if t)
            text_pages = [i for i in range(len(pages)) if i not in scanned]
            images = await asyncio.to_thread(_pdf_images, data, text_pages) if ocr else []
            return Extracted(text, page_count=len(pages), ocr_pages=min(len(scanned), MAX_OCR_PAGES) if ocr else 0, images=images)
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError(f"Dosya okunamadı ({ext}): bozuk veya parola korumalı olabilir.") from exc
    raise ExtractionError(f".{ext} biçimi desteklenmiyor.")
