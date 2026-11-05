# RECOrion Kod Çalıştırma Ortamı (ADIM 16.2) — yönetici servis (güvenilir kod).
# Docker soketiyle her koşu için yalıtılmış bir iş kabı açar, kodu içine koyar, bağımlılıkları kurar, ağı keser,
# testleri çalıştırır, sonucu döner ve kabı siler. Yalnızca backend ile ortak iç ağdadır; dışarıya port açmaz.
FROM python:3.12-slim

RUN pip install --no-cache-dir fastapi==0.115.6 uvicorn==0.32.1 docker==7.1.0

COPY runner /srv/runner
COPY runtime /srv/runtime

EXPOSE 8100
CMD ["uvicorn", "app:app", "--app-dir", "/srv/runner", "--host", "0.0.0.0", "--port", "8100"]
