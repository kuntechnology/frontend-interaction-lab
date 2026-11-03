/* ===== 55 可撤销列表操作 ===== */
(function(){
  'use strict';
  var list = document.getElementById('undo-list');
  var undoButton = document.getElementById('undo-last');
  var resetButton = document.getElementById('undo-reset');
  var status = document.getElementById('undo-status');
  if(!list || !undoButton || !resetButton || !status) return;
  var initial = Array.prototype.slice.call(list.children).map(function(node){ return node.cloneNode(true); });
  var history = [];
  function announce(message){ status.textContent = message; }
  function update(){
    undoButton.disabled = history.length === 0;
    list.querySelectorAll('.undo-remove').forEach(function(button){ button.disabled = false; });
  }
  list.addEventListener('click', function(event){
    var button = event.target.closest('.undo-remove');
    if(!button || !list.contains(button)) return;
    var item = button.closest('li');
    if(!item || !list.contains(item)) return;
    var label = item.querySelector('.undo-label');
    var name = label ? label.textContent : '列表项目';
    var next = item.nextSibling;
    history.push({ node:item, next:next, name:name });
    item.remove();
    update();
    announce('已移除“' + name + '”。列表剩余 ' + list.children.length + ' 项；可继续移除或撤销。');
    undoButton.focus();
  });
  undoButton.addEventListener('click', function(){
    if(!history.length) return;
    var entry = history.pop();
    if(entry.next && entry.next.parentNode === list) list.insertBefore(entry.node, entry.next);
    else list.appendChild(entry.node);
    update();
    announce('已撤销，恢复“' + entry.name + '”。列表共 ' + list.children.length + ' 项。');
    var restoredButton = entry.node.querySelector('.undo-remove');
    if(restoredButton) restoredButton.focus();
  });
  resetButton.addEventListener('click', function(){
    list.replaceChildren();
    initial.forEach(function(node){ list.appendChild(node.cloneNode(true)); });
    history.length = 0;
    update();
    announce('列表已重置，共 ' + list.children.length + ' 项。');
    resetButton.focus();
  });
  update();
})();

/* ===== 56 可调整分栏 ===== */
(function(){
  'use strict';
  var range = document.getElementById('split-range');
  var reset = document.getElementById('split-reset');
  var less = document.getElementById('split-less');
  var more = document.getElementById('split-more');
  var layout = document.getElementById('split-layout');
  var output = document.getElementById('split-output');
  if(!range || !reset || !less || !more || !layout || !output) return;
  var min = Number(range.min), max = Number(range.max), step = 5;
  function setValue(value){
    var bounded = Math.max(min, Math.min(max, Math.round(Number(value))));
    range.value = String(bounded);
    layout.style.setProperty('--split', bounded + 'fr');
    layout.style.setProperty('--split-rest', (100 - bounded) + 'fr');
    output.textContent = '左栏 ' + bounded + '%，右栏 ' + (100 - bounded) + '%';
    less.disabled = bounded <= min;
    more.disabled = bounded >= max;
  }
  range.addEventListener('input', function(){ setValue(range.value); });
  less.addEventListener('click', function(){ setValue(Number(range.value) - step); range.focus(); });
  more.addEventListener('click', function(){ setValue(Number(range.value) + step); range.focus(); });
  reset.addEventListener('click', function(){ setValue(50); range.focus(); });
  setValue(range.value);
})();
