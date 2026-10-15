import openpyxl

def main():
    wb = openpyxl.load_workbook('documents/Sektör Meslek Nace Kodları_2026.03.xlsx', data_only=True)
    ws = wb['Sheet0']
    
    excel_sectors = {}
    excel_professions = {}
    
    for r in range(2, ws.max_row + 1):
        s_code = ws.cell(r, 1).value
        s_name = ws.cell(r, 2).value
        p_code = ws.cell(r, 3).value
        p_name = ws.cell(r, 4).value
        
        s_code_str = str(s_code).strip() if s_code is not None else ""
        s_name_str = str(s_name).strip() if s_name is not None else ""
        p_code_str = str(p_code).strip() if p_code is not None else ""
        p_name_str = str(p_name).strip() if p_name is not None else ""
        
        if s_code_str or s_name_str:
            if s_code_str not in excel_sectors:
                excel_sectors[s_code_str] = set()
            if s_name_str:
                excel_sectors[s_code_str].add(s_name_str)
                
        if p_code_str or p_name_str:
            if p_code_str not in excel_professions:
                excel_professions[p_code_str] = []
            excel_professions[p_code_str].append((s_code_str, s_name_str, p_name_str, r))

    print(f"Total distinct sector codes: {len(excel_sectors)}")
    for sc, names in sorted(excel_sectors.items()):
        names_list = list(names)
        prof_items = [p for pc, list_p in excel_professions.items() for p in list_p if p[0] == sc]
        prof_codes = sorted(list({p[0] for pc, list_p in excel_professions.items() for p in list_p if p[0] == sc}))
        distinct_p_codes = sorted(list({pc for pc, list_p in excel_professions.items() if any(p[0] == sc for p in list_p)}))
        distinct_p_names = sorted(list({p[2] for pc, list_p in excel_professions.items() for p in list_p if p[0] == sc}))
        print(f"Sector [{sc}] {names_list}:")
        print(f"  Count of distinct profession codes: {len(distinct_p_codes)}")
        print(f"  Sample codes: {distinct_p_codes[:5]}")
        print(f"  Sample names: {distinct_p_names[:5]}")

    # Check why user said YAPI SANATLARI had no professions
    # Let's print all rows for YAPI SANATLARI
    print("\n--- YAPI SANATLARI Details ---")
    for r in range(2, ws.max_row + 1):
        s_name = str(ws.cell(r, 2).value or '')
        if 'YAPI' in s_name.upper():
            print(f"Row {r}: S_CODE={ws.cell(r, 1).value}, S_NAME={ws.cell(r, 2).value}, P_CODE={ws.cell(r, 3).value}, P_NAME={ws.cell(r, 4).value}")
            break

if __name__ == '__main__':
    main()
