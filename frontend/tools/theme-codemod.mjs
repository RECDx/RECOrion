// RECOrion tema dönüşümü: sabit renkleri CSS değişkenlerine çevirir.
// Kullanım: node theme-codemod.mjs <src_dir> [--write]
import fs from "node:fs";
import path from "node:path";
import { parse } from "@babel/parser";
import traverseMod from "@babel/traverse";

const traverse = traverseMod.default;
const SRC = process.argv[2];
const WRITE = process.argv.includes("--write");

// ---------------------------------------------------------------- renk sınıflandırma
const SLATE = [ // [hex, açık tema karşılığı]
  ["#f8fafc", "#0f172a"], ["#f1f5f9", "#1e293b"], ["#e2e8f0", "#1e293b"], ["#cbd5e1", "#334155"],
  ["#94a3b8", "#475569"], ["#64748b", "#5b6577"], ["#475569", "#94a3b8"], ["#334155", "#cbd5e1"],
  ["#1e293b", "#e2e8f0"], ["#0f172a", "#f1f5f9"],
];
const ACCENTS = {
  "#38bdf8": "#0284c7", "#34d399": "#059669", "#f87171": "#dc2626", "#fbbf24": "#b45309",
  "#c084fc": "#9333ea", "#818cf8": "#4f46e5", "#a78bfa": "#7c3aed", "#60a5fa": "#2563eb",
  "#fca5a5": "#b91c1c", "#6ee7b7": "#047857", "#a5b4fc": "#4338ca", "#4ade80": "#16a34a",
  "#93c5fd": "#1d4ed8", "#d8b4fe": "#7e22ce", "#c7d2fe": "#3730a3", "#22d3ee": "#0891b2",
  "#fde68a": "#92400e", "#fcd34d": "#a16207", "#86efac": "#15803d", "#7dd3fc": "#0369a1",
  "#f472b6": "#db2777", "#fb923c": "#c2410c", "#2dd4bf": "#0d9488", "#e879f9": "#c026d3",
};
// Doygun, açık arka planda da okunan renkler: dokunulmaz
const SATURATED_BG = /gradient|#7134e2|#146ceb|#314ccd|#1261cd|#10b981|#059669|#ef4444|#dc2626|#f59e0b|#d97706|#6366f1|#a855f7|#22c55e|#3b82f6|#0ea5e9|#8b5cf6|#e11d48|#f43f5e|#2563eb|#4f46e5|rgba?\(\s*(16|239|245|113|20|99|59|168|34|56),/i;

// Zemin yalnızca yarı saydam renklerden oluşuyorsa (açık temada zemin açık kalır) beyaz yazı da temaya uymalı
function isTranslucentOnly(bg) {
  if (/#[0-9a-f]{3,6}/i.test(bg) || /var\(--gradient/.test(bg)) return false;
  const alphas = [...bg.matchAll(/rgba\([^)]*,\s*([0-9.]+)\s*\)/g)].map((m) => +m[1]);
  return alphas.length > 0 && alphas.every((a) => a <= 0.4);
}
const hexRe = /#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b/g;
const rgbaRe = /rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*([0-9.]+)\s*)?\)/g;

const toRgb = (hex) => {
  let h = hex.slice(1).toLowerCase();
  if (h.length === 3) h = h.split("").map((c) => c + c).join("");
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
};
const toHex = ([r, g, b]) => "#" + [r, g, b].map((v) => Math.round(v).toString(16).padStart(2, "0")).join("");
const norm = (hex) => toHex(toRgb(hex));
const lum = ([r, g, b]) => 0.2126 * r + 0.7152 * g + 0.0722 * b;
const isNeutral = (rgb) => Math.max(...rgb) - Math.min(...rgb) <= 40;

const tokens = new Map(); // name -> {dark, light}
// Önceki çalıştırmalardan kalan token'ları koru
{
  const prev = path.join(process.argv[2] || "", "theme", "palette.generated.css");
  if (fs.existsSync(prev)) {
    const txt = fs.readFileSync(prev, "utf8");
    const [darkPart, lightPart] = txt.split(':root[data-theme="light"]');
    const read = (part) => Object.fromEntries([...part.matchAll(/(--[a-z0-9-]+):\s*([^;]+);/g)].map((m) => [m[1], m[2].trim()]));
    const d = read(darkPart), l = read(lightPart || "");
    for (const k of Object.keys(d)) tokens.set(k, { dark: d[k], light: l[k] ?? d[k] });
  }
}
const addToken = (name, dark, light) => { if (!tokens.has(name)) tokens.set(name, { dark, light }); return `var(${name})`; };

function lightSurface(rgb) {
  // Koyu yüzeyleri açık temada beyaz/çok açık griye eşler (koyuluk sırası korunur)
  const v = Math.round(255 - lum(rgb) * 0.25);
  return toHex([v - 3, v - 1, v]);
}
function lightForNeutralText(rgb) {
  const l = lum(rgb);
  let best = SLATE[0];
  for (const s of SLATE) if (Math.abs(lum(toRgb(s[0])) - l) < Math.abs(lum(toRgb(best[0])) - l)) best = s;
  return best[1];
}

function mapHex(hex, key, allowWhite) {
  const h = norm(hex);
  const rgb = toRgb(h);
  if (ACCENTS[h]) return addToken(`--ac-${h.slice(1)}`, h, ACCENTS[h]);
  if (!isNeutral(rgb)) return null;
  const max = Math.max(...rgb);
  if (h === "#ffffff") {
    if (!allowWhite) return null;
    return addToken("--nt-ffffff", h, "#0f172a");
  }
  if (max <= 60) {
    if (key === "color") return null; // parlak rozet üstündeki koyu yazı
    return addToken(`--sf-${h.slice(1)}`, h, lightSurface(rgb));
  }
  if (max >= 70) return addToken(`--nt-${h.slice(1)}`, h, lightForNeutralText(rgb));
  return null;
}

function mapRgba(r, g, b, a, key) {
  const alpha = a === undefined ? "1" : a;
  if (r === 255 && g === 255 && b === 255) {
    addToken("--rgb-ov", "255 255 255", "15 23 42");
    return `rgb(var(--rgb-ov) / ${alpha})`;
  }
  if (r === 0 && g === 0 && b === 0) {
    addToken("--rgb-shade", "0 0 0", "15 23 42");
    addToken("--shade-k", "1", "0.35");
    return `rgb(var(--rgb-shade) / calc(${alpha} * var(--shade-k)))`;
  }
  const rgb = [r, g, b];
  if (isNeutral(rgb) && Math.max(...rgb) <= 60 && key !== "color") {
    const name = `--rgb-sf-${toHex(rgb).slice(1)}`;
    const l = toRgb(lightSurface(rgb));
    addToken(name, `${r} ${g} ${b}`, `${l[0]} ${l[1]} ${l[2]}`);
    return `rgb(var(${name}) / ${alpha})`;
  }
  return null;
}

// Tek bir string değerini dönüştürür
function transformValue(text, key, allowWhite) {
  let changed = text.replace(rgbaRe, (m, r, g, b, a) => mapRgba(+r, +g, +b, a, key) ?? m);
  changed = changed.replace(hexRe, (m) => mapHex(m, key, allowWhite) ?? m);
  if (key === "color" && allowWhite) changed = changed.replace(/^white$/, addToken("--nt-ffffff", "#ffffff", "#0f172a"));
  return changed;
}

// ---------------------------------------------------------------- JSX dosyaları
const CSS_KEYS = /^(color|background|backgroundColor|backgroundImage|border|border(Top|Bottom|Left|Right)(Color)?|borderColor|boxShadow|outline|outlineColor|textShadow|fill|stroke|caretColor|accentColor|textDecorationColor|columnRule)$/;
const EXCLUDED_DECLS = new Set(["EMAIL_PRESET_BLOCKS", "compileBlocksToHtml"]);

function keyName(node) {
  if (!node) return null;
  if (node.type === "Identifier") return node.name;
  if (node.type === "StringLiteral") return node.value;
  return null;
}

function processJsx(file) {
  const code = fs.readFileSync(file, "utf8");
  const ast = parse(code, { sourceType: "module", plugins: ["jsx"], errorRecovery: false });
  const edits = [];
  let skipped = 0;

  const visit = (p, rawText, start, end) => {
    if (!hexRe.test(rawText) && !/rgba?\(/.test(rawText) && !/^['"`]white['"`]$/.test(rawText)) { hexRe.lastIndex = 0; return; }
    hexRe.lastIndex = 0;
    if (rawText.includes("<")) { skipped++; return; } // HTML (mail şablonu vb.)

    let key = null, inStyleAttr = false, styleObj = null, excluded = false, otherAttr = false, styleAssign = false;
    for (let q = p.parentPath; q; q = q.parentPath) {
      const n = q.node;
      if (!key && n.type === "ObjectProperty") { key = keyName(n.key); styleObj = q.parentPath?.node; }
      if (n.type === "JSXAttribute") {
        if (n.name.name === "style") inStyleAttr = true;
        else if (n.name.name === "color" && /^[A-Z]/.test(q.parentPath?.node?.name?.name || "")) { key = "stroke"; inStyleAttr = true; } // Lucide ikonları
        else otherAttr = true;
        break;
      }
      if (n.type === "AssignmentExpression" && n.left.type === "MemberExpression"
          && n.left.object.type === "MemberExpression" && n.left.object.property?.name === "style") {
        styleAssign = true; key = n.left.property?.name; break;
      }
      if ((n.type === "VariableDeclarator" && EXCLUDED_DECLS.has(n.id?.name))
          || (n.type === "FunctionDeclaration" && EXCLUDED_DECLS.has(n.id?.name))) { excluded = true; break; }
    }
    const why = excluded ? "email" : otherAttr ? "attr" : (!(inStyleAttr || styleAssign || (key && CSS_KEYS.test(key))) ? `key:${key}` : null);
    if (why) { skipped++; if (process.env.DEBUG_SKIP) console.error(`SKIP ${path.basename(file)}:${p.node.loc?.start.line} [${why}] ${rawText.slice(0,70)}`); return; }

    let allowWhite = false;
    if (key === "color") {
      const bgProp = styleObj?.properties?.find((pp) => /^background/.test(keyName(pp.key) || ""));
      const bgSrc = bgProp ? code.slice(bgProp.value.start, bgProp.value.end) : "";
      allowWhite = !SATURATED_BG.test(bgSrc) || isTranslucentOnly(bgSrc);
    }
    const quote = rawText[0];
    const inner = rawText.slice(1, -1);
    const out = transformValue(inner, key, allowWhite);
    if (out !== inner) edits.push([start, end, quote + out + quote]);
  };

  traverse(ast, {
    StringLiteral(p) {
      const { start, end } = p.node;
      visit(p, code.slice(start, end), start, end);
    },
    TemplateLiteral(p) {
      for (const q of p.node.quasis) {
        const raw = code.slice(q.start, q.end);
        if (!hexRe.test(raw) && !/rgba?\(/.test(raw)) { hexRe.lastIndex = 0; continue; }
        hexRe.lastIndex = 0;
        // Şablon parçaları: tırnak yok; sahte tırnakla aynı mantığı kullan
        const whole = code.slice(p.node.start, p.node.end);
        if (whole.includes("<")) continue;
        const fake = { parentPath: p.parentPath, node: p.node };
        let captured = null;
        const origPush = edits.push.bind(edits);
        edits.push = (e) => { captured = e; };
        visit(fake, "`" + raw + "`", q.start - 1, q.end + 1);
        edits.push = origPush;
        if (captured) edits.push([q.start, q.end, captured[2].slice(1, -1)]);
      }
    },
  });

  edits.sort((a, b) => b[0] - a[0]);
  let outCode = code;
  for (const [s, e, t] of edits) outCode = outCode.slice(0, s) + t + outCode.slice(e);
  return { edits: edits.length, skipped, outCode, changed: outCode !== code };
}

// ---------------------------------------------------------------- CSS dosyaları
function processCss(file) {
  const css = fs.readFileSync(file, "utf8");
  let edits = 0;
  // :root bloğu (anlamsal token'lar) elle yönetilir; dokunma
  const out = css.replace(/([^{}]+)\{([^{}]*)\}/g, (block, selector, body) => {
    if (/^\s*:root\s*$/.test(selector) || selector.includes("@keyframes")) return block;
    const bg = (body.match(/background[^:]*:\s*([^;]+)/) || [])[1] || "";
    const allowWhite = !SATURATED_BG.test(bg);
    const newBody = body.replace(/([a-z-]+)\s*:\s*([^;]+)/g, (decl, prop, val) => {
      if (prop.startsWith("--")) return decl;
      const key = prop === "color" ? "color" : prop;
      const nv = transformValue(val, key, key === "color" && allowWhite);
      if (nv !== val) edits++;
      return `${prop}: ${nv}`;
    });
    return selector + "{" + newBody + "}";
  });
  return { edits, outCode: out, changed: out !== css };
}

// ---------------------------------------------------------------- çalıştır
const files = [path.join(SRC, "App.jsx"), ...fs.readdirSync(path.join(SRC, "components")).filter((f) => f.endsWith(".jsx")).map((f) => path.join(SRC, "components", f))];
let total = 0;
for (const f of files) {
  const r = processJsx(f);
  total += r.edits;
  console.log(`${path.basename(f)}: ${r.edits} değişiklik, ${r.skipped} atlandı`);
  if (WRITE && r.changed) fs.writeFileSync(f, r.outCode, "utf8");
}
const cssFile = path.join(SRC, "index.css");
const c = processCss(cssFile);
console.log(`index.css: ${c.edits} bildirim değişti`);
if (WRITE && c.changed) fs.writeFileSync(cssFile, c.outCode, "utf8");

// Token dosyası
const dark = [...tokens].map(([n, v]) => `  ${n}: ${v.dark};`).join("\n");
const light = [...tokens].map(([n, v]) => `  ${n}: ${v.light};`).join("\n");
const tokenCss = `/* OTOMATİK ÜRETİLDİ (theme-codemod) - bileşenlerdeki renklerin tema değişkenleri.
   Koyu tema değerleri dönüşüm öncesi renklerin aynısıdır. */
:root,
:root[data-theme="dark"] {
${dark}
}

:root[data-theme="light"] {
${light}
}
`;
console.log(`token sayısı: ${tokens.size}, toplam JSX değişikliği: ${total}`);
if (WRITE) fs.writeFileSync(path.join(SRC, "theme", "palette.generated.css"), tokenCss, "utf8");
else fs.writeFileSync(path.join(process.cwd(), "palette.preview.css"), tokenCss, "utf8");
