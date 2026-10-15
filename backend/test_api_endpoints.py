import urllib.request
import json

base = 'http://localhost:8000/api/v1'

# 1. Test sectors
with urllib.request.urlopen(f'{base}/sectors/') as r:
    sectors = json.loads(r.read())
print(f'Total sectors from API: {len(sectors)}')
for s in sectors:
    print(f"  [{s['code']}] {s['name']}: {s['professions_count']} professions")

# 2. Test professions with sector_code=K
with urllib.request.urlopen(f'{base}/professions/?sector_code=K') as r:
    k_profs = json.loads(r.read())
print(f"\nTotal professions for sector K from API: {len(k_profs)}")
for kp in k_profs:
    print(f"  [{kp['code']}] {kp['name']} (sector_name: {kp['sector_name']})")

# 3. Test total professions
with urllib.request.urlopen(f'{base}/professions/?limit=500') as r:
    all_profs = json.loads(r.read())
print(f"\nTotal professions from API: {len(all_profs)}")
