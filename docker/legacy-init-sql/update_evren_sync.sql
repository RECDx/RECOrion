-- 1. EVREN Base URL güncelleme
UPDATE llm_providers 
SET base_url = 'https://evren-llmapi.ssyz.org.tr/v1' 
WHERE code = 'EVREN';

-- 2. Sistem Varsayılan Manifesto / Rol Promptu Modeli güncelleme
UPDATE system_settings 
SET value = '"deepseek-v4.1-flash"'::jsonb 
WHERE key = 'default_manifesto_model';

-- 3. Gerçek EVREN Model Context Uzunluklarını Güncelleme
UPDATE llm_models SET context_window = 1048576 WHERE model_code IN ('deepseek-v4.1-flash', 'deepseek-v4-flash', 'mimo-v2.6-pro');
UPDATE llm_models SET context_window = 524288 WHERE model_code = 'glm-5.3';
UPDATE llm_models SET context_window = 262144 WHERE model_code IN ('gemma-4-31b', 'qwen3.8-flash-next', 'qwen3-vl-30b');
UPDATE llm_models SET context_window = 131072 WHERE model_code = 'dots-ocr';
UPDATE llm_models SET context_window = 40960 WHERE model_code = 'qwen3-embedding-8b';
UPDATE llm_models SET context_window = 4096 WHERE model_code = 'qwen3-reranker-8b';
UPDATE llm_models SET context_window = 8192 WHERE model_code = 'deepseek-ocr-2';
UPDATE llm_models SET context_window = 32768 WHERE model_code = 'qwen3-asr-1.7b';

-- 4. EVREN'deki Ek Modeller: auto ve laya
DO $$
DECLARE
    ev_id UUID;
BEGIN
    SELECT id INTO ev_id FROM llm_providers WHERE code = 'EVREN';

    INSERT INTO llm_models (provider_id, model_code, display_name, model_type, context_window, effort_coefficient, capabilities, status)
    VALUES (ev_id, 'auto', 'EVREN Auto (Akıllı Model Seçici)', 'CHAT', 32768, 1.0, '{"auto_routing": true}'::jsonb, 'ACTIVE')
    ON CONFLICT (model_code) DO NOTHING;

    INSERT INTO llm_models (provider_id, model_code, display_name, model_type, context_window, effort_coefficient, capabilities, status)
    VALUES (ev_id, 'laya', 'Laya (Karar Destek)', 'DECISION', 8192, 1.0, '{"decision": true}'::jsonb, 'ACTIVE')
    ON CONFLICT (model_code) DO NOTHING;
END $$;
