tabs = ['LEADS', 'PERMISSIONS', 'PLANS', 'MODELS', 'NACE', 'TITLES', 'EMAIL_TEMPLATES', 'SCHEDULES']
with open('frontend/src/components/SuperAdminConsole.jsx', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        for t in tabs:
            if f"activeTab === '{t}'" in line and '{' in line:
                print(f"{t}: {idx}")
