# 前端交互实验室 · Frontend Interaction Lab

54 个可即开即用的前端交互演示：**22 原生 + 13 精选库 + 8 前沿框架 + 11 CSS 新特性 / 原生 API**。

每个演示都有：可交互的 stage、一条 Baseline 支持度标注、可直接复制的精简提示词，以及可复制的源码（HTML + CSS + JS）。

🌐 **在线访问：** https://kuntechnology.github.io/frontend-interaction-lab/

---

## 一、为什么改成了静态构建

改造前，这个站是 **97 个 2000 字符硬切片 + 运行时 `document.write` 合并**：首屏要发 98 个请求（97 片 + inject.html），每片 `cache:'no-store'`，最后由 `document.open()/write()` 把整页重写一遍。

实测（8 并发取完 97 片）耗时 8.1 秒，期间只有一个转圈；爬虫拿到的只有「加载中」三个字。

现在产物是**一份静态 HTML**：1 个请求，`gzip` 后 62.6 KB，无 JS 也能读到全部 54 个演示，搜索引擎可索引。

| 指标 | 改造前 | 改造后 |
|---|---|---|
| 首屏 HTML 请求 | 99（1 外壳 + 97 分片 + 1 inject） | **1** |
| 首次可读内容 | 4–8 秒后 | 立即可读 |
| 无 JS 用户 | 永久转圈 | 完整可读 |
| 可被搜索引擎索引 | 否（只有「加载中」外壳） | 是 |
| robots / sitemap / 404 | 全部 404 | 随产物生成 |
| 构建期断言 | 0 | 14 项 |

---

## 二、目录结构

```
frontend-interaction-lab/
├── src/lab.html            # ★ 唯一人工编辑源（改内容只改这里）
├── inject.html             # 返回主页按钮 + 自建 PV/UV 上报，构建时内联
├── tools/
│   ├── build.mjs           # src → dist：内联 inject + 生成 robots/sitemap/404 + 14 项断言
│   ├── verify.mjs          # 独立校验 dist 那份字节（不复用构建的中间变量）
│   └── deps.snapshot.json  # 产物允许出现的 29 个外部 URL 白名单
├── dist/                   # 构建产物，git 忽略，CI 里生成
├── parts/                  # 历史分片，已冻结为存档，不参与构建
├── .github/workflows/
│   └── deploy.yml          # 构建 + 校验 → 只上传 dist/
└── index.html              # 旧外壳，保留作回滚兜底，不参与构建
```

**为什么 `src/lab.html` 而不是继续改 `parts/`**：97 个分片是按 2000 字符硬切的（不是旧 README 写的 18000），96 个切点里 45 个落在标签或属性中间、33 个在 `<script>` 内、27 个在 `<style>` 内。在这种切法上做任何横切改动，都会变成 97 个文件全 diff，且极易把 `</style>` 切错片。

`parts/` 仍在仓库里可查，只是不再作为构建输入。

---

## 三、本地开发

```bash
node tools/build.mjs                  # 构建 dist/
node tools/verify.mjs                 # 校验产物
python3 -m http.server -d dist 8097   # 本地预览
```

无第三方依赖、无 `npm install`、无打包器。

---

## 四、构建期断言

`tools/build.mjs` 任一失败即 `exit 1`，CI 里构建失败就不会发布：

| 编号 | 断言 |
|---|---|
| A1 | 以 doctype 开头，`</html>` 在文件末尾 |
| A2 | `html` / `head` / `body` 各恰好 1 次 |
| A3 | `style` / `script` / `section` / `main` / `footer` 开闭平衡 |
| A4 | `title` 非空且不含「加载中」 |
| A5 | `meta description` 长度 40–220 |
| A6 | demo 数 = `DEMO_TOTAL` 且编号连续 |
| A7 | 全文档 id 无重复 |
| A8 | 每个 demo 都有 `.demo-head` / `h3` / `.stage` / `.prompt` |
| A9 | 目录链接与 demo 锚点双向对应 |
| A10 | `data-baseline` 取值合法，徽标数 = 演示数 − na 数 |
| A11 | 外部 URL 与 `deps.snapshot.json` 完全一致（防静默引入 CDN） |
| A12 | 产物无 `parts/` 引用、无 `document.write` |
| A13 | 体积预算：raw ≤ 300KB，gzip ≤ 75KB |
| A14 | 「复制代码」可切片覆盖：CSS ≥ 29、JS ≥ 46 |

新增演示时只需改 `src/lab.html`，并把 `tools/build.mjs` 的 `DEMO_TOTAL` 加一——A6 会在忘记时直接报错并指出改哪。

---

## 五、几个设计取舍

**Baseline 标注**：一半演示用的是 `scroll-timeline`、`Anchor Positioning`、`View Transitions` 这类前沿特性，读者复制走了才发现不支持。现在按 Web Platform Baseline 逐条标注（widely 27 / newly 4 / limited 3 / na 20）。库与框架类演示不适用 Baseline，不渲染徽标——渲染成「未知」只是噪音。徽标文字统一用 `--ink`，颜色只放在左侧圆点上，因为实测 `--ink-3` 在页面底上只有 2.65:1。

**筛选只有一个显示真源**：库里原本躺着一条从未被使用的 `body.is-filtering .demo:not(.is-match){display:none}`，而搜索是直接写 `style.display` 的。现在搜索与分类筛选共用 `paint()`，显示与否完全由 CSS 决定，JS 只切类。分类从左侧目录的 `.rail-cat` / `.rail-link` 派生——目录即分类，不维护第二份映射。

**「复制代码」零额外体积**：没有在构建期把 54 段代码塞进 JSON（那要多背 100KB），而是点击时从当前文档的 `style` / `script` 里按 `/* ===== NN` 注释切段。代价是部分演示的 CSS 写在公共样式表里、切不出来（CSS 可切片 36/54、JS 53/54）——这种情况下 toast 会明说「已复制 HTML + JS（样式依赖页面公共样式表）」，不暗示能独立运行。

**外部依赖仍是 jsdelivr 单源**：20 个库按需懒加载（进入视口 420px 才注入），CDN 失败有兜底提示。若要换成多源或自托管，改 `LIBS` 表即可，但记得同步 `deps.snapshot.json`，否则 A11 会拦住。

---

## 六、已知问题

**浅色主题的对比度**：暗色主题 axe 审计 0 违规；浅色主题有约 180 处对比度不达标，根因收敛到三个令牌——`--ink-2` 在 `--accent-soft` 上 4.39:1、`--ink-3` 仅 2.40:1、`--accent-deep` 3.62:1。整站调色属于视觉决策，尚未落地。可选取值已算好（`--ink-2 #5A554B` / `--ink-3 #6B6558` / `--accent-deep #B03A08`，对三种背景均 ≥4.5:1）。

---

## 七、更新记录

### v3.7.0
- 新增 7 个演示（47 → 54）：原生 dialog + Popover、⌘K 命令面板、虚拟滚动 10 万行、前后对比滑块、拖拽上传预览、Scroll Snap 吸附、`@property` 色阶
- 每个演示加 Baseline 支持度徽标与图例
- 新增分类筛选条，与搜索合并为单一显示真源，筛选状态写入 URL
- 每个演示可复制自身代码（HTML + CSS + JS），覆盖率纳入断言
- 交付方式重构：静态构建 + 14 项断言 + 只上传 dist/，首屏请求 99 → 1
- 新增 robots.txt / sitemap.xml / 404.html
- 无障碍：Swiper 箭头改真 button、可滚动区域补 tabindex、暗色下 ghost 按钮对比度

### v3.6.0
- 单文件源页面按 2000 字符切片存放于 `parts/`，运行时合并渲染
