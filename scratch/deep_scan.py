import openpyxl

wb = openpyxl.load_workbook('documents/Sektör Meslek Nace Kodları_2026.03.xlsx', data_only=True)
ws = wb['Sheet0']

print("=== DEEP EXCEL SCAN ===")
all_sectors_map = {}
all_professions_map = {}

# Check for all non-empty rows
rows_with_s_and_p = 0
for r in range(2, ws.max_row + 1):
    s_code = ws.cell(r, 1).value
    s_name = ws.cell(r, 2).value
    p_code = ws.cell(r, 3).value
    p_name = ws.cell(r, 4).value
    
    if s_code is not None or s_name is not None:
        sc = str(s_code).strip() if s_code is not None else ""
        sn = str(s_name).strip() if s_name is not None else ""
        if sc not in all_sectors_map:
            all_sectors_map[sc] = set()
        if sn:
            all_sectors_map[sc].add(sn)
            
    if p_code is not None or p_name is not None:
        pc = str(p_code).strip() if p_code is not None else ""
        pn = str(p_name).strip() if p_name is not None else ""
        sc = str(s_code).strip() if s_code is not None else ""
        if pc not in all_professions_map:
            all_professions_map[pc] = set()
        all_professions_map[pc].add((sc, pn))

print(f"Total rows scanned: {ws.max_row}")
print(f"Distinct Sector Codes: {len(all_sectors_map)}")
for sc, names in sorted(all_sectors_map.items()):
    # count how many professions belong to this sc
    profs_for_sc = {pc: [pn for s, pn in items if s == sc] for pc, items in all_professions_map.items() if any(s == sc for s, pn in items)}
    print(f"Sector Code: '{sc}' -> Names: {names} | Professions Count: {len(profs_for_sc)}")
    for pc, pnames in sorted(profs_for_sc.items()):
        print(f"     {pc}: {pnames}")

print(f"\nTotal Distinct Profession Codes: {len(all_professions_map)}")
