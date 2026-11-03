# 前端交互实验室 · 技术计划

状态：G0 冻结。基于读取核实的远端 main `ed9a355`；初始快照与 eaaf3ee 的 101 个文件逐字节一致。任何实现均限于本隔离副本。

## 架构与保留

继承远端 `src/lab.html` 唯一人工源、`tools/build.mjs` → `dist/index.html`、`tools/verify.mjs` 和八上下文 `tools/contrast.mjs`。原始 `parts/` 是归档，不作为人工横切修改点；已无 97 次运行时加载和 document.write。本次不新建另一套构建系统，56 个 demo 的静态 HTML 直接提供内容，脚本失败不阻塞正文。

G1 仅新增 `src/shell.html` 静态可复用外壳、`assets/lab.css` 首屏样式、`design/prototype.html` 静态预览与证据。冻结的 `design/tokens.css` 是壳层统一令牌。原入口、旧演示和交互代码在门禁前不动。

G1 双通过后才恢复本目录尚未导入的已审计上游文件，将外壳标记整合进 `src/lab.html`，并由既有构建器内联本地 tokens/CSS/增强 JS 到 dist。`assets/lab.js` 采用逐功能独立初始化；不新增生产依赖。部署仍只上传 dist。保留旧源 54 个 demo id、描述、提示词、代码复制标记、Baseline 与筛选协议。

## 静态外壳

桌面 72px 顶栏与 224px 左栏，主区标题/说明/真实导航入口和功能明确的交互流程图示；移动顶栏换行，分类可横向滚动但页面本身不横溢。使用语义 main/nav、跳过导航、真实锚点与可见焦点。G1 不加入新的 JS 行为。新外壳不展示虚构统计或内部审查状态。

截图使用既有 Python Playwright 和系统 Chromium（开发验证工具，不成为网站依赖）。两名审查者独立看源和截图，分别评分技术/美感/工作流/适配，权重 .30/.25/.25/.20；AI 套路感单列。阈值与 PRD 一致。任何失败先改壳并复评，禁止创建新交互实现。

## 定点安全与健壮性

RxJS 搜索结果用 textContent 与 b 文本节点，保持模拟请求语义；归档 parts/89.html 的同一漏洞可定点同步修补，避免旧入口回退暴露。新 demo 的可变内容一律文本节点或安全 DOM 操作。

LAB 的 flush/waiter 每项独立 try/catch；依赖失败给显式重试，成功的初始化不重复绑定。剪贴板 fallback 检查 execCommand 返回值，所有调用拒绝有可见反馈。存储读写保护。统计 API 异常不得阻塞，真实计数返回前隐藏而非伪造 0。不增加追踪服务。

原有无限动画/音频不得自动发声；增加减少动态效果入口并尊重系统偏好，关闭 CSS 动画/过渡，合理停止新循环。不能声称所有旧第三方渲染器均已性能优化。

## 等价操作

拖拽列表保留原拖放，补每项上/下移按钮；焦点跟随移动、边界禁用、live region 反馈位置。锚点方向键移动（Shift 加速）与重置。手势区增按钮等价事件。Tab 补 id/aria-controls/tabindex、panel id/aria-labelledby，支持方向键/Home/End；Accordion 的 aria-expanded/aria-controls 与 hidden 同步。3D 场景提供可键盘操作的旋转/重置。触控画板保留 pointer capture 并验证不会阻止舞台外滚动。

既有命令面板不是原生 modal，审核其 Escape、焦点返回、过滤/选择；如发现焦点逃逸，使用原生 dialog 或等效正确焦点管理修复，不另建重复 demo。

## 两个新 demo

55 可撤销列表：原生选项/操作按钮，移除保存快照，撤销精确还原，无计时过期；状态与边界禁用一致。

56 可调整分栏：原生 range 15–85 与 +/- 按钮共享同一比例；CSS grid 或 flex 驱动两栏，方向键/Home/End 与触屏无额外手势依赖；重置50%。小屏内容可读。用途、提示词与 CSS/JS 编号标记满足原代码复制器契约，Baseline 如实标注。

## 完整回归

保留远端 54 个 demo 标题/描述/提示词基线；构建两次正文一致，56 个唯一 demo、56 个提示词与代码复制入口、所有目录锚点有效。运行原构建17项、verify、contrast；新增静态断言禁止用户输入拼入 innerHTML，禁止运行时 parts/document.write。

逐个滚入56个演示触发依赖并记录状态，对所有可自动操作的 demo 执行关键行为；权限API检查真实成功/拒绝路径，不伪称所有设备支持。桌面1440、平板768/1024、手机390/320，深浅主题与强调色；键盘 Tab/Enter/Escape/箭头/Home/End，触控排序/对比/Popover/撤销/分栏，系统减弱动画。

脚本关闭仍有正文与导航；阻断归档分片请求不影响静态产物；CDN全拒绝原生演示可用且第三方有诚实反馈；localStorage/Clipboard拒绝不崩溃。输入 img onerror、svg onload、引号文本，验证无注入节点/执行，按原样显示。控制台无新增异常。浏览器和权限限制须记录而非隐藏。

## 最终审查与发布

两位终审独立依同一分数门槛复核源、diff、截图与测试结果；失败阻止发布。只常规 push 精确实验室仓库，不操作其他项目或服务。发布前再 fetch main；如并发前进，逐文件比对，不能无损整合则停并告知，绝不 force。Pages workflow 成功后检查公开页计数、关键交互和控制台。
