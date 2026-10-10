-- ==============================================================================
-- RECOrion: PostgreSQL 16 Başlangıç Betiği (pgvector & Core Extensions)
-- ==============================================================================

-- pgvector uzantısını aktifleştir
CREATE EXTENSION IF NOT EXISTS vector;

-- UUID ve Kripto uzantılarını aktifleştir
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Sistem bilgi mesajı
DO $$
BEGIN
    RAISE NOTICE 'RECOrion veritabanı uzantıları (vector, uuid-ossp, pgcrypto) başarıyla yüklendi.';
END $$;
