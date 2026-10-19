# Arayüz dönüşüm araçları

Adım 2.5'te mevcut ekranları temaya ve ekran boyutlarına uyarlamak için kullanıldı.
Yeni yazılan ekranlarda gerek yoktur (bkz. `src/ui/README.md`); eski bir ekran
sabit renklerle güncellenirse tekrar çalıştırılabilir. İkisi de tekrar çalıştırılabilir
(idempotent) ve önce kuru modda rapor verir.

```bash
npm install --no-save @babel/parser@7.26.3 @babel/traverse@7.26.4
node tools/theme-codemod.mjs src           # rapor
node tools/theme-codemod.mjs src --write   # renkleri tema değişkenlerine çevirir, src/theme/palette.generated.css üretir
node tools/layout-codemod.mjs src --write  # ızgara sınıfları (ui-grid-2/3) ve min(100%, …) genişlikler
```

`theme-codemod` mail şablonu editörüne (EMAIL_PRESET_BLOCKS, compileBlocksToHtml), HTML içeren
metinlere ve `value=`/`placeholder=` gibi özniteliklere dokunmaz; e-postalara giden renkler değişmez.
