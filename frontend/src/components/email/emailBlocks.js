/**
 * E-posta şablonu blokları: her blok türü kendi HTML'ini üretir (e-posta istemcileri için satır içi stil).
 * compileBlocksToHtml blokları tam e-posta HTML'ine, htmlToBlocks kayıtlı HTML'i bloklara çevirir.
 */
export const EMAIL_PRESET_BLOCKS = [
  {
    type: 'HEADER',
    label: 'Kurumsal Başlık & Logo',
    subtitle: 'Yapay Zeka Destekli Kurumsal Çalışma Platformu',
    logoUrl: '',
    bgColor: '#1e1b4b',
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    fontSize: '26px',
    textColor: '#ffffff',
    renderHtml: (b) => {
      const bg = b.bgColor ? b.bgColor : 'linear-gradient(135deg, #1e1b4b 0%, #31104b 50%, #0f172a 100%)';
      const font = b.fontFamily || "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
      const fSize = b.fontSize || '26px';
      const color = b.textColor || '#ffffff';
      return `<div style="background: ${bg}; padding: 32px 25px; border-radius: 12px 12px 0 0; text-align: center; border-bottom: 2px solid #7134e2; font-family: ${font};">
  ${b.logoUrl ? `<div style="margin-bottom: 12px;"><img src="${b.logoUrl}" alt="Kurumsal Logo" style="max-height: 55px; max-width: 220px; object-fit: contain;" /></div>` : `<div style="font-size: ${fSize}; font-weight: 900; color: ${color}; letter-spacing: 0.5px;">🪐 RECOrion</div>`}
  <div style="font-size: 13px; color: #a78bfa; margin-top: 5px; font-weight: 600;">${b.subtitle || 'Yapay Zeka Destekli Kurumsal İşletim Sistemi'}</div>
</div>`;
    }
  },
  {
    type: 'IMAGE',
    label: 'Özel Görsel / Logo / Banner',
    imageUrl: '',
    caption: '',
    renderHtml: (b) => b.imageUrl ? `<div style="padding: 15px 25px; background: #0b0f19; text-align: center;">
  <img src="${b.imageUrl}" alt="${b.caption || 'Görsel'}" style="max-width: 100%; max-height: 250px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); object-fit: contain;" />
  ${b.caption ? `<div style="font-size: 11px; color: #94a3b8; margin-top: 6px;">${b.caption}</div>` : ''}
</div>` : ''
  },
  {
    type: 'GREETING',
    label: 'Karşılama Metni',
    text: 'Sayın <b>{{company_name}}</b> Yetkilisi, Sayın <b>{{contact_name}}</b>,',
    bgColor: '#0b0f19',
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    fontSize: '15px',
    textColor: '#f1f5f9',
    renderHtml: (b) => {
      const bg = b.bgColor || '#0b0f19';
      const font = b.fontFamily || "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
      const fSize = b.fontSize || '15px';
      const color = b.textColor || '#f1f5f9';
      return `<div style="padding: 22px 25px 12px 25px; background: ${bg}; color: ${color}; font-size: ${fSize}; font-family: ${font}; line-height: 1.6;">
  <p style="margin: 0;">${b.text || 'Sayın <b>{{company_name}}</b> Yetkilisi,'}</p>
</div>`;
    }
  },
  {
    type: 'CONTENT',
    label: 'Açıklama / Duyuru Paragrafı (Body)',
    text: 'RECOrion kurumsal aboneliğiniz başarıyla aktif edilmiştir. Kurumunuza özel olarak hazırlanan yapay zeka ajanları ve şirket çalışma ortamınız hazır durumdadır.',
    bgColor: '#0b0f19',
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    fontSize: '14px',
    textColor: '#cbd5e1',
    imageUrl: '',
    renderHtml: (b) => {
      const bg = b.bgColor || '#0b0f19';
      const font = b.fontFamily || "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
      const fSize = b.fontSize || '14px';
      const color = b.textColor || '#cbd5e1';
      const imgHtml = b.imageUrl ? `<div style="text-align: center; margin-top: 12px;"><img src="${b.imageUrl}" alt="Body Görseli" style="max-width: 100%; max-height: 220px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); object-fit: contain;" /></div>` : '';
      return `<div style="padding: 10px 25px 15px 25px; background: ${bg}; color: ${color}; font-size: ${fSize}; font-family: ${font}; line-height: 1.7;">
  <p style="margin: 0;">${b.text || ''}</p>
  ${imgHtml}
</div>`;
    }
  },
  {
    type: 'PACKAGE_INFO',
    label: 'Paket & Süre Özeti',
    planName: '{{plan_name}}',
    expiryDate: '{{package_expiry_date}}',
    daysRemaining: '{{days_remaining}}',
    renderHtml: (b) => `<div style="padding: 15px 25px; background: #0b0f19;">
  <div style="background: rgba(113, 52, 226, 0.12); border: 1px solid rgba(113, 52, 226, 0.35); border-radius: 10px; padding: 18px 20px;">
    <div style="font-size: 12px; font-weight: 800; color: #a78bfa; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;">📦 Kurumsal Abonelik Özeti</div>
    <table style="width: 100%; border-collapse: collapse; font-size: 13px; color: #e2e8f0;">
      <tr>
        <td style="padding: 5px 0; color: #94a3b8;">Tanımlanan Paket:</td>
        <td style="padding: 5px 0; text-align: right; font-weight: 800; color: #38bdf8;">${b.planName || '{{plan_name}}'}</td>
      </tr>
      <tr>
        <td style="padding: 5px 0; color: #94a3b8;">Paket Bitiş Tarihi:</td>
        <td style="padding: 5px 0; text-align: right; font-weight: 700; color: #34d399;">${b.expiryDate || '{{package_expiry_date}}'}</td>
      </tr>
      <tr>
        <td style="padding: 5px 0; color: #94a3b8;">Kalan Kullanım Süresi:</td>
        <td style="padding: 5px 0; text-align: right; font-weight: 700; color: #fbbf24;">${b.daysRemaining || '{{days_remaining}}'} Gün</td>
      </tr>
    </table>
  </div>
</div>`
  },
  {
    type: 'CREDENTIALS',
    label: 'Yönetici Giriş Bilgileri Kartı',
    loginEmail: '{{login_email}}',
    passwordText: '{{password_instruction}}',
    renderHtml: (b) => `<div style="padding: 15px 25px; background: #0b0f19;">
  <div style="background: rgba(14, 165, 233, 0.1); border: 1px solid rgba(14, 165, 233, 0.3); border-radius: 10px; padding: 18px 20px;">
    <div style="font-size: 12px; font-weight: 800; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;">🔐 Yönetici Giriş Bilgileri</div>
    <table style="width: 100%; border-collapse: collapse; font-size: 13px; color: #e2e8f0;">
      <tr>
        <td style="padding: 5px 0; color: #94a3b8;">Kullanıcı E-Posta:</td>
        <td style="padding: 5px 0; text-align: right; font-family: monospace; font-weight: 700; color: #ffffff;">${b.loginEmail || '{{login_email}}'}</td>
      </tr>
      <tr>
        <td style="padding: 5px 0; color: #94a3b8;">Şifre:</td>
        <td style="padding: 5px 0; text-align: right; font-family: monospace; font-weight: 700; color: #fbbf24;">${b.passwordText || '{{password_instruction}}'}</td>
      </tr>
    </table>
  </div>
</div>`
  },
  {
    type: 'BUTTON',
    label: 'Aksiyon Butonu (CTA)',
    buttonText: 'Yönetim Paneline Giriş Yap →',
    buttonUrl: '{{login_url}}',
    renderHtml: (b) => `<div style="padding: 20px 25px; background: #0b0f19; text-align: center;">
  <a href="${b.buttonUrl || '{{login_url}}'}" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #7134e2 0%, #146ceb 100%); color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 800; padding: 13px 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(113, 52, 226, 0.4);">
    ${b.buttonText || 'Panele Giriş Yap →'}
  </a>
</div>`
  },
  {
    type: 'DIVIDER',
    label: 'Ayırıcı Çizgi',
    renderHtml: () => `<div style="padding: 10px 25px; background: #0b0f19;">
  <hr style="border: none; height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent); margin: 0;" />
</div>`
  },
  {
    type: 'FOOTER',
    label: 'Kurumsal Alt Bilgi & İmza',
    footerText: 'Bu e-posta RECDx Bilişim Teknolojileri ve Yapay Zeka A.Ş. tarafından otomatik olarak iletilmiştir. Destek için info@recdx.com adresiyle iletişime geçebilirsiniz.',
    bgColor: '#060911',
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    fontSize: '11px',
    textColor: '#64748b',
    imageUrl: '',
    renderHtml: (b) => {
      const bg = b.bgColor || '#060911';
      const font = b.fontFamily || "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
      const fSize = b.fontSize || '11px';
      const color = b.textColor || '#64748b';
      const imgHtml = b.imageUrl ? `<div style="text-align: center; margin-bottom: 12px;"><img src="${b.imageUrl}" alt="Footer Görseli" style="max-height: 48px; max-width: 200px; object-fit: contain;" /></div>` : '';
      return `<div style="padding: 25px; background: ${bg}; border-radius: 0 0 12px 12px; border-top: 1px solid rgba(255,255,255,0.06); text-align: center; color: ${color}; font-size: ${fSize}; font-family: ${font}; line-height: 1.6;">
  ${imgHtml}
  <div style="font-weight: 700; color: #94a3b8; margin-bottom: 4px;">RECDx Bilişim Teknolojileri ve Yapay Zeka A.Ş.</div>
  <div>${b.footerText}</div>
  <div style="margin-top: 8px; color: #475569;">© 2026 RECOrion. Tüm Hakları Saklıdır.</div>
</div>`;
    }
  },
  {
    type: 'HEADING',
    label: 'Başlık',
    text: 'Başlık metni',
    textColor: '#ffffff',
    fontSize: '20px',
    align: 'left',
    renderHtml: (b) => `<div style="padding: 20px 25px 6px 25px; background: #0b0f19; text-align: ${b.align || 'left'};">
  <h2 style="margin: 0; font-size: ${b.fontSize || '20px'}; font-weight: 800; color: ${b.textColor || '#ffffff'}; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">${b.text || ''}</h2>
</div>`
  },
  {
    type: 'CODE_BOX',
    label: 'Doğrulama Kodu Kutusu',
    code: '{{code}}',
    note: 'Kod 10 dakika geçerlidir. Bu işlemi siz başlatmadıysanız e-postayı dikkate almayın.',
    renderHtml: (b) => `<div style="padding: 15px 25px; background: #0b0f19; text-align: center;">
  <div style="display: inline-block; padding: 14px 28px; border-radius: 10px; background: rgba(113, 52, 226, 0.15); border: 1px dashed rgba(167, 139, 250, 0.6); font-family: 'Courier New', monospace; font-size: 30px; font-weight: 800; letter-spacing: 8px; color: #ffffff;">${b.code || '{{code}}'}</div>
  ${b.note ? `<div style="font-size: 12px; color: #94a3b8; margin-top: 10px; font-family: 'Segoe UI', Tahoma, sans-serif;">${b.note}</div>` : ''}
</div>`
  },
  {
    type: 'INFO_BOX',
    label: 'Bilgi / Uyarı Kutusu',
    text: 'Önemli bilgi metni',
    tone: 'info',
    renderHtml: (b) => {
      const tones = {
        info: ['rgba(14,165,233,0.1)', 'rgba(14,165,233,0.35)', '#7dd3fc'],
        warning: ['rgba(245,158,11,0.1)', 'rgba(245,158,11,0.4)', '#fcd34d'],
        success: ['rgba(16,185,129,0.1)', 'rgba(16,185,129,0.4)', '#6ee7b7'],
        danger: ['rgba(239,68,68,0.1)', 'rgba(239,68,68,0.4)', '#fca5a5'],
      };
      const [bg, border, color] = tones[b.tone] || tones.info;
      return `<div style="padding: 12px 25px; background: #0b0f19;">
  <div style="background: ${bg}; border: 1px solid ${border}; border-radius: 10px; padding: 14px 18px; color: ${color}; font-size: 13px; line-height: 1.6; font-family: 'Segoe UI', Tahoma, sans-serif;">${b.text || ''}</div>
</div>`;
    }
  },
  {
    type: 'HTML',
    label: 'Serbest HTML Bölümü',
    html: '<p style="margin: 0; color: #cbd5e1;">HTML içerik</p>',
    renderHtml: (b) => `<div style="padding: 10px 25px; background: #0b0f19; color: #cbd5e1; font-family: 'Segoe UI', Tahoma, sans-serif; font-size: 14px; line-height: 1.6;">
${b.html || ''}
</div>`
  }
];

export function compileBlocksToHtml(blocks) {
  const inner = blocks.map(b => {
    const preset = EMAIL_PRESET_BLOCKS.find(p => p.type === b.type);
    return preset ? preset.renderHtml(b) : '';
  }).filter(Boolean).join('\n');

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RECOrion Kurumsal Bildirim</title>
</head>
<body style="margin: 0; padding: 30px 15px; background-color: #030712; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
  <div style="max-width: 620px; margin: 0 auto; background: #0b0f19; border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 10px 40px rgba(0,0,0,0.6);">
${inner}
  </div>
</body>
</html>`;
}

/** Blok türlerinin düzenleyicide gösterilen alanları. */
const STYLE_FIELDS = [
  { key: 'textColor', label: 'Yazı rengi', kind: 'color' },
  { key: 'bgColor', label: 'Arka plan', kind: 'color' },
  { key: 'fontSize', label: 'Yazı boyutu', kind: 'select', options: ['11px', '12px', '13px', '14px', '15px', '16px', '18px', '20px', '24px', '26px', '30px'] },
];
export const BLOCK_FIELDS = {
  HEADER: [{ key: 'subtitle', label: 'Alt başlık', kind: 'text' }, { key: 'logoUrl', label: 'Logo adresi (URL)', kind: 'text' }, ...STYLE_FIELDS],
  IMAGE: [{ key: 'imageUrl', label: 'Görsel adresi (URL)', kind: 'text' }, { key: 'caption', label: 'Açıklama', kind: 'text' }],
  HEADING: [
    { key: 'text', label: 'Başlık', kind: 'text' },
    { key: 'align', label: 'Hizalama', kind: 'select', options: ['left', 'center'] },
    { key: 'textColor', label: 'Yazı rengi', kind: 'color' },
    { key: 'fontSize', label: 'Yazı boyutu', kind: 'select', options: ['16px', '18px', '20px', '24px', '28px'] },
  ],
  GREETING: [{ key: 'text', label: 'Karşılama metni', kind: 'textarea' }, ...STYLE_FIELDS],
  CONTENT: [{ key: 'text', label: 'Paragraf', kind: 'textarea' }, { key: 'imageUrl', label: 'Görsel adresi (isteğe bağlı)', kind: 'text' }, ...STYLE_FIELDS],
  CODE_BOX: [{ key: 'code', label: 'Kod (değişken)', kind: 'text' }, { key: 'note', label: 'Not', kind: 'textarea' }],
  INFO_BOX: [{ key: 'text', label: 'Metin', kind: 'textarea' }, { key: 'tone', label: 'Tür', kind: 'select', options: ['info', 'warning', 'success', 'danger'] }],
  PACKAGE_INFO: [{ key: 'planName', label: 'Paket', kind: 'text' }, { key: 'expiryDate', label: 'Bitiş tarihi', kind: 'text' }, { key: 'daysRemaining', label: 'Kalan gün', kind: 'text' }],
  CREDENTIALS: [{ key: 'loginEmail', label: 'Kullanıcı e-postası', kind: 'text' }, { key: 'passwordText', label: 'Şifre açıklaması (açık şifre yazmayın)', kind: 'text' }],
  BUTTON: [{ key: 'buttonText', label: 'Buton yazısı', kind: 'text' }, { key: 'buttonUrl', label: 'Bağlantı (URL veya değişken)', kind: 'text' }],
  DIVIDER: [],
  FOOTER: [{ key: 'footerText', label: 'Alt bilgi metni', kind: 'textarea' }, { key: 'imageUrl', label: 'Görsel adresi (isteğe bağlı)', kind: 'text' }, ...STYLE_FIELDS],
  HTML: [{ key: 'html', label: 'HTML', kind: 'code' }],
};
export const OPTION_LABELS = { left: 'Sola', center: 'Ortaya', info: 'Bilgi', warning: 'Uyarı', success: 'Başarılı', danger: 'Kritik' };

let seq = 0;
export const newBlockId = () => `b_${Date.now().toString(36)}_${(seq += 1).toString(36)}`;

export function createBlock(type) {
  const preset = EMAIL_PRESET_BLOCKS.find((p) => p.type === type);
  if (!preset) return null;
  const defaults = Object.fromEntries(Object.entries(preset).filter(([k]) => k !== 'renderHtml' && k !== 'label'));
  return { ...defaults, id: newBlockId(), type };
}

/** Bloğun tuvalde görünen kısa özeti (HTML etiketleri olmadan). */
export function blockSummary(b) {
  const text = b.text || b.subtitle || b.buttonText || b.footerText || b.caption || b.code || b.html || b.planName || b.loginEmail || b.imageUrl || '';
  return String(text).replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 120);
}

/**
 * Kayıtlı HTML şablonunu düzenlenebilir bloklara çevirir. Tanınan öğeler (paragraf, başlık, buton,
 * görsel, ayırıcı) kendi bloğuna, diğerleri biçimi korunarak Serbest HTML bloğuna dönüşür.
 */
const CONTAINER = /^(DIV|TABLE|TBODY|THEAD|TFOOT|TR|TD|TH|CENTER|SECTION|ARTICLE|MAIN|HEADER|FOOTER)$/;
const BLOCK_CHILD = /^(P|H[1-6]|DIV|TABLE|TBODY|TR|TD|TH|UL|OL|HR|CENTER|SECTION|ARTICLE|HEADER|FOOTER|BLOCKQUOTE)$/;
const fontPx = (el) => Number((/font-size:\s*(\d+)px/i.exec(el.getAttribute('style') || '') || [])[1] || 0);

export function htmlToBlocks(html) {
  const doc = new DOMParser().parseFromString(html || '', 'text/html');
  const blocks = [];
  const add = (type, data) => blocks.push({ ...createBlock(type), ...data });

  // Yalnızca metin/satır içi öğe içeren yaprak kutu: başlık, buton, görsel, alt bilgi veya paragraf olur
  const leaf = (el) => {
    const text = el.textContent.trim();
    const only = el.children.length === 1 ? el.children[0] : null;
    const style = el.getAttribute('style') || '';
    if (!text && !el.querySelector('img')) return;
    if (only?.tagName === 'A' && text === only.textContent.trim()) {
      add('BUTTON', { buttonText: only.innerHTML.trim(), buttonUrl: only.getAttribute('href') || '' });
    } else if (only?.tagName === 'IMG' && !text) {
      add('IMAGE', { imageUrl: only.getAttribute('src') || '', caption: only.getAttribute('alt') || '' });
    } else if (/^\{\{\s*\w*code\w*\s*\}\}$/i.test(text)) {
      add('CODE_BOX', { code: text, note: '' }); // tek başına duran doğrulama kodu değişkeni
    } else if (blocks.length === 0 && /background/i.test(style) && text.length <= 40) {
      add('HEADER', {}); // marka başlık şeridi
    } else if (fontPx(el) >= 18 && text.length <= 90) {
      add('HEADING', { text: el.innerHTML.trim() });
    } else if (fontPx(el) && fontPx(el) <= 12 && /otomatik|©|gönderilmiştir|iletilmiştir/i.test(text)) {
      add('FOOTER', { footerText: el.innerHTML.trim() });
    } else {
      add('CONTENT', { text: el.innerHTML.trim() });
    }
  };

  const walk = (container) => {
    container.childNodes.forEach((node) => {
      if (node.nodeType === 3) {
        if (node.textContent.trim()) add('CONTENT', { text: node.textContent.trim() });
        return;
      }
      if (node.nodeType !== 1) return;
      const el = node;
      const tag = el.tagName;
      if (tag === 'STYLE' || tag === 'SCRIPT' || tag === 'META' || tag === 'TITLE') return;
      if (tag === 'P') add('CONTENT', { text: el.innerHTML.trim() });
      else if (/^H[1-6]$/.test(tag)) add('HEADING', { text: el.innerHTML.trim() });
      else if (tag === 'HR') add('DIVIDER', {});
      else if (tag === 'IMG') add('IMAGE', { imageUrl: el.getAttribute('src') || '', caption: el.getAttribute('alt') || '' });
      else if (tag === 'A') add('BUTTON', { buttonText: el.innerHTML.trim(), buttonUrl: el.getAttribute('href') || '' });
      else if (tag === 'UL' || tag === 'OL' || tag === 'BLOCKQUOTE') add('HTML', { html: el.outerHTML });
      else if (CONTAINER.test(tag)) {
        if ([...el.children].some((c) => BLOCK_CHILD.test(c.tagName))) walk(el); // iç içe düzen: içine in
        else leaf(el);
      } else if (el.textContent.trim()) add('CONTENT', { text: el.outerHTML });
    });
  };

  walk(doc.body);
  return blocks;
}
