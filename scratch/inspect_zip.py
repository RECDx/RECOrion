import zipfile

with zipfile.ZipFile('documents/Sektör Meslek Nace Kodları_2026.03.xlsx', 'r') as z:
    for name in z.namelist():
        print(name)
    if 'xl/sharedStrings.xml' in z.namelist():
        raw = z.read('xl/sharedStrings.xml')
        print("sharedStrings.xml length:", len(raw))
        print("Sample raw (first 500 bytes):", raw[:500])
        # Find where YAPI SANATLARI is
        idx = raw.find(b'YAPI SANATLARI')
        if idx != -1:
            print("Context around YAPI SANATLARI:", raw[idx-100:idx+300])
        idx_a = raw.find(b'A')
        print("Context around first string:", raw[raw.find(b'<t>'):raw.find(b'<t>')+300])
