import urllib.request
import json

def get(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

leads = get("http://localhost:8000/api/v1/tenants/leads")
tenants = get("http://localhost:8000/api/v1/tenants")

print(f"Total leads: {len(leads)}")
pending = [l for l in leads if l.get('status') == 'PENDING']
approved = [l for l in leads if l.get('status') == 'APPROVED']
other = [l for l in leads if l.get('status') not in ('PENDING', 'APPROVED')]

print(f"Pending leads: {len(pending)}")
print(f"Approved leads: {len(approved)}")
print(f"Other leads: {len(other)}")

print(f"Total tenants: {len(tenants)}")

print("\n--- LEADS ---")
for l in leads:
    print(f"Lead ID: {l.get('id')} | Company: {l.get('company_name')} | Status: {l.get('status')} | Email: {l.get('contact_email')}")

print("\n--- TENANTS ---")
for t in tenants:
    print(f"Tenant ID: {t.get('id')} | Name: {t.get('name')} | Slug: {t.get('slug')} | Email: {t.get('contact_email')}")
