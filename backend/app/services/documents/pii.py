"""
KVKK maskeleme: dokümandaki kişisel veriler vektörlemeden ve öğrenme kartından önce etiketlerle değiştirilir.
Asıl dosya MinIO'da erişim kontrollü olarak kalır; AI personeller yalnızca maskeli metni öğrenir.

Maskelenenler: T.C. kimlik no (kontrol haneli), IBAN (TR), kredi kartı (Luhn), e-posta, telefon (TR).
Kurumsal vergi numarası (VKN) şirket bilgisi olduğu için maskelenmez.
"""
import re
from typing import Dict, Tuple

LABELS = {"TCKN": "[TCKN]", "IBAN": "[IBAN]", "CARD": "[KART_NO]", "EMAIL": "[E-POSTA]", "PHONE": "[TELEFON]"}
TITLES = {"TCKN": "T.C. kimlik numarası", "IBAN": "IBAN", "CARD": "Kart numarası", "EMAIL": "E-posta adresi", "PHONE": "Telefon numarası"}

_IBAN = re.compile(r"\bTR\s?\d{2}(?:\s?\d{4}){5}\s?\d{2}\b", re.IGNORECASE)
_CARD = re.compile(r"\b(?:\d[ -]?){15,18}\d\b")
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_TCKN = re.compile(r"(?<!\d)[1-9]\d{10}(?!\d)")
_PHONE = re.compile(r"(?<![\d+])(?:\+?90[\s.-]?|0)?\(?5\d{2}\)?[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}(?!\d)"
                    r"|(?<![\d+])(?:\+?90[\s.-]?|0)\(?[2-4]\d{2}\)?[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}(?!\d)")


def tckn_ok(v: str) -> bool:
    d = [int(c) for c in v]
    if len(d) != 11 or d[0] == 0:
        return False
    if (sum(d[0:9:2]) * 7 - sum(d[1:8:2])) % 10 != d[9]:
        return False
    return sum(d[:10]) % 10 == d[10]


def luhn_ok(v: str) -> bool:
    digits = [int(c) for c in re.sub(r"\D", "", v)]
    if not 16 <= len(digits) <= 19:
        return False
    total = 0
    for i, n in enumerate(reversed(digits)):
        if i % 2:
            n *= 2
            n = n - 9 if n > 9 else n
        total += n
    return total % 10 == 0


def mask(text: str) -> Tuple[str, Dict[str, int]]:
    found: Dict[str, int] = {}

    def sub(pattern, kind, check=None):
        nonlocal text

        def repl(m):
            if check and not check(m.group(0)):
                return m.group(0)
            found[kind] = found.get(kind, 0) + 1
            return LABELS[kind]
        text = pattern.sub(repl, text)

    # Sıra önemli: IBAN ve kart numaraları içindeki rakam dizileri TCKN/telefon sanılmasın
    sub(_IBAN, "IBAN")
    sub(_CARD, "CARD", luhn_ok)
    sub(_EMAIL, "EMAIL")
    sub(_TCKN, "TCKN", tckn_ok)
    sub(_PHONE, "PHONE")
    return text, found
