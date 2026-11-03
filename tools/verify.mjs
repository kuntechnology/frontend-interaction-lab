// ============================================================
// 前端交互实验室 · 产物校验
// 用法：node tools/verify.mjs   （需先 node tools/build.mjs）
// ------------------------------------------------------------
// 与 build.mjs 的区别：build 校验「源」，verify 校验「dist 里那份字节」。
// 故意不复用 build 的中间变量——如果构建脚本本身写错了文件，这里能拦住。
// ============================================================

import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');
const dist = path.join(root, 'dist/index.html');

const fail = [];
const check = (name, ok, detail = '') => {
    if (!ok) fail.push(name + (detail ? '：' + detail : ''));
};

if (!fs.existsSync(dist)) {
    console.error('✗ dist/index.html 不存在，请先运行 node tools/build.mjs');
    process.exit(1);
}

const html = fs.readFileSync(dist, 'utf8');
const bytes = Buffer.byteLength(html, 'utf8');
const gzip = zlib.gzipSync(Buffer.from(html, 'utf8'), { level: 9 }).length;
const count = (re) => (html.match(re) || []).length;

// 1 体积
check('体积 raw ≤ 300KB', bytes <= 300 * 1024, `${(bytes / 1024).toFixed(1)}KB`);
check('体积 gzip ≤ 75KB', gzip <= 75 * 1024, `${(gzip / 1024).toFixed(1)}KB`);

// 2 结构完整
check('以 doctype 开头', /^<!DOCTYPE html>/i.test(html));
check('</html> 位于末尾', html.lastIndexOf('</html>') >= bytes - 40 || html.lastIndexOf('</html>') >= html.length - 40);

// 3 不再依赖运行时拼接
check('无 parts/ 引用', !/\bparts\//.test(html));
check('无 document.write', !/document\.write/.test(html));
check('无 fetch 分片', !/fetchBuf\(|fetch\('parts/.test(html));

// 4 内容完整（这是本次改造的核心收益：无 JS 也能读到全部内容）
const demos = new Set([...html.matchAll(/id="demo-(\d{2})"/g)].map((m) => m[1])).size;
check('demo 数量 ≥ 54', demos >= 54, `实际 ${demos}`);
check('有正文标题层级', count(/<h3>/g) >= demos, `h3 ${count(/<h3>/g)} 个 / demo ${demos} 个`);
check('有 noscript 或静态正文', /<section class="demo"/.test(html));

// 4b SEO 基建随产物一起发布
['robots.txt', 'sitemap.xml', '404.html'].forEach((f) => {
    check(`dist/${f} 存在`, fs.existsSync(path.join(root, 'dist', f)));
});

// 5 外部依赖与快照一致
const snapshot = JSON.parse(fs.readFileSync(path.join(root, 'tools/deps.snapshot.json'), 'utf8')).urls;
const urls = [...new Set(html.match(/https?:\/\/[^\s"'<>)]+/g) || [])].sort();
const added = urls.filter((u) => !snapshot.includes(u));
check('无未登记的外部 URL', added.length === 0, added.join(', '));

// 6 关键 UI 存在
check('#home-link 唯一', count(/id="home-link"/g) === 1, `${count(/id="home-link"/g)} 个`);
check('有 meta description', /name="description"\s+content="[^"]{40,}"/.test(html));

console.log(`产物 ${path.relative(root, dist)}`);
console.log(`  raw ${(bytes / 1024).toFixed(1)} KB / gzip ${(gzip / 1024).toFixed(1)} KB / demo ${demos} 个`);

if (fail.length) {
    console.error('\n校验失败 ' + fail.length + ' 项：');
    fail.forEach((f) => console.error('  ✗ ' + f));
    process.exit(1);
}
console.log('\n产物校验通过');
