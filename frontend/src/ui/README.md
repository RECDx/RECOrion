# RECOrion Arayüz Temeli

## Tema
- Koyu tema varsayılan; kullanıcı **Koyu / Açık / Sistem** seçebilir (`ThemeToggle`). Tercih `localStorage`
  (`recorion_theme`) içinde saklanır ve `index.html`'deki küçük betikle ilk boyamadan önce uygulanır.
- Renkleri **asla sabit yazmayın**; anlamsal değişkenleri kullanın:
  `--text-main`, `--text-muted`, `--text-dim`, `--bg-dark`, `--bg-surface`, `--bg-card`, `--bg-input`,
  `--border-subtle`, `--border-highlight`, `--gradient-brand`. Yarı saydam katman: `rgb(var(--rgb-ov) / 0.08)`.
- `src/theme/palette.generated.css` eski ekranların dönüştürülmüş renkleridir (otomatik üretildi).

## Bileşenler (`src/ui/components.jsx`)
`Button` (primary · secondary · ghost · danger · success; sm · md · lg), `Card`, `Badge`, `EmptyState`,
`Modal` (telefonda tam ekran, ESC ile kapanır), `DataTable` (arama, sıralama, sayfalama; telefonda karta döner).

## Bildirim ve onay (`src/ui/feedback.js`)
```js
import { notify, toast, confirmDialog, promptDialog } from '../ui/feedback';
toast.success('Kaydedildi');
if (!(await confirmDialog({ message: 'Silinsin mi?', danger: true }))) return;
const email = await promptDialog({ message: 'Alıcı e-posta', defaultValue: '' });
```
Tarayıcının `alert/confirm/prompt` pencereleri kullanılmaz.

## Responsive
Kesme noktaları: ≤1280 küçük masaüstü · ≤1024 tablet · ≤640 telefon (`src/ui/responsive.css`).
Yardımcı sınıflar: `ui-hide-tablet`, `ui-hide-mobile`, `ui-show-tablet`, `ui-show-mobile-only`,
`ui-grid-2`, `ui-grid-3` (tablette 2, telefonda 1 sütun).
