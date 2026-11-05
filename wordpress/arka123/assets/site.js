/* АРКА 123: общий скрипт всех страниц. Каждый блок включается, только если его разметка есть на странице. */
(()=>{
  const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
    /* якоря внутри сайта: прокрутка в своём контейнере */
  $$('.site a[href^="#"]').forEach(a=>{const id=a.getAttribute('href').slice(1); const t=document.getElementById(id); if(!t) return;
    a.addEventListener('click',e=>{e.preventDefault(); t.scrollIntoView({behavior:'smooth',block:'start'})})});

  /* меню на телефоне и телефон в шапке */
  /* меню на телефоне */
  {const bg=$('.burger'),m=$('#mmenu'),ic=bg.querySelector('.msi');
   const tog=o=>{m.hidden=!o;bg.setAttribute('aria-expanded',o);ic.textContent=o?'close':'menu'};
   bg.onclick=e=>{e.stopPropagation();tog(m.hidden)};
   m.addEventListener('click',e=>{if(e.target.closest('a')) tog(false)});
   document.addEventListener('keydown',e=>{if(e.key==='Escape') tog(false)});
   addEventListener('resize',()=>{if(innerWidth>1000) tog(false)});}
  {const tb=$('#telBtn'),tp=$('#telPop'); tb.onclick=e=>{e.stopPropagation();tp.hidden=!tp.hidden;tb.setAttribute('aria-expanded',!tp.hidden)}; document.addEventListener('click',()=>{tp.hidden=true;tb.setAttribute('aria-expanded','false')});}

  /* Аркадий: складки гиматия очень медленно золотеют, пока блок с ним на экране.
     Работает и на телефоне, где наведения нет. Скорость задаётся в styles.css (--fold-in). */
  {const arks=$$('.hov');
   if(arks.length&&'IntersectionObserver' in window){
     const io=new IntersectionObserver(es=>es.forEach(e=>{
       if(e.isIntersecting&&e.intersectionRatio>=.35) e.target.classList.add('is-seen');
       else if(!e.isIntersecting) e.target.classList.remove('is-seen');
     }),{threshold:[0,.35,.6]});
     arks.forEach(a=>io.observe(a));
   } else arks.forEach(a=>a.classList.add('is-seen'));}

  /* галерея зала: фото открывается крупно */
  {const dlg=$('#lb');
   if(dlg){const img=dlg.querySelector('img'), cap=dlg.querySelector('figcaption'), items=$$('[data-lb]'); let i=0;
     const open=n=>{i=(n+items.length)%items.length; const a=items[i]; img.src=a.getAttribute('href'); img.alt=a.querySelector('img').alt; cap.textContent=a.dataset.lb+'  ·  '+(i+1)+' / '+items.length; if(!dlg.open) dlg.showModal()};
     items.forEach((a,n)=>a.addEventListener('click',e=>{e.preventDefault(); open(n)}));
     dlg.querySelector('[data-lb-prev]').onclick=()=>open(i-1); dlg.querySelector('[data-lb-next]').onclick=()=>open(i+1);
     dlg.querySelector('[data-lb-close]').onclick=()=>dlg.close();
     dlg.addEventListener('click',e=>{if(e.target===dlg) dlg.close()});
     dlg.addEventListener('keydown',e=>{if(e.key==='ArrowRight') open(i+1); if(e.key==='ArrowLeft') open(i-1)});}}

  /* карусель форматов */
  if($('#track')){
  /* карусель */
  const tr=$('#track'), cards=[...tr.children], bar=$('#bar'), cnt=$('#cnt');
  function idx(){const x=tr.scrollLeft, w=cards[0].offsetWidth+16; return Math.min(cards.length-1,Math.round(x/w))}
  function upd(){
    const max=tr.scrollWidth-tr.clientWidth, vis=tr.clientWidth/tr.scrollWidth;
    bar.style.width=(vis*100)+'%'; bar.style.transform=`translateX(${max>0?(tr.scrollLeft/max)*(1/vis-1)*100:0}%)`;
    const i=tr.scrollLeft>=max-4?cards.length-1:idx(); cnt.textContent=(i+1)+' / '+cards.length;
    $('[data-dir="-1"]').disabled=tr.scrollLeft<4; $('[data-dir="1"]').disabled=tr.scrollLeft>=max-4;
  }
  tr.addEventListener('scroll',upd,{passive:true}); addEventListener('resize',upd);
  $$('[data-dir]').forEach(b=>b.onclick=()=>tr.scrollBy({left:+b.dataset.dir*(cards[0].offsetWidth+16)}));
  tr.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();tr.scrollBy({left:(e.key==='ArrowRight'?1:-1)*(cards[0].offsetWidth+16)})}});
  upd();
  }

  /* видео на первом экране */
  if($('#heroV')){
  /* видео на первом экране: здание 4 с → пролёт 6 с → снова здание → через 6 с снова пролёт, и так по кругу.
     Кнопка останавливает цикл и запускает его заново. Если первый экран не виден или вкладка скрыта, следующий пролёт ждёт. */
  {const v=$('#heroV'),pb=$('#flyBtn'),lab=$('#flyLab'),ic=$('#flyIc'),art=$('.hero-art');
   const set=(i,l)=>{ic.textContent=i;lab.textContent=l;pb.setAttribute('aria-label',l)};
   const calm=matchMedia('(prefers-reduced-motion:reduce)').matches;
   const FIRST=4000, PAUSE=6000;
   /* видео 1 МБ грузится скриптом: не мешает первой картинке, не качается при экономии трафика, 2G и «меньше движения» */
   const nc=navigator.connection, slow=!!(nc&&(nc.saveData||/2g/.test(nc.effectiveType||'')));
   if(!calm&&!slow){v.preload='auto';v.load()}
   let t=0, stopped=calm||slow, seen=true;
   new IntersectionObserver(e=>{const was=seen;seen=e[0].isIntersecting;if(seen&&!was&&!stopped&&v.paused&&!art.classList.contains('flying'))plan(1500)},{threshold:.4}).observe(art);
   const go=()=>{if(stopped)return;if(!seen||document.hidden){plan(1500);return}v.currentTime=0;v.play().catch(()=>{stopped=true;idle()})};
   const plan=ms=>{clearTimeout(t);t=setTimeout(go,ms)};
   const idle=()=>set('play_arrow','Пролёт в зал, 6 с');
   v.addEventListener('playing',()=>{art.classList.add('flying');set('pause','Остановить')});
   v.addEventListener('ended',()=>{art.classList.remove('flying');idle();plan(PAUSE)});
   pb.onclick=()=>{ if(v.paused){stopped=false;clearTimeout(t);v.play().catch(()=>{})} else {stopped=true;clearTimeout(t);v.pause();art.classList.remove('flying');idle()} };
   idle(); if(!stopped) plan(FIRST);}
  }

  /* бронь: календарь, два шага и вторая заявка */
  if($('#book-s')){
  /* ===== данные: сервер (/api), а без сервера (файл или статический хостинг) резервное хранилище в браузере ===== */
  const CFG=window.ARKA_CFG||{}, API=CFG.api||'/api', TZ='Europe/Minsk', OPEN=CFG.open||9, CLOSE=CFG.close||21, P_DAY=CFG.priceDay||90, P_EVE=CFG.priceEvening||120, EVE=CFG.eveningFrom||17, LS='arka_requests_v1', HOLD=24*3600e3;
  const minsk=()=>{const p=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:TZ,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',hour12:false}).formatToParts(new Date()).map(x=>[x.type,x.value]));return {date:`${p.year}-${p.month}-${p.day}`,hour:+p.hour%24}};
  const addDays=(iso,n)=>{const d=new Date(iso+'T00:00:00Z');d.setUTCDate(d.getUTCDate()+n);return d.toISOString().slice(0,10)};
  const MONTHS=['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'], WD=['вс','пн','вт','ср','чт','пт','сб'];
  const fmt=iso=>{const d=new Date(iso+'T00:00:00Z');return d.getUTCDate()+' '+MONTHS[d.getUTCMonth()]};
  const wd=iso=>WD[new Date(iso+'T00:00:00Z').getUTCDay()];
  const priceOf=(s,d)=>{let x=0;for(let h=s;h<s+d;h++)x+=h>=EVE?P_EVE:P_DAY;return x};
  const localList=()=>{try{return JSON.parse(localStorage.getItem(LS)||'[]')}catch(e){return []}};
  const localBusy=()=>{const b={};localList().forEach(r=>{if(!r.booking||Date.now()-r.createdAt>HOLD)return;for(let h=r.booking.start;h<r.booking.start+r.booking.dur;h++)(b[r.booking.date]=b[r.booking.date]||[]).push(h)});return b};
  const api={
    async avail(){
      try{const r=await fetch(API+'/availability',{cache:'no-store'}); if(!r.ok) throw 0; const j=await r.json(); return {busy:j.busy,today:j.today,hour:j.hour,remote:true}}
      catch(e){const n=minsk(); return {busy:localBusy(),today:n.date,hour:n.hour,remote:false}}
    },
    async send(p){
      try{
        const r=await fetch(API+'/requests',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});
        if([404,405,501].includes(r.status)) throw 0;
        const j=await r.json().catch(()=>({}));
        return r.ok?{ok:true}:{ok:false,error:j.error||'Не удалось отправить, попробуйте ещё раз'};
      }catch(e){
        const b=p.booking, busy=localBusy()[b&&b.date]||[];
        if(b) for(let h=b.start;h<b.start+b.dur;h++) if(busy.includes(h)) return {ok:false,error:'Это время уже заняли, выберите другое'};
        const l=localList(); l.push({...p,createdAt:Date.now(),status:'new'}); try{localStorage.setItem(LS,JSON.stringify(l))}catch(x){}
        return {ok:true,local:true};
      }
    }
  };

  /* ===== календарь ===== */
  let day=null,t=null,dur=2,chan='Telegram',A={busy:{},today:minsk().date,hour:minsk().hour};
  const hrs=n=>n+' '+(n%10===1&&n%100!==11?'час':(n%10>=2&&n%10<=4&&(n%100<10||n%100>=20))?'часа':'часов');
  const show=(el,on)=>{el=typeof el==='string'?$(el):el; if(on) el.classList.add('in'); else el.classList.remove('in')};
  const free=(d,h)=>!(A.busy[d]||[]).includes(h)&&!(d===A.today&&h<=A.hour);
  const starts=d=>{const r=[];for(let h=OPEN;h<=CLOSE-2;h++) if(free(d,h)&&free(d,h+1)) r.push(h);return r};
  const maxDur=()=>{let d=0;for(let h=t;h<CLOSE&&free(day,h);h++)d++;return d};
  const price=()=>priceOf(t,dur);
  const range=()=>fmt(day)+', '+t+':00–'+(t+dur)+':00';
  const HORIZON=180;
  function renderDays(){
    const box=$('#days'), keep=day&&!$('#days [data-d="'+day+'"]')?day:null;
    let h='';
    for(let i=0;i<14;i++){const d=addDays(A.today,i), ok=starts(d).length>0, first=i===0||d.endsWith('-01');
      h+=`<button class="fchip" type="button" ${ok?'data-d="'+d+'"':'disabled'} aria-pressed="${d===day}">${+d.slice(8)} <small>${wd(d)}${first?' · '+MONTHS[+d.slice(5,7)-1].slice(0,3):''}</small></button>`}
    if(keep) h+=`<button class="fchip" type="button" data-d="${keep}" aria-pressed="true">${+keep.slice(8)} <small>${MONTHS[+keep.slice(5,7)-1].slice(0,3)}</small></button>`;
    h+=`<button class="fchip" type="button" id="dOtherB" aria-label="Другая дата"><span class="msi" style="font-size:18px">event</span><small>Другая</small></button>`;
    box.innerHTML=h;
  }
  function renderTimes(){
    $('#timeL').textContent='Начало, '+fmt(day);
    const ok=starts(day);
    $('#times').innerHTML=Array.from({length:CLOSE-1-OPEN},(_,i)=>OPEN+i).map(h=>ok.includes(h)?`<button class="fchip" type="button" data-t="${h}" aria-pressed="${h===t}">${h}:00</button>`:`<button class="fchip" type="button" disabled>${h}:00</button>`).join('');
  }
  function calc(){
    if(t===null) return;
    dur=Math.max(2,Math.min(dur,maxDur()));
    $('#dv').textContent=hrs(dur); $('#dm').disabled=dur<=2; $('#dp').disabled=dur>=maxDur();
    $('#sum').textContent=price()+' BYN'; $('#sumHint').textContent=range();
    $('#pick2').textContent=range()+' · '+price()+' BYN';
    $('#nextD').textContent='Забронировать '+fmt(day);
  }
  function selectDay(d){day=d;t=null;renderDays();renderTimes();show('#rvTime',true);show('#rvDur',false);$('#pick2').textContent=fmt(day)+', время не выбрано'}
  function selectTime(h){t=h;dur=2;renderTimes();calc();show('#rvDur',true)}
  $('#days').addEventListener('click',e=>{
    const b=e.target.closest('button'); if(!b) return;
    if(b.id==='dOtherB'){const i=$('#dOther'); i.min=A.today; i.max=addDays(A.today,HORIZON); try{i.showPicker()}catch(x){i.focus();i.click()} return}
    if(b.dataset.d) selectDay(b.dataset.d);
  });
  $('#dOther').addEventListener('change',e=>{const v=e.target.value; if(!v||v<A.today||v>addDays(A.today,HORIZON)) return;
    if(!starts(v).length){$('#dOtherNote').textContent='На '+fmt(v)+' свободного времени нет, выберите другую дату.';return}
    $('#dOtherNote').textContent=''; selectDay(v)});
  $('#times').addEventListener('click',e=>{const b=e.target.closest('button[data-t]'); if(b) selectTime(+b.dataset.t)});
  $('#dm').onclick=()=>{dur--;calc()}; $('#dp').onclick=()=>{dur++;calc()};
  function pick(box,attr,fn){box.addEventListener('click',e=>{const b=e.target.closest('button[data-'+attr+']'); if(!b) return;
    box.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',x===b)); fn(b)})}
  pick($('#chan'),'c',b=>{$('#lc').textContent=b.dataset.l;$('#f-contact').placeholder=b.dataset.p;chan=b.dataset.c; show('#rvContact',true); setTimeout(()=>$('#f-contact').focus({preventScroll:true}),30)});
  $('#f-name').addEventListener('input',e=>{if(e.target.value.trim().length>=2) show('#rvChan',true)});
  $('#f-contact').addEventListener('input',e=>{if(e.target.value.trim().length>=3) $$('.rvLast').forEach(x=>show(x,true))});
  const isDesk=()=>innerWidth>760;
  function step(n,quiet){
    const one=n===1;
    $('#b1').hidden=!one; $('#sum1').hidden=one; $('#edit1').hidden=one; $('#sum2h').hidden=!one;
    $('#st1').classList.toggle('done',!one); $('#n1').innerHTML=one?'1':'<span class="msi" style="font-size:18px">check</span>';
    $('#st2').classList.toggle('off',one); $('#b2').hidden=one; $('#ok').hidden=true;
    if(t!==null) $('#sum1').textContent=range()+' · '+price()+' BYN';
    $('#arkSay').textContent=one?'управляющий залом. Держу дату 24 часа без предоплаты.':'Осталось сказать, куда прислать подтверждение.';
    if(!one) setTimeout(()=>$('#f-name').focus({preventScroll:true}),50);
    $('.book').classList.toggle('s2',!one);
    if(!quiet){const el=$(one?'#st1':'#st2'), r=el.getBoundingClientRect(); if(r.top<72||r.top>innerHeight*.6) el.scrollIntoView({block:'start'})}
  }
  async function refresh(){A=await api.avail(); renderDays(); if(day&&!starts(day).length){day=null;t=null} if(day){renderTimes(); if(t!==null&&!(starts(day).includes(t)&&maxDur()>=2)){t=null;show('#rvDur',false);$('#pick2').textContent=fmt(day)+', время не выбрано'}else calc()}}
  async function resetBook(){
    day=null;t=null;dur=2; await refresh(); renderDays();
    ['#rvTime','#rvDur','#rvChan','#rvContact'].forEach(x=>show(x,false)); $$('.rvLast').forEach(x=>show(x,false));
    step(1,true); $('#pick2').textContent='Дата не выбрана';
    if(isDesk()){ const d=addDays(A.today,0), f=[...Array(14).keys()].map(i=>addDays(A.today,i)).find(x=>starts(x).length); if(f){selectDay(f); selectTime(starts(f)[0])} }
  }
  window.__resetBook=resetBook;
  $('#next').onclick=()=>step(2); $('#edit1').onclick=()=>step(1);
  const errBox=(form)=>{let e=form.querySelector('.err'); if(!e){e=document.createElement('p');e.className='err';e.setAttribute('role','alert');form.querySelector('.total').before(e)} return e};
  async function submit(form,btn,p,onOk){
    const e=errBox(form); e.textContent='';
    if(p.name.trim().length<2){e.textContent='Введите имя';return}
    if(p.contact.trim().length<3){e.textContent='Укажите, как с вами связаться';return}
    btn.disabled=true; const old=btn.innerHTML; btn.innerHTML='Отправляем…';
    const r=await api.send(p);
    btn.disabled=false; btn.innerHTML=old;
    if(!r.ok){e.textContent=r.error; if(p.booking){await refresh(); step(1)} else e.scrollIntoView({block:'center',behavior:'smooth'}); return}
    onOk(); refresh();
  }
  const bookingPart=()=>t!==null?{date:day,start:t,dur}:undefined;
  $('#b2').addEventListener('submit',e=>{e.preventDefault(); const btn=e.submitter||$('#b2 button[type=submit]');
    submit($('#b2'),btn,{booking:bookingPart(),name:$('#f-name').value,channel:chan,contact:$('#f-contact').value,format:$('#f-fmt').value,guests:$('#f-guests').value,website:$('#hp1').value},()=>{
      $('#b2').hidden=true; $('#ok').hidden=false; $('#edit1').hidden=true; {const r=$('#ok').getBoundingClientRect(); if(r.top<72||r.bottom>innerHeight) $('#ok').scrollIntoView({block:'center'})}
      $('#okTx').textContent=`Анна ответит ${chan==='звонок'?'звонком':'в '+chan} в течение 15 минут.`;
      $('#arkSay').textContent='Окна к вашему приходу откроем. До встречи на Мстиславца, 10.'})});
  pick($('#chan2'),'c',b=>{$('#l-cl').textContent=b.dataset.l;$('#l-contact').placeholder=b.dataset.p});
  $('#leadF').addEventListener('submit',e=>{e.preventDefault(); const btn=$('#lsend'), ch=$('#chan2 [aria-pressed="true"]');
    submit($('#leadF'),btn,{booking:bookingPart(),name:$('#l-name').value,channel:ch?ch.textContent.trim().replace('Звонок','звонок'):'Telegram',contact:$('#l-contact').value,format:$('#l-fmt').value,guests:$('#l-guests').value,message:$('#l-msg').value,website:$('#hp2').value},()=>{
      btn.innerHTML='<span class="msi">check</span>Заявка отправлена'; btn.disabled=true; setTimeout(()=>{btn.disabled=false;btn.innerHTML='<span class="msi">send</span>Отправить заявку'},6000)})});
  /* формат из ссылки: bron.html?f=Съёмка */
  {const f=new URLSearchParams(location.search).get('f'); if(f) ['#f-fmt','#l-fmt'].forEach(s=>{const el=$(s); if(el&&[...el.options].some(o=>o.value===f)) el.value=f});}
  addEventListener('resize',()=>{if(window.__wasDesk!==isDesk()){window.__wasDesk=isDesk(); resetBook()}});
  resetBook(); window.__wasDesk=isDesk();
  }
})();
