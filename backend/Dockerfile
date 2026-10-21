FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    # Eski Office biçimlerini (.doc, .ppt, .xls) metne çevirmek için başsız LibreOffice
    libreoffice-writer-nogui \
    libreoffice-impress-nogui \
    libreoffice-calc-nogui \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

EXPOSE 8000

# Açılışta: migrasyonlar -> ilk kurulum hazırlığı -> API
CMD ["sh", "-c", "alembic upgrade head && python -m app.bootstrap && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
