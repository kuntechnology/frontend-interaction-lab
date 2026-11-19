# 前端交互实验室 · Frontend Interaction Lab

61 个可直接体验的前端交互演示，涵盖原生 CSS / JavaScript、动画与可视化库、组件框架及现代浏览器 API。新增目录筛选与 URL 状态、多步骤表单、键盘自动补全、上传状态、响应式导航、分页/加载更多及本地视频交互。每个演示提供说明、精简提示词和代码片段复制。库与框架演示需要联网，原生演示不依赖 CDN；Baseline 徽标只用于适用的 Web 平台特性。

**在线访问：** https://kuntechnology.github.io/frontend-interaction-lab/

## v3.9.0：更完整的交互路径

原有 56 个演示全部保留；#36 搜索升级为支持键盘操作的自动补全，#52 上传增加进度、取消、失败与重试。新增 #57 列表筛选与 URL 同步、#58 多步骤表单、#59 响应式导航、#60 分页/加载更多，以及 #61 本地多视频交互（按需加载、离屏暂停、字幕与自动播放回退）。

新的编辑式外壳提供真实演示索引、搜索、分类、全局命令导航和显示偏好。明暗主题、四种强调色和 URL 筛选继续保留；减少动效可跟随系统或手动开启。拖拽列表增加上/下移动，锚点增加方向键与 Home，手势和 3D 增加按钮替代，Tab / Accordion 状态与无障碍语义同步。命令面板使用原生 dialog，实际跳转到所选演示，而不是假装执行未实现的命令。

RxJS 查询结果使用文本节点渲染；历史 `parts/89.html` 同一问题已同步修补。复制拒绝和旧式复制返回 false 不会被报告为成功。依赖失败仅影响对应演示，提供局部重试；异步模块也进入容错路径。本版本不再请求访问统计或生成访客标识；此前的本地匿名标识仅被清理，不向外发送。

## 静态直出，而不是运行时拼接

站点发布一份自包含 HTML，正文不再等待 97 个分片全部返回，不使用 `document.write`、分片 `fetch` 或 `cache:'no-store'`。关闭 JavaScript 后仍可阅读全部说明和提示词、使用目录锚点；运行交互需要启用 JavaScript。

`node tools/build.mjs` 同时生成 `dist/index.html` 与仓库根 `index.html`，两者字节一致。根入口也已替换，不再保留会空白的旧加载器。Pages 仍只上传 `dist/`，并包含 robots、sitemap、404 和 `.nojekyll`。

## 编辑位置与构建

```text
src/lab.html             全部61项演示、正式外壳和交互的唯一HTML编辑源
src/shell.html           静态首屏门禁原型输入；非另一份正式演示源
assets/lab.css          正式壳层与等价操作样式
assets/lab.js           按功能独立初始化的渐进增强
assets/modern.css/js    55/56 的编号样式和行为片段
design/tokens.css      签封设计令牌
inject.html            仅清理旧本地标识，构建时内联
tools/build.mjs        内联本地资产、生成产物、运行17组断言
tools/verify.mjs       独立校验产物字节与61项计数
tools/contrast.mjs     原有明/暗×四强调色的令牌对比度断言
tests/                 浏览器回归、安全、键盘与触屏验证
dist/                  构建产物，Git忽略，由CI生成
parts/                 历史归档，不参与构建
```

```bash
node tools/build.mjs
node tools/verify.mjs
node tools/contrast.mjs
python3 -m http.server 8873 --directory .
# 浏览 http://localhost:8873/dist/
```

构建只使用 Node 内置模块，无需 `npm install`。不要再以硬切分片作为编辑源；切点会落在标签、脚本和样式中间。设计文档及令牌的签封可用 `sha256sum -c design/freeze.sha256` 核对。

## 校验与体积约束

构建检查文档/标签平衡、唯一 ID、演示连续编号、61 项完整结构、目录双向对应、合法 Baseline、外部 URL 白名单、静态直出、代码切片标记和色彩约束。任一失败使 CI 失败，不上传 Pages。体积门禁只测生成的 `dist/index.html`：**raw ≤1,000,000 B、gzip -9 ≤250,000 B**；不按整个 `dist/` 中图片和视频资源的压缩总和判定。构建不新增生产依赖。

代码复制从当前文档的全部内联 style/script 中按 `/* ===== NN` 切片，不内嵌第二份代码 JSON。#55/#56 与 #57–#61 按各自编号提供代码片段；构建输出会报告 CSS/JS 切片覆盖数。复制结果是片段：公共样式、辅助逻辑、第三方库或特定运行环境可能仍需引入，提示不会保证粘贴后即可独立运行。

开发验证使用 Python Playwright、系统 Chromium 和 Beautiful Soup（仅测试工具，不随网站发布）：

```bash
python3 tests/regression.py
python3 tests/robustness.py
```

脚本默认本地端口 8873。验证记录位于 `design/evidence/`，应阅读每项结果及 degraded / 权限限制，不只看总数。不同浏览器、辅助技术和设备的支持不能由一次 Chromium 回归推断；当前不声称已经完成 Safari / Firefox 或真实屏幕阅读器认证。减少动效会停止 CSS 动画/过渡并减轻部分原生循环，不代表所有第三方 GPU 渲染器都已优化。

`tools/contrast.mjs` 是显式令牌配对检查，不是整页无障碍合规证明；浏览器测试仍需验证实际颜色、焦点、键盘、触屏和权限拒绝。前沿 API 的不支持状态须有可理解的说明，不应伪称所有平台可用。

## 历史版本

v3.8：保留 v3.7 的 54 个演示，增加 **55 可撤销列表操作**和 **56 可调整分栏**；前者支持连续移除与精确撤销，后者支持原生 range、按钮、键盘与触屏操作。

v3.7：47→54 个演示；加入原生 dialog/Popover、命令面板、虚拟滚动、对比滑块、上传预览、Scroll Snap 和 @property；引入 Baseline、分类/URL 筛选、代码复制、静态构建、SEO 产物及多主题对比度检查。

v3.6：原单文件按 2000 字符切分为 `parts/`，在浏览器运行时合并；现只保留归档用于历史追溯。
