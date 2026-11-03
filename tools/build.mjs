// ============================================================
// 前端交互实验室 · 构建脚本
// 用法：node tools/build.mjs
// ------------------------------------------------------------
// 只做四件事，不做任何 minify / 美化 / DOM 改写：
//   1) 读 src/lab.html（UTF-8 原样读入，不做换行归一）
//   2) 在唯一的 </body> 前内联 inject.html（返回主页 + PV/UV 上报）
//   3) 写 dist/index.html，并拷贝 .nojekyll
//   4) 跑结构断言，任一失败 exit 1
//
// 为什么不压缩：构建期魔法会让 src 与线上不一致，排查成本立刻翻倍。
// 压缩交给 GitHub Pages 的 gzip。
// ============================================================

import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');
const SRС = path.join(root, 'src/lab.html');
const INJECT = path.join(root, 'inject.html');
const OUT_DIR = path.join(root, 'dist');
const OUT = path.join(OUT_DIR, 'index.html');

/* 演示总数：新增 demo 时只改这一处，断言失败信息会告诉你改哪 */
const DEMO_TOTAL = 54;
/* 体积预算（gzip -9） */
const BUDGET_RAW = 300 * 1024;
const BUDGET_GZIP = 75 * 1024;

const problems = [];
const notes = [];
const fail = (msg) => problems.push(msg);

/* ---------- 1. 读源 ---------- */
const src = fs.readFileSync(SRС, 'utf8');
const inject = fs.readFileSync(INJECT, 'utf8').trim();

/* ---------- 2. 内联 inject.html ---------- */
const bodyTags = (src.match(/<\/body>/g) || []).length;
if (bodyTags !== 1) {
    fail(`A2 </body> 出现 ${bodyTags} 次，应恰好 1 次（内联注入点必须唯一）`);
}
let html = src.replace('</body>', inject + '\n</body>');
notes.push(`已内联 inject.html（${(inject.length / 1024).toFixed(1)} KB）`);

/* ---------- 3. 写产物 ---------- */
fs.mkdirSync(OUT_DIR, { recursive: true });
fs.writeFileSync(OUT, html, 'utf8');
const nojekyll = path.join(root, '.nojekyll');
if (fs.existsSync(nojekyll)) fs.copyFileSync(nojekyll, path.join(OUT_DIR, '.nojekyll'));

/* ---------- 3b. SEO 基建：robots / sitemap / 404 ----------
   改前这三样都不存在（线上 404），搜索与分享基本没有抓手。
   单页站只有一个可索引 URL，但 robots + sitemap 仍是抓取入口的必要声明。 */
const SITE = 'https://kuntechnology.github.io/frontend-interaction-lab/';
const today = new Date().toISOString().slice(0, 10);

fs.writeFileSync(path.join(OUT_DIR, 'robots.txt'),
    `User-agent: *\nAllow: /\n\nSitemap: ${SITE}sitemap.xml\n`, 'utf8');

fs.writeFileSync(path.join(OUT_DIR, 'sitemap.xml'),
    `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url>\n    <loc>${SITE}</loc>\n    <lastmod>${today}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>\n</urlset>\n`, 'utf8');

/* 404：GitHub Pages 会对任意不存在路径返回它，给一个回主站的出口而不是空白页 */
fs.writeFileSync(path.join(OUT_DIR, '404.html'),
    `<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<title>页面不存在 · 前端交互实验室</title>\n<style>html,body{margin:0;height:100%;background:#141210;color:#f2efe8;font:15px/1.7 system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;display:flex;align-items:center;justify-content:center}\ndiv{text-align:center;padding:24px}\nh1{font-size:19px;margin:0 0 10px;font-weight:600}\np{margin:0 0 18px;color:#b9b3a6;font-size:13.5px}\na{color:#f2efe8;border:1px solid rgba(255,255,255,.28);border-radius:8px;padding:8px 16px;text-decoration:none;font-size:13.5px}\na:hover{border-color:rgba(255,255,255,.55)}</style>\n</head>\n<body><div><h1>这个地址没有内容</h1><p>演示可能已重命名，或者链接输错了。</p><a href="/frontend-interaction-lab/">回到实验室首页</a></div></body>\n</html>\n`, 'utf8');
notes.push('已生成 robots.txt / sitemap.xml / 404.html');

/* ---------- 4. 断言 ---------- */
const count = (re) => (html.match(re) || []).length;

// A1 起止完整
if (!html.startsWith('<!DOCTYPE html>') && !html.startsWith('<!doctype html>')) {
    fail('A1 产物未以 <!DOCTYPE html> 开头');
}
if (html.lastIndexOf('</html>') < html.length - 40) {
    fail('A1 </html> 不在文件末尾 40 字符内，疑似被截断');
}

// A2 结构标签各一次（注意 <head[\s>] 不能写成 <head，否则会把 <header> 也数进去）
[['<html[\\s>]', 1], ['<head[\\s>]', 1], ['</head>', 1], ['<body[\\s>]', 1], ['</body>', 1], ['</html>', 1]]
    .forEach(([tag, n]) => {
        const got = count(new RegExp(tag, 'g'));
        if (got !== n) fail(`A2 ${tag} 出现 ${got} 次，应为 ${n} 次`);
    });

// A3 标签闭合平衡
[['style'], ['script'], ['section'], ['main'], ['footer']].forEach(([tag]) => {
    const open = count(new RegExp('<' + tag + '[\\s>]', 'g'));
    const close = count(new RegExp('</' + tag + '>', 'g'));
    if (open !== close) fail(`A3 <${tag}> 开 ${open} / 闭 ${close} 不匹配`);
});

// A4 标题
const title = (/<title>([\s\S]*?)<\/title>/.exec(html) || [])[1] || '';
if (!title.trim()) fail('A4 缺少 <title>');
if (title.includes('加载中')) fail('A4 title 仍是外壳占位文案「加载中」');
notes.push(`title: ${title.trim()}`);

// A5 描述
const desc = (/<meta\s+name="description"\s+content="([^"]*)"/.exec(html) || [])[1] || '';
if (desc.length < 40 || desc.length > 220) fail(`A5 meta description 长度 ${desc.length}，应在 40–220`);

// A6 演示计数与连续性
const demoIds = [...html.matchAll(/id="demo-(\d{2})"/g)].map((m) => m[1]);
const uniqIds = [...new Set(demoIds)].sort();
if (uniqIds.length !== DEMO_TOTAL) {
    fail(`A6 演示 ${uniqIds.length} 个，DEMO_TOTAL=${DEMO_TOTAL}。新增/删除 demo 时同步 tools/build.mjs 的 DEMO_TOTAL`);
}
const expected = Array.from({ length: uniqIds.length }, (_, i) => String(i + 1).padStart(2, '0'));
const missing = expected.filter((n) => !uniqIds.includes(n));
if (missing.length) fail(`A6 演示编号不连续，缺 ${missing.join(', ')}`);

// A7 id 唯一
const allIds = [...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]);
const dupIds = allIds.filter((v, i) => allIds.indexOf(v) !== i);
if (dupIds.length) fail(`A7 id 重复: ${[...new Set(dupIds)].slice(0, 8).join(', ')}`);

// A8 每个 demo 的结构契约
const demoBlocks = [...html.matchAll(/<section class="demo"[\s\S]*?<\/section>/g)].map((m) => m[0]);
if (demoBlocks.length !== uniqIds.length) {
    fail(`A8 匹配到 ${demoBlocks.length} 个 demo 区块，但 id 有 ${uniqIds.length} 个`);
}
let badStructure = 0;
demoBlocks.forEach((b) => {
    const hasHead = /class="demo-head"/.test(b);
    const hasH3 = /<h3>/.test(b);
    const hasStage = /class="stage/.test(b);
    const hasPrompt = /class="prompt/.test(b);
    if (!(hasHead && hasH3 && hasStage && hasPrompt)) badStructure += 1;
});
if (badStructure) fail(`A8 有 ${badStructure} 个 demo 缺少 .demo-head / h3 / .stage / .prompt 之一`);

// A9 目录与锚点双向对应
const railHrefs = [...html.matchAll(/class="rail-link" href="#(demo-\d{2})"/g)].map((m) => m[1]);
const railSet = new Set(railHrefs);
const demoSet = new Set(uniqIds.map((n) => 'demo-' + n));
const railOrphan = [...railSet].filter((h) => !demoSet.has(h));
const demoNoRail = [...demoSet].filter((h) => !railSet.has(h));
if (railOrphan.length) fail(`A9 目录链接指向不存在的 demo: ${railOrphan.slice(0, 6).join(', ')}`);
if (demoNoRail.length) fail(`A9 有 ${demoNoRail.length} 个 demo 没有目录入口: ${demoNoRail.slice(0, 6).join(', ')}`);

// A10 Baseline 标注合法且覆盖完整
const baselineVals = [...html.matchAll(/<section class="demo"[^>]*data-baseline="([^"]+)"/g)].map((m) => m[1]);
const allowedBaseline = ['widely', 'newly', 'limited', 'na'];
if (baselineVals.length !== uniqIds.length) {
    fail(`A10 有 ${uniqIds.length - baselineVals.length} 个 demo 缺少 data-baseline`);
}
const badBaseline = baselineVals.filter((v) => !allowedBaseline.includes(v));
if (badBaseline.length) fail(`A10 非法 data-baseline 值: ${[...new Set(badBaseline)].join(', ')}`);
// 只数 demo 头部里的徽标（图例里也有同样 class，不能直接数 class）
const badgeCount = count(/<\/h3><span class="bl-badge bl-/g);
const naCount = baselineVals.filter((v) => v === 'na').length;
if (badgeCount !== uniqIds.length - naCount) {
    fail(`A10 徽标 ${badgeCount} 个，应为非 na 的 ${uniqIds.length - naCount} 个`);
}
const bDist = allowedBaseline.map((v) => `${v} ${baselineVals.filter((x) => x === v).length}`).join(' / ');
notes.push(`Baseline 分布: ${bDist}`);

// A14 代码切片覆盖面（「复制代码」按 /* ===== NN 注释切段，没有注释就切不出来）
const styleRegion = (() => {
    const i = html.indexOf('/* ===== 01 ');
    if (i === -1) return '';
    const s = html.lastIndexOf('<style', i);
    const e = html.indexOf('</style>', i);
    return html.slice(s, e);
})();
const scriptRegion = (() => {
    const i = html.indexOf('function copyText');
    if (i === -1) return '';
    const s = html.lastIndexOf('<script', i);
    const e = html.indexOf('</' + 'script>', i);
    return html.slice(s, e);
})();
const cssDemos = uniqIds.filter((n) => styleRegion.includes('/* ===== ' + n + ' ')).length;
const jsDemos = uniqIds.filter((n) => scriptRegion.includes('/* ===== ' + n + ' ')).length;
notes.push(`代码切片覆盖: CSS ${cssDemos}/${uniqIds.length} · JS ${jsDemos}/${uniqIds.length}`);
if (cssDemos < 29) fail(`A14 可切片的 CSS 跌到 ${cssDemos} 个（基线 29），复制代码功能退化`);
if (jsDemos < 46) fail(`A14 可切片的 JS 跌到 ${jsDemos} 个（基线 46），复制代码功能退化`);

// A11 外部依赖快照
const snapshot = JSON.parse(fs.readFileSync(path.join(root, 'tools/deps.snapshot.json'), 'utf8')).urls;
const liveUrls = [...new Set(html.match(/https?:\/\/[^\s"'<>)]+/g) || [])].sort();
const added = liveUrls.filter((u) => !snapshot.includes(u));
const removed = snapshot.filter((u) => !liveUrls.includes(u));
if (added.length) fail(`A11 出现未登记的外部 URL: ${added.join(', ')}（确认后更新 tools/deps.snapshot.json）`);
if (removed.length) fail(`A11 快照里的 URL 已不存在: ${removed.join(', ')}（确认后更新快照）`);

// A12 切换残留
if (/\bparts\//.test(html)) fail('A12 产物仍引用 parts/');
if (/document\.write/.test(html)) fail('A12 产物仍含 document.write');
if (count(/id="home-link"/g) !== 1) fail('A12 #home-link 应恰好 1 个（inject.html 未正确内联或重复）');

// A13 体积预算（按 UTF-8 字节算——中文页面的字符串长度远小于字节数，用 length 会低估）
const rawBytes = Buffer.byteLength(html, 'utf8');
const gzipSize = zlib.gzipSync(Buffer.from(html, 'utf8'), { level: 9 }).length;
if (rawBytes > BUDGET_RAW) fail(`A13 raw ${(rawBytes / 1024).toFixed(1)}KB 超出预算 ${BUDGET_RAW / 1024}KB`);
if (gzipSize > BUDGET_GZIP) fail(`A13 gzip ${(gzipSize / 1024).toFixed(1)}KB 超出预算 ${BUDGET_GZIP / 1024}KB`);

/* ---------- 报告 ---------- */
console.log('构建产物:', path.relative(root, OUT));
notes.forEach((n) => console.log('  · ' + n));
console.log(`  · demo ${uniqIds.length} 个 / 目录链接 ${railSet.size} 个`);
console.log(`  · raw ${(rawBytes / 1024).toFixed(1)} KB / gzip ${(gzipSize / 1024).toFixed(1)} KB`);

if (problems.length) {
    console.error('\n断言失败 ' + problems.length + ' 项:');
    problems.forEach((p) => console.error('  ✗ ' + p));
    process.exit(1);
}
console.log('\n全部断言通过');
