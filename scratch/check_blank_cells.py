import openpyxl

wb = openpyxl.load_workbook('documents/Sektör Meslek Nace Kodları_2026.03.xlsx', data_only=True)
ws = wb['Sheet0']

print(f"Total rows in Sheet0: {ws.max_row}")

none_col0 = 0
rows_with_data_but_none_col0 = []

for r in range(2, ws.max_row + 1):
    c0 = ws.cell(r, 1).value
    c1 = ws.cell(r, 2).value
    c2 = ws.cell(r, 3).value
    c3 = ws.cell(r, 4).value
    
    if c0 is None:
        none_col0 += 1
        if any(c is not None for c in [c1, c2, c3]):
            rows_with_data_but_none_col0.append((r, c0, c1, c2, c3))

print(f"Rows where col 0 is None: {none_col0}")
print(f"Rows where col 0 is None but other cols have data: {len(rows_with_data_but_none_col0)}")
for x in rows_with_data_but_none_col0[:10]:
    print(x)

# Let's inspect all merged cell ranges in the sheet!
print(f"Merged cells count: {len(ws.merged_cells.ranges)}")
for rng in list(ws.merged_cells.ranges)[:15]:
    print(rng)
