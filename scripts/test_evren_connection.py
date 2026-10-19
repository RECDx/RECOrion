import os
import requests
import json

headers = {
    "Authorization": f"Bearer {os.getenv('EVREN_API_KEY', '')}",
    "Content-Type": "application/json"
}
base_url = "https://evren-llmapi.ssyz.org.tr/v1"

print("[1] EVREN Models...")
r = requests.get(f"{base_url}/models", headers=headers, timeout=10)
print("Status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    models = data.get("data", [])
    print(f"Toplam Model Sayisi: {len(models)}")
    for m in models:
        print(f" - {m.get('id')} (Task: {m.get('task')}, Context: {m.get('context_length')})")

print("\n[2] Test Chat Completion...")
test_payload = {
    "model": "deepseek-v4-flash",
    "messages": [
        {"role": "system", "content": "Sen RECOrion platformunun kurumsal yapay zeka asistanısın."},
        {"role": "user", "content": "RECOrion projesine hoş geldin. Kendini tek bir Türkçe cümle ile tanıt."}
    ],
    "max_tokens": 100,
    "temperature": 0.7
}
print(f"Testing model: {test_payload['model']}")
cr = requests.post(f"{base_url}/chat/completions", headers=headers, json=test_payload, timeout=20)
print("Chat Status:", cr.status_code)
print("Chat Response:", cr.text[:500])
