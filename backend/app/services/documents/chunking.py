"""Metni paragraf sınırlarına saygı göstererek örtüşmeli parçalara böler (vektör araması için)."""
import re
from typing import List

CHUNK_CHARS = 1400
OVERLAP_CHARS = 200


def split(text: str, size: int = CHUNK_CHARS, overlap: int = OVERLAP_CHARS) -> List[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]
    chunks: List[str] = []
    current = ""
    for para in paragraphs:
        # Çok uzun paragrafları cümle sınırından böl
        pieces = [para] if len(para) <= size else re.split(r"(?<=[.!?])\s+", para)
        for piece in pieces:
            while len(piece) > size:  # cümle de çok uzunsa kes
                chunks.append((current + "\n" + piece[:size]).strip() if current else piece[:size])
                current, piece = "", piece[size - overlap:]
            if len(current) + len(piece) + 1 > size and current:
                chunks.append(current.strip())
                current = current[-overlap:] + "\n" + piece  # örtüşme: önceki parçanın sonu
            else:
                current = f"{current}\n{piece}" if current else piece
    if current.strip():
        chunks.append(current.strip())
    return chunks
