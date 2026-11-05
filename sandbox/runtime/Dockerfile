# RECOrion Kod Çalıştırma Ortamı (ADIM 16.2) — iş kabı imajı.
# AI personelin yazdığı kod bu imajdan açılan, her koşuda yeniden oluşturulup silinen kapta çalışır.
# Root olmayan kullanıcı; sistem bilgisi, gizli anahtar veya RECOrion ağı yoktur.
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends nodejs npm git ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && useradd -m -u 1000 runner \
 && mkdir /work && chown runner:runner /work

USER runner
WORKDIR /work
ENV CI=true PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 npm_config_update_notifier=false
CMD ["sleep", "infinity"]
