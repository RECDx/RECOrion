// RECOrion responsive dönüşümü: satır içi ızgara ve sabit genişlikleri ekrana uyumlu hale getirir.
// Kullanım: node layout-codemod.mjs <src_dir> [--write]
import fs from "node:fs";
import path from "node:path";
import { parse } from "@babel/parser";
import traverseMod from "@babel/traverse";

const traverse = traverseMod.default;
const SRC = process.argv[2];
const WRITE = process.argv.includes("--write");

function topLevelTokens(v) {
  const out = []; let depth = 0, cur = "";
  for (const ch of v.trim()) {
    if (ch === "(") depth++;
    if (ch === ")") depth--;
    if (ch === " " && depth === 0) { if (cur) out.push(cur); cur = ""; } else cur += ch;
  }
  if (cur) out.push(cur);
  return out;
}

function gridClass(v) {
  if (/auto-(fit|fill)/.test(v)) return null;
  const toks = topLevelTokens(v);
  let n = 0;
  for (const t of toks) {
    const m = /^repeat\((\d+)/.exec(t);
    n += m ? +m[1] : 1;
  }
  if (n === 2 && /^\d+px$/.test(toks[0]) && parseInt(toks[0]) <= 160) return null; // etiket/değer satırı
  if (n >= 3) return "ui-grid-3";
  if (n === 2) return "ui-grid-2";
  return null;
}

function processFile(file) {
  const code = fs.readFileSync(file, "utf8");
  const ast = parse(code, { sourceType: "module", plugins: ["jsx"] });
  const edits = [];
  const stats = { grids: 0, minmax: 0, widths: 0 };

  traverse(ast, {
    JSXOpeningElement(p) {
      const attrs = p.node.attributes;
      const style = attrs.find((a) => a.type === "JSXAttribute" && a.name.name === "style");
      if (!style || style.value?.type !== "JSXExpressionContainer" || style.value.expression.type !== "ObjectExpression") return;
      let cls = null;
      for (const prop of style.value.expression.properties) {
        if (prop.type !== "ObjectProperty") continue;
        const key = prop.key.name || prop.key.value;
        const val = prop.value;
        if (key === "gridTemplateColumns" && val.type === "StringLiteral") {
          if (/minmax\(\s*\d+px/.test(val.value)) {
            const nv = val.value.replace(/minmax\(\s*(\d+)px/g, "minmax(min(100%, $1px)");
            edits.push([val.start, val.end, `'${nv}'`]); stats.minmax++;
          }
          cls = gridClass(val.value) || cls;
        }
        if ((key === "width" && 1) || key === "minWidth") {
          const limit = key === "width" ? 340 : 300;
          if (val.type === "StringLiteral") {
            const m = /^(\d+)px$/.exec(val.value);
            if (m && +m[1] >= limit) { edits.push([val.start, val.end, `'min(100%, ${m[1]}px)'`]); stats.widths++; }
          } else if (val.type === "NumericLiteral" && val.value >= limit) {
            edits.push([val.start, val.end, `'min(100%, ${val.value}px)'`]); stats.widths++;
          }
        }
      }
      if (!cls) return;
      stats.grids++;
      const cn = attrs.find((a) => a.type === "JSXAttribute" && a.name.name === "className");
      if (!cn) {
        edits.push([style.start, style.start, `className="${cls}" `]);
      } else if (cn.value.type === "StringLiteral") {
        edits.push([cn.value.start, cn.value.end, JSON.stringify(`${cn.value.value} ${cls}`)]);
      } else if (cn.value.type === "JSXExpressionContainer") {
        const expr = code.slice(cn.value.expression.start, cn.value.expression.end);
        edits.push([cn.value.start, cn.value.end, `{\`\${${expr}} ${cls}\`}`]);
      }
    },
  });

  edits.sort((a, b) => b[0] - a[0] || b[1] - a[1]);
  let out = code;
  for (const [s, e, t] of edits) out = out.slice(0, s) + t + out.slice(e);
  return { stats, out, changed: out !== code };
}

const files = [path.join(SRC, "App.jsx"), ...fs.readdirSync(path.join(SRC, "components")).filter((f) => f.endsWith(".jsx")).map((f) => path.join(SRC, "components", f))];
for (const f of files) {
  const r = processFile(f);
  console.log(path.basename(f), JSON.stringify(r.stats));
  if (WRITE && r.changed) fs.writeFileSync(f, r.out, "utf8");
}
