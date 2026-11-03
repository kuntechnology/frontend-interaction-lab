# 原生交互参考

[MDN：Using the Popover API](https://developer.mozilla.org/en-US/docs/Web/API/Popover_API/Using)：auto popover 可外点和 Escape 关闭；popovertarget 建立隐式展开/详情关系和后续键盘焦点顺序；Popover 非模态，不应当作模态对话框。

[MDN：dialog 元素](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog)：showModal 令背景 inert，原生 Escape 关闭；必须有明确关闭按钮；选择合理初始焦点，不给 dialog 添加 tabindex。关闭后应检查焦点返回触发者。

[WAI APG：可重新排列列表](https://www.w3.org/WAI/ARIA/apg/patterns/listbox/examples/listbox-rearrangeable/)：移动按钮为拖拽提供等价路径；移动后保留有意义焦点，并以 live region 通告结果。APG 示例不是直接可投产保证，使用原生 HTML 优先，仍需真实移动端/键盘测试。

远端基线核对通过已启用 GitHub 连接器读取 `kuntechnology/frontend-interaction-lab` 的 `eaaf3ee...ed9a355` 比较：15 个新增提交；已完整继承其 54 个 demo、静态 dist 构建、分类与代码复制、Baseline 和对比度检查。未使用搜索摘要替代上述已打开原文。
