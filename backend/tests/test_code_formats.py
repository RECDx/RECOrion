"""
Senaryo Aşama 3 (12–13.11.2026) bulguları: AI personel dosya yolunu farklı biçimlerde yazıyor; kod depoya düşmüyordu.

- C3-21: yol bloğun İLK satırında çıplak (```python\\nsrc/app/main.py)
- C3-27: yol bloğun ÜSTÜNDEKİ başlıkta (### `src/web/index.html`, **src/x.py**, Dosya: README.md)
- C3-29: başlık + açıklama satırı + blok; KISMİ blok ("// ... mevcut importlar ...") dosyanın üzerine YAZILMAZ
- C3-33: yol başlıkta parantez içinde + açıklama; README markdown bloğu İÇ İÇE ```bash blokları içerir → tam alınır, kesilmez
- Yanlış eşleşme yok: düz cümle, URL, yolsuz kod bloğu dosya olmaz.
"""
import json
from types import SimpleNamespace

from app.services import code_repo

TASK = SimpleNamespace(order_index=3, title="Kurulum ve Duman Testi")


def files(text):
    return {k: v for k, v in code_repo.files_from_output(TASK, text).items() if not k.startswith("docs/")}


def test_bare_path_first_line():
    f = files("Açıklama\n```python\nsrc/app/main.py\nimport os\nprint(1)\n```\n```text\nrequirements.txt\nfastapi\n```\n")
    assert f == {"src/app/main.py": "import os\nprint(1)\n", "requirements.txt": "fastapi\n"}


def test_heading_path_variants():
    text = ("### `src/web/index.html`\n\n```html\n<!DOCTYPE html>\n```\n\n**src/web/app.js**\n```javascript\nconst a = 1;\n```\n"
            "Dosya: README.md\n```markdown\n# Başlık\n```\n")
    assert files(text) == {"src/web/index.html": "<!DOCTYPE html>\n", "src/web/app.js": "const a = 1;\n", "README.md": "# Başlık\n"}


def test_heading_with_description_and_partial_block_skipped():
    text = ("### `src/web/admin.js`\n*Yönetim paneli mantığı.*\n\n```javascript\nexport function x() {}\n```\n\n"
            "### `src/web/app.js` (Güncellenmiş bölüm)\n*Yalnız değişen kısım.*\n\n```javascript\n// ... mevcut importlar ...\nrender();\n```\n")
    f = files(text)
    assert f == {"src/web/admin.js": "export function x() {}\n"}  # kısmi app.js yazılmadı (dosyanın geri kalanı silinmesin)


def test_paren_heading_and_nested_readme():
    text = ("## 2. Kurulum Talimatları (README.md)\n\nAşağıdaki `README.md` dosyası kurulumu anlatır.\n\n```markdown\n# GEZİ 101\n\n"
            "## Kurulum\n\n1. Bağımlılıklar:\n   ```bash\n   pip install -r requirements.txt\n   ```\n\n## Çalıştırma\n\n```bash\n"
            "uvicorn --app-dir src app.main:app\n```\n\n## Son bölüm\nGerçek kart verisi alınmaz.\n```\n\n"
            "## 3. Duman Testi Konfigürasyonu (recorion.json)\n\nYapılandırma dosyasıdır.\n\n```json\n{\"services\": [], \"checks\": []}\n```\n")
    f = files(text)
    assert set(f) == {"README.md", "recorion.json"}
    assert f["README.md"].startswith("# GEZİ 101") and "uvicorn --app-dir src" in f["README.md"] and f["README.md"].rstrip().endswith("alınmaz.")
    assert json.loads(f["recorion.json"]) == {"services": [], "checks": []}


def test_no_false_positives():
    text = ("Bu kodda bir örnek var:\n```python\nprint(1)\n```\nSiteye bakın: https://fonts.googleapis.com/css2\n```\nyolsuz\n```\n"
            "```html\n<!DOCTYPE html>\n```\n")
    assert files(text) == {}


def test_opening_line_path_still_wins():
    text = "### `src/eski.py`\n```python src/yeni.py\nx = 1\n```\n"
    assert files(text) == {"src/yeni.py": "x = 1\n"}  # başlıktaki yol ikinci (yinelenen) dosya üretmez
