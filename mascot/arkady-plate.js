/* Аркадий — маскот АРКА 123.
   ArkadyPlate.mount(figureEl, scene, { label, note, hoverArea, text })
   scene = { w, h, ink, cloth, folds, mid, gold, goldmid } из make_paths.py; text = { x, y, value } — надпись в координатах сцены (адрес на табличке).
   Параллакс от прокрутки: слои на разной глубине смещаются по вертикали, пока панель проходит через экран. */
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  // Построения в портретном листе 618 × 1000: сетка 61.8, квадраты 618 → 382 → 236 → 146 → 90 со спиралью, ось, линия φ, круг пропорций.
  const FINE = `<g class="g-fine">${Array.from({ length: 10 }, (_, i) => `<line x1="${61.8 * (i + 1)}" y1="0" x2="${61.8 * (i + 1)}" y2="1000"/>`).join('')}${Array.from({ length: 16 }, (_, i) => `<line x1="0" y1="${61.8 * (i + 1)}" x2="618" y2="${61.8 * (i + 1)}"/>`).join('')}</g>`;
  const GEO = `<g class="g-geo"><line x1="0" y1="382" x2="618" y2="382"/><line x1="236" y1="0" x2="236" y2="382"/><line x1="0" y1="236" x2="236" y2="236"/><line x1="146" y1="236" x2="146" y2="382"/><line x1="146" y1="292" x2="236" y2="292"/>
    <path d="M618 382A618 618 0 0 1 0 1000M618 382A382 382 0 0 0 236 0A236 236 0 0 0 0 236A146 146 0 0 0 146 382A90 90 0 0 0 236 292"/><circle cx="309" cy="618" r="236"/></g>
    <g class="g-geo g-dash"><line x1="309" y1="0" x2="309" y2="1000"/><line x1="0" y1="618" x2="618" y2="618"/></g><line class="g-geo" x1="40" y1="962" x2="578" y2="962"/>`;
  // широкий лист 1000 × 618 — тот же чертёж, повёрнутый на 90°
  const wrap = (inner, wide) => wide ? `<g transform="translate(0 618) rotate(-90)">${inner}</g>` : inner;
  const layer = (cls, vb, inner) => { const s = document.createElementNS(NS, 'svg'); s.setAttribute('class', 'plate__layer ' + cls); s.setAttribute('viewBox', vb); s.setAttribute('aria-hidden', 'true'); s.innerHTML = inner; return s; };

  const visible = new Set(); let raf = 0, uid = 0;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  function loop() {
    raf = 0; let moving = false; const vh = innerHeight;
    for (const p of visible) {
      const r = p.panel.getBoundingClientRect();
      p.ty = Math.max(-1, Math.min(1, (r.top + r.height / 2 - vh / 2) / vh));
      p.y += (p.ty - p.y) * .14;
      if (Math.abs(p.ty - p.y) > .002) moving = true;
      p.layers.forEach(([el, depth]) => { el.style.transform = `translate3d(0,${(p.y * depth).toFixed(2)}px,0)`; });
    }
    if (moving) raf = requestAnimationFrame(loop);
  }
  const kick = () => { if (!raf && !reduce) raf = requestAnimationFrame(loop); };
  document.addEventListener('scroll', kick, { passive: true, capture: true });
  addEventListener('resize', kick, { passive: true });

  function mount(fig, sc, { label = '', note = '', hoverArea = fig, text = null } = {}) {
    const wide = sc.w > sc.h, W = wide ? 1000 : 618, H = wide ? 618 : 1000, vb = `0 0 ${W} ${H}`;
    const s = Math.min(W * .92 / sc.w, H * (wide ? .9 : .94) / sc.h), ox = (W - sc.w * s) / 2, oy = H - sc.h * s - H * .03;
    const g = inner => `<g transform="translate(${ox.toFixed(1)} ${oy.toFixed(1)}) scale(${s.toFixed(4)})">${inner}</g>`;
    const label_ = text ? `<text class="l-text" x="${text.x}" y="${text.y}" text-anchor="middle" font-size="${text.size || 30}">${text.value}</text>` : '';
    const panel = document.createElement('div'); panel.className = 'plate__panel';
    const grid = layer('plate__grid', vb, wrap(FINE, wide)), geo = layer('plate__grid plate__geo', vb, wrap(GEO, wide));
    const glow = document.createElement('div'); glow.className = 'plate__glow';
    // маска складок: полоса вдвое выше сцены, верх белый, низ чёрный; при наведении съезжает вниз на высоту сцены
    const mid_ = 'plate-sweep-' + (++uid);
    const sweep = `<defs><linearGradient id="${mid_}-g" x1="0" y1="0" x2="0" y2="1"><stop offset=".42" stop-color="#fff"/><stop offset=".58" stop-color="#000"/></linearGradient>
      <mask id="${mid_}" maskUnits="userSpaceOnUse" x="0" y="0" width="${sc.w}" height="${sc.h}"><rect class="m-sweep" style="--sweep:${sc.h}px" x="0" y="${-sc.h}" width="${sc.w}" height="${sc.h * 2}" fill="url(#${mid_}-g)"/></mask></defs>`;
    const ink = layer('plate__ink', vb, g(`${sweep}<path class="l-mid" d="${sc.mid}"/><path class="l-ink" d="${sc.ink}"/><path class="l-cloth" d="${sc.cloth || ''}"/><path class="l-fold" mask="url(#${mid_})" d="${sc.folds || ''}"/>`));
    const gold = layer('plate__gold', vb, g(`<path class="l-goldmid" d="${sc.goldmid}"/><path class="l-gold" d="${sc.gold}"/>${label_}`));
    panel.append(grid, geo, glow, ink, gold);
    const meta = document.createElement('figcaption'); meta.className = 'plate__meta'; meta.innerHTML = `<span>${label}</span><span>${note}</span>`;
    fig.classList.add('plate'); if (wide) fig.classList.add('plate--wide'); fig.prepend(panel); fig.append(meta);
    // сетка чуть отстаёт, Аркадий и его предметы чуть опережают; золото едет вместе с фигурой, чтобы предметы не отрывались от рук
    const p = { panel, y: 0, ty: 0, layers: [[grid, -10], [geo, -16], [ink, 10], [gold, 10]] };
    hoverArea.addEventListener('pointerenter', () => fig.classList.add('is-hover'));
    hoverArea.addEventListener('pointerleave', () => fig.classList.remove('is-hover'));
    fig.addEventListener('click', () => { if (matchMedia('(hover: none)').matches) fig.classList.toggle('is-hover'); });
    const show = on => { fig.classList.toggle('is-visible', on); on ? visible.add(p) : visible.delete(p); kick(); };
    if ('IntersectionObserver' in window) new IntersectionObserver(es => es.forEach(en => show(en.isIntersecting))).observe(fig);
    else show(true);
    return fig;
  }
  window.ArkadyPlate = { mount };
})();
