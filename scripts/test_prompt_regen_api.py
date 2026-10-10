import requests

r = requests.get('http://localhost:8000/api/v1/actors/job-titles')
titles = r.json()
first = titles[0]
print(f"Testing regeneration for: {first['title']} (ID: {first['id']})")
reg = requests.post(f"http://localhost:8000/api/v1/actors/job-titles/{first['id']}/regenerate-prompt")
print("Status:", reg.status_code)
res = reg.json()
print("Model used:", res.get("model_used"))
print("Message:", res.get("message"))
print("New prompt preview:\n", res.get("new_prompt", "")[:400])
