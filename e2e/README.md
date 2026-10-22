# Canlı uçtan uca testler (e2e)

Her adım bitince `backend/tests` (pytest) ile birlikte çalıştırılır. Sahte veri kullanılmaz: gerçek arayüz,
gerçek backend, gerçek EVREN (Beyin AI) ve gerçek Temporal akışı.

## Ne yapar

1. `backend/scripts/live_test_setup.py` ile **RECOrion Canlı Test A.Ş.** şirketini kurar (yoksa oluşturur, varsa
   kullanıcı şifrelerini yeniler). Şifreler dosyaya yazılmaz; yalnızca test sürecinin belleğinde tutulur.
   Gerçek müşteri şirketlerine dokunulmaz.
2. Tarayıcıda proje yöneticisi olarak giriş yapar; proje oluşturur, Beyin AI planı alır, onaylar, ekip kurar,
   simüle eder, başlatır.
3. İş akışını yürütür: teslim, 3 ret, karantina, yeniden deneme, onay; tüm adımların bağımlılık sırasıyla
   tamamlanmasını ve akış geçmişinin tutarlılığını denetler.
4. Ekip üyesinin onaylayamadığını ve ekip dışı kullanıcının projeyi göremediğini doğrular.
5. Tarayıcı konsol hatalarını ve 5xx yanıtlarını raporlar.

## Çalıştırma

Ön koşul: `docker compose up -d` (backend, frontend, postgres, temporal...) ve Playwright Chromium
(`npx playwright-core install chromium`, varsayılan yol `%LOCALAPPDATA%\ms-playwright\chromium-1243`).

```bash
cd e2e
npm install
npm test
```

Ortam değişkenleri (isteğe bağlı): `APP_URL` (varsayılan `http://localhost:5173`), `CHROME_PATH`,
`BACKEND_CONTAINER` (varsayılan `recorion_backend`).

Çıktı: her adım için `GEÇTİ`/`KALDI`, sorun listesi; ekran görüntüleri ve `report.json`
`e2e/artifacts/<zaman>/` altında (git dışı). Çıkış kodu: tüm adımlar geçerse 0.

Her yeni adımda bu teste o adımın özellikleri eklenir.
