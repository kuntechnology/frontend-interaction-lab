/* Progressive enhancements: one feature failure never blocks another. */
(function(){
  'use strict';
  function run(name,fn){try{fn();}catch(e){console.error('Lab enhancement: '+name,e);}}
  function button(text,label){var b=document.createElement('button');b.type='button';b.className='btn btn-ghost btn-sm';b.textContent=text;if(label)b.setAttribute('aria-label',label);return b;}
  run('preferences',function(){
    var d=document.documentElement, motion=document.getElementById('lab-motion-toggle');
    try{if(localStorage.getItem('lab-motion')==='reduce') d.dataset.motion='reduce';}catch(e){}
    function sync(){motion.setAttribute('aria-pressed',String(d.dataset.motion==='reduce'));motion.textContent=d.dataset.motion==='reduce'?'减少动效：已开启':'减少动效：跟随系统';}
    motion.addEventListener('click',function(){d.dataset.motion=d.dataset.motion==='reduce'?'system':'reduce';try{localStorage.setItem('lab-motion',d.dataset.motion);}catch(e){}sync();});sync();
    var details=document.querySelector('.lab-appearance');document.addEventListener('click',function(e){if(!details.contains(e.target))details.open=false;});details.addEventListener('keydown',function(e){if(e.key==='Escape'){details.open=false;details.querySelector('summary').focus();}});
    document.querySelectorAll('.accent-dot').forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.accent===d.dataset.accent || (!d.dataset.accent&&b.dataset.accent==='orange')));b.addEventListener('click',function(){document.querySelectorAll('.accent-dot').forEach(function(x){x.setAttribute('aria-pressed',String(x===b));});});});
  });
  run('sorting',function(){
    var list=document.getElementById('drag-list'), status=document.createElement('p');status.className='lab-demo-status';status.id='drag-status';status.setAttribute('role','status');status.textContent='可拖拽，也可用每行的上移和下移按钮。';list.after(status);
    Array.from(list.children).forEach(function(li){
      var label=li.textContent.replace('⋮⋮','').trim(), actions=document.createElement('span');actions.className='lab-sort-actions';li.dataset.label=label;
      ['up','down'].forEach(function(dir){var b=button(dir==='up'?'↑':'↓',label+(dir==='up'?'上移':'下移'));b.classList.add('lab-sort-'+dir);b.addEventListener('click',function(){var target=dir==='up'?li.previousElementSibling:li.nextElementSibling;if(!target)return;if(dir==='up')list.insertBefore(li,target);else list.insertBefore(target,li);sync();var fallback=li.querySelector(dir==='up'?'.lab-sort-down':'.lab-sort-up');(b.disabled?fallback:b).focus();status.textContent=label+'，现在位于第 '+(Array.from(list.children).indexOf(li)+1)+' 项，共 '+list.children.length+' 项。';});actions.appendChild(b);});li.appendChild(actions);
    });
    function sync(){Array.from(list.children).forEach(function(li,i,all){li.querySelector('.lab-sort-up').disabled=i===0;li.querySelector('.lab-sort-down').disabled=i===all.length-1;});}
    list.addEventListener('dragend',function(){sync();status.textContent='排序已更新，可继续使用上移和下移按钮调整。';});sync();
    list.closest('.stage').querySelector('.stage-hint').textContent='拖拽 / 上下移动按钮 · 支持键盘与触屏';
  });
  run('accordion',function(){
    var stage=document.getElementById('stage-10'), items=Array.from(stage.querySelectorAll('.acc-item'));
    function sync(){items.forEach(function(item,i){var head=item.querySelector('.acc-head'),body=item.querySelector('.acc-body');if(!body)return;head.id='accordion-head-'+i;body.id='accordion-body-'+i;head.setAttribute('aria-controls',body.id);head.setAttribute('aria-expanded',String(item.classList.contains('acc-open')));body.setAttribute('aria-labelledby',head.id);body.hidden=!item.classList.contains('acc-open');});}
    stage.addEventListener('click',sync);sync();
  });
  run('tabs',function(){
    var tabs=document.querySelectorAll('#stage-11 .tab-btn'),panels=document.querySelectorAll('#stage-11 .tab-panel');
    tabs.forEach(function(tab,i){tab.id='demo-tab-'+i;tab.setAttribute('aria-controls','demo-panel-'+i);tab.tabIndex=i===0?0:-1;panels[i].id='demo-panel-'+i;panels[i].setAttribute('aria-labelledby',tab.id);panels[i].hidden=i!==0;});
  });
  run('gesture-alternative',function(){
    var stage=document.getElementById('stage-27'), controls=document.createElement('div');controls.className='lab-equivalent-controls';controls.setAttribute('aria-label','手势等价操作');
    ['轻点','长按','向左滑动','捏合'].forEach(function(text){var b=button(text);b.addEventListener('click',function(){var log=document.getElementById('gesture-log'),line=document.createElement('span');line.textContent=text+' · 按钮等价操作';log.prepend(line);while(log.children.length>6)log.lastChild.remove();});controls.appendChild(b);});stage.appendChild(controls);
  });
  run('3d-alternative',function(){
    var stage=document.getElementById('stage-21'),controls=document.createElement('div');controls.className='lab-equivalent-controls';controls.setAttribute('aria-label','3D键盘操作');
    [['left','向左旋转'],['right','向右旋转'],['reset','复位']].forEach(function(pair){var b=button(pair[1]);b.addEventListener('click',function(){stage.dispatchEvent(new CustomEvent('lab-rotate',{detail:pair[0]}));});controls.appendChild(b);});stage.appendChild(controls);
  });
  run('spotlight-alternative',function(){
    var stage=document.getElementById('stage-03');stage.tabIndex=0;stage.setAttribute('role','group');stage.setAttribute('aria-label','聚光灯舞台，方向键移动光斑');var x=.5,y=.5;
    stage.addEventListener('keydown',function(e){var delta={ArrowLeft:[-.1,0],ArrowRight:[.1,0],ArrowUp:[0,-.1],ArrowDown:[0,.1]}[e.key];if(!delta)return;e.preventDefault();x=Math.max(0,Math.min(1,x+delta[0]));y=Math.max(0,Math.min(1,y+delta[1]));var r=stage.getBoundingClientRect();stage.dispatchEvent(new MouseEvent('mousemove',{clientX:r.left+r.width*x,clientY:r.top+r.height*y,bubbles:true}));});
    stage.addEventListener('pointerdown',function(e){stage.dispatchEvent(new MouseEvent('mousemove',{clientX:e.clientX,clientY:e.clientY,bubbles:true}));});
  });
  run('upload-keyboard',function(){
    var zone=document.getElementById('up-zone'),input=document.getElementById('up-input');zone.tabIndex=0;zone.setAttribute('role','button');zone.setAttribute('aria-label','选择本地图片，仅在浏览器内预览');zone.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();input.click();}});
  });
  run('dialog-support',function(){
    var dialog=document.getElementById('dlg-demo');dialog.setAttribute('aria-label','原生对话框示例');
    var trigger=document.getElementById('dlg-pop-btn'),pop=document.getElementById('dlg-pop');
    if(!('popover' in HTMLElement.prototype)){
      pop.hidden=true;pop.classList.add('lab-popover-fallback');trigger.removeAttribute('popovertarget');trigger.setAttribute('aria-controls',pop.id);trigger.setAttribute('aria-expanded','false');
      function close(){pop.hidden=true;trigger.setAttribute('aria-expanded','false');}
      trigger.addEventListener('click',function(){pop.hidden=!pop.hidden;trigger.setAttribute('aria-expanded',String(!pop.hidden));});document.addEventListener('click',function(e){if(!pop.contains(e.target)&&e.target!==trigger)close();});document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!pop.hidden){close();trigger.focus();}});
    }
  });
})();
