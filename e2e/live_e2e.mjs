// Canlı uçtan uca test (Adım 6, 7.1–7.4, 7.5, 8): gerçek arayüz, gerçek backend, gerçek EVREN ve Temporal. Sahte veri yok. Ayrıntı: e2e/README.md
import { chromium } from 'playwright-core';
import { execFileSync, spawn } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';

// Test şirketi kurulur/şifreler yenilenir; şifreler yalnızca bu süreçte bellekte tutulur
const cfg = JSON.parse(execFileSync('docker', ['exec', '-w', '/app', process.env.BACKEND_CONTAINER || 'recorion_backend',
  'python', 'scripts/live_test_setup.py'], { encoding: 'utf8', env: { ...process.env, MSYS_NO_PATHCONV: '1' } }).trim().split('\n').pop());
const APP = process.env.APP_URL || 'http://localhost:5173';
const OUT = path.resolve('artifacts', new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-'));
const CHROME = process.env.CHROME_PATH || path.join(process.env.LOCALAPPDATA || path.join(os.homedir(), '.cache'), 'ms-playwright', 'chromium-1243', 'chrome-win64', 'chrome.exe');
fs.mkdirSync(OUT, { recursive: true });
const report = [];
const problems = [];
const t0 = Date.now();
const step = (ok, name, detail = '') => { report.push({ ok, name, detail, s: Math.round((Date.now() - t0) / 1000) }); console.log(`${ok ? 'GEÇTİ ' : 'KALDI '} ${name}${detail ? ' - ' + detail : ''}`); };

// Sahte mikrofon (ADIM 11.3 tarayıcıda kayıt senaryosu): izin sorulmaz, cihaz bip sesi üretir
const browser = await chromium.launch({ executablePath: CHROME, args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'] });

async function session(userKey, viewport = { width: 1440, height: 1000 }) {
  const ctx = await browser.newContext({ viewport });
  const page = await ctx.newPage();
  page.on('console', (m) => { if (m.type() === 'error') problems.push(`[${userKey}] konsol: ${m.text().slice(0, 200)}`); });
  page.on('response', (r) => { if (r.status() >= 500) problems.push(`[${userKey}] ${r.status()} ${r.request().method()} ${r.url()}`); });
  page.on('pageerror', (e) => problems.push(`[${userKey}] sayfa hatası: ${e.message.slice(0, 200)}`));
  const u = cfg.users[userKey];
  await page.goto(`${APP}/#/landing`);
  await page.getByRole('button', { name: /Giriş Yap/ }).first().click();
  await page.locator('input[type="email"]').last().fill(u.email);
  await page.locator('input[type="password"]').last().fill(u.password);
  await page.getByRole('button', { name: /Giriş Yap →/ }).click();
  // Şirket yöneticisi doğrudan Şirket Yönetimi'ne, diğerleri Work Space'e yönlenir
  await page.waitForURL(/#\/(workspace|company-admin|super-admin)/, { timeout: 20000 });
  return { ctx, page };
}
const shot = (page, name) => page.screenshot({ path: `${OUT}/${name}.png` });
// Bağlantı kataloğundan sistem kartı seçer (ADIM 12.1); aynı iletişim kutusu bağlantı formuna döner
const pickCard = async (dlg, title) => {
  await dlg.getByRole('list', { name: 'Bağlantı kataloğu' }).getByRole('listitem').filter({ hasText: title }).first().click();
  await dlg.locator('#ig-name').waitFor({ timeout: 10000 });
};
const dialogOk = async (page, text) => {
  const d = page.getByRole('alertdialog');
  await d.waitFor({ timeout: 10000 });
  if (text !== undefined) await d.locator('input').fill(text);
  await d.locator('button[type="submit"]').click();
};
// Başlık tam eşleşmeli: bir adımın adı diğerinin içinde geçebilir ("Tasarım" / "Tasarım Doğrulama")
const escapeRe = (t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const stepCard = (page, title) => page.locator('.pj-step').filter({
  has: page.locator('strong', { hasText: new RegExp(`^\\s*${escapeRe(title.trim())}\\s*$`) }),
}).first();
const statusOf = async (page, title) => (await stepCard(page, title).locator('.ui-badge').first().textContent())?.trim();
const waitStatus = async (page, title, label, timeout = 45000) => {
  await stepCard(page, title).locator('.ui-badge', { hasText: label }).waitFor({ timeout });
};

// Onay bağlantısı belirteci (e-postadakiyle aynı tür; yalnızca canlı test şirketi için üretilebilir)
const mintToken = (taskId) => execFileSync('docker', ['exec', '-w', '/app', process.env.BACKEND_CONTAINER || 'recorion_backend',
  'python', 'scripts/live_test_token.py', taskId], { encoding: 'utf8', env: { ...process.env, MSYS_NO_PATHCONV: '1' } }).trim().split('\n').pop();

const NAME = `Canlı Test ${new Date().toISOString().slice(0, 16).replace('T', ' ')}`;
let ok = true;
try {
  // 1. Yönetici girişi ve proje oluşturma
  const { page } = await session('manager');
  // Önceki yarım kalmış canlı test projeleri kapatılır (test şirketinde açık proje birikmesin)
  const closed = await page.evaluate(async () => {
    const token = sessionStorage.getItem('recorion_token') || localStorage.getItem('recorion_token');
    const h = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
    const ps = await (await fetch('/api/v1/projects/?scope=mine', { headers: h })).json();
    const open = ps.filter((p) => p.name.startsWith('Canlı Test') && !['COMPLETED', 'CANCELLED'].includes(p.status));
    for (const p of open) await fetch(`/api/v1/projects/${p.id}/status`, { method: 'POST', headers: h, body: JSON.stringify({ action: 'cancel', summary: 'Yeni canlı test başladı' }) });
    return open.length;
  });
  if (closed) step(true, 'Önceki yarım kalmış test projeleri iptal edildi', `${closed} proje`);
  await page.getByRole('button', { name: 'Yeni Proje / Case' }).first().click();
  await page.locator('#pj-name').fill(NAME);
  await page.locator('#pj-desc').fill('Bayilerin sipariş verebileceği basit bir web portalı.');
  await page.locator('#pj-req').fill('Bayi girişi olmalı. Bayi ürün listesini görüp sipariş oluşturabilmeli. Sipariş durumu izlenebilmeli. '
    + 'Kapsam küçük tutulsun: en fazla 4 iş adımı yeterli (analiz, geliştirme, test).');
  await page.getByRole('button', { name: 'Oluştur', exact: true }).click();
  await page.getByRole('heading', { name: NAME }).waitFor({ timeout: 15000 });
  step(true, 'Proje oluşturuldu (Taslak)', NAME);

  // 2. Beyin AI planı (gerçek EVREN çağrısı)
  await page.getByRole('tab', { name: /Beyin AI Planlama/ }).click();
  const t1 = Date.now();
  // Kullanıcı gibi: EVREN yoğunluğunda "yapay zeka şu anda yanıt veremiyor" görürse bir dakika bekleyip yeniden dener (en fazla 3 kez)
  let planTries = 0;
  let planOk = false;
  while (!planOk && planTries < 3) {
    planTries += 1;
    const resp = page.waitForResponse((r) => r.url().includes('/plan/suggest') && r.request().method() === 'POST', { timeout: 11 * 60000 });
    await page.getByRole('button', { name: 'Beyin AI plan önersin' }).click();
    const r = await resp;
    if (r.status() < 400) {
      await page.locator('.pj-step').first().waitFor({ timeout: 30000 });
      planOk = true;
    } else if (planTries < 3) {
      await page.waitForTimeout(60000);
    }
  }
  const stepCount = await page.locator('.pj-step').count();
  step(stepCount > 0, 'Beyin AI iş adımı önerdi',
    `${stepCount} adım, ${Math.round((Date.now() - t1) / 1000)} sn${planTries > 1 ? ` (EVREN yoğun: ${planTries}. denemede)` : ''}`);
  if (!planOk) throw new Error(`Beyin AI ${planTries} denemede plan öneremedi (EVREN yanıt vermiyor)`);
  // Personeli atanmamış adımlara havuzdan personel ata
  const selects = page.locator('select[aria-label="AI personel"]');
  let assigned = 0;
  for (let i = 0; i < await selects.count(); i += 1) {
    if (!(await selects.nth(i).inputValue())) { await selects.nth(i).selectOption({ index: 1 + (i % 2) }); assigned += 1; }
  }
  if (assigned) step(true, 'Boş adımlara personel atandı', `${assigned} adım`);
  // Kontrol personeli (7.2): yalnızca ilk adımda (süre ve kredi sınırlı kalsın)
  const reviewers = page.locator('.pj-step select', { has: page.locator('option', { hasText: 'Kontrol yok' }) });
  for (let i = 0; i < await reviewers.count(); i += 1) await reviewers.nth(i).selectOption(i === 0 ? { index: 1 } : '');
  step(await reviewers.count() > 0, 'İlk adıma kontrol personeli atandı');

  // 7.4 Akış şeması: düğüm/bağlantı, sürükle-bırak konum, son adımda "onay gerekmez"
  const planSteps = await page.locator('.pj-step').count();
  await page.getByRole('button', { name: 'Akış şeması' }).click();
  await page.locator('.pj-flow-node').first().waitFor({ timeout: 15000 });
  const nodeCount = await page.locator('.pj-flow-node').count();
  const edgeCount = await page.locator('.react-flow__edge').count();
  step(nodeCount === planSteps && edgeCount >= 1, 'Akış şeması adımları ve bağımlılıkları gösteriyor', `${nodeCount} düğüm, ${edgeCount} bağlantı`);
  const firstNode = page.locator('.pj-flow-node').first();
  const box = await firstNode.boundingBox();
  await page.mouse.move(box.x + 60, box.y + 12);
  await page.mouse.down();
  await page.mouse.move(box.x + 160, box.y + 12, { steps: 8 });
  await page.mouse.up();
  await page.locator('.pj-flow-node').last().click();
  await page.getByText('İnsan onayı gerekli').click();
  const lastTitle = await page.locator('#si-title').inputValue();
  step(true, 'Son adımda insan onayı kapatıldı (şema düzenleyici)', lastTitle);
  await shot(page, '01b-akis-semasi');
  await shot(page, '01-plan');
  await page.getByRole('button', { name: 'Onayla ve iş adımlarına dönüştür' }).click();
  await dialogOk(page);
  await page.locator('.ui-badge', { hasText: 'Onaylandı' }).first().waitFor({ timeout: 20000 });
  step(true, 'Plan onaylandı, iş adımlarına dönüştü');
  await page.getByRole('button', { name: 'Liste', exact: true }).click();
  const titles = await page.locator('input[aria-label="Adım adı"]').evaluateAll((els) => els.map((e) => e.value));
  const savedPlan = await page.evaluate(async (name) => {
    const token = sessionStorage.getItem('recorion_token') || localStorage.getItem('recorion_token');
    const h = { Authorization: `Bearer ${token}` };
    const p = (await (await fetch('/api/v1/projects/?scope=mine', { headers: h })).json()).find((x) => x.name === name);
    return (await (await fetch(`/api/v1/projects/${p.id}`, { headers: h })).json()).plan.steps;
  }, NAME);
  step(savedPlan.some((x) => x.pos) && savedPlan[savedPlan.length - 1].requires_approval === false,
    'Şemadaki konum ve onay ayarı plana kaydedildi', `konumlu adım: ${savedPlan.filter((x) => x.pos).length}, son adım onay: ${savedPlan[savedPlan.length - 1].requires_approval}`);

  // 3. Ekip ve simülasyon
  await page.getByRole('tab', { name: /Ekip & Simülasyon/ }).click();
  await page.locator('select[aria-label="Eklenecek personel"]').selectOption({ label: 'Canlı Test Uzmanı' });
  await page.getByRole('button', { name: 'Ekle', exact: true }).click();
  await page.locator('.pj-list li', { hasText: 'Canlı Test Uzmanı' }).waitFor({ timeout: 10000 });
  step(true, 'İnsan personel ekibe eklendi');
  await page.locator('input[aria-label="Başlangıç tarihi"]').fill(new Date().toISOString().slice(0, 10));
  await page.getByRole('button', { name: 'Simüle et' }).click();
  await page.locator('.pj-stat', { hasText: 'Tahmini bitiş' }).waitFor({ timeout: 20000 });
  const sim = await page.locator('.pj-stats').first().innerText();
  step(true, 'Simülasyon yapıldı', sim.replace(/\s+/g, ' '));
  const apply = page.getByRole('button', { name: 'Bu tarihleri projeye uygula' });
  if (await apply.count()) { await apply.click(); await page.waitForTimeout(1500); step(true, 'Simülasyon tarihleri projeye uygulandı'); }
  await shot(page, '02-simulasyon');

  // 8.5 Kod deposu: yönetici projeyi başlatmadan önce RECOrion (Gitea) deposunu açar
  await page.getByRole('tab', { name: 'Kod Deposu' }).click();
  await page.getByRole('button', { name: 'RECOrion deposunu aç' }).click();
  const repoOn = await page.getByText('RECOrion deposu açık').waitFor({ timeout: 30000 }).then(() => true).catch(() => false);
  const repoUrl = repoOn ? await page.locator('.pj-hint[title^="Depo özeldir"]').first().innerText() : '';
  step(repoOn && /rx-.+\/.+/.test(repoUrl), 'Proje kod deposu açıldı (özel Gitea deposu)', repoUrl);

  // 4. Hazırlık ve başlatma (Temporal akışı başlar)
  await page.getByRole('tab', { name: /Hazırlık & Bildirim/ }).click();
  await page.getByRole('button', { name: 'Başlamaya hazır yap' }).click();
  await page.getByRole('button', { name: 'Projeyi şimdi başlat' }).waitFor({ timeout: 10000 });
  step(true, 'Proje başlamaya hazır');
  await page.getByRole('button', { name: 'Projeyi şimdi başlat' }).click();
  await dialogOk(page);
  await page.locator('.ui-badge', { hasText: 'Aktif' }).first().waitFor({ timeout: 15000 });
  step(true, 'Proje başlatıldı (Aktif)');

  // 5. İş akışı: AI personel adımları kendisi yürütür (gerçek EVREN), kontrol personeli değerlendirir
  await page.getByRole('tab', { name: /İş Akışı/ }).click();
  const first = titles[0];
  await page.getByRole('button', { name: 'Akış şeması' }).click();
  await page.locator('.pj-flow-node').first().waitFor({ timeout: 15000 });
  step(await page.locator('.pj-flow-node').count() === titles.length, 'İş Akışı şeması canlı durumları gösteriyor',
    (await page.locator('.pj-flow-node .ui-badge').allTextContents()).join(', '));
  await shot(page, '02b-canli-sema');
  await page.getByRole('button', { name: 'Liste', exact: true }).click();
  const versionOf = async (title) => Number(((await stepCard(page, title).getByRole('button', { name: /Çıktıyı gör/ }).textContent()) || '').match(/sürüm (\d+)/)?.[1] || 0);
  // Onaya gelene kadar bekle; kontrol personeli 3 kez reddederse karantina olur (raporlanır, bir kez yeniden denenir)
  // 8.2: İş Akışı ekranında AI'ın o anki adımı (canlı akış) sayfa yenilemeden görünüyor mu
  const liveSeen = new Set();
  const untilApproval = async (title, minutes) => {
    const start = Date.now();
    let retried = 0;
    while (Date.now() - start < minutes * 60000) {
      const note = await page.locator('.pj-note[role="status"]').first().innerText().catch(() => '');
      if (/Canlı/.test(note)) liveSeen.add('canlı');
      const m2 = note.match(/(yazıyor|değerlendiriyor|devam ediyor|kaynak)/);
      if (m2) liveSeen.add(m2[1]);
      const st = await statusOf(page, title);
      if (st === 'Onay bekliyor') return retried;
      if (st === 'Karantinada' && retried < 1) {
        retried += 1;
        step(false, `'${title}' kontrol personelinin 3 reddiyle karantinaya düştü`, 'yönetici yeniden deniyor');
        await stepCard(page, title).getByRole('button', { name: 'Yeniden dene' }).click();
      }
      await page.waitForTimeout(3000);
    }
    throw new Error(`'${title}' ${minutes} dakikada onaya gelmedi (durum: ${await statusOf(page, title)})`);
  };
  const tw = Date.now();
  await untilApproval(first, 20);
  const v1 = await versionOf(first);
  const reviewNotes = await page.locator('.pj-list li', { hasText: 'Kontrol' }).count();
  step(v1 >= 1, 'AI personel ilk adımı kendisi yürüttü, kontrolden geçip onaya geldi',
    `sürüm ${v1}, ${Math.round((Date.now() - tw) / 1000)} sn, kontrol kaydı: ${reviewNotes}`);
  step(liveSeen.has('canlı') && liveSeen.size > 1, "İş Akışı canlı: AI'ın o anki adımı sayfa yenilemeden göründü", [...liveSeen].join(', '));
  const noSubmit = await stepCard(page, first).getByRole('button', { name: /teslim et/ }).count();
  step(noSubmit === 0, 'AI adımında elle teslim butonu yok (AI kendi teslim eder)');
  await stepCard(page, first).getByRole('button', { name: /Çıktıyı gör/ }).click();
  const modal = page.getByRole('dialog');
  await modal.locator('.ui-modal-body').waitFor({ timeout: 15000 });
  await page.waitForTimeout(1500);
  const out1 = await modal.locator('.ui-modal-body').innerText();
  step(out1.length > 200, 'AI çıktısı görüntülendi', `${out1.length} karakter: "${out1.slice(0, 70).replace(/\s+/g, ' ')}…"`);
  await shot(page, '03-ai-cikti');
  await modal.getByRole('button', { name: 'Kapat' }).click();

  // 5.1 Onaylarım kuyruğu (7.3): sayaç ve liste; İncele projeye götürür
  await page.getByRole('button', { name: /Onaylarım \(\d+\)/ }).waitFor({ timeout: 45000 });
  await page.getByRole('button', { name: /Onaylarım/ }).click();
  await page.locator('.pj-list li', { hasText: first }).waitFor({ timeout: 20000 });
  const inboxText = await page.locator('.pj-list li', { hasText: first }).innerText();
  step(/Onay bekliyor/.test(inboxText), 'Onaylarım kuyruğunda bekleyen karar görünüyor', inboxText.replace(/\s+/g, ' ').slice(0, 90));
  await shot(page, '03b-onaylarim');
  await page.locator('.pj-list li', { hasText: first }).getByRole('button', { name: 'İncele' }).click();
  await stepCard(page, first).waitFor({ timeout: 20000 });
  step(true, 'Onaylarım > İncele projenin İş Akışı sekmesini açtı');

  // 5a. Üye ve ekip dışı kullanıcı kontrolleri
  const m = await session('member');
  await m.page.locator('.pj-card', { hasText: NAME }).click();
  await m.page.getByRole('tab', { name: /İş Akışı/ }).click();
  await m.page.locator('.pj-step').first().waitFor({ timeout: 15000 });
  const memberApprove = await m.page.getByRole('button', { name: 'Onayla', exact: true }).count();
  const memberView = await m.page.getByRole('button', { name: /Çıktıyı gör/ }).count();
  step(memberApprove === 0 && memberView > 0, 'Ekip üyesi çıktıyı görüyor ama onaylayamıyor', `Onayla: ${memberApprove}, Çıktıyı gör: ${memberView}`);

  // 8.2 İki kişi aynı anda: yönetici Çalışma Alanında soru yazar, açık duran ekip üyesi ekranında sayfa yenilemeden görür
  const openWork = async (pg) => {
    await pg.getByRole('button', { name: 'Çalışma alanında aç' }).click();
    await pg.locator('main.pane textarea').waitFor({ timeout: 15000 });
    await pg.locator('main.pane .live-dot.live-live').waitFor({ timeout: 20000 });
  };
  await openWork(m.page);
  // 8.3 Paylaşılan doğrudan bağlantıyla giriş: #/workspace?project=ID&view=work
  const mgr2 = await session('manager');
  const projId = await mgr2.page.evaluate(async (name) => {
    const token = sessionStorage.getItem('recorion_token') || localStorage.getItem('recorion_token');
    const ps = await (await fetch('/api/v1/projects/?scope=mine', { headers: { Authorization: `Bearer ${token}` } })).json();
    return ps.find((x) => x.name === name)?.id;
  }, NAME);
  await mgr2.page.goto(`${APP}/#/workspace?project=${projId}&view=work`);
  await mgr2.page.reload();
  // Sohbet kutusu proje yüklenmeden görünür; canlı bağlantı kurulduysa proje de yüklenmiştir
  const deep = await mgr2.page.locator('main.pane .live-dot.live-live').waitFor({ timeout: 25000 }).then(() => true).catch(() => false);
  const picker = mgr2.page.locator('select[aria-label="Proje seç"]');
  const pickedName = !deep ? '' : (await picker.count())
    ? await picker.evaluate((sel) => sel.selectedOptions[0]?.text || '')
    : await mgr2.page.locator('.tri-pane-container aside.pane').first().locator('.pane-header strong').innerText();
  step(deep && pickedName.includes(NAME), 'Doğrudan bağlantı Çalışma Alanını doğru projeyle açtı', pickedName.slice(0, 60));
  await mgr2.page.locator('main.pane .live-dot.live-live').waitFor({ timeout: 20000 });

  // 8.3 Ekip üyesinin ekranında sahte içerik yok; karar düğmesi yok ama gerçek çıktı açılıyor
  const memberWork = await m.page.locator('.tri-pane-container').innerText();
  const fakes = ['OTONOM İŞ AKIŞI ZİNCİRİ', 'Mimar➔Coder', 'MİMARİ_PLAN_V1', 'REC-001', 'NS_GLOBAL', 'Cüneyt (Yönetici)', 'Temporal Engine'].filter((t) => memberWork.includes(t));
  step(fakes.length === 0, 'Çalışma Alanında sahte/sabit içerik yok', fakes.length ? `kalan: ${fakes.join(', ')}` : 'proje ekibi, gerçek ilerleme ve durumlar');
  const right = m.page.locator('aside.pane').last();
  const memberDecide = await right.getByRole('button', { name: /Onayla & İlerlet/ }).count();
  const decider = await right.getByText(/tarafından verilecek/).count();
  await right.getByRole('button', { name: /Çıktıyı gör/ }).click();
  const artModal = m.page.getByRole('dialog');
  await artModal.locator('.ui-modal-body').waitFor({ timeout: 15000 });
  await m.page.waitForTimeout(1500);
  const artText = await artModal.locator('.ui-modal-body').innerText();
  step(memberDecide === 0 && decider === 1 && artText.length > 200, 'Ekip üyesi sağ panelde gerçek çıktıyı açıyor, onay düğmesi görmüyor',
    `çıktı ${artText.length} karakter · karar düğmesi: ${memberDecide}`);
  await artModal.getByRole('button', { name: 'Kapat' }).click();

  // 8.2 + 8.3 İki kişi aynı anda; yönetici mesaja dosya ekleyip dosyanın içeriğini sorar
  const taskTitle = (await mgr2.page.locator('main.pane .pane-header span').first().innerText()).trim();
  const memberTask = (await m.page.locator('main.pane .pane-header span').first().innerText()).trim();
  const bubbles = () => m.page.locator('main.pane .chat-bubble:not(.thinking-pulse)').count();
  const before = await bubbles();
  const code = `ZEYTIN-${Date.now() % 1000}`;
  await mgr2.page.locator('main.pane input[type="file"]').setInputFiles({ name: 'toplanti-notu.txt', mimeType: 'text/plain',
    buffer: Buffer.from(`Toplantı notu (canlı test)\nBu projenin iç kod adı ${code} olarak belirlendi.\nTeslim tarihi değişmedi.\n`) });
  await mgr2.page.locator('main.pane .wa-chip', { hasText: 'toplanti-notu.txt' }).waitFor({ timeout: 30000 });
  const question = `Ekteki toplantı notuna göre projenin iç kod adı nedir? Sadece kod adını yaz.`;
  await mgr2.page.locator('main.pane textarea').fill(question);
  await mgr2.page.locator('main.pane textarea').press('Enter');
  const tq = Date.now();
  const seenQuestion = await m.page.locator('main.pane', { hasText: question }).waitFor({ timeout: 15000 }).then(() => true).catch(() => false);
  const senderShown = await m.page.locator('main.pane .chat-bubble-user', { hasText: question }).innerText().catch(() => '');
  step(seenQuestion && taskTitle === memberTask, 'Ekip üyesi, yöneticinin mesajını sayfa yenilemeden anında gördü',
    `${((Date.now() - tq) / 1000).toFixed(1)} sn · görev: ${taskTitle}`);
  step(/Canlı Test Yöneticisi/.test(senderShown) && /toplanti-notu\.txt/.test(senderShown), 'Mesajda gerçek gönderen adı ve dosya eki görünüyor',
    senderShown.split('\n')[0].slice(0, 60));
  const thinking = await m.page.locator('main.pane .thinking-pulse').waitFor({ timeout: 20000 }).then(() => true).catch(() => false);
  let answered = false;
  const ta = Date.now();
  while (Date.now() - ta < 6 * 60000 && !answered) {
    answered = (await bubbles()) >= before + 2;
    if (!answered) await m.page.waitForTimeout(2000);
  }
  step(answered, "AI'ın yanıtı da ekip üyesinin ekranına kendiliğinden düştü",
    `${Math.round((Date.now() - tq) / 1000)} sn · "yazıyor" göstergesi ekip üyesinde: ${thinking ? 'göründü' : 'görünmedi'}`);
  const reply = await m.page.locator('main.pane .chat-bubble-ai:not(.thinking-pulse)').last().innerText().catch(() => '');
  step(reply.includes(code), 'AI mesaja eklenen dosyayı okuyup doğru yanıtladı', reply.replace(/\s+/g, ' ').slice(0, 90));
  await shot(m.page, '04b-canli-sohbet-uye');

  // 8.4 Kurum Hafızası: yönetici sohbette şirket kuralı söyler; AI aday çıkarırsa yönetici onaylar, iz görünür, gerekçeyle geri alır
  const memberTabs = await m.page.locator('aside.pane').last().getByRole('tab').allTextContents();
  step(!memberTabs.some((t) => /Onay bekliyor|Reddedilen/.test(t)), 'Ekip üyesi onay bekleyen/reddedilen hafızayı görmüyor', memberTabs.join(', '));
  const mBefore = await bubbles();
  // Önceki koşulardan kalan kayıtlar karışmasın: bu koşuda oluşan aday kimliğiyle seçilir
  const memory = async () => {
    const token = await mgr2.page.evaluate(() => sessionStorage.getItem('recorion_token') || localStorage.getItem('recorion_token'));
    const h = { Authorization: `Bearer ${token}` };
    const proj = (await (await fetch(`${APP}/api/v1/projects/?scope=mine`, { headers: h })).json()).find((x) => x.name === NAME);
    return (await fetch(`${APP}/api/v1/memory?tenant_id=${proj.tenant_id}`, { headers: h })).json();
  };
  const memBefore = new Set((await memory()).map((i) => i.id));
  const rule = 'Şirket kuralı: tüm müşteri tekliflerimiz 15 gün geçerlidir ve fiyatlar KDV hariç verilir. Bundan sonraki tüm işlerde bunu dikkate al.';
  // Yanıt gelince yazma kutusu hemen açılır (öğrenme arka planda); en fazla 30 sn beklenir
  const tUnlock = Date.now();
  await mgr2.page.locator('main.pane textarea:not([disabled])').waitFor({ timeout: 30000 });
  const unlockSec = Math.round((Date.now() - tUnlock) / 1000);
  await mgr2.page.locator('main.pane textarea').fill(rule);
  await mgr2.page.locator('main.pane textarea').press('Enter');
  const tr0 = Date.now();
  while (Date.now() - tr0 < 6 * 60000 && (await bubbles()) < mBefore + 2) await m.page.waitForTimeout(2000);
  await mgr2.page.locator('main.pane textarea:not([disabled])').waitFor({ timeout: 6 * 60000 });  // gönderim (öğrenme dahil) bitti
  const mright = mgr2.page.locator('aside.pane').last();
  await mright.getByRole('tab', { name: /Onay bekliyor/ }).click();
  const fresh = (await memory()).find((i) => !memBefore.has(i.id) && i.status === 'CANDIDATE' && /15 gün/.test(i.content));
  const cardOf = () => mright.locator('.wa-artifact', { hasText: fresh.content.slice(0, 60) }).first();
  const cand = fresh ? cardOf() : null;
  if (!fresh || !(await cand.count())) {
    step(true, 'Kurum Hafızası adayı', 'AI bu konuşmadan şirket geneli bilgi çıkarmadı; onay senaryosu bu koşuda atlandı');
  } else {
    await cand.getByRole('button', { name: 'Onayla' }).click();
    await dialogOk(mgr2.page);
    await mright.getByRole('tab', { name: 'Onaylı' }).click();
    const approved = cardOf();
    await approved.waitFor({ timeout: 15000 });
    const approvedText = await approved.innerText();
    step(/Onaylayan: Canlı Test Yöneticisi/.test(approvedText) && /Kurum hafızası/.test(approvedText),
      'Yönetici adayı Kurum Hafızasına onayladı; onaylayan ve zaman görünüyor',
      (approvedText.split('\n').find((l) => l.startsWith('Onaylayan')) || '').slice(0, 90));
    await approved.getByRole('button', { name: 'Geri al' }).click();
    await dialogOk(mgr2.page, 'Canlı test: geri alma denemesi');
    await mright.getByRole('tab', { name: 'Reddedilen' }).click();
    const revoked = cardOf();
    await revoked.waitFor({ timeout: 15000 });
    const revokedText = await revoked.innerText();
    const after = (await memory()).find((i) => i.id === fresh.id);
    step(/geri alma denemesi/.test(revokedText) && after?.status === 'REVOKED' && after?.review_note === 'Canlı test: geri alma denemesi',
      'Onaylı bilgi gerekçeyle geri alındı (AI personel artık kullanmaz)', revokedText.split('\n').slice(-1)[0].slice(0, 90));
  }
  // Güvenlik: dosyadaki projeye özgü kod adı personel/şirket hafızasına taşınmamalı (başka projeye sızmasın)
  await mgr2.page.waitForTimeout(20000);  // arka plandaki öğrenme bitsin
  const leaked = (await memory()).filter((i) => i.content.includes(code) && i.status !== 'REVOKED');
  step(leaked.length === 0, 'Projeye özgü bilgi (dosyadaki kod adı) AI personelin ve şirketin hafızasına taşınmadı',
    `${code}: ${leaked.length ? leaked.map((i) => `${i.scope}/${i.status}`).join(', ') : 'hafızada yok'} · yanıttan sonra yazma kutusu ${unlockSec} sn içinde açıldı`);
  await shot(mgr2.page, '04c-hafiza');
  await mgr2.ctx.close();
  await m.ctx.close();
  const o = await session('outsider');
  await o.page.getByText('Henüz proje yok').waitFor({ timeout: 15000 }).then(() => step(true, 'Ekip dışı kullanıcı projeyi göremiyor'))
    .catch(async () => step(false, 'Ekip dışı kullanıcı projeyi göremiyor', await o.page.locator('.pj-page').innerText()));
  await o.ctx.close();

  // 5b. Yönetici reddi > AI geri bildirimle düzeltir
  await stepCard(page, first).getByRole('button', { name: 'Revizyon iste' }).click();
  await dialogOk(page, "Çıktıya 'Riskler ve Önlemler' başlıklı bir bölüm ekle.");
  const tr = Date.now();
  while (Date.now() - tr < 12 * 60000 && !((await versionOf(first)) > v1 && (await statusOf(page, first)) === 'Onay bekliyor')) {
    await page.waitForTimeout(3000);
  }
  const v2 = await versionOf(first);
  await stepCard(page, first).getByRole('button', { name: /Çıktıyı gör/ }).click();
  await page.waitForTimeout(2000);
  const out2 = await page.getByRole('dialog').locator('.ui-modal-body').innerText();
  await page.getByRole('dialog').getByRole('button', { name: 'Kapat' }).click();
  step(v2 > v1 && /risk/i.test(out2), 'Ret sonrası AI geri bildirimle düzeltilmiş sürüm üretti',
    `sürüm ${v1} > ${v2}, ${Math.round((Date.now() - tr) / 1000)} sn, 'Risk' bölümü: ${/risk/i.test(out2) ? 'var' : 'yok'}`);

  // 5c. Tüm adımlar AI tarafından sırayla yürütülür; yönetici onaylar
  const deadline = Date.now() + 40 * 60000;
  let approved = 0;
  let released = 0;
  let linkApproved = false;
  while (Date.now() < deadline) {
    const waiting = page.locator('.pj-step', { has: page.getByRole('button', { name: 'Onayla', exact: true }) });
    const quarantined = page.locator('.pj-step', { has: page.getByRole('button', { name: 'Yeniden dene' }) });
    if (await waiting.count() && !linkApproved) {
      // 7.3: e-postadaki bağlantının açtığı sayfa, giriş yapılmamış tarayıcıda
      linkApproved = true;
      const title = (await waiting.first().locator('strong').first().textContent()).trim();
      const taskId = await page.evaluate(async ({ name, t }) => {
        const token = sessionStorage.getItem('recorion_token') || localStorage.getItem('recorion_token');
        const h = { Authorization: `Bearer ${token}` };
        const p = (await (await fetch('/api/v1/projects/?scope=mine', { headers: h })).json()).find((x) => x.name === name);
        return (await (await fetch(`/api/v1/projects/${p.id}/workflow`, { headers: h })).json()).tasks.find((x) => x.title === t).id;
      }, { name: NAME, t: title });
      const raw = mintToken(taskId);
      const anon = await browser.newContext({ viewport: { width: 1280, height: 900 } });
      const ap = await anon.newPage();
      ap.on('response', (r) => { if (r.status() >= 500) problems.push(`[onay sayfası] ${r.status()} ${r.url()}`); });
      await ap.goto(`${APP}/#/approve?token=${raw}`);
      await ap.getByText(title).first().waitFor({ timeout: 20000 });
      const hasOutput = await ap.getByText(/Çıktı · sürüm/).count();
      await ap.screenshot({ path: `${OUT}/04b-onay-sayfasi.png` });
      await ap.getByRole('button', { name: 'Onayla', exact: true }).click();
      await ap.getByText('Kararınız iş akışına iletildi').waitFor({ timeout: 20000 });
      await ap.goto(`${APP}/#/landing`);
      await ap.goto(`${APP}/#/approve?token=${raw}`);
      await ap.reload();
      const reused = await ap.getByText('Bağlantı kullanılamıyor').waitFor({ timeout: 20000 }).then(() => true).catch(() => false);
      await anon.close();
      await waitStatus(page, title, 'Tamamlandı', 60000);
      step(hasOutput > 0 && reused, 'Onay bağlantısıyla girişsiz karar verildi; bağlantı ikinci kez kullanılamıyor',
        `'${title}' onaylandı, çıktı gösterildi: ${hasOutput > 0 ? 'evet' : 'hayır'}, tekrar kullanım engellendi: ${reused ? 'evet' : 'hayır'}`);
      approved += 1;
    } else if (await waiting.count()) {
      await waiting.first().getByRole('button', { name: 'Onayla', exact: true }).click();
      approved += 1;
      await page.waitForTimeout(2500);
    } else if (await quarantined.count() && released < 2) {
      released += 1;
      await quarantined.first().getByRole('button', { name: 'Yeniden dene' }).click();
      await page.waitForTimeout(2500);
    } else {
      const done = await page.locator('.pj-step .ui-badge', { hasText: 'Tamamlandı' }).count();
      if (done === titles.length) break;
      await page.waitForTimeout(3000);
    }
  }
  const doneCount = await page.locator('.pj-step .ui-badge', { hasText: 'Tamamlandı' }).count();
  if (!linkApproved) step(false, 'Onay bağlantısı senaryosu çalışmadı (onay bekleyen adım bulunamadı)');
  step(doneCount === titles.length, 'Tüm adımları AI personel sırayla yürüttü, yönetici onayladı',
    `${doneCount}/${titles.length} tamamlandı, ${approved} onay${released ? `, ${released} karantinadan yeniden deneme` : ''}`);
  await page.getByText('Tüm adımlar tamamlandı').first().waitFor({ timeout: 30000 })
    .then(() => step(true, 'Proje akışı bitti, yöneticiye bildirim kaydı düştü'))
    .catch(() => step(false, 'Proje akışı bitti kaydı'));
  await shot(page, '05-akis-tamam');

  // 6. API ile olay geçmişi sağlaması (aynı oturum)
  const flow = await page.evaluate(async () => {
    const token = sessionStorage.getItem('recorion_token') || localStorage.getItem('recorion_token');
    const ps = await (await fetch('/api/v1/projects/?scope=mine', { headers: { Authorization: `Bearer ${token}` } })).json();
    return Promise.all(ps.map(async (p) => ({ name: p.name, f: await (await fetch(`/api/v1/projects/${p.id}/workflow`, { headers: { Authorization: `Bearer ${token}` } })).json() })));
  });
  const mine = flow.find((x) => x.name === NAME)?.f;
  const kinds = (mine?.events || []).map((e) => e.kind);
  const cnt = (k) => kinds.filter((x) => x === k).length;
  step(cnt('AI_OUTPUT') >= titles.length + 1 && cnt('REVIEW_PASSED') + cnt('REVIEW_FAILED') >= 1 && cnt('REJECTED') >= 1
    && cnt('DONE') === titles.length && cnt('PROJECT_FINISHED') === 1,
    'Silinemez akış geçmişi tutarlı', `AI_OUTPUT:${cnt('AI_OUTPUT')} REVIEW_PASSED:${cnt('REVIEW_PASSED')} REVIEW_FAILED:${cnt('REVIEW_FAILED')} REJECTED:${cnt('REJECTED')} BLOCKED:${cnt('BLOCKED')} APPROVED:${cnt('APPROVED')} DONE:${cnt('DONE')} FINISHED:${cnt('PROJECT_FINISHED')}`);
  const lastTask = mine?.tasks.find((t) => t.title === lastTitle);
  const lastKinds = (mine?.events || []).filter((e) => e.task_id === lastTask?.id).map((e) => e.kind);
  step(lastKinds.includes('DONE') && !lastKinds.includes('APPROVED'), "'Onay gerekmez' adımı onaysız tamamlandı", `${lastTitle}: ${[...new Set(lastKinds)].join(', ')}`);
  const channels = (mine?.events || []).filter((e) => e.kind === 'APPROVED').map((e) => e.data?.channel || 'WEB');
  step(channels.includes('EMAIL'), 'Onay kanalları akış geçmişinde kayıtlı', channels.join(', '));
  const credits = (mine?.events || []).filter((e) => e.kind === 'AI_OUTPUT').reduce((sum, e) => sum + (e.data?.credits || 0), 0);
  const outs = (mine?.events || []).filter((e) => e.kind === 'AI_OUTPUT');
  const models = [...new Set(outs.map((e) => e.data?.model))].join(', ');
  const fallbacks = outs.filter((e) => e.data?.fallback_from).map((e) => `${e.data.fallback_from} > ${e.data.model}`);
  step(true, 'Kullanılan modeller ve yedek model geçişleri', `${models}${fallbacks.length ? ` · yedek: ${fallbacks.join('; ')}` : ' · yedek gerekmedi'}`);
  step(credits > 0, 'AI çalışmaları ölçüldü ve krediden düştü', `${credits.toFixed(2)} kredi (${cnt('AI_OUTPUT')} çıktı)`);

  // 8.5 Kod deposu: onaylanan adımlar ana dala birleşti; onay gerektirmeyen son adımı yönetici birleştirir; dosya görüntülenir
  await page.getByRole('tab', { name: 'Kod Deposu' }).click();
  await page.locator('.pj-steps .ui-badge', { hasText: /Ana dala birleşti|Onay bekliyor/ }).first().waitFor({ timeout: 30000 });
  const lastCard = page.locator('.ui-card', { hasText: lastTitle }).filter({ has: page.getByRole('button', { name: 'Ana dala birleştir' }) });
  let manualMerge = 'gerekmedi';
  if (await lastCard.count()) {
    await lastCard.getByRole('button', { name: 'Ana dala birleştir' }).click();
    await dialogOk(page);
    manualMerge = await page.locator('.ui-card', { hasText: lastTitle }).locator('.ui-badge', { hasText: 'Ana dala birleşti' })
      .waitFor({ timeout: 60000 }).then(() => 'birleştirildi').catch(() => 'birleştirilemedi');
  }
  const merged = await page.locator('.ui-badge', { hasText: 'Ana dala birleşti' }).count();
  const paths = await page.locator('.pj-list li span[style*="mono"]').allTextContents();
  const codeFiles = paths.filter((x) => !x.startsWith('docs/'));
  step(merged >= titles.length && paths.some((x) => x.startsWith('docs/adimlar/')) && manualMerge !== 'birleştirilemedi',
    'Onaylanan adımlar ana dala birleşti; onay gerektirmeyen adım yönetici tarafından birleştirildi',
    `${merged}/${titles.length} birleşti · son adım: ${manualMerge} · ${paths.length} dosya (${codeFiles.length} kod/yapılandırma: ${codeFiles.slice(0, 4).join(', ') || '—'})`);
  await page.locator('.pj-list li').filter({ hasText: codeFiles[0] || 'docs/adimlar/' }).first().getByRole('button').click();
  const fileModal = page.getByRole('dialog');
  await fileModal.locator('pre').waitFor({ timeout: 20000 });
  const fileText = await fileModal.locator('pre').innerText();
  step(fileText.length > 50, 'Depodaki dosya RECOrion içinden görüntülendi', `${codeFiles[0] || 'doküman'} · ${fileText.length} karakter`);
  await shot(page, '06b-kod-deposu');
  await fileModal.getByRole('button', { name: 'Kapat' }).click();

  // 7.5 Maliyet: rapor, bütçe, belgeli kalem, Excel, kapanış özeti ve kapanış kilidi
  await page.getByRole('tab', { name: /^Maliyet/ }).click();
  await page.locator('.pj-stat', { hasText: 'Gerçekleşen' }).first().waitFor({ timeout: 20000 });
  const unpricedNote = await page.getByText(/LLM çağrısının TL fiyatı tanımlı değil/).count();
  const stepRows = await page.locator('.ui-table').first().locator('tbody tr').count();
  step(stepRows >= titles.length, 'Maliyet sekmesi adım bazında maliyeti gösteriyor',
    `${stepRows} satır (proje geneli dahil), fiyatsız çağrı uyarısı: ${unpricedNote ? 'var (LLM fiyatı henüz girilmedi)' : 'yok'}`);
  await page.locator('#cost-budget').fill('15000');
  await page.locator('#cost-budget-note').fill('Canlı test bütçesi');
  await page.getByRole('button', { name: 'Bütçeyi kaydet' }).click();
  await page.waitForTimeout(1500);
  await page.getByRole('button', { name: 'Kalem ekle' }).click();
  const dlg = page.getByRole('dialog');
  await dlg.locator('#ci-cat').selectOption('DANISMANLIK');
  await dlg.locator('#ci-desc').fill('Güvenlik danışmanlığı (canlı test)');
  await dlg.locator('#ci-qty').fill('2');
  await dlg.locator('#ci-unit').fill('gün');
  await dlg.locator('#ci-price').fill('1750');
  await dlg.locator('#ci-task').selectOption({ index: 1 });
  await dlg.locator('input[type="file"]').setInputFiles({ name: 'fatura-canli-test.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-1.4\n% canlı test faturası\n%%EOF') });
  await dlg.getByRole('button', { name: 'Kaydet' }).click();
  await page.locator('.pj-list li', { hasText: 'Güvenlik danışmanlığı (canlı test)' }).waitFor({ timeout: 20000 });
  const itemRow = await page.locator('.pj-list li', { hasText: 'Güvenlik danışmanlığı (canlı test)' }).innerText();
  const hasDoc = await page.locator('.pj-list li', { hasText: 'Güvenlik danışmanlığı (canlı test)' }).getByRole('button', { name: 'Belgeyi indir' }).count();
  step(/3\.500,00 ₺/.test(itemRow) && hasDoc === 1, 'Arayüzden belgeli maliyet kalemi eklendi (2 gün × 1.750 ₺)', itemRow.replace(/\s+/g, ' ').slice(0, 90));
  const stats = await page.locator('.pj-stats').first().innerText();
  const costApi = await page.evaluate(async (name) => {
    const token = sessionStorage.getItem('recorion_token') || localStorage.getItem('recorion_token');
    const h = { Authorization: `Bearer ${token}` };
    const p = (await (await fetch('/api/v1/projects/?scope=mine', { headers: h })).json()).find((x) => x.name === name);
    return (await (await fetch(`/api/v1/projects/${p.id}/costs`, { headers: h })).json());
  }, NAME);
  step(costApi.budget.amount === 15000 && costApi.totals.other === 3500 && Math.abs(costApi.totals.budget_variance - (15000 - costApi.totals.actual)) < 0.01,
    'Bütçe ve fark doğru', `${stats.replace(/\s+/g, ' ')}`);
  const [download] = await Promise.all([page.waitForEvent('download', { timeout: 30000 }), page.getByRole('button', { name: 'Excel', exact: true }).click()]);
  const xlsxPath = path.join(OUT, download.suggestedFilename());
  await download.saveAs(xlsxPath);
  const xlsx = fs.readFileSync(xlsxPath);
  step(xlsx.length > 3000 && xlsx.slice(0, 2).toString() === 'PK' && download.suggestedFilename().endsWith('.xlsx'), 'Excel maliyet raporu indirildi',
    `${download.suggestedFilename()} · ${Math.round(xlsx.length / 1024)} KB`);
  await shot(page, '07-maliyet');
  await page.getByRole('tab', { name: /Kapanış/ }).click();
  await page.getByText('Maliyet özeti').waitFor({ timeout: 15000 });
  step(true, 'Kapanış sekmesinde maliyet özeti var');
  await page.locator('#pj-close').fill('Canlı test kapanışı: maliyet raporu Excel olarak indirildi.');
  await page.getByRole('button', { name: 'Projeyi tamamla' }).click();
  await dialogOk(page);
  await page.locator('.ui-badge', { hasText: 'Tamamlandı' }).first().waitFor({ timeout: 20000 });
  await page.getByRole('tab', { name: /^Maliyet/ }).click();
  await page.locator('.pj-stat', { hasText: 'Gerçekleşen' }).first().waitFor({ timeout: 20000 });
  step(await page.getByRole('button', { name: 'Kalem ekle' }).count() === 0 && await page.locator('#cost-budget').isDisabled(),
    'Proje kapanınca maliyet kalemleri ve bütçe kilitlendi');

  // 7. Çalışma Alanı Kalite Kapısı gerçek durumu gösteriyor mu
  await page.getByRole('button', { name: 'Çalışma alanında aç' }).click();
  await page.getByText('Kalite Kapısı').first().waitFor({ timeout: 15000 });
  await page.waitForTimeout(2000);
  const gate = await page.locator('aside.pane').last().innerText();
  step(/Onaylandı/i.test(gate), 'Çalışma Alanı Kalite Kapısı gerçek durumu gösteriyor', gate.split('\n').slice(0, 3).join(' | '));
  const chat = await page.locator('main.pane').innerText();
  step(!/RECOrion Otonom Çalışma Alanı/.test(chat) && chat.length > 300, 'AI çıktısı görev sohbetine düştü', `${chat.length} karakter`);
  await shot(page, '06-calisma-alani');

  // 8.1 Silinemez mesaj kaydı: kullanıcı gibi dene (ekip dışı okuma, kapanmış projeye yazma, kaydı değiştirme)
  // Bilerek reddedilecek istekler tarayıcı dışından (aynı oturum belirteciyle) gider; konsolda sahte hata oluşmaz
  const api = async (pg, url, opts = {}) => {
    const token = await pg.evaluate(() => sessionStorage.getItem('recorion_token') || localStorage.getItem('recorion_token'));
    const r = await fetch(APP + url, { ...opts, headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } });
    let body = null;
    try { body = await r.json(); } catch { /* boş yanıt */ }
    return { status: r.status, body };
  };
  const proj = (await api(page, '/api/v1/projects/?scope=mine')).body.find((x) => x.name === NAME);
  const log = await api(page, `/api/v1/chat/project/${proj.id}`);
  const taskId = log.body.find((x) => x.task_id)?.task_id;
  step(log.status === 200 && log.body.length > 0 && log.body.every((x) => x.sender_name), 'Proje yazışma kaydı gönderen adlarıyla okunuyor',
    `${log.body.length} mesaj · ${[...new Set(log.body.map((x) => x.sender_name))].join(', ')}`);
  const send = await api(page, '/api/v1/chat/send', { method: 'POST', body: JSON.stringify({ task_id: taskId, content: 'Kapanıştan sonra bir not eklemek istiyorum.' }) });
  step(send.status === 409, 'Kapanmış projeye mesaj yazılamıyor (kayıt salt okunur)', `${send.status} ${send.body?.detail || ''}`);
  const fake = await api(page, '/api/v1/chat/send', { method: 'POST', body: JSON.stringify({ task_id: taskId, content: 'Ajan gibi yazayım', message_type: 'AGENT_TO_AGENT' }) });
  step(fake.status === 422, 'Kullanıcı AI-AI mesajı taklit edemiyor', String(fake.status));
  const o2 = await session('outsider');
  const peek = await api(o2.page, `/api/v1/chat/project/${proj.id}`);
  const peekTask = await api(o2.page, `/api/v1/chat/history/${taskId}`);
  step(peek.status === 403 && peekTask.status === 403, 'Ekip dışı kullanıcı yazışmaları API ile de okuyamıyor', `${peek.status}/${peekTask.status}`);
  await o2.ctx.close();
  const tamper = (sql) => {
    try {
      execFileSync('docker', ['exec', 'recorion_postgres', 'sh', '-c', `psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "${sql}"`],
        { encoding: 'utf8', stdio: 'pipe', env: { ...process.env, MSYS_NO_PATHCONV: '1' } });
      return 'değişti';
    } catch (err) { return /değiştirilemez/.test(String(err.stderr)) ? 'engellendi' : String(err.stderr).slice(0, 120); }
  };
  const upd = tamper(`UPDATE chat_messages SET content = 'oynandı' WHERE project_id = '${proj.id}'`);
  const del = tamper(`DELETE FROM chat_messages WHERE project_id = '${proj.id}'`);
  const after = await api(page, `/api/v1/chat/project/${proj.id}`);
  step(upd === 'engellendi' && del === 'engellendi' && after.body.length === log.body.length && !after.body.some((x) => x.content === 'oynandı'),
    'Mesaj kaydı veritabanında bile değiştirilemiyor/silinemiyor', `güncelleme: ${upd}, silme: ${del}, mesaj: ${after.body.length}`);

  // 9.1 Şirket panosu: şirket yöneticisi girişte genel bakışı görür; bu koşunun projesi panoya yansır
  const adm = await session('admin');
  await adm.page.getByRole('heading', { name: 'Günlük kredi tüketimi' }).waitFor({ timeout: 30000 });
  const dash = await adm.page.locator('.dash-root').innerText();
  const completed = Number((dash.match(/TAMAMLANAN\s*\n\s*(\d+)/i) || [])[1] || 0);
  const budgetRow = adm.page.locator('.viz-bars li', { hasText: NAME });
  const budgetText = (await budgetRow.count()) ? await budgetRow.first().innerText() : '';
  step(completed >= 1 && /mimo|deepseek/.test(dash) && /3\.500|15\.000/.test(budgetText + dash),
    'Şirket panosu proje durumlarını, LLM kırılımını ve bu koşunun bütçesini gösteriyor',
    `tamamlanan proje ${completed} · ${budgetText.replace(/\s+/g, ' ').slice(0, 70) || 'proje satırı yok'}`);
  await adm.page.getByRole('tab', { name: '7 gün' }).click();
  await adm.page.waitForTimeout(1500);
  const week = (await adm.page.locator('.viz-root svg g.viz-hit').count());
  const deptSel = adm.page.locator('select[aria-label="Departman"]');
  let deptNote = 'departman yok';
  if (await deptSel.count()) {
    await deptSel.selectOption({ index: 1 });
    await adm.page.waitForTimeout(1500);
    deptNote = `departman: ${await deptSel.evaluate((x) => x.selectedOptions[0]?.text)}`;
  }
  // Departman seçilince şirket düzeyindeki kredi kartı kalkar (kredi hakkı şirkete aittir)
  const creditCard = await adm.page.getByRole('heading', { name: 'Kredi', exact: true }).count();
  step(week > 0 && week % 7 === 0 && (deptNote === 'departman yok' || creditCard === 0),
    'Pano filtreleri (dönem, departman) tüm görünümü yeniliyor', `7 günlük seri: ${week} sütun · ${deptNote} · kredi kartı: ${creditCard ? 'var' : 'yok'}`);
  // 9.2 AI personel karnesi ve tahmini tasarruf: bu koşuda çalışan AI personel karnede; ROI ya hesaplanır ya KVKK gerekçesi yazar
  await adm.page.getByRole('tab', { name: '30 gün' }).click();
  if (await deptSel.count()) await deptSel.selectOption({ index: 0 });
  await adm.page.getByRole('heading', { name: 'AI personel karnesi' }).waitFor({ timeout: 20000 });
  await adm.page.waitForTimeout(1500);
  const karne = await adm.page.locator('.dash-table tbody').innerText();
  const roiText = await adm.page.locator('.ui-card', { has: adm.page.getByRole('heading', { name: 'Tahmini tasarruf (ROI)' }) }).innerText();
  const rows = karne.split('\n').filter((l) => /^(Deniz|Kaan)$/.test(l.trim()));
  step(rows.length >= 2 && /%\d+/.test(karne) && (/₺/.test(roiText) || /KVKK/.test(roiText)),
    'AI personel karnesi ve tahmini tasarruf gösteriliyor', `${rows.join(', ')} · ROI: ${/KVKK/.test(roiText) ? 'KVKK gerekçesiyle gizli (ücret tanımlı kişi < 3)' : 'hesaplandı'}`);
  await shot(adm.page, '08-sirket-panosu');
  await adm.ctx.close();

  // 9.3 Departman müdürü: Work Space'te Pano sekmesi, yalnızca kendi departmanı, parasal bilgi yok; sıradan üye Pano'yu görmez
  const dm = await session('deptmgr');
  await dm.page.getByRole('button', { name: 'Pano', exact: true }).click();
  await dm.page.getByRole('heading', { name: 'Ekip iş durumu' }).waitFor({ timeout: 30000 });
  await dm.page.waitForTimeout(1500);
  const dmText = await dm.page.locator('.dash-root').innerText();
  const deptOk = /Departman: Bilgi Teknolojileri/.test(dmText) && !(await dm.page.locator('select[aria-label="Departman"]').count());
  const noMoney = !/Maliyet dağılımı|Tahmini tasarruf|bütçe ve gerçekleşen|Günlük token maliyeti/.test(dmText);
  // Departmanın AI personeli karnede; insan personel bölümü var (canlı testte adımlar AI'a atandığı için boş olabilir)
  const team = /Ekip iş durumu/.test(dmText) && /Deniz/.test(dmText) && /Kaan/.test(dmText);
  const otherDept = await api(dm.page, `/api/v1/company/${cfg.tenant_id}/dashboard?department_id=${'0'.repeat(8)}-0000-0000-0000-${'0'.repeat(12)}`);
  step(deptOk && noMoney && team && otherDept.status === 403, 'Departman müdürü yalnızca kendi departmanını görüyor; parasal bilgi yok',
    `departman kilidi: ${deptOk ? 'var' : 'yok'} · parasal kart: ${noMoney ? 'yok' : 'VAR'} · ekip: ${team ? 'görünüyor' : 'yok'} · başka departman: ${otherDept.status}`);
  await shot(dm.page, '09-departman-panosu');
  await dm.ctx.close();
  const mb = await session('member');
  const memberPano = await mb.page.getByRole('button', { name: 'Pano', exact: true }).count();
  const memberApi = await api(mb.page, `/api/v1/company/${cfg.tenant_id}/dashboard`);
  step(memberPano === 0 && memberApi.status === 403, 'Sıradan ekip üyesi panoyu göremiyor', `sekme: ${memberPano} · API: ${memberApi.status}`);
  await mb.ctx.close();

  // 9.4 Süper Admin panosu: gerçek sistem durumu, LLM sağlığı; müşteri içeriği (proje adı) görünmez (KVKK)
  const sa = await session('super');
  await sa.page.getByRole('heading', { name: 'Model sağlığı' }).waitFor({ timeout: 40000 });
  await sa.page.getByText(/^(Tüm sistemler çalışıyor|Bazı bileşenlerde sorun var|Çekirdek bileşen erişilemiyor)$/).first().waitFor({ timeout: 20000 });
  const healthCard = sa.page.locator('.ui-card', { has: sa.page.getByRole('heading', { name: 'Altyapı ve entegrasyon durumu' }) });
  const services = await healthCard.locator('.pj-list li').count();
  const states = (await healthCard.locator('.ui-badge').allTextContents()).map((x) => x.replace(/^[●▲✕○]\s*/, ''));
  const modelRows = await sa.page.locator('.dash-table tbody tr').count();
  const saText = await sa.page.locator('main, .super-admin-main, body').first().innerText();
  step(services === 8 && modelRows > 0 && !saText.includes(NAME),
    'Süper Admin panosu gerçek sistem durumunu ve LLM sağlığını gösteriyor; müşteri içeriği yok',
    `${services} bileşen (${[...new Set(states)].join(', ')}) · ${modelRows} model · proje adı görünüyor: ${saText.includes(NAME) ? 'EVET' : 'hayır'}`);
  // 10.1 KVKK: Süper Admin müşterinin entegrasyon bağlantılarını göremez
  const saConns = await api(sa.page, `/api/v1/company/${cfg.tenant_id}/integrations`);
  step(saConns.status === 403, 'Süper Admin müşterinin entegrasyon bağlantılarını göremiyor (KVKK)', String(saConns.status));
  await shot(sa.page, '10-super-admin-pano');
  await sa.ctx.close();

  // 10.1 Entegrasyonlar: şirket yöneticisi yanlış token'la Telegram bağlantısı ekler, dener, AI personele yetki verir
  const ig = await session('admin');
  await ig.page.getByRole('button', { name: 'Entegrasyonlar' }).click();
  await ig.page.getByRole('button', { name: 'Bağlantı ekle' }).click();
  const igName = `Telegram ${NAME.slice(-5)}`;
  const badToken = `999999:YANLIS-${Date.now()}`;
  const igDlg = ig.page.getByRole('dialog');
  await pickCard(igDlg, 'Telegram');
  await igDlg.locator('#ig-name').fill(igName);
  await igDlg.locator('#ig-s-bot_token').fill(badToken);
  await igDlg.getByRole('button', { name: 'Kaydet' }).click();
  const igRow = ig.page.locator('.pj-list li', { hasText: igName });
  await igRow.waitFor({ timeout: 15000 });
  await igRow.getByRole('button', { name: 'Dene' }).click();
  await igRow.getByText(/Son deneme/).waitFor({ timeout: 30000 });
  const igRowText = await igRow.innerText();
  await igRow.getByRole('button', { name: 'Araçlar ve yetkiler' }).click();
  const grantBox = ig.page.getByRole('checkbox', { name: 'Deniz: send_message' });
  await grantBox.waitFor({ timeout: 15000 });
  await grantBox.check();
  await ig.page.getByRole('button', { name: 'Yetkileri kaydet' }).click();
  await ig.page.waitForTimeout(1500);
  const igPage = await ig.page.content();
  const conns = await api(ig.page, `/api/v1/company/${cfg.tenant_id}/integrations`);
  const igConn = (conns.body || []).find((c) => c.name === igName);
  const grants = igConn ? await api(ig.page, `/api/v1/company/${cfg.tenant_id}/integrations/${igConn.id}/grants`) : { body: [] };
  step(/başarısız|hata|Unauthorized|Not Found/i.test(igRowText) && !igPage.includes(badToken) && igConn?.secrets_set?.bot_token && grants.body.length === 1,
    'Entegrasyon: bağlantı eklendi, yanlış token anlaşılır hatayla reddedildi, AI personele yetki verildi; token hiçbir yerde görünmüyor',
    `${igRowText.split('\n').find((l) => /Son deneme/.test(l)) || ''} · yetki: ${grants.body.map((g) => g.tool).join(', ')} · token sayfada: ${igPage.includes(badToken) ? 'EVET' : 'yok'}`);
  await shot(ig.page, '11-entegrasyonlar');
  await ig.ctx.close();

  // 10.2 Araç kullanımı: yönetici yeni bir işte Deniz'den Telegram'a duyuru göndermesini ister; yazma işlemi
  // gönderilmeden yöneticinin onayına düşer; yönetici Onaylarım'dan gerekçeyle reddeder, kayıt değişmez
  const tm = await session('manager');
  const tProj = await api(tm.page, '/api/v1/projects/', { method: 'POST',
    body: JSON.stringify({ tenant_id: cfg.tenant_id, name: `${NAME} duyuru`, description: 'Araç kullanımı canlı testi' }) });
  const deniz = (await api(tm.page, '/api/v1/actors/')).body.find((a) => a.display_name === 'Deniz');
  const tTask = await api(tm.page, `/api/v1/projects/${tProj.body.id}/tasks`, { method: 'POST',
    body: JSON.stringify({ title: 'Ekibe duyuru', assignee_actor_id: deniz.id }) });
  const asks = ['Telegram aracını kullanarak 12345 numaralı sohbete "Toplantı yarın saat 10:00" mesajını gönderir misin?',
    'Lütfen send_message aracını çağır: chat_id 12345, metin "Toplantı yarın saat 10:00".'];
  let pending = [];
  let toolReply = '';
  for (const content of asks) {
    const r = await api(tm.page, '/api/v1/chat/send', { method: 'POST', body: JSON.stringify({ task_id: tTask.body.id, content }) });
    toolReply = r.body?.assistant_message?.content || JSON.stringify(r.body || r.status).slice(0, 200);
    pending = ((await api(tm.page, '/api/v1/me/tool-approvals')).body || []).filter((c) => c.task_id === tTask.body.id);
    if (pending.length) break;
  }
  step(pending.length === 1 && pending[0].tool === 'send_message' && pending[0].actor_name === 'Deniz',
    'AI personel yazma aracını kullanmak istedi; işlem gönderilmeden yöneticinin onayına düştü',
    `${pending.map((c) => `${c.tool} ${JSON.stringify(c.arguments)}`).join('; ') || 'araç çağrılmadı'} · yanıt: ${toolReply.replace(/\s+/g, ' ').slice(0, 90)}`);
  await tm.page.getByRole('button', { name: /Onaylarım/ }).click();
  const toolRow = tm.page.locator('[aria-label="Onay bekleyen araç işlemleri"] li', { hasText: 'send_message' });
  let decided = null;
  if (pending.length) {
    await toolRow.first().waitFor({ timeout: 30000 });
    await shot(tm.page, '12-arac-onayi');
    await toolRow.first().getByRole('button', { name: 'Reddet' }).click();
    await dialogOk(tm.page, 'Duyuruyu ben göndereceğim');
    await toolRow.first().waitFor({ state: 'detached', timeout: 20000 });
    const adm2 = await session('admin');
    decided = ((await api(adm2.page, `/api/v1/company/${cfg.tenant_id}/tool-calls`)).body || []).find((c) => c.id === pending[0].id);
    await adm2.ctx.close();
  }
  step(decided?.status === 'REJECTED' && /ben göndereceğim/.test(decided?.decision_note || '') && !decided?.result,
    'Yönetici araç işlemini Onaylarım ekranından gerekçeyle reddetti; mesaj gönderilmedi ve kayıt günlükte duruyor',
    decided ? `${decided.status} · not: ${decided.decision_note || '-'}` : 'karar yok');

  // 10.3 Odoo (gerçek RECDx Odoo'su, YALNIZCA OKUMA — kullanıcı kararı: gerçek Odoo'ya test kaydı yazılmaz):
  // şirket yöneticisi bağlantıyı ekrandan ekler, dener; yazma araçları hiç görünmez; Kaan'a okuma yetkisi verir
  const odooEnv = Object.fromEntries(['ODOO_URL', 'ODOO_DB', 'ODOO_USER', 'ODOO_PASSWORD'].map((k) => [k,
    execFileSync('docker', ['exec', 'recorion_backend', 'printenv', k], { encoding: 'utf8' }).trim()]));  // bellekte; yazdırılmaz
  const od = await session('admin');
  await od.page.getByRole('button', { name: 'Entegrasyonlar' }).click();
  await od.page.getByRole('button', { name: 'Bağlantı ekle' }).click();
  const odName = `Odoo ${NAME.slice(-5)}`;
  const odDlg = od.page.getByRole('dialog');
  await pickCard(odDlg, 'Odoo');
  await odDlg.locator('#ig-name').fill(odName);
  await odDlg.locator('#ig-c-url').fill(odooEnv.ODOO_URL);
  await odDlg.locator('#ig-c-db').fill(odooEnv.ODOO_DB);
  await odDlg.locator('#ig-c-username').fill(odooEnv.ODOO_USER);
  await odDlg.locator('#ig-c-allowed_models').fill('project.project, project.task');
  await odDlg.locator('#ig-c-access').selectOption('READ_ONLY');
  await odDlg.locator('#ig-s-api_key').fill(odooEnv.ODOO_PASSWORD);
  await odDlg.getByRole('button', { name: 'Kaydet' }).click();
  const odRow = od.page.locator('.pj-list li', { hasText: odName });
  await odRow.waitFor({ timeout: 15000 });
  await odRow.getByRole('button', { name: 'Dene' }).click();
  await odRow.getByText(/Son deneme/).waitFor({ timeout: 40000 });
  const odRowText = await odRow.innerText();
  await odRow.getByRole('button', { name: 'Araçlar ve yetkiler' }).click();
  await od.page.getByRole('checkbox', { name: 'Kaan: count_records' }).waitFor({ timeout: 20000 });
  const writeBoxes = await od.page.getByRole('checkbox', { name: /Kaan: (create_record|update_record)/ }).count();
  await od.page.getByRole('checkbox', { name: 'Kaan: count_records' }).check();
  await od.page.getByRole('checkbox', { name: 'Kaan: search_records' }).check();
  await od.page.getByRole('button', { name: 'Yetkileri kaydet' }).click();
  await od.page.waitForTimeout(1500);
  const odPage = await od.page.content();
  step(/Son deneme[^\n]*başarılı/.test(odRowText) && /Yalnızca okuma/.test(odRowText) && writeBoxes === 0 && !odPage.includes(odooEnv.ODOO_PASSWORD),
    'Odoo yalnızca okuma bağlandı ve denendi; yazma araçları hiç sunulmuyor; anahtar sayfada yok',
    `${odRowText.split('\n').find((l) => /Son deneme/.test(l)) || odRowText.slice(0, 80)} · yazma kutusu: ${writeBoxes}`);
  await shot(od.page, '13-odoo-salt-okunur');

  // Proje yöneticisi Kaan'a sohbette Odoo'dan bilgi sorar: okuma aracı anında çalışır, sonuç yanıta yansır
  const kaan = (await api(tm.page, '/api/v1/actors/')).body.find((a) => a.display_name === 'Kaan');
  const kTask = await api(tm.page, `/api/v1/projects/${tProj.body.id}/tasks`, { method: 'POST',
    body: JSON.stringify({ title: 'Odoo durum özeti', assignee_actor_id: kaan.id }) });
  let odCall = null;
  let odReply = '';
  for (const content of ['Odoo\'da 47 numaralı projede (project_id = 47) toplam kaç görev var? Odoo aracını kullanarak bak.',
    'Lütfen count_records aracını model project.task, domain [["project_id", "=", 47]] ile çağır ve sonucu söyle.']) {
    const r = await api(tm.page, '/api/v1/chat/send', { method: 'POST', body: JSON.stringify({ task_id: kTask.body.id, content }) });
    odReply = r.body?.assistant_message?.content || JSON.stringify(r.body || r.status).slice(0, 200);
    const done = ((await api(od.page, `/api/v1/company/${cfg.tenant_id}/tool-calls`)).body || [])
      .filter((c) => c.task_id === kTask.body.id && c.status === 'EXECUTED');
    odCall = done.find((c) => c.tool === 'count_records') || done[0];
    if (odCall) break;
  }
  const odCount = odCall?.result?.count ?? (odCall?.result?.records || []).length;
  step(Boolean(odCall) && odCall.kind === 'READ' && new RegExp(`(^|\\D)${odCount}(\\D|$)`).test(odReply),
    'AI personel Odoo okuma aracını sohbette kullandı; gerçek veri yanıta yansıdı (onay beklemeden)',
    `${odCall ? `${odCall.tool} → ${odCount}` : 'araç çağrılmadı'} · yanıt: ${odReply.replace(/\s+/g, ' ').slice(0, 90)}`);

  // Trello: yönetici yanlış token girer; anlaşılır hata, token sayfada görünmez
  await od.page.getByRole('button', { name: 'Bağlantı ekle' }).click();
  const trName = `Trello ${NAME.slice(-5)}`;
  const trToken = `YANLIS-TRELLO-${Date.now()}`;
  const trDlg = od.page.getByRole('dialog');
  await pickCard(trDlg, 'Trello');
  await trDlg.locator('#ig-name').fill(trName);
  await trDlg.locator('#ig-s-api_key').fill('0123456789abcdef0123456789abcdef');
  await trDlg.locator('#ig-s-token').fill(trToken);
  await trDlg.getByRole('button', { name: 'Kaydet' }).click();
  const trRow = od.page.locator('.pj-list li', { hasText: trName });
  await trRow.waitFor({ timeout: 15000 });
  await trRow.getByRole('button', { name: 'Dene' }).click();
  await trRow.getByText(/Son deneme/).waitFor({ timeout: 30000 });
  const trText = await trRow.innerText();
  step(/Trello hata|başarısız|401|invalid/i.test(trText) && !(await od.page.content()).includes(trToken),
    'Trello: yanlış anahtar anlaşılır hatayla reddedildi; token sayfada görünmüyor',
    trText.split('\n').find((l) => /Son deneme/.test(l)) || trText.slice(0, 90));

  // 10.4 Dış MCP sunucusu (gerçek, herkese açık DeepWiki MCP; kimlik gerektirmez): yönetici ekrandan bağlar, işaretsiz bir
  // aracı "okuma" diye tanımlar, dener, Kaan'a yetki verir; Kaan sohbette aracı kullanır
  const addConn = async (card, name, fill) => {
    await od.page.getByRole('button', { name: 'Bağlantı ekle' }).click();
    const dlg = od.page.getByRole('dialog');
    await pickCard(dlg, card);
    await dlg.locator('#ig-name').fill(name);
    await fill(dlg);
    await dlg.getByRole('button', { name: 'Kaydet' }).click();
    const row = od.page.locator('.pj-list li', { hasText: name });
    await row.waitFor({ timeout: 15000 });
    await row.getByRole('button', { name: 'Dene' }).click();
    await row.getByText(/Son deneme/).waitFor({ timeout: 60000 });
    return row;
  };
  const mcpName = `DeepWiki ${NAME.slice(-5)}`;
  const mcpRow = await addConn('Diğer MCP sunucusu', mcpName, async (dlg) => {
    await dlg.locator('#ig-c-url').fill('https://mcp.deepwiki.com/mcp');
    await dlg.locator('#ig-c-read_tools').fill('read_wiki_structure');
  });
  const mcpRowText = await mcpRow.innerText();
  await mcpRow.getByRole('button', { name: 'Araçlar ve yetkiler' }).click();
  const mcpBox = od.page.getByRole('checkbox', { name: 'Kaan: read_wiki_structure' });
  await mcpBox.waitFor({ timeout: 30000 });
  const mcpTools = await od.page.getByRole('checkbox', { name: /^Kaan: (?!tüm)/ }).count();
  await mcpBox.check();
  await od.page.getByRole('button', { name: 'Yetkileri kaydet' }).click();
  await od.page.waitForTimeout(1500);
  step(/başarılı/.test(mcpRowText) && mcpTools >= 2, 'Dış MCP sunucusu bağlandı; araçları otomatik keşfedildi ve AI personele yetkiyle açıldı',
    `${mcpRowText.split('\n').find((l) => /Son deneme/.test(l)) || mcpRowText.slice(0, 80)} · keşfedilen araç: ${mcpTools}`);
  await shot(od.page, '14-mcp-sunucusu');

  const mTask = await api(tm.page, `/api/v1/projects/${tProj.body.id}/tasks`, { method: 'POST',
    body: JSON.stringify({ title: 'Kütüphane araştırması', assignee_actor_id: kaan.id }) });
  let mCall = null;
  let mReply = '';
  for (const content of ['encode/httpx GitHub deposunun dokümantasyonunda hangi ana başlıklar var? DeepWiki aracıyla bakıp listele.',
    'Lütfen read_wiki_structure aracını repoName "encode/httpx" ile çağır ve başlıkları yaz.']) {
    const r = await api(tm.page, '/api/v1/chat/send', { method: 'POST', body: JSON.stringify({ task_id: mTask.body.id, content }) });
    mReply = r.body?.assistant_message?.content || JSON.stringify(r.body || r.status).slice(0, 200);
    mCall = ((await api(od.page, `/api/v1/company/${cfg.tenant_id}/tool-calls`)).body || [])
      .find((c) => c.task_id === mTask.body.id && c.tool === 'read_wiki_structure' && c.status === 'EXECUTED');
    if (mCall) break;
  }
  step(Boolean(mCall) && /Overview|Genel Bakış|Installation|Kurulum/i.test(mReply),
    'AI personel dış MCP aracını sohbette kullandı; sunucudan gelen gerçek bilgi yanıta yansıdı',
    `${mCall ? `${mCall.tool} ${mCall.latency_ms} ms` : 'araç çağrılmadı'} · yanıt: ${mReply.replace(/\s+/g, ' ').slice(0, 90)}`);

  // Yönetici (yanlışlıkla veya kötü niyetle) iç ağdaki bir adresi MCP sunucusu diye girer: bağlanma reddedilir (SSRF koruması)
  const ssrfRow = await addConn('Diğer MCP sunucusu', `İç ağ ${NAME.slice(-5)}`, async (dlg) => {
    await dlg.locator('#ig-c-url').fill('http://backend:8000/api/v1/health');
  });
  const ssrfText = await ssrfRow.innerText();
  step(/özel\/yerel ağ/.test(ssrfText), 'İç ağdaki bir adres MCP sunucusu olarak bağlanamıyor (SSRF koruması)',
    ssrfText.split('\n').find((l) => /Son deneme/.test(l)) || ssrfText.slice(0, 90));

  // 10.5 Edge Connector: şirket sunucusundaki Logo'ya (sahte Logo veritabanı) ajanla bağlanma. Yönetici bağlantıyı ekler,
  // ajan yokken dener (anlaşılır uyarı), ajan anahtarını alır; "şirket sunucusunda" ajan başlatılır (backend konteyneri içinde,
  // yalnızca dışa bağlanır); ekran çevrimiçi gösterir; Kaan'a yetki verilir; proje yöneticisi sohbette Logo'dan cari bakiye sorar
  const edName = `Logo ${NAME.slice(-5)}`;
  const edRow = await addConn('Logo (Tiger, GO', edName, async () => {});
  const edBefore = await edRow.innerText();
  await edRow.getByRole('button', { name: 'Ajan anahtarı' }).click();
  const tokenBox = od.page.getByLabel('Ajan anahtarı', { exact: true });
  await tokenBox.waitFor({ timeout: 15000 });
  const edToken = (await tokenBox.innerText()).trim();
  await od.page.getByRole('button', { name: 'Kaydettim, kapat' }).click();
  const edDir = '/tmp/edge_e2e';
  execFileSync('docker', ['exec', 'recorion_backend', 'sh', '-c', `rm -rf ${edDir} && mkdir -p ${edDir} && python /edge_agent/fake_logo.py ${edDir}/sahte_logo.db && `
    + `printf '%s' '{"hostname":"LOGO-SUNUCU","database":{"driver":"sqlite","path":"${edDir}/sahte_logo.db"},"templates_file":"/edge_agent/templates.example.json","allow_write":false,"audit_log":"${edDir}/audit.log"}' > ${edDir}/cfg.json`],
  { encoding: 'utf8', env: { ...process.env, MSYS_NO_PATHCONV: '1' } });
  const edAgent = spawn('docker', ['exec', '-e', 'RECORION_URL=http://localhost:8000', '-e', `RECORION_EDGE_TOKEN=${edToken}`, 'recorion_backend',
    'timeout', '900', 'python', '/edge_agent/recorion_edge.py', '--config', `${edDir}/cfg.json`], { stdio: 'ignore', env: { ...process.env, MSYS_NO_PATHCONV: '1' } });
  await od.page.waitForTimeout(4000);
  await edRow.getByRole('button', { name: 'Dene' }).click();
  await edRow.getByText(/Ajan çevrimiçi ·/).waitFor({ timeout: 30000 });
  const edAfter = await edRow.innerText();
  await edRow.getByRole('button', { name: 'Araçlar ve yetkiler' }).click();
  await od.page.getByRole('checkbox', { name: 'Kaan: cari_bakiye' }).waitFor({ timeout: 20000 });
  const edWrite = await od.page.getByRole('checkbox', { name: 'Kaan: cari_not_ekle' }).count();
  await od.page.getByRole('checkbox', { name: 'Kaan: cari_bakiye' }).check();
  await od.page.getByRole('checkbox', { name: 'Kaan: cari_ara' }).check();
  await od.page.getByRole('button', { name: 'Yetkileri kaydet' }).click();
  await od.page.waitForTimeout(1500);
  step(/henüz bağlanmadı/.test(edBefore) && /4 izinli şablon/.test(edAfter) && edWrite === 0 && edToken.startsWith('rxe_')
      && !(await od.page.content()).includes(edToken),
    'Edge Connector: ajan yokken anlaşılır uyarı; anahtar bir kez gösterildi; ajan bağlandı, 4 okuma şablonu (yazma kapalı) görünüyor',
    `${edAfter.split('\n').find((l) => /Ajan çevrimiçi ·/.test(l)) || ''} · yazma kutusu: ${edWrite}`);
  await shot(od.page, '15-edge-connector');

  const eTask = await api(tm.page, `/api/v1/projects/${tProj.body.id}/tasks`, { method: 'POST',
    body: JSON.stringify({ title: 'Tahsilat ön kontrolü', assignee_actor_id: kaan.id }) });
  let eCall = null;
  let eReply = '';
  for (const content of ['Logo\'da 120.01.001 kodlu cari (ABC Makine) şu an ne kadar borçlu? Logo aracından bakiyeye bakar mısın?',
    'Lütfen cari_bakiye aracını cari_kodu "120.01.001" ile çağır ve bakiyeyi TL olarak yaz.']) {
    const r = await api(tm.page, '/api/v1/chat/send', { method: 'POST', body: JSON.stringify({ task_id: eTask.body.id, content }) });
    eReply = r.body?.assistant_message?.content || JSON.stringify(r.body || r.status).slice(0, 200);
    eCall = ((await api(od.page, `/api/v1/company/${cfg.tenant_id}/tool-calls`)).body || [])
      .find((c) => c.task_id === eTask.body.id && c.tool === 'cari_bakiye' && c.status === 'EXECUTED');
    if (eCall) break;
  }
  step(Boolean(eCall) && /103[.,\s]?500/.test(eReply),
    'AI personel şirket sunucusundaki Logo\'dan Edge ajanıyla cari bakiyeyi okudu; doğru tutar yanıta yansıdı',
    `${eCall ? `${eCall.tool} ${eCall.latency_ms} ms → ${JSON.stringify(eCall.result?.rows)}` : 'araç çağrılmadı'} · yanıt: ${eReply.replace(/\s+/g, ' ').slice(0, 80)}`);

  // Yönetici bağlantıyı devre dışı bırakır: ajan bir sonraki yoklamada reddedilir ve kendiliğinden durur
  await edRow.getByRole('button', { name: 'Devre dışı bırak' }).click();
  await dialogOk(od.page);
  const edStopped = await new Promise((resolve) => {
    const t = setTimeout(() => resolve(false), 45000);
    edAgent.on('exit', () => { clearTimeout(t); resolve(true); });
  });
  if (!edStopped) edAgent.kill();
  step(edStopped, 'Edge bağlantısı devre dışı bırakılınca şirket sunucusundaki ajan bağlanamadı ve durdu', edStopped ? 'ajan durdu' : 'ajan 45 sn içinde durmadı');

  // Temizlik: gerçek Odoo anahtarı test kaydında kalmaz (kasadaki değer değiştirilir, bağlantı devre dışı)
  const odConn = ((await api(od.page, `/api/v1/company/${cfg.tenant_id}/integrations`)).body || []).find((c) => c.name === odName);
  if (odConn) {
    await api(od.page, `/api/v1/company/${cfg.tenant_id}/integrations/${odConn.id}`, { method: 'PUT',
      body: JSON.stringify({ status: 'DISABLED', secrets: { api_key: 'silindi' } }) });
  }
  await od.ctx.close();
  await api(tm.page, `/api/v1/projects/${tProj.body.id}/status`, { method: 'POST', body: JSON.stringify({ action: 'cancel' }) });
  await tm.ctx.close();

  // 11.1 Proje şablonları: proje yöneticisi RECDx'in hazır "Müşteri şikâyeti vakası" şablonundan Case açar (plan taslak gelir),
  // sonra bunu şirket şablonu olarak kaydeder; şablon şirkette görünür, RECDx Süper Admin'e görünmez (KVKK)
  const tp = await session('manager');
  await tp.page.getByRole('button', { name: 'Şablondan oluştur' }).click();
  const gallery = tp.page.getByRole('dialog');
  await gallery.getByRole('button', { name: 'RECDx hazır' }).click();
  await gallery.getByRole('listitem').filter({ hasText: 'Müşteri şikâyeti vakası' }).click();
  const tplProject = `${NAME} şikâyet`;
  await gallery.locator('#tpl-name').fill(tplProject);
  await gallery.getByRole('list', { name: 'Şablon adımları' }).locator('li').first().waitFor({ timeout: 15000 });
  const tplSteps = await gallery.getByRole('list', { name: 'Şablon adımları' }).locator('li').count();
  await gallery.getByRole('button', { name: 'Projeyi oluştur' }).click();
  await tp.page.getByRole('heading', { name: tplProject }).waitFor({ timeout: 20000 });
  await tp.page.locator('.pj-step').first().waitFor({ timeout: 20000 });
  const tplPlanSteps = await tp.page.locator('.pj-step').count();
  step(tplSteps === 4 && tplPlanSteps === 4, 'Şablondan Case açıldı; şablonun 4 adımı plana taslak olarak geldi (Beyin AI çağrısı olmadan)',
    `galeride ${tplSteps} adım, planda ${tplPlanSteps} adım`);
  await tp.page.getByRole('button', { name: 'Şablon olarak kaydet' }).click();
  const tplName = `Şikâyet akışı ${NAME.slice(-5)}`;
  const saveDlg = tp.page.getByRole('dialog');
  await saveDlg.locator('#st-name').fill(tplName);
  await saveDlg.locator('#st-cat').fill('Müşteri Hizmetleri');
  await saveDlg.getByRole('button', { name: 'Kaydet' }).click();
  await saveDlg.waitFor({ state: 'detached', timeout: 15000 });
  const myTpl = ((await api(tp.page, '/api/v1/project-templates')).body || []).find((t) => t.name === tplName);
  const sa2 = await session('super');
  const saSees = ((await api(sa2.page, '/api/v1/project-templates')).body || []).some((t) => t.name === tplName);
  const saDirect = myTpl ? (await api(sa2.page, `/api/v1/project-templates/${myTpl.id}`)).status : 0;
  await sa2.ctx.close();
  step(myTpl?.scope === 'COMPANY' && myTpl.step_count === 4 && !saSees && saDirect === 404,
    'Proje şirket şablonu olarak kaydedildi; şirkette görünüyor, RECDx Süper Admin göremiyor (KVKK)',
    `${myTpl ? `${myTpl.name} · ${myTpl.step_count} adım` : 'şablon yok'} · Süper Admin listede: ${saSees ? 'EVET' : 'hayır'}, doğrudan: ${saDirect}`);
  await shot(tp.page, '16-sablondan-proje');
  // Temizlik: test şablonu arşivlenir, test Case'i iptal edilir (test şirketinde birikmesin)
  if (myTpl) await api(tp.page, `/api/v1/project-templates/${myTpl.id}`, { method: 'PUT', body: JSON.stringify({ status: 'ARCHIVED' }) });
  const tplProj = ((await api(tp.page, '/api/v1/projects/?scope=mine')).body || []).find((x) => x.name === tplProject);
  if (tplProj) await api(tp.page, `/api/v1/projects/${tplProj.id}/status`, { method: 'POST', body: JSON.stringify({ action: 'cancel' }) });
  await tp.ctx.close();

  // 11.2 Mevzuat paketleri: canlı ortamda YAYIMLANMAZ (yayın tüm müşterilere açılır; uzman kontrolü şart — kullanıcı kararı).
  // Süper Admin taslakları "uzman kontrolü bekliyor" görür; uzman beyanı ve adı olmadan Yayımla düğmesi kilitli kalır, vazgeçer.
  // Şirket yöneticisi taslakları göremez.
  const rg = await session('super');
  await rg.page.goto(`${APP}/#/super-admin/regulations`);
  const rgList = rg.page.getByRole('list', { name: 'Mevzuat paketleri (yönetim)' });
  await rgList.waitFor({ timeout: 30000 });
  const sgkRow = rgList.locator('li', { hasText: 'SGK' });
  const sgkText = await sgkRow.innerText();
  const draftOnly = /Taslak · uzman kontrolü bekliyor/.test(sgkText);
  await sgkRow.getByRole('button', { name: 'Uzman kontrolüyle yayımla' }).click();
  const pubDlg = rg.page.getByRole('dialog');
  const lockedEmpty = await pubDlg.getByRole('button', { name: 'Yayımla' }).isDisabled();
  await pubDlg.locator('#rg-reviewer').fill('Deneme Uzman');
  const lockedNoConfirm = await pubDlg.getByRole('button', { name: 'Yayımla' }).isDisabled();
  await shot(rg.page, '17-mevzuat-yayin-kilidi');
  await pubDlg.getByRole('button', { name: 'Vazgeç' }).click();
  const rgAfter = ((await api(rg.page, '/api/v1/system/regulation-packs')).body || []).find((p) => p.code === 'sgk');
  await rg.ctx.close();
  const rgAdm = await session('admin');
  const companyPacks = (await api(rgAdm.page, `/api/v1/company/${cfg.tenant_id}/regulation-packs`)).body || [];
  const draftLeak = rgAfter && !rgAfter.published ? companyPacks.some((p) => p.code === 'sgk') : false;
  await rgAdm.ctx.close();
  step((draftOnly ? lockedEmpty && lockedNoConfirm && !rgAfter?.published : true) && !draftLeak,
    'Mevzuat paketi uzman kontrolü olmadan yayımlanamıyor; taslak şirkete görünmüyor',
    `${sgkText.split('\n')[0].slice(0, 70)} · boşken kilitli: ${lockedEmpty} · beyansız kilitli: ${lockedNoConfirm} · şirkette taslak: ${draftLeak ? 'EVET' : 'yok'}`);

  // 11.3 Toplantıdan proje: proje yöneticisi önce tarayıcıda kısa bir kayıt dener (sahte mikrofon yalnızca bip sesi verir →
  // anlaşılır konuşma yok uyarısı), sonra toplantı kaydını dosya olarak yükler (EVREN voxcpm2 ile üretilmiş sentetik Türkçe
  // toplantı); gerçek qwen3-asr yazıya çevirir, Beyin AI taslak çıkarır; yönetici düzeltip projeyi oluşturur, plan taslak gelir
  const mtFile = path.join(OUT, 'toplanti.mp3');
  execFileSync('docker', ['exec', '-w', '/app', 'recorion_backend', 'python', 'scripts/live_test_meeting_audio.py', '/tmp/e2e_toplanti.mp3'],
    { encoding: 'utf8', env: { ...process.env, MSYS_NO_PATHCONV: '1' } });
  execFileSync('docker', ['cp', 'recorion_backend:/tmp/e2e_toplanti.mp3', mtFile], { env: { ...process.env, MSYS_NO_PATHCONV: '1' } });
  const mt = await session('manager');
  await mt.page.getByRole('button', { name: 'Toplantıdan oluştur' }).click();
  let mtDlg = mt.page.getByRole('dialog');
  await mtDlg.getByRole('button', { name: 'Tarayıcıda kaydet' }).click();
  await mtDlg.getByRole('button', { name: 'Kaydı başlat' }).click();
  await mtDlg.getByText(/Kaydediliyor/).waitFor({ timeout: 10000 });
  await mt.page.waitForTimeout(4000);
  await mtDlg.getByRole('button', { name: 'Kaydı bitir' }).click();
  const recAlert = mtDlg.getByRole('alert');
  await recAlert.waitFor({ timeout: 240000 });  // ses-yazı: kısa kayıtta ~1 dk bekleme + bir yeniden deneme
  const recMsg = await recAlert.innerText();
  step(/anlaşılır konuşma/.test(recMsg), 'Tarayıcıda kayıt alındı; konuşma olmayan kayıt anlaşılır uyarıyla reddedildi', recMsg.slice(0, 90));
  await mtDlg.getByRole('button', { name: 'Yeniden dene' }).click();
  await mtDlg.getByRole('button', { name: 'Dosya yükle' }).click();
  await mtDlg.locator('#mt-title').fill('Depo sayım ön görüşmesi');
  await mtDlg.locator('#mt-file').setInputFiles(mtFile);
  const mt0 = Date.now();
  await mtDlg.getByRole('button', { name: 'Yükle ve işle' }).click();
  await mtDlg.locator('#mt-name').waitFor({ timeout: 8 * 60000 });
  const mtSecs = Math.round((Date.now() - mt0) / 1000);
  const draftName = await mtDlg.locator('#mt-name').inputValue();
  const draftReq = await mtDlg.locator('#mt-req').inputValue();
  const draftSteps = await mtDlg.getByRole('list', { name: 'Önerilen adımlar' }).locator('li').count();
  const mtName = `${NAME} toplantı`;
  await mtDlg.locator('#mt-name').fill(mtName);
  await shot(mt.page, '18-toplantidan-taslak');
  step(draftName.length > 3 && /barkod/i.test(draftReq) && /onay/i.test(draftReq) && draftSteps >= 3,
    'Toplantı kaydı yazıya çevrildi ve Beyin AI isterleri (barkod, muhasebe onayı) ile adımları çıkardı',
    `${mtSecs} sn · "${draftName}" · ${draftSteps} adım · isterler: ${draftReq.replace(/\s+/g, ' ').slice(0, 80)}`);
  await mtDlg.getByRole('button', { name: 'Projeyi oluştur' }).click();
  await mt.page.getByRole('heading', { name: mtName }).waitFor({ timeout: 20000 });
  await mt.page.locator('.pj-step').first().waitFor({ timeout: 20000 });
  const mtPlanSteps = await mt.page.locator('.pj-step').count();
  step(mtPlanSteps === draftSteps, 'Toplantıdan proje oluştu; önerilen adımlar onay bekleyen plan taslağı olarak geldi',
    `${mtPlanSteps} adım`);
  const mtProj = ((await api(mt.page, '/api/v1/projects/?scope=mine')).body || []).find((x) => x.name === mtName);
  if (mtProj) await api(mt.page, `/api/v1/projects/${mtProj.id}/status`, { method: 'POST', body: JSON.stringify({ action: 'cancel' }) });
  await mt.ctx.close();

  // 11.4 Model yönlendirici: canlıda ONAY VERİLMEZ (platform varsayılanını tüm müşteriler için değiştirir). Süper Admin ekranda
  // beş iş türünü, son kalite testinin matrisini ve önerileri görür; şirket yöneticisi bu uçlara erişemez
  const mr = await session('super');
  await mr.page.goto(`${APP}/#/super-admin/model-router`);
  const routeTable = mr.page.getByRole('table', { name: 'İş türü yönlendirmeleri' });
  await routeTable.waitFor({ timeout: 30000 });
  const routeRows = await routeTable.locator('tbody tr').count();
  const matrixRows = await mr.page.getByRole('table', { name: 'Kalite matrisi' }).locator('tbody tr').count().catch(() => 0);
  const recCount = await routeTable.getByRole('button', { name: 'Önerileni onayla' }).count();
  await shot(mr.page, '19-model-yonlendirici');
  await mr.ctx.close();
  const mrAdm = await session('admin');
  const mrDenied = (await api(mrAdm.page, '/api/v1/system/model-router')).status;
  await mrAdm.ctx.close();
  step(routeRows === 5 && mrDenied === 403, 'Model yönlendirici: 5 iş türü, kalite matrisi ve öneriler Süper Admin\'de; şirket yöneticisi erişemiyor',
    `iş türü: ${routeRows} · matriste model: ${matrixRows} · onay bekleyen öneri: ${recCount} · şirket yöneticisi: ${mrDenied}`);

  // 12.1 Bağlantı kataloğu: yönetici galeride arar ve kategori seçer; "yakında" kartı anlaşılır bilgi verir; sistemini bulamayınca
  // RECAi'ye sorar (gerçek EVREN) ve önerilen kartla devam eder
  const ct = await session('admin');
  await ct.page.getByRole('button', { name: 'Entegrasyonlar' }).click();
  await ct.page.getByRole('button', { name: 'Bağlantı ekle' }).click();
  const ctDlg = ct.page.getByRole('dialog');
  const catList = ctDlg.getByRole('list', { name: 'Bağlantı kataloğu' });
  await catList.waitFor({ timeout: 15000 });
  const allCards = await catList.getByRole('listitem').count();
  await ctDlg.locator('#ig-search').fill('muhasebe');
  const foundErp = (await catList.getByRole('listitem').allInnerTexts()).map((t) => t.split('\n').find((l) => /Odoo|Logo|Mikro|Netsis/.test(l))).filter(Boolean);
  await ctDlg.locator('#ig-search').fill('');
  await ctDlg.getByRole('button', { name: 'ERP', exact: true }).click();
  const erpCount = await catList.getByRole('listitem').count();
  await catList.getByRole('listitem').filter({ hasText: 'SAP Business One' }).click();
  const plannedToast = await ct.page.getByRole('status').filter({ hasText: 'SAP Business One' }).first().innerText({ timeout: 5000 }).catch(() => '');
  const stillGallery = await catList.isVisible();
  await shot(ct.page, '20-baglanti-katalogu');
  step(allCards >= 25 && foundErp.length >= 3 && erpCount >= 8 && /Planlanıyor|Edge/.test(plannedToast) && stillGallery,
    'Bağlantı kataloğu: arama ve kategori çalışıyor; "yakında" kartı anlaşılır bilgi veriyor',
    `kart: ${allCards} · "muhasebe" araması: ${foundErp.join(', ')} · ERP: ${erpCount} · yakında: ${plannedToast.slice(0, 70)}`);

  await ctDlg.getByRole('button', { name: 'Tümü', exact: true }).click();
  await ctDlg.locator('#ig-ask').fill('Logo Tiger 3 kullanıyoruz, veritabanı şirketin kendi sunucusunda. Cari bakiyeleri ve stokları AI personelin görmesini istiyoruz.');
  const advStart = Date.now();
  await ctDlg.getByRole('button', { name: 'Nasıl bağlanırım?' }).click();
  const advice = ctDlg.getByLabel('RECAi önerisi');
  await advice.waitFor({ timeout: 180000 });
  const adviceText = await advice.innerText();
  const continueBtn = advice.getByRole('button', { name: /ile devam et$/ });
  const continueLabel = await continueBtn.innerText().catch(() => '');
  step(/Edge|ajan/i.test(adviceText) && /Logo|şirket sunucusu/i.test(continueLabel),
    'RECAi bağlanma rehberi: "Logo Tiger 3" için Edge yolunu ve adımları önerdi, önerilen kartla devam edilebiliyor',
    `${((Date.now() - advStart) / 1000).toFixed(0)} sn · ${continueLabel} · ${adviceText.replace(/\s+/g, ' ').slice(0, 120)}`);

  // 12.1 Tek tık giriş (gerçek Linear MCP sunucusu): kart kurulum adımlarını gösterir, kimlik yöntemi OAuth gelir, anahtar alanı
  // görünmez; kaydedince "giriş yapalım mı" sorulur; Linear'ın GERÇEK giriş sayfasına gidilir (keşif + otomatik istemci kaydı +
  // PKCE gerçek sunucuyla). Test hesabımız olmadığı için izin vermeden dönülür → anlaşılır bildirim, bağlantı "Giriş gerekli" kalır
  await ctDlg.locator('#ig-search').fill('linear');
  await pickCard(ctDlg, 'Linear');
  const setupSteps = await ctDlg.getByRole('list', { name: 'Kurulum adımları' }).locator('li').count();
  const authMode = await ctDlg.locator('#ig-c-auth_mode').inputValue();
  const tokenFields = await ctDlg.locator('#ig-s-token').count();
  const lnName = `Linear ${NAME.slice(-5)}`;
  await ctDlg.locator('#ig-name').fill(lnName);
  await ctDlg.getByRole('button', { name: 'Kaydet' }).click();
  const ask = ct.page.getByRole('alertdialog');
  await ask.waitFor({ timeout: 15000 });
  await ask.getByRole('button', { name: 'Giriş yap' }).click();
  await ct.page.waitForURL(/mcp\.linear\.app|linear\.app/, { timeout: 45000 });
  const authUrl = new URL(ct.page.url());
  await ct.page.waitForLoadState('domcontentloaded').catch(() => {});
  await shot(ct.page, '21-linear-giris-sayfasi');
  const authQ = Object.fromEntries(authUrl.searchParams);
  step(setupSteps >= 1 && authMode === 'oauth' && tokenFields === 0 && /linear\.app$/.test(authUrl.hostname)
      && authQ.code_challenge_method === 'S256' && !!authQ.client_id && authQ.resource === 'https://mcp.linear.app/mcp' && (authQ.state || '').length >= 32,
    'Tek tık giriş: Linear kartı OAuth ile geldi; "Giriş yap" Linear\'ın gerçek giriş sayfasına götürdü (otomatik istemci kaydı, PKCE, resource)',
    `kurulum adımı: ${setupSteps} · yöntem: ${authMode} · anahtar alanı: ${tokenFields} · ${authUrl.hostname}${authUrl.pathname} · istemci: ${authQ.client_id ? 'var' : 'yok'}`);

  await ct.page.goto(`${APP}/api/v1/integrations/oauth/callback?state=${encodeURIComponent(authQ.state || '')}&error=access_denied`);
  await ct.page.waitForURL(/#\/company-admin/, { timeout: 30000 });
  const deniedToast = await ct.page.getByRole('alert').filter({ hasText: 'izin verilmedi' }).first().innerText({ timeout: 20000 }).catch(() => '');
  const lnRow = ct.page.locator('.pj-list li', { hasText: lnName });
  await lnRow.waitFor({ timeout: 20000 });
  const lnRowText = await lnRow.innerText();
  const cleanUrl = !ct.page.url().includes('oauth=');
  const replay = await (await ct.page.request.get(`${APP}/api/v1/integrations/oauth/callback?state=${encodeURIComponent(authQ.state || '')}&code=x`, { maxRedirects: 0 })).headers().location || '';
  await shot(ct.page, '22-giris-izin-verilmedi');
  step(!!deniedToast && /Giriş gerekli/.test(lnRowText) && /Giriş yap/.test(lnRowText) && cleanUrl && /oauth=error/.test(replay),
    'Linear\'da izin verilmeden dönüldü: Entegrasyonlar açıldı, anlaşılır bildirim; bağlantı "Giriş gerekli"; aynı giriş oturumu ikinci kez kullanılamıyor',
    `${deniedToast.slice(0, 60)} · satır: ${lnRowText.replace(/\s+/g, ' ').slice(0, 80)} · adres temiz: ${cleanUrl}`);
  const lnConn = ((await api(ct.page, `/api/v1/company/${cfg.tenant_id}/integrations`)).body || []).find((c) => c.name === lnName);
  if (lnConn) await api(ct.page, `/api/v1/company/${cfg.tenant_id}/integrations/${lnConn.id}`, { method: 'PUT', body: JSON.stringify({ status: 'DISABLED' }) });
  await ct.ctx.close();

  // 12.1 Süper Admin kataloğu yönetir (canlıda kart DEĞİŞTİRİLMEZ: tüm müşterilerin galerisini etkiler); şirket yöneticisi erişemez
  const cs = await session('super');
  await cs.page.goto(`${APP}/#/super-admin/integration-catalog`);
  const csTable = cs.page.locator('table.ui-table');
  await csTable.locator('tbody tr').first().waitFor({ timeout: 30000 });
  const csRows = await csTable.locator('tbody tr').count();
  await csTable.locator('tbody tr', { hasText: 'Linear' }).getByRole('button', { name: 'Düzenle' }).click();
  const csPreset = await cs.page.getByRole('dialog').locator('#ca-preset').inputValue();
  await cs.page.getByRole('dialog').getByRole('button', { name: 'Vazgeç' }).click();
  await shot(cs.page, '23-katalog-yonetimi');
  await cs.ctx.close();
  const csAdm = await session('admin');
  const csDenied = (await api(csAdm.page, '/api/v1/system/integration-catalog')).status;
  await csAdm.ctx.close();
  step(csRows >= 25 && /mcp\.linear\.app/.test(csPreset) && csDenied === 403,
    'Bağlantı kataloğu Süper Admin\'de yönetiliyor (kart ön ayarı görünüyor); şirket yöneticisi erişemiyor',
    `kart: ${csRows} · Linear ön ayarı: ${csPreset.replace(/\s+/g, ' ').slice(0, 60)} · şirket yöneticisi: ${csDenied}`);

  // 12.2–12.3 Test Odoo'su (Odoo.sh, recdx-recorion-test — gerçek RECDx Odoo DEĞİL): yönetici katalogdan Odoo ekler (JSON-2,
  // kullanıcı adı gerekmez), Eşlemeler'de RECDx hazır "Odoo ürün kartı"yla başlar, hedefin alan tanımlarıyla denetler, YAZMADAN
  // dener ve onaylar; ayrıca boş bir "görev" eşlemesini RECAi'ye önerdirir (gerçek EVREN, gerçek Odoo alanları)
  const envFile = fs.readFileSync(path.resolve('..', '.env'), 'utf8');
  const otest = Object.fromEntries(envFile.split(/\r?\n/).filter((l) => l.startsWith('ODOO_TEST_')).map((l) => [l.split('=')[0], l.slice(l.indexOf('=') + 1)]));
  const ot = await session('admin');
  await ot.page.getByRole('button', { name: 'Entegrasyonlar' }).click();
  await ot.page.getByRole('button', { name: 'Bağlantı ekle' }).click();
  const otDlg = ot.page.getByRole('dialog');
  await pickCard(otDlg, 'Odoo');
  const otName = `Test Odoo ${NAME.slice(-5)}`;
  await otDlg.locator('#ig-name').fill(otName);
  await otDlg.locator('#ig-c-url').fill(otest.ODOO_TEST_URL);
  await otDlg.locator('#ig-c-db').fill(otest.ODOO_TEST_DB);
  await otDlg.locator('#ig-s-api_key').fill(otest.ODOO_TEST_API_KEY);
  await otDlg.getByRole('button', { name: 'Kaydet' }).click();
  const otRow = ot.page.locator('.pj-list li', { hasText: otName });
  await otRow.waitFor({ timeout: 15000 });
  await otRow.getByRole('button', { name: 'Dene' }).click();
  await otRow.getByText(/Son deneme/).waitFor({ timeout: 60000 });
  const otText = await otRow.innerText();
  step(/başarılı/.test(otText) && !(await ot.page.content()).includes(otest.ODOO_TEST_API_KEY),
    'Test Odoo\'su (Odoo 20) katalogdan bağlandı; JSON-2 API ile kullanıcı adı gerekmeden denendi; anahtar sayfada yok',
    otText.split('\n').find((l) => /Son deneme/.test(l)) || '');

  await otRow.getByRole('button', { name: 'Eşlemeler' }).click();
  let studio = ot.page.getByRole('dialog');
  await studio.getByRole('button', { name: 'Yeni eşleme' }).click();
  await studio.getByRole('list', { name: 'Hazır eşlemeler' }).getByRole('listitem').filter({ hasText: 'Odoo ürün kartı' }).getByRole('button', { name: 'Bununla başla' }).click();
  const rulesTable = studio.getByRole('table', { name: 'Eşleme kuralları' });
  await rulesTable.waitFor({ timeout: 60000 });
  const ruleCount = await rulesTable.locator('tbody tr').count();
  await studio.getByRole('button', { name: 'Denetle' }).click();
  const checkBox = studio.getByLabel('Denetim sonucu');
  await checkBox.waitFor({ timeout: 60000 });
  const checkText = await checkBox.innerText();
  await studio.getByRole('button', { name: 'Dene (yazmadan)' }).click();
  const dryBox = studio.getByLabel('Deneme sonucu');
  await dryBox.waitFor({ timeout: 90000 });
  const dryText = await dryBox.innerText();
  const dryRows = await studio.getByRole('table', { name: 'Hedefe gidecek değerler' }).locator('tbody tr').count();
  await shot(ot.page, '24-esleme-studyosu-deneme');
  const approveBtn = studio.getByRole('button', { name: 'Onayla', exact: true });
  const canApprove = await approveBtn.isEnabled();
  if (canApprove) await approveBtn.click();
  await studio.locator('.ui-badge', { hasText: 'Onaylı' }).first().waitFor({ timeout: 15000 }).catch(() => {});
  const approvedBadge = await studio.locator('.ui-badge', { hasText: 'Onaylı' }).count();
  step(ruleCount >= 10 && /hata yok/.test(checkText) && /yeni kayıt açılacak|güncellenecek/.test(dryText) && dryRows >= 8 && approvedBadge > 0,
    'Eşleme stüdyosu: hazır "Odoo ürün kartı" gerçek Odoo alanlarıyla hatasız denetlendi, yazmadan denendi (birim/vergi arandı) ve onaylandı',
    `${ruleCount} kural · ${checkText.replace(/\s+/g, ' ').slice(0, 50)} · ${dryText.split('\n')[0].slice(0, 70)} · ${dryRows} değer`);
  await studio.getByRole('button', { name: 'Kapat' }).click();

  // Görev eşlemesi RECAi önerisiyle (gerçek EVREN + gerçek Odoo project.task alanları)
  studio = ot.page.getByRole('dialog');
  await studio.getByRole('button', { name: 'Yeni eşleme' }).click();
  await studio.locator('#mp-object').selectOption('TASK');
  await studio.getByRole('button', { name: 'Boş eşleme oluştur' }).click();
  await studio.getByRole('table', { name: 'Eşleme kuralları' }).waitFor({ timeout: 60000 });
  const sugStart = Date.now();
  await studio.getByRole('button', { name: 'RECAi önersin' }).click();
  await ot.page.getByRole('status').filter({ hasText: 'RECAi eşleme önerdi' }).first().waitFor({ timeout: 240000 }).catch(() => {});
  const sugRows = await studio.getByRole('table', { name: 'Eşleme kuralları' }).locator('tbody tr').count();
  const sugTargets = await studio.getByRole('table', { name: 'Eşleme kuralları' }).locator('tbody tr select').first().inputValue().catch(() => '');
  await studio.getByRole('button', { name: 'Kaydet' }).click();
  await ot.page.waitForTimeout(1500);
  await studio.getByRole('button', { name: 'Denetle' }).click();
  await studio.getByLabel('Denetim sonucu').waitFor({ timeout: 60000 });
  const sugCheck = await studio.getByLabel('Denetim sonucu').innerText();
  await shot(ot.page, '25-recai-esleme-onerisi');
  step(sugRows >= 2 && !/hedefte yok/.test(await studio.innerText()),
    'RECAi görev eşlemesi önerdi: yalnızca Odoo\'da gerçekten olan alanlar (uydurma alan yok), denetim sonucu görünüyor',
    `${((Date.now() - sugStart) / 1000).toFixed(0)} sn · ${sugRows} kural (ilk: ${sugTargets}) · ${sugCheck.replace(/\s+/g, ' ').slice(0, 70)}`);
  await studio.getByRole('button', { name: 'Kapat' }).click();
  await studio.getByRole('button', { name: 'Kapat' }).click().catch(() => {});

  // 12.4 Hazır "Odoo proje görevi" eşlemesi: görev adına "[RECOrion Test]" öneki (test verisi ayırt edilsin) — stüdyoda kural
  // düzenleme gibi, API ile; denenir ve onaylanır
  const otConn = ((await api(ot.page, `/api/v1/company/${cfg.tenant_id}/integrations`)).body || []).find((c) => c.name === otName);
  const tplTask = ((await api(ot.page, `/api/v1/company/${cfg.tenant_id}/mappings/templates?connector=odoo`)).body || []).find((t) => t.code === 'odoo_task');
  const taskMap = (await api(ot.page, `/api/v1/company/${cfg.tenant_id}/mappings`, { method: 'POST', body: JSON.stringify({
    connection_id: otConn.id, object_type: 'TASK', name: `Görev → Test Odoo ${NAME.slice(-5)}`, template_id: tplTask.id }) })).body;
  const taskRules = taskMap.rules.map((r) => (r.target === 'name' ? { target: 'name', transform: 'template', params: { text: '[RECOrion Test] {title}' } } : r));
  await api(ot.page, `/api/v1/company/${cfg.tenant_id}/mappings/${taskMap.id}`, { method: 'PUT', body: JSON.stringify({ rules: taskRules }) });
  const taskDry = (await api(ot.page, `/api/v1/company/${cfg.tenant_id}/mappings/${taskMap.id}/dry-run`, { method: 'POST', body: '{}' })).body;
  const taskAppr = await api(ot.page, `/api/v1/company/${cfg.tenant_id}/mappings/${taskMap.id}/approve`, { method: 'POST' });
  await ot.ctx.close();

  // 12.4 Proje yöneticisi biten projenin analiz adımı çıktısındaki yapılacak işleri "Sisteme aktar" ile test Odoo'suna görev
  // olarak gönderir: RECAi çıkarır, önizleme Onaylarım'a düşer; biri onaylanır (Temporal kuyruğuyla yazılır), biri reddedilir;
  // yazılan görev Odoo'da doğrulanır, sonra "Geri al" ile arşivlenir
  const tx = await session('manager');
  const trProj = (await api(tx.page, '/api/v1/projects/?scope=mine')).body.find((x) => x.name === NAME);
  await tx.page.goto(`${APP}/#/workspace?project=${trProj.id}`);
  await tx.page.getByRole('tab', { name: /İş Akışı/ }).click();
  const transferBtn = tx.page.getByRole('button', { name: 'Sisteme aktar' }).first();
  await transferBtn.waitFor({ timeout: 20000 });
  await transferBtn.click();
  const trDlg2 = tx.page.getByRole('dialog');
  await trDlg2.locator('#tt-map').selectOption({ label: new RegExp(`Görev → Test Odoo ${NAME.slice(-5)}`) }).catch(async () => {
    const opt = await trDlg2.locator('#tt-map option', { hasText: `Görev → Test Odoo ${NAME.slice(-5)}` }).getAttribute('value');
    await trDlg2.locator('#tt-map').selectOption(opt);
  });
  const exStart = Date.now();
  await trDlg2.getByRole('button', { name: 'RECAi ile hazırla' }).click();
  const trList = trDlg2.getByRole('list', { name: 'Bu adımın aktarımları' });
  await trList.waitFor({ timeout: 20000 });
  let trRows = [];
  for (let i = 0; i < 90; i++) {
    trRows = ((await api(tx.page, `/api/v1/projects/${trProj.id}/transfers`)).body || []).filter((x) => x.connection_name === otName);
    if (trRows.length && trRows.every((x) => x.status !== 'EXTRACTING')) break;
    await tx.page.waitForTimeout(2000);
  }
  const pendingT = trRows.filter((x) => x.status === 'PENDING_APPROVAL');
  await shot(tx.page, '26-sisteme-aktar-onizleme');
  step(pendingT.length >= 1 && pendingT.every((x) => x.preview.some((p) => p.target === 'name' && p.value.startsWith('[RECOrion Test]'))),
    'Sisteme aktar: RECAi adım çıktısından görevleri çıkardı; önizlemeler onaya düştü, hiçbiri onaysız yazılmadı',
    `${((Date.now() - exStart) / 1000).toFixed(0)} sn · ${trRows.length} öneri (${pendingT.length} onay bekliyor) · ilk: ${pendingT[0]?.preview.find((p) => p.target === 'name')?.value.slice(0, 60) || '-'}`
    + ` · eşleme denemesi: ${taskDry?.ok ? 'hatasız' : 'hatalı'}, onay ${taskAppr.status}`);
  await trDlg2.getByRole('button', { name: 'Kapat' }).click();

  await tx.page.getByRole('button', { name: /Onaylarım/ }).click();
  const inbox = tx.page.getByRole('list', { name: 'Onay bekleyen aktarımlar' });
  await inbox.waitFor({ timeout: 30000 });
  const trFirst = pendingT[0];
  const firstCard = inbox.getByRole('listitem', { name: `Aktarım: ${trFirst.object.title}` });
  await firstCard.getByRole('button', { name: 'Onayla ve aktar' }).click();
  if (pendingT[1]) {
    await inbox.getByRole('listitem', { name: `Aktarım: ${pendingT[1].object.title}` }).getByRole('button', { name: 'Reddet' }).click();
    await dialogOk(tx.page, 'Bu işi Odoo\'da biz açacağız');
  }
  let doneT = null;
  for (let i = 0; i < 60; i++) {
    doneT = ((await api(tx.page, `/api/v1/projects/${trProj.id}/transfers`)).body || []).find((x) => x.id === trFirst.id);
    if (['DONE', 'FAILED'].includes(doneT.status)) break;
    await tx.page.waitForTimeout(2000);
  }
  const otCall = async (model, method, body) => (await fetch(`${otest.ODOO_TEST_URL}/json/2/${model}/${method}`, { method: 'POST',
    headers: { Authorization: `bearer ${otest.ODOO_TEST_API_KEY}`, 'X-Odoo-Database': otest.ODOO_TEST_DB, 'Content-Type': 'application/json' },
    body: JSON.stringify(body) })).json();
  const odooTask = doneT.external_id ? (await otCall('project.task', 'read', { ids: [Number(doneT.external_id)], fields: ['name', 'active', 'priority'] }))[0] : null;
  const rejected = pendingT[1] ? ((await api(tx.page, `/api/v1/projects/${trProj.id}/transfers`)).body || []).find((x) => x.id === pendingT[1].id) : null;
  step(doneT.status === 'DONE' && odooTask?.name?.startsWith('[RECOrion Test]') && (!rejected || rejected.status === 'REJECTED'),
    'Onaylanan aktarım Temporal kuyruğuyla test Odoo\'suna yazıldı (görev Odoo\'da doğrulandı); reddedilen yazılmadı',
    `${doneT.status} · ${doneT.external_ref || doneT.error || ''} · Odoo: ${odooTask?.name?.slice(0, 50) || '-'} · ret: ${rejected?.status || '—'}`);

  await tx.page.goto(`${APP}/#/workspace?project=${trProj.id}`);
  await tx.page.getByRole('tab', { name: /Kapanış/ }).click();
  const extCard = tx.page.getByRole('list', { name: 'Proje aktarımları' });
  await extCard.waitFor({ timeout: 20000 });
  const extLink = await tx.page.locator('a.ig-link', { hasText: otName }).first().getAttribute('href').catch(() => null);
  await extCard.getByRole('listitem', { name: `Aktarım: ${trFirst.object.title}` }).getByRole('button', { name: 'Geri al' }).click();
  await dialogOk(tx.page);
  await tx.page.waitForTimeout(2500);
  const afterRb = (await otCall('project.task', 'read', { ids: [Number(doneT.external_id)], fields: ['active'] }))[0];
  await shot(tx.page, '27-dis-sistem-kayitlari');
  step(!!extLink && extLink.includes(`/odoo/project.task/${doneT.external_id}`) && afterRb?.active === false,
    'Proje kapanışında dış sistem kaydı bağlantısıyla görünüyor; "Geri al" ile Odoo\'daki görev arşivlendi',
    `bağlantı: ${extLink ? extLink.replace(otest.ODOO_TEST_URL, '…') : '-'} · Odoo active: ${afterRb?.active}`);
  await tx.ctx.close();

  // 12.5 Logo (sahte Logo REST servisi — GERÇEK LOGO DEĞİL) Edge ajanının REST şablonlarıyla: yazma açık ajan bağlanır, hazır
  // "Logo malzeme kartı" eşlemesi ajanın şablonlarıyla denetlenir ve onaylanır; RECAi ürün bulamadığı öneriyi yönetici "Düzelt"
  // ile doldurur, onaylar; malzeme kartı sahte Logo'da açılır; aynı kodla ikinci aktarım güncelleme olarak gider
  const lgDir = '/tmp/edge_logo_e2e';
  execFileSync('docker', ['exec', 'recorion_backend', 'sh', '-c', `rm -rf ${lgDir} && mkdir -p ${lgDir} && `
    + `printf '%s' '{"hostname":"LOGO-REST","templates_file":"/edge_agent/templates.logo_rest.example.json","allow_write":true,"audit_log":"${lgDir}/audit.log",`
    + `"http_api":{"base_url":"http://127.0.0.1:32991","auth":{"type":"oauth_password","token_path":"/api/v1/token","username_env":"LOGO_USER","password_env":"LOGO_PASSWORD",`
    + `"client_id_env":"LOGO_CLIENT_ID","client_secret_env":"LOGO_CLIENT_SECRET","form":{"firmno":"1"}}}}' > ${lgDir}/cfg.json`], { env: { ...process.env, MSYS_NO_PATHCONV: '1' } });
  const lgRest = spawn('docker', ['exec', 'recorion_backend', 'timeout', '1200', 'python', '/edge_agent/fake_logo_rest.py', '32991'], { stdio: 'ignore', env: { ...process.env, MSYS_NO_PATHCONV: '1' } });
  const lg = await session('admin');
  await lg.page.getByRole('button', { name: 'Entegrasyonlar' }).click();
  await lg.page.getByRole('button', { name: 'Bağlantı ekle' }).click();
  const lgDlg = lg.page.getByRole('dialog');
  await pickCard(lgDlg, 'Logo (Tiger, GO');
  const lgName = `Logo REST ${NAME.slice(-5)}`;
  await lgDlg.locator('#ig-name').fill(lgName);
  await lgDlg.getByRole('button', { name: 'Kaydet' }).click();
  const lgRow = lg.page.locator('.pj-list li', { hasText: lgName });
  await lgRow.waitFor({ timeout: 15000 });
  await lgRow.getByRole('button', { name: 'Ajan anahtarı' }).click();
  const lgToken = (await lg.page.getByLabel('Ajan anahtarı').innerText()).trim();
  await lg.page.getByRole('button', { name: 'Kaydettim, kapat' }).click();
  const lgAgent = spawn('docker', ['exec', '-e', 'RECORION_URL=http://localhost:8000', '-e', `RECORION_EDGE_TOKEN=${lgToken}`, '-e', 'LOGO_USER=LOGO',
    '-e', 'LOGO_PASSWORD=sahte-parola', '-e', 'LOGO_CLIENT_ID=recorion', '-e', 'LOGO_CLIENT_SECRET=sahte-istemci', 'recorion_backend',
    'timeout', '1200', 'python', '/edge_agent/recorion_edge.py', '--config', `${lgDir}/cfg.json`], { stdio: 'ignore', env: { ...process.env, MSYS_NO_PATHCONV: '1' } });
  let lgConn = null;
  for (let i = 0; i < 30; i++) {
    lgConn = ((await api(lg.page, `/api/v1/company/${cfg.tenant_id}/integrations`)).body || []).find((c) => c.name === lgName);
    if (lgConn?.agent?.online) break;
    await lg.page.waitForTimeout(1000);
  }
  const lgTpl = ((await api(lg.page, `/api/v1/company/${cfg.tenant_id}/mappings/templates?connector=edge`)).body || []).find((t) => t.code === 'logo_material');
  const lgMap = (await api(lg.page, `/api/v1/company/${cfg.tenant_id}/mappings`, { method: 'POST', body: JSON.stringify({
    connection_id: lgConn.id, object_type: 'PRODUCT', name: `Ürün → Logo ${NAME.slice(-5)}`, template_id: lgTpl.id }) })).body;
  const lgCheck = (await api(lg.page, `/api/v1/company/${cfg.tenant_id}/mappings/${lgMap.id}/check`, { method: 'POST' })).body;
  const lgDry = (await api(lg.page, `/api/v1/company/${cfg.tenant_id}/mappings/${lgMap.id}/dry-run`, { method: 'POST', body: '{}' })).body;
  const lgAppr = await api(lg.page, `/api/v1/company/${cfg.tenant_id}/mappings/${lgMap.id}/approve`, { method: 'POST' });
  step(lgConn?.agent?.online && lgConn.agent.templates === 5 && lgCheck?.ok && lgDry?.ok && lgDry.action === 'CREATE' && lgAppr.status === 200,
    'Logo (Edge + Logo REST şablonları): ajan yazma açık bağlandı (5 şablon); hazır "Logo malzeme kartı" ajanın şablonlarıyla denetlendi, yazmadan denendi, onaylandı',
    `şablon: ${lgConn?.agent?.templates} · denetim: ${lgCheck?.ok ? 'hatasız' : JSON.stringify(lgCheck?.errors)} · deneme: ${lgDry?.action} · birim seti: ${lgDry?.values?.birim_seti}`);
  await lg.ctx.close();

  const lm = await session('manager');
  const firstTask = ((await api(lm.page, `/api/v1/projects/${trProj.id}/workflow`)).body.tasks || []).find((t) => t.can_transfer);
  await api(lm.page, `/api/v1/tasks/${firstTask.id}/transfers`, { method: 'POST', body: JSON.stringify({ mapping_id: lgMap.id }) });
  let lgRows = [];
  for (let i = 0; i < 90; i++) {
    lgRows = ((await api(lm.page, `/api/v1/projects/${trProj.id}/transfers`)).body || []).filter((x) => x.connection_name === lgName);
    if (lgRows.length && lgRows.every((x) => x.status !== 'EXTRACTING')) break;
    await lm.page.waitForTimeout(2000);
  }
  const lgFirst = lgRows[0];
  await lm.page.goto(`${APP}/#/workspace?project=${trProj.id}`);
  await lm.page.getByRole('tab', { name: /Kapanış/ }).click();
  const lgCard = lm.page.getByRole('list', { name: 'Proje aktarımları' }).getByRole('listitem').filter({ hasText: lgName }).first();
  await lgCard.waitFor({ timeout: 20000 });
  await lgCard.getByRole('button', { name: 'Düzelt' }).click();
  const fixDlg = lm.page.getByRole('dialog');
  await fixDlg.locator('#tf-code').fill(`RECT-${NAME.slice(-5).replace(':', '')}`);
  await fixDlg.locator('#tf-name').fill('RECOrion Test Bayi Portalı Tablet');
  await fixDlg.locator('#tf-type').selectOption('STOCK');
  await fixDlg.locator('#tf-unit').selectOption('Adet');
  await fixDlg.locator('#tf-vat_rate').fill('20');
  await fixDlg.locator('#tf-sale_price').fill('18500');
  await fixDlg.getByRole('button', { name: 'Kaydet ve önizle' }).click();
  await lm.page.waitForTimeout(2500);
  const fixed = ((await api(lm.page, `/api/v1/projects/${trProj.id}/transfers`)).body || []).find((x) => x.id === lgFirst.id);
  await lm.page.getByRole('button', { name: /Onaylarım/ }).click();
  const lgInbox = lm.page.getByRole('list', { name: 'Onay bekleyen aktarımlar' });
  await lgInbox.waitFor({ timeout: 30000 });
  await lgInbox.getByRole('listitem', { name: 'Aktarım: RECOrion Test Bayi Portalı Tablet' }).getByRole('button', { name: 'Onayla ve aktar' }).click();
  let lgDone = null;
  for (let i = 0; i < 60; i++) {
    lgDone = ((await api(lm.page, `/api/v1/projects/${trProj.id}/transfers`)).body || []).find((x) => x.id === lgFirst.id);
    if (['DONE', 'FAILED'].includes(lgDone.status)) break;
    await lm.page.waitForTimeout(2000);
  }
  const logoState = JSON.parse(execFileSync('docker', ['exec', 'recorion_backend', 'python', '-c',
    "import urllib.request,json;print(urllib.request.urlopen('http://127.0.0.1:32991/__state').read().decode())"], { encoding: 'utf8', env: { ...process.env, MSYS_NO_PATHCONV: '1' } }));
  const logoCard = (logoState.items || []).find((x) => x.NAME === 'RECOrion Test Bayi Portalı Tablet');
  await shot(lm.page, '28-logo-aktarim');
  step(fixed?.status === 'PENDING_APPROVAL' && lgDone.status === 'DONE' && logoCard?.UNITSET_CODE === 'ADET' && logoCard?.VAT === 20,
    'Düzeltilen ürün kartı onaydan sonra Edge ajanı + Logo REST ile Logo\'da açıldı (sahte Logo servisi; Logo tablolarına doğrudan yazılmadı)',
    `düzeltme: ${fixed?.status} · aktarım: ${lgDone.status} ${lgDone.external_ref || lgDone.error || ''} · Logo kartı: ${logoCard ? `${logoCard.CODE} / ${logoCard.UNITSET_CODE} / KDV ${logoCard.VAT}` : 'yok'}`);
  await lm.ctx.close();
  lgAgent.kill();
  lgRest.kill();

  // 12.6 RECOrion'un kendi MCP sunucusu: proje yöneticisi "Bağlantılarım"da yazma kapsamlı anahtar oluşturur (bir kez gösterilir);
  // dış istemci gibi MCP ile bağlanılır: araçlar keşfedilir, Case açılır (RECAi plan taslağı hazırlar, onay bekler), taslağa adım
  // eklenir; onay aracı yoktur; anahtar iptal edilince bağlantı reddedilir
  const mc = await session('manager');
  await mc.page.getByRole('button', { name: 'Bağlantılarım' }).click();
  await mc.page.getByRole('button', { name: 'Anahtar oluştur' }).click();
  const mcDlg = mc.page.getByRole('dialog');
  await mcDlg.locator('#pt-name').fill(`Claude ${NAME.slice(-5)}`);
  await mcDlg.locator('#pt-write').check();
  await mcDlg.getByRole('button', { name: 'Oluştur' }).click();
  const pat = (await mc.page.getByLabel('Erişim anahtarı').innerText()).trim();
  const claudeCmd = await mc.page.getByLabel('Claude Code komutu').innerText();
  await shot(mc.page, '29-baglantilarim-anahtar');
  await mc.page.getByRole('button', { name: 'Kaydettim, kapat' }).click();
  const mcpCall = async (method, params, id = 1) => {
    const r = await fetch('http://localhost:8000/api/v1/mcp', { method: 'POST', headers: { Authorization: `Bearer ${pat}`, 'Content-Type': 'application/json',
      Accept: 'application/json, text/event-stream' }, body: JSON.stringify({ jsonrpc: '2.0', id, method, params }) });
    return { status: r.status, body: await r.json().catch(() => null) };
  };
  const init = await mcpCall('initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'e2e', version: '1' } });
  const mtools = (await mcpCall('tools/list', {})).body?.result?.tools || [];
  const caseName = `Canlı Test MCP Case ${NAME.slice(-5)}`;
  const created = (await mcpCall('tools/call', { name: 'create_project', arguments: { name: caseName, kind: 'CASE',
    requirements: 'Bir bayi sipariş portalında yavaşlık şikâyeti geldi. Şikâyeti incele, kök nedeni bul, çözüm önerisi ve müşteriye yanıt taslağı hazırla.' } })).body?.result?.structuredContent;
  let planned = null;
  const planStart = Date.now();
  for (let i = 0; i < 60; i++) {
    planned = (await mcpCall('tools/call', { name: 'get_project', arguments: { project_id: created?.id } })).body?.result?.structuredContent;
    if (planned?.plan_draft_steps?.length) break;
    await mc.page.waitForTimeout(4000);
  }
  const added = (await mcpCall('tools/call', { name: 'add_step', arguments: { project_id: created?.id, title: 'Müşteriye yanıt gönderimi', job_title: 'Müşteri Temsilcisi', estimated_days: 1 } })).body?.result;
  step(init.body?.result?.serverInfo?.name === 'RECOrion' && mtools.length === 6 && !mtools.some((t) => /approve|decide/.test(t.name))
      && planned?.status === 'PLANNING' && planned?.plan_approved === false && planned.plan_draft_steps.length >= 1 && added?.isError === false && /claude mcp add/.test(claudeCmd),
    'MCP sunucusu: anahtar bir kez gösterildi; dış istemci 6 aracı keşfetti (onay aracı yok), Case açtı; RECAi plan taslağı hazırladı (onay bekliyor); taslağa adım eklendi',
    `plan ${((Date.now() - planStart) / 1000).toFixed(0)} sn · ${planned?.plan_draft_steps?.length || 0} adım + 1 · durum ${planned?.status}`);

  await mc.page.getByRole('button', { name: 'Projeler' }).click();
  await mc.page.getByText(caseName).first().waitFor({ timeout: 20000 }).catch(() => {});
  const inHub = await mc.page.getByText(caseName).count();
  await mc.page.getByRole('button', { name: 'Bağlantılarım' }).click();
  const patRow = mc.page.getByRole('list', { name: 'Erişim anahtarları' }).getByRole('listitem').filter({ hasText: `Claude ${NAME.slice(-5)}` });
  await patRow.getByRole('button', { name: 'İptal et' }).click();
  await dialogOk(mc.page);
  await mc.page.waitForTimeout(1500);
  const afterRevoke = await mcpCall('tools/list', {});
  step(inHub > 0 && afterRevoke.status === 401,
    'MCP ile açılan Case RECOrion\'da proje listesinde görünüyor; anahtar iptal edilince dış istemci reddedildi',
    `listede: ${inHub > 0 ? 'var' : 'yok'} · iptal sonrası: ${afterRevoke.status}`);
  await api(mc.page, `/api/v1/projects/${created?.id}/status`, { method: 'POST', body: JSON.stringify({ action: 'cancel', summary: 'Canlı test bitti' }) });
  await mc.ctx.close();
} catch (e) {
  ok = false;
  step(false, 'Beklenmeyen hata', e.message.split('\n')[0]);
}
await browser.close();
fs.writeFileSync(path.join(OUT, 'report.json'), JSON.stringify({ name: NAME, report, problems, seconds: Math.round((Date.now() - t0) / 1000) }, null, 2));
console.log(`\nSonuç: ${report.filter((r) => r.ok).length}/${report.length} adım geçti · ${Math.round((Date.now() - t0) / 1000)} sn · çıktılar: ${OUT}`);
console.log(`SORUNLAR (${problems.length}):\n` + problems.slice(0, 30).join('\n'));
process.exit(ok && report.every((r) => r.ok) ? 0 : 1);
