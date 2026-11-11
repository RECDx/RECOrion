# RECOrion Kod Çalıştırma Ortamı (ADIM 16.2) — iş kabı imajı (sürüm 2: duman testi için Playwright, #734).
# AI personelin yazdığı kod bu imajdan açılan, her koşuda yeniden oluşturulup silinen kapta çalışır.
# Root olmayan kullanıcı; sistem bilgisi, gizli anahtar veya RECOrion ağı yoktur.
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends nodejs npm git ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && useradd -m -u 1000 runner \
 && mkdir /work && chown runner:runner /work

# Duman testi (#734): arayüz akışını denemek için Chromium (Debian paketi) + Playwright (sistem Python'una; proje venv'lerinden ayrı)
RUN apt-get update \
 && apt-get install -y --no-install-recommends chromium fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir playwright==1.49.1
ENV SMOKE_CHROMIUM=/usr/bin/chromium

USER runner
WORKDIR /work
ENV CI=true PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 npm_config_update_notifier=false
CMD ["sleep", "infinity"]
