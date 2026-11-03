// ============================================================
// 前端交互实验室 · 色彩令牌对比度断言
// 用法：node tools/contrast.mjs
// ------------------------------------------------------------
// 为什么需要它：axe 对「渐变背景 / 半透明叠色」上的文字只会报 incomplete
// （needs review），不报 violation。实测被 axe 漏掉的有：
//   .btn-primary 玻璃叠白底 3.90、.toast-trigger 三态 2.54/2.17/3.19、
//   .e4 白字 3.39、.s1 渐变最亮停靠点 1.94。
// 所以本脚本是判定「是否真的达标」的唯一权威，axe 只作补充。
//
// 覆盖 8 个上下文：明/暗 × orange/cyan/violet/lime
// 断言分组见 GROUPS，阈值语义：
//   - 文字类 4.5:1（WCAG AA 正文）
//   - 按钮轮廓 3:1（WCAG 1.4.11 非文本对比）
//
// 退出码：任一硬性断言失败 → 1
// ============================================================

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');
const srcPath = path.join(root, 'src/lab.html');

/* ---------- 颜色工具 ---------- */
function parseColor(str) {
    if (!str) return null;
    const s = str.trim();
    let m = /^#([0-9a-f]{6})$/i.exec(s);
    if (m) {
        return {
            r: parseInt(m[1].slice(0, 2), 16),
            g: parseInt(m[1].slice(2, 4), 16),
            b: parseInt(m[1].slice(4, 6), 16),
            a: 1,
        };
    }
    m = /^#([0-9a-f]{3})$/i.exec(s);
    if (m) {
        const [r, g, b] = m[1].split('').map((c) => parseInt(c + c, 16));
        return { r, g, b, a: 1 };
    }
    m = /^rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)$/i.exec(s);
    if (m) {
        return { r: +m[1], g: +m[2], b: +m[3], a: m[4] === undefined ? 1 : +m[4] };
    }
    return null;
}

const toHex = (c) => '#' + [c.r, c.g, c.b].map((v) => Math.round(v).toString(16).padStart(2, '0')).join('').toUpperCase();

/* 半透明前景叠在不透明底上 —— 取「最坏情况」近似 */
function composite(fg, bg) {
    if (!fg) return bg;
    if (fg.a >= 1) return fg;
    return {
        r: fg.r * fg.a + bg.r * (1 - fg.a),
        g: fg.g * fg.a + bg.g * (1 - fg.a),
        b: fg.b * fg.a + bg.b * (1 - fg.a),
        a: 1,
    };
}

function luminance(c) {
    const ch = [c.r, c.g, c.b].map((v) => v / 255).map((v) => (v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)));
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2];
}

function ratio(fg, bg) {
    const a = luminance(fg);
    const b = luminance(bg);
    return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}

/* ---------- 从 src/lab.html 抽令牌 ---------- */
const html = fs.readFileSync(srcPath, 'utf8');

function extractBlock(selector) {
    const start = html.indexOf(selector + '{');
    if (start === -1) return null;
    const open = html.indexOf('{', start);
    let depth = 0;
    for (let i = open; i < html.length; i += 1) {
        if (html[i] === '{') depth += 1;
        else if (html[i] === '}') {
            depth -= 1;
            if (depth === 0) return html.slice(open + 1, i);
        }
    }
    return null;
}

function parseTokens(block) {
    const out = {};
    if (!block) return out;
    // 值末尾的分号可有可无：块内最后一个声明常常没有分号（例如暗色盘的 --accent-soft）
    const re = /--([a-z0-9-]+)\s*:\s*([^;{}]+)/gi;
    let m;
    while ((m = re.exec(block)) !== null) {
        const val = m[2].trim();
        const col = parseColor(val);
        if (col) out[m[1]] = { raw: val, color: col };
    }
    return out;
}

const base = parseTokens(extractBlock(':root'));
if (!base['bg']) {
    console.error('✗ 未能从 :root 解析出 --bg，脚本需要同步更新');
    process.exit(1);
}

const darkBlock = parseTokens(extractBlock('html[data-theme="dark"]'));
const accents = ['orange', 'cyan', 'violet', 'lime'];
const accentLight = {};
const accentDark = {};
accents.forEach((a) => {
    accentLight[a] = a === 'orange' ? {} : parseTokens(extractBlock(`html[data-accent="${a}"]`));
    accentDark[a] = a === 'orange' ? {} : parseTokens(extractBlock(`html[data-theme="dark"][data-accent="${a}"]`));
});

/* 组装 8 个上下文；--bg 先解析出来作为合成底 */
function buildContext(theme, accent) {
    const merged = { ...base };
    if (theme === 'dark') Object.assign(merged, darkBlock);
    Object.assign(merged, accentLight[accent] || {});
    if (theme === 'dark') Object.assign(merged, accentDark[accent] || {});
    const bg = merged['bg'].color;
    // 其余令牌若为半透明，一律按最坏情况合成到 --bg 上
    const flat = {};
    Object.keys(merged).forEach((k) => { flat[k] = k === 'bg' ? bg : composite(merged[k].color, bg); });
    return { theme, accent, tokens: merged, flat, bg };
}

const contexts = [];
['light', 'dark'].forEach((t) => accents.forEach((a) => contexts.push(buildContext(t, a))));

/* ---------- 断言分组 ---------- */
// [标签, 前景令牌, 背景取值(令牌名或字面色), 阈值]
const HARDCODED = {
    '#ECE8DD': parseColor('#ECE8DD'), // .rail-link:hover 的合成底
    '#EFEBE0': parseColor('#EFEBE0'), // .jt-graph code 的合成底
};

const GROUPS = [
    {
        name: 'A 正文与次要文字',
        items: [
            ['ink × bg', 'ink', 'bg', 4.5],
            ['ink × panel', 'ink', 'panel', 4.5],
            ['ink-2 × bg', 'ink-2', 'bg', 4.5],
            ['ink-2 × panel', 'ink-2', 'panel', 4.5],
            ['ink-2 × accent-soft', 'ink-2', 'accent-soft', 4.5],
            ['ink-2 × #ECE8DD', 'ink-2', '#ECE8DD', 4.5],
            ['ink-2 × #EFEBE0', 'ink-2', '#EFEBE0', 4.5],
        ],
    },
    {
        name: 'B 强调文字',
        items: [
            ['accent-deep × bg', 'accent-deep', 'bg', 4.5],
            ['accent-deep × panel', 'accent-deep', 'panel', 4.5],
            ['accent-deep × accent-soft', 'accent-deep', 'accent-soft', 4.5],
            ['accent-deep × #EFEBE0', 'accent-deep', '#EFEBE0', 4.5],
        ],
    },
    {
        name: 'C 代码面板内文字',
        items: [
            ['code-ink × code-bg', 'code-ink', 'code-bg', 4.5],
            ['code-ink-2 × code-bg', 'code-ink-2', 'code-bg', 4.5],
            ['ok × code-bg', 'ok', 'code-bg', 4.5],
        ],
    },
    {
        name: 'D 实色按钮上的文字',
        items: [
            ['accent-btn-ink × accent-btn', 'accent-btn-ink', 'accent-btn', 4.5],
            ['accent-btn-ink × accent-btn-hover', 'accent-btn-ink', 'accent-btn-hover', 4.5],
            ['ok-btn-ink × ok-btn', 'ok-btn-ink', 'ok-btn', 4.5],
            ['err-btn-ink × err-btn', 'err-btn-ink', 'err-btn', 4.5],
            ['warn-btn-ink × warn-btn', 'warn-btn-ink', 'warn-btn', 4.5],
        ],
    },
    {
        name: 'E 按钮轮廓（非文本）',
        items: [
            ['accent-btn × bg', 'accent-btn', 'bg', 3],
            ['accent-btn × panel', 'accent-btn', 'panel', 3],
            ['accent-btn-hover × bg', 'accent-btn-hover', 'bg', 3],
            // 以下三项只提示：实心语义按钮靠文字识别，1.4.11 不要求填充本身与背景成比
            ['ok-btn × bg', 'ok-btn', 'bg', 0],
            ['err-btn × bg', 'err-btn', 'bg', 0],
            ['warn-btn × bg', 'warn-btn', 'bg', 0],
        ],
    },
];

let failures = 0;
const missing = [];

for (const ctx of contexts) {
    const label = `${ctx.theme}/${ctx.accent}`;
    console.log(`\n[${label}]  bg ${toHex(ctx.bg)}`);
    console.log('  断言                          前景      背景      比值   判定');
    for (const group of GROUPS) {
        for (const [name, fgKey, bgKey, min] of group.items) {
            const fgRaw = ctx.flat[fgKey];
            // #ECE8DD / #EFEBE0 是浅色主题下合成出来的底色，暗色主题不适用
            if (bgKey.startsWith('#') && ctx.theme === 'dark') continue;
            const bgRaw = bgKey.startsWith('#') ? HARDCODED[bgKey] : ctx.flat[bgKey];
            if (!fgRaw) { missing.push(`${label} 缺少令牌 --${fgKey}`); failures += 1; console.log(`  ${name.padEnd(30)} —         —         缺失   ✗ 未定义 --${fgKey}`); continue; }
            if (!bgRaw) { missing.push(`${label} 缺少令牌 --${bgKey}`); failures += 1; console.log(`  ${name.padEnd(30)} ${toHex(fgRaw)}  —         缺失   ✗ 未定义 --${bgKey}`); continue; }
            const r = ratio(fgRaw, bgRaw);
            if (min === 0) { console.log(`  ${name.padEnd(30)} ${toHex(fgRaw)}  ${toHex(bgRaw)}  ${r.toFixed(2).padStart(5)}   · 仅提示`); continue; }
            const ok = r >= min;
            if (!ok) failures += 1;
            console.log(`  ${name.padEnd(30)} ${toHex(fgRaw)}  ${toHex(bgRaw)}  ${r.toFixed(2).padStart(5)}   ${ok ? '✓' : '✗ <' + min}`);
            if (!ok) {
                const dir = min >= 4.5 ? '前景需更深（或背景更浅）' : '需提高与背景的明度差';
                console.log(`      ↳ ${dir}；目标 ≥ ${min}:1，当前差 ${(min - r).toFixed(2)}`);
            }
        }
    }
}

/* demo-29 的四套局部主题（--t-*），存在才校验 */
const themeBlocks = [...html.matchAll(/--t-accent-btn\s*:\s*(#[0-9a-fA-F]{6})[^;]*;\s*--t-accent-btn-ink\s*:\s*(#[0-9a-fA-F]{6})/g)];
if (themeBlocks.length) {
    console.log('\n[demo-29 局部主题]');
    themeBlocks.forEach(([, btn, ink], i) => {
        const r = ratio(parseColor(ink), parseColor(btn));
        const ok = r >= 4.5;
        if (!ok) failures += 1;
        console.log(`  第 ${i + 1} 套  ${ink} on ${btn}  ${r.toFixed(2).padStart(5)}   ${ok ? '✓' : '✗ <4.5'}`);
    });
}

console.log('\n────────────────────────────');
if (failures) {
    console.log(`  对比度断言失败 ${failures} 项`);
    if (missing.length) {
        console.log(`  其中缺令牌 ${missing.length} 项（多半是本轮尚未添加的 --accent-btn 系列）：`);
        [...new Set(missing)].slice(0, 8).forEach((m) => console.log('    · ' + m));
    }
    process.exit(1);
}
console.log('  对比度断言全部通过');
