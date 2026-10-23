// Canlı uçtan uca test (Adım 6, 7.1–7.4, 7.5, 8): gerçek arayüz, gerçek backend, gerçek EVREN ve Temporal. Sahte veri yok. Ayrıntı: e2e/README.md
import { chromium } from 'playwright-core';
import { execFileSync } from 'child_process';
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

const browser = await chromium.launch({ executablePath: CHROME });

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
  await page.waitForURL(/#\/workspace/, { timeout: 20000 });
  return { ctx, page };
}
const shot = (page, name) => page.screenshot({ path: `${OUT}/${name}.png` });
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
  await page.getByRole('button', { name: 'Oluştur' }).click();
  await page.getByRole('heading', { name: NAME }).waitFor({ timeout: 15000 });
  step(true, 'Proje oluşturuldu (Taslak)', NAME);

  // 2. Beyin AI planı (gerçek EVREN çağrısı)
  await page.getByRole('tab', { name: /Beyin AI Planlama/ }).click();
  const t1 = Date.now();
  await page.getByRole('button', { name: 'Beyin AI plan önersin' }).click();
  await page.locator('.pj-step').first().waitFor({ timeout: 11 * 60000 });
  const stepCount = await page.locator('.pj-step').count();
  step(stepCount > 0, 'Beyin AI iş adımı önerdi', `${stepCount} adım, ${Math.round((Date.now() - t1) / 1000)} sn`);
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
  const untilApproval = async (title, minutes) => {
    const start = Date.now();
    let retried = 0;
    while (Date.now() - start < minutes * 60000) {
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
  step(/ONAYLANDI/.test(gate), 'Çalışma Alanı Kalite Kapısı gerçek durumu gösteriyor', gate.split('\n').slice(0, 3).join(' | '));
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
} catch (e) {
  ok = false;
  step(false, 'Beklenmeyen hata', e.message.split('\n')[0]);
}
await browser.close();
fs.writeFileSync(path.join(OUT, 'report.json'), JSON.stringify({ name: NAME, report, problems, seconds: Math.round((Date.now() - t0) / 1000) }, null, 2));
console.log(`\nSonuç: ${report.filter((r) => r.ok).length}/${report.length} adım geçti · ${Math.round((Date.now() - t0) / 1000)} sn · çıktılar: ${OUT}`);
console.log(`SORUNLAR (${problems.length}):\n` + problems.slice(0, 30).join('\n'));
process.exit(ok && report.every((r) => r.ok) ? 0 : 1);
