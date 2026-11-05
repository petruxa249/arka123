/* АРКА 123 · 3D-режим: прогулка по залу в браузере (three.js).
   Зал строится кодом по замерам: 14,2 × 8,7 м, потолок 4,5 м, два арочных окна 4 × 3,5 м (подоконник 0,9 м),
   две колонны, экран у глухой восточной стены, вход в юго-восточном углу (как на плане на главной).
   Координаты: x 0…14,2 (запад → восток), z 0…8,7 (окна → вход), y вверх; окна смотрят на север (−z), там Библиотека.
   Сборка: см. build3d.sh (esbuild, three 0.170) → out/arka3d.js. Подключается только на 3d.html и только по требованию. */
import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { ConvexGeometry } from 'three/examples/jsm/geometries/ConvexGeometry.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import DIGITS from './digits.json';

const W = 14.2, D = 8.7, H = 4.5, T = 0.45;            // зал и толщина стен
const WW = 4, WH = 3.5, SILL = 0.9, RISE = 1.2;          // окно 4 × 3,5 м, стрела арки 1,2 м
const WINX = [3.5, 11.2];                                // центры окон по плану
const SPRING = SILL + WH - RISE;                         // пята арки
const RA = ((WW / 2) ** 2 + RISE ** 2) / (2 * RISE);     // радиус арки
const AC = SPRING + RISE - RA;                           // центр дуги по высоте
const COLS = [[6.44, 3.28], [6.44, 5.83]], COLW = 0.44;  // две колонны
const EYE = 1.65, G = -5.2;                              // глаза; земля на 5,2 м ниже пола зала
const LIB = [11, -210];                                  // Национальная библиотека
const PLINTH = [7.35, 0.3, 1.7, 0.5];                    // постамент «123»: x, z, ширина, глубина

const RM = matchMedia('(prefers-reduced-motion: reduce)').matches;
const MOBILE = matchMedia('(max-width: 720px), (pointer: coarse)').matches;

/* ---------- расстановки ---------- */
const LAYOUTS = {
  empty:  { name: 'Пустой зал', cap: '123 м², свободная планировка', fmt: '' },
  meet:   { name: 'Переговорная', cap: 'Стол на 14 человек у экрана и лаунж', fmt: 'Другое' },
  work:   { name: 'Мастер-класс', cap: '8 рабочих столов · 24 участника', fmt: 'Мастер-класс' },
  conf:   { name: 'Конференция', cap: 'Театр · 80 мест', fmt: 'Конференция' },
  party:  { name: 'Фуршет', cap: 'Фуршет · до 70 гостей', fmt: 'Фуршет или праздник' },
  shoot:  { name: 'Съёмка', cap: 'Фотозона у стены и свет из окон', fmt: 'Съёмка' },
  show:   { name: 'Шоурум', cap: 'Подиумы и стойки · до 30 гостей', fmt: 'Шоурум или pop-up' },
  office: { name: 'Офис', cap: '12 рабочих мест и переговорная', fmt: 'Офис на месяц' },
};
const VIEWS = {
  start:  { p: [0.9, EYE, 2.5], at: [10, 1.55, 1.2] },
  door:   { p: [12.9, EYE, 7.9], at: [4, 1.5, 1.0] },
  window: { p: [11.2, EYE, 2.7], at: [LIB[0], G + 30, LIB[1]] },
  stage:  { p: [13.25, EYE, 4.35], at: [0, 1.3, 4.35] },
  plan:   { plan: true },
};

/* ---------- утилиты ---------- */
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const ease = t => t < .5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2;
const easeBack = t => { const c = 1.4; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2; };
function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function paint(g, color) {
  g = g.index ? g.toNonIndexed() : g;
  const c = new THREE.Color(color), n = g.attributes.position.count, a = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { a[i * 3] = c.r; a[i * 3 + 1] = c.g; a[i * 3 + 2] = c.b; }
  g.setAttribute('color', new THREE.BufferAttribute(a, 3)); return g;
}
const B = (w, h, d, x, y, z, col, ry = 0, rx = 0) => { const g = new THREE.BoxGeometry(w, h, d); if (rx) g.rotateX(rx); if (ry) g.rotateY(ry); g.translate(x, y, z); return paint(g, col); };
const Cy = (rt, rb, h, x, y, z, col, seg = 18) => { const g = new THREE.CylinderGeometry(rt, rb, h, seg); g.translate(x, y, z); return paint(g, col); };
const Sp = (r, x, y, z, col, sx = 1, sy = 1, sz = 1, det = 2) => { const g = new THREE.IcosahedronGeometry(r, det); g.scale(sx, sy, sz); g.translate(x, y, z); return paint(g, col); };
const merge = (...gs) => mergeGeometries(gs);

function archPts(cx, inset = 0, n = 40, bottom = SILL) {
  const hw = WW / 2 - inset, R = RA - inset, ys = AC + Math.sqrt(R * R - hw * hw), a0 = Math.atan2(ys - AC, hw);
  const pts = [new THREE.Vector2(cx - hw, bottom + inset)];
  for (let i = 0; i <= n; i++) { const a = Math.PI - a0 - (Math.PI - 2 * a0) * i / n; pts.push(new THREE.Vector2(cx + R * Math.cos(a), AC + R * Math.sin(a))); }
  pts.push(new THREE.Vector2(cx + hw, bottom + inset));
  return pts;
}
const archTop = (dx, inset = 0) => AC + Math.sqrt((RA - inset) ** 2 - dx * dx);

/* паркет ёлочкой: плашка 9 × 36 см, текстура бесшовная (период 4√2 × √2 плашки) */
function parquet() {
  const cw = 512, ch = 128, cv = document.createElement('canvas'); cv.width = cw; cv.height = ch;
  const cx = cv.getContext('2d'), img = cx.createImageData(cw, ch), d = img.data, S = Math.SQRT2;
  const hash = (a, b) => { let h = Math.imul(a * 374761393 + b * 668265263 | 0, 1274126177); h ^= h >>> 13; return ((Math.imul(h, 1103515245) >>> 0) % 1000) / 1000; };
  for (let py = 0; py < ch; py++) for (let px = 0; px < cw; px++) {
    const X = (px + .5) / cw * 4 * S, Y = (py + .5) / ch * S, u = (X + Y) / S, v = (Y - X) / S;
    const a = Math.floor(v), q = ((u - a) % 8 + 8) % 8;
    let id, along, across, len;
    if (q < 4) { id = hash(a, Math.floor((u - a) / 8)); along = q; across = v - a; }
    else { const b = Math.floor(u), r = ((v - b - 1) % 8 + 8) % 8; id = hash(b + 999, Math.floor((v - b - 1) / 8)) ; along = r; across = u - b; }
    len = Math.min(along, 4 - along) * 9, across = Math.min(across, 1 - across) * 9;  // расстояние до шва в см
    const tone = .86 + id * .2, grain = .97 + .03 * Math.sin(along * 23 + id * 40 + Math.sin(along * 7) * 2);
    const seam = Math.min(len, across) < .35 ? .72 : 1;
    const k = tone * grain * seam, i = (py * cw + px) * 4;
    d[i] = 214 * k; d[i + 1] = 176 * k; d[i + 2] = 128 * k; d[i + 3] = 255;
  }
  cx.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping;
  const P = 0.09; t.repeat.set(W / (4 * S * P), D / (S * P)); return t;
}

function label(text, w = 1.1, opts = {}) {
  const cv = document.createElement('canvas'), s = 4, fs = 40;
  const cx = cv.getContext('2d'); cx.font = `500 ${fs}px Roboto, system-ui, sans-serif`;
  const tw = Math.ceil(cx.measureText(text).width) + 36; cv.width = tw * s / 2; cv.height = 64 * s / 2;
  cx.scale(s / 2, s / 2); cx.font = `500 ${fs}px Roboto, system-ui, sans-serif`;
  cx.fillStyle = opts.bg || 'rgba(33,54,65,.92)'; cx.beginPath(); cx.roundRect(0, 4, tw, 56, 12); cx.fill();
  cx.fillStyle = opts.fg || '#F5EAD8'; cx.textBaseline = 'middle'; cx.fillText(text, 18, 33);
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.SpriteMaterial({ map: tex, depthTest: opts.depth !== false, toneMapped: false });
  const sp = new THREE.Sprite(m); const ww = w * tw / 160; sp.scale.set(ww, ww * 64 / tw, 1); sp.renderOrder = 5; return sp;
}

/* ---------- мебель (одна геометрия с цветами вершин на тип) ---------- */
function furniture() {
  const NAVY = '#213641', BLK = '#1c1f22', WHT = '#f1efea', GRY = '#8d949a', GOLD = '#c9a26a';
  const legs = (w, d, h, col, r = .012) => [-1, 1].flatMap(sx => [-1, 1].map(sz => Cy(r, r, h, sx * w / 2, h / 2, sz * d / 2, col, 8)));
  const F = {};
  F.chair = merge(B(.44, .05, .44, 0, .45, 0, NAVY), B(.44, .42, .04, 0, .71, -.2, NAVY), ...legs(.38, .38, .45, BLK));
  F.lectern = merge(B(.55, 1.05, .42, 0, .525, 0, '#2b2e31'), B(.62, .04, .5, 0, 1.08, -.02, '#2b2e31', 0, -.2), B(.3, .2, .02, 0, .75, .215, GOLD));
  F.screen = merge(B(.06, 2.1, 3.7, 0, 1.95, 0, BLK), B(.04, 2.0, 3.6, .02, 1.95, 0, '#fbfbf8'), B(.08, .08, 3.8, 0, 3.04, 0, BLK));
  F.table = merge(Cy(.3, .43, 1.04, 0, .52, 0, WHT, 24), Cy(.37, .37, .03, 0, 1.055, 0, WHT, 24), Cy(.035, .035, .16, .12, 1.15, .05, '#d9e4e8', 8), Cy(.035, .035, .16, -.1, 1.15, -.08, '#d9e4e8', 8));
  F.buffet = merge(B(2.4, .75, .8, 0, .375, 0, WHT), ...[-.9, -.3, .3, .9].map((x, i) => B(.42, .05, .3, x, .775, (i % 2 ? .12 : -.1), i % 2 ? '#c4734f' : '#7f9b5a')),
    ...[-1.05, -.6, .6, 1.05].map(x => Cy(.035, .035, .16, x, .83, .25, '#d9e4e8', 8)));
  F.backdrop = merge(B(2.9, 2.9, .03, 0, 1.45, 0, '#aeb9bf'), B(2.9, .01, 2.2, 0, .005, 1.1, '#aeb9bf'), Cy(.05, .05, 3.2, 0, 2.95, -.02, BLK, 10).rotateZ(Math.PI / 2).translate(2.95, 2.95, 0));
  F.softbox = merge(Cy(.018, .018, 1.7, 0, .85, 0, BLK, 8), ...[0, 2.1, 4.2].map(a => B(.03, .02, .6, Math.sin(a) * .25, .02, Math.cos(a) * .25, BLK, a)), B(.7, .9, .22, 0, 1.75, .08, '#f4f4f2', 0, -.25));
  F.tripod = merge(...[0, 2.1, 4.2].map(a => Cy(.012, .012, 1.4, Math.sin(a) * .22, .68, Math.cos(a) * .22, BLK, 6)), B(.16, .12, .22, 0, 1.42, 0, BLK), Cy(.04, .04, .1, 0, 0, 0, '#2b2e31', 12).rotateX(Math.PI / 2).translate(0, 1.43, .14));
  F.stool = merge(Cy(.2, .2, .04, 0, .66, 0, WHT, 20), Cy(.025, .025, .64, 0, .32, 0, BLK, 8), Cy(.2, .2, .02, 0, .01, 0, BLK, 20));
  F.podium = B(1, 1, 1, 0, .5, 0, WHT);
  const garments = [];
  const gc = ['#213641', '#c9a26a', '#e8e2d6', '#8a3b3b', '#5b6b75', '#3d5a4a', '#b86a4a', '#2b2e31'];
  for (let i = 0; i < 9; i++) garments.push(B(.06, .78, .46, -.62 + i * .155, 1.05, 0, gc[i % gc.length]));
  F.rail = merge(Cy(.016, .016, 1.6, -.75, .8, 0, BLK, 8), Cy(.016, .016, 1.6, .75, .8, 0, BLK, 8), Cy(.016, .016, 1.52, 0, 1.58, 0, BLK, 8).rotateZ(Math.PI / 2).translate(1.58, 1.58, 0), B(1.6, .03, .5, 0, .02, 0, BLK), ...garments);
  F.mirror = merge(B(.7, 1.9, .04, 0, .97, 0, '#c7d1d5'), B(.78, 1.98, .03, 0, .99, -.03, GOLD));
  F.desk = merge(B(1.4, .03, .7, 0, .735, 0, WHT), B(.03, .72, .62, -.66, .36, 0, BLK), B(.03, .72, .62, .66, .36, 0, BLK), B(.56, .33, .03, 0, 1.08, -.22, BLK), B(.06, .16, .06, 0, .83, -.24, BLK), B(.42, .015, .14, 0, .758, .05, '#3a3e42'));
  F.ochair = merge(B(.48, .07, .46, 0, .48, 0, '#3a3e42'), B(.46, .5, .05, 0, .8, -.21, '#3a3e42'), Cy(.03, .03, .4, 0, .24, 0, BLK, 8), ...[0, 1.26, 2.51, 3.77, 5.03].map(a => B(.03, .03, .3, Math.sin(a) * .15, .03, Math.cos(a) * .15, BLK, a)));
  F.wtable = merge(B(2.4, .04, .8, 0, .74, 0, WHT), B(.05, .72, .7, -1.12, .36, 0, BLK), B(.05, .72, .7, 1.12, .36, 0, BLK),
    ...[-.8, 0, .8].flatMap((x, i) => [B(.32, .02, .24, x, .77, -.12, ['#c9a26a', '#8a3b3b', '#5b6b75'][i]), Cy(.04, .04, .1, x + .22, .81, -.2, '#e8e2d6', 10)]));
  F.flip = merge(B(.7, 1.0, .03, 0, 1.35, 0, '#fbfbf8'), B(.74, .05, .05, 0, 1.88, 0, BLK), ...[-.3, .3].map(x => Cy(.015, .015, 1.9, x, .95, .05, BLK, 6)), Cy(.015, .015, 1.6, 0, .8, -.4, BLK, 6), B(.4, .02, .02, -.05, 1.5, .02, '#213641'), B(.3, .02, .02, -.1, 1.42, .02, '#c9a26a'));
  F.meet = merge(B(2.8, .04, 1.1, 0, .74, 0, '#e9e4da'), B(.08, .72, .7, -1.1, .36, 0, BLK), B(.08, .72, .7, 1.1, .36, 0, BLK));
  F.sofa = merge(B(2.0, .42, .85, 0, .21, 0, NAVY), B(2.0, .45, .18, 0, .62, -.34, NAVY), B(.18, .25, .85, -.91, .55, 0, NAVY), B(.18, .25, .85, .91, .55, 0, NAVY));
  /* люди: тело (цвет одежды через instanceColor) и голова отдельно */
  const WH_ = '#ffffff';
  F.pStand = merge(B(.15, .82, .2, -.09, .41, 0, '#3a3e42'), B(.15, .82, .2, .09, .41, 0, '#3a3e42'), Cy(.17, .2, .64, 0, 1.13, 0, WH_, 14), Sp(.1, -.23, 1.12, 0, WH_, .55, 2.6, .55, 1), Sp(.1, .23, 1.12, 0, WH_, .55, 2.6, .55, 1));
  F.pSit = merge(B(.36, .15, .46, 0, .55, .14, '#3a3e42'), B(.34, .45, .13, 0, .25, .33, '#3a3e42'), Cy(.17, .2, .6, 0, .82, -.04, WH_, 14), Sp(.1, -.23, .82, .06, WH_, .55, 2.2, .7, 1), Sp(.1, .23, .82, .06, WH_, .55, 2.2, .7, 1));
  F.head = Sp(.095, 0, 0, 0, '#ffffff', .92, 1.1, 1, 2);
  // пересчёт: голова ставится по позе
  return F;
}

/* расстановки: [тип, x, z, поворот, масштаб?] и люди [поза, x, z, поворот] */
function layoutItems(name) {
  const it = [], pp = [], r = rng(name.length * 977 + 13);
  const face = (x, z, tx, tz) => Math.atan2(tx - x, tz - z);   // поворот, чтобы смотреть на точку
  const near = (x, z, R = .55) => COLS.some(([cx, cz]) => Math.abs(x - cx) < R && Math.abs(z - cz) < R) || (Math.abs(x - PLINTH[0]) < 1.2 && z < 1.1);
  if (name === 'meet') {
    it.push(['meet', 9.6, 4.35, 0], ['meet', 12.4, 4.35, 0], ['screen', W - .14, 4.35, 0]);
    const xs = [8.6, 9.6, 10.6, 11.6, 12.6, 13.4];
    xs.forEach(x => { it.push(['ochair', x, 3.55, 0], ['ochair', x, 5.15, Math.PI]); });
    it.push(['ochair', 7.75, 4.35, Math.PI / 2], ['sofa', 1.3, 6.8, Math.PI / 2], ['sofa', 3.4, 7.9, Math.PI], ['podium', 2.5, 6.8, 0, [.9, .4, .6]], ['podium', 1.2, 2.0, 0, [.6, .9, .6]]);
    xs.forEach((x, i) => { if (i !== 5 || r() < .5) pp.push(['pSit', x, 3.55, 0]); if (r() < .85) pp.push(['pSit', x, 5.15, Math.PI]); });
    pp.push(['pSit', 7.75, 4.35, Math.PI / 2], ['pStand', 13.5, 2.9, -Math.PI / 2 - .5], ['pSit', 1.3, 6.6, Math.PI / 2], ['pSit', 1.3, 7.1, Math.PI / 2], ['pStand', 2.6, 5.9, -2.6]);
  } else if (name === 'work') {
    for (const x of [2.5, 4.7, 8.6, 10.8]) for (const z of [2.45, 6.25]) {
      it.push(['wtable', x, z, Math.PI / 2]);
      for (const dz of [-.8, 0, .8]) { it.push(['ochair', x - .62, z + dz, Math.PI / 2]); if (r() < .92) pp.push(['pSit', x - .62, z + dz, Math.PI / 2]); }
    }
    it.push(['screen', W - .14, 4.35, 0], ['wtable', 12.9, 2.3, Math.PI / 2], ['flip', 13.2, 6.6, -Math.PI / 2 - .4]);
    pp.push(['pStand', 13.1, 3.3, -Math.PI / 2 - .2], ['pStand', 6.7, 7.4, -2.2]);
  } else if (name === 'conf') {
    const xs = [1.41, 2.45, 3.49, 4.53, 5.58, 7.28, 8.32, 9.36, 10.4, 11.44], zs = [1.26, 2.1, 2.93, 3.76, 4.6, 5.43, 6.26, 7.1];
    for (const x of xs) for (const z of zs) { it.push(['chair', x, z, Math.PI / 2]); if (r() < .82) pp.push(['pSit', x, z, Math.PI / 2]); }
    it.push(['screen', W - .14, 4.35, 0], ['lectern', 13.0, 2.0, -Math.PI / 2]);
    pp.push(['pStand', 12.85, 2.75, -Math.PI / 2 - .3]);
  } else if (name === 'party') {
    const T_ = [[2.4, 2.4], [4.7, 1.9], [2.1, 5.4], [4.4, 4.6], [8.8, 2.2], [11.4, 2.5], [9.0, 5.0], [11.9, 5.5], [3.6, 7.2], [12.6, 7.6]];
    T_.forEach(([x, z]) => it.push(['table', x, z, r() * 6]));
    it.push(['buffet', 6.2, 8.15, 0], ['buffet', 8.75, 8.15, 0]);
    T_.forEach(([x, z]) => { const n = 3 + Math.floor(r() * 3), a0 = r() * 6; for (let k = 0; k < n; k++) { const a = a0 + k * Math.PI * 2 / n + (r() - .5) * .4, px = x + Math.sin(a) * .72, pz = z + Math.cos(a) * .72; if (!near(px, pz)) pp.push(['pStand', px, pz, face(px, pz, x, z)]); } });
    for (let k = 0; k < 10; k++) { const px = 5.2 + r() * 4.6, pz = 6.8 + r() * .6; pp.push(['pStand', px, pz, Math.PI + (r() - .5) * 1.2]); }
    for (let k = 0; k < 6; k++) { const px = WINX[k % 2] + (r() - .5) * 3, pz = .9 + r() * .5; pp.push(['pStand', px, pz, Math.PI * (r() < .5 ? 1 : 0) + (r() - .5)]); }
  } else if (name === 'shoot') {
    it.push(['backdrop', .35, 5.4, Math.PI / 2], ['stool', 1.55, 5.4, 0], ['softbox', 2.5, 3.9, face(2.5, 3.9, 1.5, 5.4)], ['softbox', 2.5, 7.1, face(2.5, 7.1, 1.5, 5.4)], ['tripod', 4.6, 5.4, -Math.PI / 2],
      ['stool', WINX[0], 1.1, 0], ['softbox', 5.6, 2.2, face(5.6, 2.2, WINX[0], 1.1)], ['tripod', WINX[0] + .3, 3.4, Math.PI], ['rail', 12.4, 7.9, 0], ['mirror', 13.9, 6.6, -Math.PI / 2]);
    pp.push(['pSit', 1.55, 5.4, Math.PI / 2], ['pStand', 4.75, 5.0, -Math.PI / 2], ['pStand', 3.3, 7.6, -2.4], ['pStand', WINX[0] + .35, 3.75, Math.PI], ['pSit', WINX[0], 1.1, .3], ['pStand', 12.0, 7.3, 2.6]);
  } else if (name === 'show') {
    [[1.3, 2.1, .9, .8, .9], [1.3, 6.6, .9, 1.0, .9], [4.0, 4.4, 1.3, .45, 1.3], [9.4, 4.4, 1.3, .6, 1.3], [13.2, 2.2, .9, .9, .9], [12.4, 4.8, .8, .5, .8], [9.4, 1.0, .9, .7, .7]].forEach(([x, z, sx, sy, sz]) => it.push(['podium', x, z, 0, [sx, sy, sz]]));
    it.push(['rail', 3.6, 7.75, 0], ['rail', 6.5, 7.75, 0], ['rail', 9.4, 7.75, 0], ['rail', 11.9, 1.4, Math.PI / 2 + .3], ['mirror', .3, 4.4, Math.PI / 2], ['sofa', 13.4, 7.2, -Math.PI / 2]);
    for (let k = 0; k < 18; k++) { let px, pz; do { px = 1 + r() * 12; pz = 1.2 + r() * 6.2; } while (near(px, pz, .8) || Math.hypot(px - 4, pz - 4.4) < 1.1 || Math.hypot(px - 9.4, pz - 4.4) < 1.1); pp.push(['pStand', px, pz, r() * 6.28]); }
  } else if (name === 'office') {
    const isl = [[3.5, 2.6], [11.2, 2.6], [3.5, 5.9]], seats = [];
    isl.forEach(([x, z]) => [-.7, .7].forEach(dx => [[-.36, Math.PI], [.36, 0]].forEach(([dz, ry]) => {
      it.push(['desk', x + dx, z + dz, ry]);
      const sz = z + dz + (ry ? -.55 : .55); it.push(['ochair', x + dx, sz, ry + Math.PI]); seats.push([x + dx, sz, ry + Math.PI]);
    })));
    it.push(['meet', 10.4, 6.3, 0]);
    [[9.3, 5.45, 0], [10.4, 5.45, 0], [11.5, 5.45, 0], [9.3, 7.15, Math.PI], [10.4, 7.15, Math.PI], [11.5, 7.15, Math.PI]].forEach(([x, z, ry]) => it.push(['ochair', x, z, ry]));
    it.push(['sofa', .75, 7.4, Math.PI / 2], ['podium', .5, 5.6, 0, [.5, .45, .5]]);
    seats.forEach(s => { if (r() < .7) pp.push(['pSit', ...s]); });
    pp.push(['pSit', 9.3, 5.45, 0], ['pSit', 11.5, 7.15, Math.PI], ['pStand', 12.6, 6.3, -Math.PI / 2]);
  }
  return { it, pp };
}

/* ---------- основной запуск ---------- */
export function start(root, opts = {}) {
  const canvas = root.querySelector('canvas');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, MOBILE ? 1.5 : 1.75));
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1;
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap; renderer.shadowMap.autoUpdate = false;  // тени пересчитываются только когда меняется сцена, не при ходьбе
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(62, 1, .05, 2600); camera.rotation.order = 'YXZ';
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), .04).texture; scene.environmentIntensity = .5;
  scene.fog = new THREE.Fog(0xe6ecef, 160, 1300);

  /* материалы */
  const mWall = new THREE.MeshStandardMaterial({ color: '#e9dfcd', roughness: .92 });
  const mAnth = new THREE.MeshStandardMaterial({ color: '#2b2e31', roughness: .62 });
  const mCeil = new THREE.MeshStandardMaterial({ color: '#2a2c2f', roughness: .9 });
  const mFrame = new THREE.MeshStandardMaterial({ color: '#15181b', roughness: .38, metalness: .4 });
  const mGlass = new THREE.MeshStandardMaterial({ color: '#cfe0e6', roughness: .03, metalness: .1, transparent: true, opacity: .1, depthWrite: false, envMapIntensity: 1.4 });
  const mLed = new THREE.MeshStandardMaterial({ color: '#ffffff', emissive: '#fff4e3', emissiveIntensity: .8 });
  const mNavy = new THREE.MeshStandardMaterial({ color: '#213641', roughness: .75 });
  const mGold = new THREE.MeshStandardMaterial({ color: '#c9a26a', roughness: .3, metalness: .9 });
  const mFloor = new THREE.MeshStandardMaterial({ map: parquet(), roughness: .34, envMapIntensity: .8 });
  mFloor.map.anisotropy = renderer.capabilities.getMaxAnisotropy();
  const mFurn = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: .62 });
  const mBody = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: .85 });
  const mHead = new THREE.MeshStandardMaterial({ roughness: .7 });

  const room = new THREE.Group(), ceilingGroup = new THREE.Group(); scene.add(room); room.add(ceilingGroup);
  const add = (geo, mat, x = 0, y = 0, z = 0, parent = room, shadow = true) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = shadow; m.receiveShadow = true; parent.add(m); return m; };

  /* пол, стены, потолок */
  const fl = add(new THREE.PlaneGeometry(W, D), mFloor, W / 2, 0, D / 2); fl.rotation.x = -Math.PI / 2; fl.castShadow = false;
  const wallShape = new THREE.Shape([new THREE.Vector2(-T, 0), new THREE.Vector2(W + T, 0), new THREE.Vector2(W + T, H + .3), new THREE.Vector2(-T, H + .3)]);
  WINX.forEach(cx => wallShape.holes.push(new THREE.Path(archPts(cx))));
  add(new THREE.ExtrudeGeometry(wallShape, { depth: T, bevelEnabled: false, curveSegments: 40 }), mWall, 0, 0, -T);
  add(new THREE.BoxGeometry(W + 2 * T, H + .3, T), mWall, W / 2, (H + .3) / 2, D + T / 2);
  add(new THREE.BoxGeometry(T, H + .3, D), mWall, -T / 2, (H + .3) / 2, D / 2);
  add(new THREE.BoxGeometry(T, H + .3, D), mWall, W + T / 2, (H + .3) / 2, D / 2);
  add(new THREE.BoxGeometry(W + 2 * T, .3, D + 2 * T), mCeil, W / 2, H + .15, D / 2, ceilingGroup);
  add(new THREE.BoxGeometry(W + 2 * T, .2, D + 2 * T + .5), mAnth, W / 2, -.1, D / 2 - .2).receiveShadow = false;  // перекрытие под полом (видно снаружи)
  for (const bx of [2.6, COLS[0][0], 10.3]) add(new THREE.BoxGeometry(.3, .4, D), mCeil, bx, H - .2, D / 2, ceilingGroup);
  COLS.forEach(([x, z]) => add(new THREE.BoxGeometry(COLW, H, COLW), mAnth, x, H / 2, z));
  /* плинтус */
  add(new THREE.BoxGeometry(W, .09, .02), mAnth, W / 2, .045, D - .01, room, false);
  add(new THREE.BoxGeometry(.02, .09, D), mAnth, .01, .045, D / 2, room, false);
  add(new THREE.BoxGeometry(.02, .09, D), mAnth, W - .01, .045, D / 2, room, false);
  /* окна: рама, импосты, стекло, подоконник, радиатор */
  WINX.forEach(cx => {
    const ring = new THREE.Shape(archPts(cx, 0)); ring.holes.push(new THREE.Path(archPts(cx, .09)));
    add(new THREE.ExtrudeGeometry(ring, { depth: .12, bevelEnabled: false, curveSegments: 40 }), mFrame, 0, 0, -.32);
    const zsp = SPRING;
    add(new THREE.BoxGeometry(WW - .1, .08, .1), mFrame, cx, zsp, -.26);
    for (const dx of [-WW / 6, WW / 6]) { const top = archTop(dx, .05); add(new THREE.BoxGeometry(.07, top - SILL, .1), mFrame, cx + dx, (top + SILL) / 2, -.26); }
    const gl = add(new THREE.ShapeGeometry(new THREE.Shape(archPts(cx, .06))), mGlass, 0, 0, -.25, room, false); gl.receiveShadow = false; gl.renderOrder = 2;
    add(new THREE.BoxGeometry(WW + .3, .05, .36), mAnth, cx, SILL - .025, .0);
    add(new THREE.BoxGeometry(1.7, .55, .09), mAnth, cx, .42, .07);
  });
  /* экранная стена: тёмно-синяя панель с золотой аркой логотипа */
  add(new THREE.BoxGeometry(.04, 2.5, 4.4), mNavy, W - .02, 1.95, D / 2, room, false);
  {
    const s = .62, o = [], inn = [];
    const ap = (ins) => { const hw = 1 - ins, pts = [new THREE.Vector2(-hw, -1.2)]; for (let i = 0; i <= 32; i++) { const a = Math.PI - Math.PI * i / 32; pts.push(new THREE.Vector2(hw * Math.cos(a), .3 + hw * Math.sin(a))); } pts.push(new THREE.Vector2(hw, -1.2)); return pts; };
    const sh = new THREE.Shape(ap(0)); sh.holes.push(new THREE.Path(ap(.09)));
    const g = new THREE.ExtrudeGeometry(sh, { depth: .025, bevelEnabled: false }); g.scale(s, s, 1);
    const m = add(g, mGold, W - .045, 1.95, D / 2, room, false); m.rotation.y = -Math.PI / 2;
    add(new THREE.BoxGeometry(.03, .05, 1.6 * s * 1.15), mGold, W - .05, 1.95 - 1.2 * s, D / 2, room, false);
  }
  /* вход */
  add(new THREE.BoxGeometry(1.1, 2.3, .05), mAnth, 13.02, 1.15, D - .03);
  add(new THREE.BoxGeometry(.04, .04, .18), mGold, 12.6, 1.05, D - .1, room, false);
  /* светильники: линейные и два подвеса */
  const leds = new THREE.Group(); ceilingGroup.add(leds);
  for (const x of [1.3, 4.5, 8.4, 12.2]) for (const z of [1.7, 4.35, 7.0]) add(new THREE.BoxGeometry(1.5, .04, .06), mLed, x, H - .05, z, leds, false);
  for (const x of [4.5, 8.4]) { add(new THREE.CylinderGeometry(.006, .006, 1.0, 4), mFrame, x, H - .5, 3.0, ceilingGroup, false); add(new THREE.ConeGeometry(.2, .2, 24, 1, true), mFrame, x, H - 1.08, 3.0, ceilingGroup, false); add(new THREE.SphereGeometry(.07, 12, 8), mLed, x, H - 1.17, 3.0, ceilingGroup, false); }
  /* растения в углах у окон */
  const plant = merge(Cy(.2, .16, .45, 0, .225, 0, '#24272a', 16), Cy(.02, .02, .8, 0, .8, 0, '#4a3826', 6), Sp(.42, 0, 1.45, 0, '#3f6a34', 1, 1.15, 1, 1), Sp(.3, .15, 1.75, .1, '#4f7d3c', 1, 1, 1, 1));
  for (const [x, z] of [[.6, .7], [13.6, .7]]) add(plant, mFurn, x, 0, z);
  /* объёмные «123» на постаменте у простенка */
  {
    const shapes = [];
    for (const k of ['1', '2', '3']) for (const p of DIGITS[k]) {
      const sh = new THREE.Shape(p.o.map(([x, y]) => new THREE.Vector2(x, -y)));
      p.h.forEach(h => sh.holes.push(new THREE.Path(h.map(([x, y]) => new THREE.Vector2(x, -y)))));
      shapes.push(sh);
    }
    const g = new THREE.ExtrudeGeometry(shapes, { depth: 40, bevelEnabled: false, curveSegments: 6 });
    g.translate(-628, 1002, -20); const s = 1.05 / 440; g.scale(s, s, s);
    add(new THREE.BoxGeometry(PLINTH[2], .5, PLINTH[3]), new THREE.MeshStandardMaterial({ color: '#f1efea', roughness: .5 }), PLINTH[0], .25, PLINTH[1]);
    add(g, mAnth, PLINTH[0], .5, PLINTH[1]);
  }

  /* ---------- за окном: небо, земля, Библиотека, город ---------- */
  const sky = new THREE.Mesh(new THREE.SphereGeometry(2000, 32, 16), new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, toneMapped: false, fog: false,
    uniforms: { top: { value: new THREE.Color() }, hor: { value: new THREE.Color() }, bot: { value: new THREE.Color() }, sunDir: { value: new THREE.Vector3() }, sunCol: { value: new THREE.Color() } },
    vertexShader: 'varying vec3 vW;void main(){vec4 w=modelMatrix*vec4(position,1.);vW=w.xyz;gl_Position=projectionMatrix*viewMatrix*w;gl_Position.z=gl_Position.w;}',
    fragmentShader: 'uniform vec3 top,hor,bot,sunDir,sunCol;varying vec3 vW;void main(){vec3 d=normalize(vW-cameraPosition);float h=d.y;vec3 c=h>0.?mix(hor,top,pow(h,.5)):mix(hor,bot,pow(min(-h*6.,1.),.6));float s=max(dot(d,sunDir),0.);c+=sunCol*(pow(s,900.)*3.+pow(s,10.)*.22);gl_FragColor=vec4(c,1.);\n#include <colorspace_fragment>\n}',
  })); sky.renderOrder = -1; scene.add(sky);
  const outside = new THREE.Group(); scene.add(outside);
  const mGround = new THREE.MeshStandardMaterial({ color: '#7d8a6f', roughness: 1 });
  const gnd = new THREE.Mesh(new THREE.PlaneGeometry(4000, 4000), mGround); gnd.rotation.x = -Math.PI / 2; gnd.position.y = G; outside.add(gnd);
  const mRoad = new THREE.MeshStandardMaterial({ color: '#55595c', roughness: .95 });
  const road = new THREE.Mesh(new THREE.PlaneGeometry(4000, 16), mRoad); road.rotation.x = -Math.PI / 2; road.position.set(0, G + .02, -18); outside.add(road);
  const plaza = new THREE.Mesh(new THREE.CircleGeometry(150, 48), new THREE.MeshStandardMaterial({ color: '#a59a8e', roughness: .95 })); plaza.rotation.x = -Math.PI / 2; plaza.position.set(LIB[0], G + .03, LIB[1]); outside.add(plaza);
  /* Национальная библиотека: ромбокубооктаэдр на стилобате */
  const k2 = 1 + Math.SQRT2, pts = [];
  for (const [a, b, c] of [[1, 1, k2], [1, k2, 1], [k2, 1, 1]]) for (const sx of [-1, 1]) for (const sy of [-1, 1]) for (const sz of [-1, 1]) pts.push(new THREE.Vector3(a * sx, b * sy, c * sz));
  const S_ = 14, libGeo = new ConvexGeometry(pts.map(p => p.multiplyScalar(S_)));
  const mLib = new THREE.MeshStandardMaterial({ color: '#36606b', roughness: .12, metalness: .7, flatShading: true, emissive: '#000000' });
  const lib = new THREE.Mesh(libGeo, mLib); lib.position.set(LIB[0], G + 9 + k2 * S_, LIB[1]); lib.rotation.y = .35; outside.add(lib);
  const libEdges = new THREE.LineSegments(new THREE.EdgesGeometry(libGeo), new THREE.LineBasicMaterial({ color: '#c9d6da', transparent: true, opacity: .55 }));
  lib.add(libEdges);
  const stylo = new THREE.Mesh(new THREE.BoxGeometry(110, 9, 80), new THREE.MeshStandardMaterial({ color: '#cfc6b8', roughness: .9 })); stylo.position.set(LIB[0], G + 4.5, LIB[1]); stylo.rotation.y = .35; outside.add(stylo);
  /* город и деревья (инстансы) */
  {
    const r = rng(7), m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), cols = ['#d8d0c3', '#c5c9cb', '#e4ddd0', '#b9b2a6', '#cfd5d8'];
    const bld = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1).translate(0, .5, 0), new THREE.MeshStandardMaterial({ roughness: .9 }), 70);
    let n = 0;
    while (n < 70) {
      const a = r() * Math.PI * 2, dist = 120 + r() * 650, x = LIB[0] + Math.sin(a) * dist * 1.2, z = -Math.abs(Math.cos(a)) * dist - 60;
      if (Math.abs(x - LIB[0]) < 130 && z > LIB[1] - 120) continue;
      const h = 15 + r() * 45, w = 20 + r() * 50, d = 14 + r() * 20;
      e.set(0, (r() - .5) * .5, 0); q.setFromEuler(e); m4.compose(new THREE.Vector3(x, G, z), q, new THREE.Vector3(w, h, d)); bld.setMatrixAt(n, m4);
      bld.setColorAt(n, new THREE.Color(cols[n % cols.length])); n++;
    }
    outside.add(bld);
    const treeGeo = merge(Cy(.25, .35, 3, 0, 1.5, 0, '#4a3826', 6), Sp(2.6, 0, 4.6, 0, '#4d6e3a', 1, 1.2, 1, 1));
    const trees = new THREE.InstancedMesh(treeGeo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1, flatShading: true }), 140);
    for (let i = 0; i < 140; i++) {
      let x, z;
      if (i < 40) { x = -90 + i * 5 + r() * 2; z = -34 - r() * 4; }            // аллея вдоль улицы
      else { do { x = LIB[0] + (r() - .5) * 420; z = -40 - r() * 170; } while (Math.hypot(x - LIB[0], z - LIB[1]) < 95); }
      const s = (i < 40 ? .55 : .7) + r() * .5; e.set(0, r() * 6, 0); q.setFromEuler(e); m4.compose(new THREE.Vector3(x, G, z), q, new THREE.Vector3(s, s, s)); trees.setMatrixAt(i, m4);
    }
    outside.add(trees);
  }

  /* ---------- свет ---------- */
  const hemi = new THREE.HemisphereLight('#e3ebf0', '#c4a57f', .6); scene.add(hemi);
  const sun = new THREE.DirectionalLight('#fff1dc', 2.6); sun.castShadow = true;
  sun.shadow.mapSize.set(MOBILE ? 1024 : 2048, MOBILE ? 1024 : 2048);
  Object.assign(sun.shadow.camera, { left: -11, right: 11, top: 11, bottom: -11, near: 1, far: 90 });
  sun.shadow.bias = -.0004; sun.shadow.normalBias = .03;
  sun.target.position.set(W / 2, 0, D / 2); scene.add(sun, sun.target);
  const lamps = [[3.2, 3.0], [11, 3.0], [3.2, 6.4], [11, 6.4]].map(([x, z]) => { const l = new THREE.PointLight('#ffd6a3', 0, 14, 1.6); l.position.set(x, H - .4, z); scene.add(l); return l; });
  const MODES = {
    day: { top: '#7fa6c6', hor: '#e7edf0', bot: '#9aa596', sunCol: '#fff4e0', sunEl: 30, sunAz: -26, sun: 2.8, hemi: .65, env: .5, led: .5, lamp: 0, exp: 1, fog: '#e2e8ea', lib: 0, ground: '#7d8a6f' },
    evening: { top: '#1f2d4a', hor: '#e6935c', bot: '#3b3a3c', sunCol: '#ff9a4d', sunEl: 7, sunAz: -40, sun: 1.5, hemi: .18, env: .2, led: 3.2, lamp: 9, exp: 1.08, fog: '#b98066', lib: 1, ground: '#4c4c45' },
  };
  const cur = {}; let modeName = 'day';
  function applyMode(a, b, t) {
    const L = (k) => a[k] + (b[k] - a[k]) * t, LC = (k) => new THREE.Color(a[k]).lerp(new THREE.Color(b[k]), t);
    const el = THREE.MathUtils.degToRad(L('sunEl')), az = THREE.MathUtils.degToRad(L('sunAz'));
    const dir = new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el)).normalize();
    sun.position.copy(sun.target.position).addScaledVector(dir, 45); sun.intensity = L('sun'); sun.color.copy(LC('sunCol'));
    const u = sky.material.uniforms; u.top.value.copy(LC('top')); u.hor.value.copy(LC('hor')); u.bot.value.copy(LC('bot')); u.sunDir.value.copy(dir); u.sunCol.value.copy(LC('sunCol'));
    hemi.intensity = L('hemi'); scene.environmentIntensity = L('env'); mLed.emissiveIntensity = L('led');
    lamps.forEach(l => l.intensity = L('lamp')); renderer.toneMappingExposure = L('exp'); scene.fog.color.copy(LC('fog')); mGround.color.copy(LC('ground'));
    cur.lib = L('lib');
  }
  applyMode(MODES.day, MODES.day, 1);
  ceilingGroup.traverse(o => o.layers.set(1)); camera.layers.enable(1); sun.shadow.camera.layers.enable(1);

  /* ---------- размеры (как на чертеже) ---------- */
  const dims = new THREE.Group(); dims.visible = false; scene.add(dims);
  {
    const lm = new THREE.LineBasicMaterial({ color: '#c9a26a', depthTest: true, toneMapped: false });
    const line = (a, b) => dims.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...a), new THREE.Vector3(...b)]), lm));
    const y = .02, o = .25;
    line([0, y, D - o], [W, y, D - o]); line([0, y, D - o - .15], [0, y, D - o + .15]); line([W, y, D - o - .15], [W, y, D - o + .15]);
    line([o, y, 0], [o, y, D]); line([o - .15, y, 0], [o + .15, y, 0]); line([o - .15, y, D], [o + .15, y, D]);
    line([.06, 0, .06], [.06, H, .06]);
    const L1 = label('14,2 м'); L1.position.set(W / 2, .35, D - o); dims.add(L1);
    const L2 = label('8,7 м'); L2.position.set(o + .1, .35, D / 2); dims.add(L2);
    const L3 = label('потолок 4,5 м'); L3.position.set(.35, H - .5, .45); dims.add(L3);
    WINX.forEach(cx => { const l = label('окно 4 × 3,5 м'); l.position.set(cx, 2.4, .35); dims.add(l); });
    const L4 = label('123 м²', 1.6); L4.position.set(W / 2 - 2.4, .5, D / 2); dims.add(L4);
    COLS.forEach(([x, z], i) => { if (i) return; const l = label('колонна', .9); l.position.set(x, 2.3, z + .35); dims.add(l); });
    const L5 = label('экран', .9); L5.position.set(W - .4, 3.4, D / 2); dims.add(L5);
    const L6 = label('вход', .9); L6.position.set(13.0, 2.6, D - .4); dims.add(L6);
  }

  /* ---------- мебель и люди ---------- */
  const F = furniture();
  let layoutName = 'empty', layoutMeshes = [];
  const anims = [];
  const PAL = ['#213641', '#5b6b75', '#c9a26a', '#8a3b3b', '#e8e2d6', '#3d5a4a', '#2b2e31', '#7c8da0', '#b86a4a', '#d8ccbb', '#4b4f6b', '#9a8f84'];
  const SKIN = ['#e9c6a8', '#d7a888', '#b98564', '#f1d3bb', '#8d5e43', '#e0b494'];
  let showPeople = true;
  function makeInst(geo, mat, list, t0, stagger, dur, colorOf) {
    const mesh = new THREE.InstancedMesh(geo, mat, list.length); mesh.castShadow = true; mesh.receiveShadow = true; mesh.frustumCulled = false;
    const items = list.map((o, i) => {
      const q = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), o.ry || 0);
      if (colorOf) mesh.setColorAt(i, new THREE.Color(colorOf(i)));
      return { p: new THREE.Vector3(o.x, o.y || 0, o.z), q, s: new THREE.Vector3(...(o.s || [1, 1, 1])), d: o.delay ?? i * stagger };
    });
    const a = { mesh, items, t0, dur, done: false }; anims.push(a); stepAnim(a, RM ? 1e9 : t0);
    scene.add(mesh); layoutMeshes.push(mesh); return mesh;
  }
  const m4 = new THREE.Matrix4(), tmpS = new THREE.Vector3();
  function stepAnim(a, now) {
    let all = true;
    a.items.forEach((it, i) => {
      let k = clamp((now - a.t0 - it.d) / a.dur, 0, 1); if (k < 1) all = false;
      const e = k <= 0 ? 0.0001 : easeBack(k);
      tmpS.set(it.s.x * (.6 + .4 * Math.min(e, 1)), it.s.y * e, it.s.z * (.6 + .4 * Math.min(e, 1)));
      m4.compose(it.p, it.q, tmpS); a.mesh.setMatrixAt(i, m4);
    });
    a.mesh.instanceMatrix.needsUpdate = true; a.done = all; return !all;
  }
  function setLayout(name, now = performance.now()) {
    layoutMeshes.forEach(m => { scene.remove(m); m.dispose(); }); layoutMeshes = []; anims.length = 0; crowd = null;
    layoutName = name; const { it, pp } = layoutItems(name);
    const camP = camera.position, byType = {};
    it.forEach(([t, x, z, ry, s]) => (byType[t] = byType[t] || []).push({ x, z, ry, s }));
    let all = it.map(([t, x, z]) => ({ t, x, z, d: Math.hypot(x - camP.x, z - camP.z) })).sort((a, b) => a.d - b.d);
    const order = new Map(all.map((o, i) => [o.t + o.x + ',' + o.z, i]));
    const span = Math.min(900, 18 * all.length), per = all.length ? span / all.length : 0;
    for (const t in byType) makeInst(F[t], mFurn, byType[t].map(o => ({ ...o, delay: (order.get(t + o.x + ',' + o.z) || 0) * per })), now, 0, 420);
    if (showPeople && pp.length) placePeople(pp, now + span + 300); else setTimeout(() => onSettled(), span + 600);
    dirty = true; shadowDirty = true;
  }
  /* гости заходят через дверь по одному и идут к своим местам; сидящие садятся, когда дошли */
  const DOOR = [13.0, 8.45], AISLE = 7.95;
  let crowd = null;
  function placePeople(pp, t0) {
    pp = pp.filter(([, x, z]) => !Object.values(VIEWS).some(v => v.p && Math.hypot(v.p[0] - x, v.p[2] - z) < .75));
    const r = rng(pp.length * 31 + 5), n = pp.length;
    // ближние к двери заходят последними, чтобы не загораживать проход
    const order = pp.map((q, i) => [i, -Math.hypot(q[1] - DOOR[0], q[2] - DOOR[1]) + r() * 3]).sort((a, b) => a[1] - b[1]).map(a => a[0]);
    const gap = RM ? 0 : clamp(9000 / n, 140, 650), rank = new Map(order.map((v, i) => [v, i]));
    const ppl = pp.map(([k, x, z, ry], i) => {
      ry += (r() - .5) * .25;
      const sit = k === 'pSit', fx = Math.sin(ry), fz = Math.cos(ry), s = .93 + r() * .14;
      const ax = sit ? x - fx * .5 : x, az = sit ? z - fz * .5 : z;     // к стулу подходят сзади
      const pts = [[DOOR[0], DOOR[1]], [DOOR[0] - .3, AISLE], [ax, AISLE], [ax, az], [x, z]]
        .filter((q, j, a) => !j || Math.hypot(q[0] - a[j - 1][0], q[1] - a[j - 1][1]) > .01);
      const segs = []; let len = 0; for (let j = 1; j < pts.length; j++) { const l = Math.hypot(pts[j][0] - pts[j - 1][0], pts[j][1] - pts[j - 1][1]); segs.push(l); len += l; }
      return { pts, segs, len, sit, ry, s, x, z, delay: rank.get(i) * gap, speed: 1.25 + r() * .35, phase: r() * 6 };
    });
    const mk = (geo, mat, count) => { const m = new THREE.InstancedMesh(geo, mat, Math.max(count, 1)); m.count = count; m.castShadow = true; m.frustumCulled = false; scene.add(m); layoutMeshes.push(m); return m; };
    const sitters = ppl.filter(p => p.sit);
    const stand = mk(F.pStand, mBody, n), sitM = mk(F.pSit, mBody, sitters.length), head = mk(F.head, mHead, n);
    let si = 0;
    ppl.forEach((p, i) => {
      const c = new THREE.Color(PAL[Math.floor(r() * PAL.length)]); stand.setColorAt(i, c);
      if (p.sit) { p.si = si; sitM.setColorAt(si++, c); }
      head.setColorAt(i, new THREE.Color(SKIN[Math.floor(r() * SKIN.length)]));
    });
    crowd = { ppl, stand, sitM, head, t0, done: false };
    stepCrowd(RM ? 1e12 : t0);
  }
  const ZERO = new THREE.Vector3(0, 0, 0), qY = new THREE.Quaternion(), vP = new THREE.Vector3(), vS = new THREE.Vector3(), UP = new THREE.Vector3(0, 1, 0);
  function put(mesh, i, x, y, z, ry, s) { qY.setFromAxisAngle(UP, ry); vP.set(x, y, z); if (s) vS.set(s, s, s); m4.compose(vP, qY, s ? vS : ZERO); mesh.setMatrixAt(i, m4); }
  function stepCrowd(now) {
    if (!crowd || crowd.done) return false;
    let moving = false;
    crowd.ppl.forEach((p, i) => {
      const d = (now - crowd.t0 - p.delay) / 1000 * p.speed;
      if (d < 0) { moving = true; put(crowd.stand, i, 0, 0, 0, 0, 0); put(crowd.head, i, 0, 0, 0, 0, 0); if (p.sit) put(crowd.sitM, p.si, 0, 0, 0, 0, 0); return; }
      if (d < p.len) {
        moving = true; let rest = d, j = 0; while (j < p.segs.length - 1 && rest > p.segs[j]) rest -= p.segs[j++];
        const a = p.pts[j], b = p.pts[j + 1], k = p.segs[j] ? rest / p.segs[j] : 1, x = a[0] + (b[0] - a[0]) * k, z = a[1] + (b[1] - a[1]) * k;
        const yaw = Math.atan2(b[0] - a[0], b[1] - a[1]), bob = Math.abs(Math.sin(d * 5.2 + p.phase)) * .035;
        const sc = Math.hypot(x - camera.position.x, z - camera.position.z) < .9 ? 0 : p.s;  // проходящих сквозь камеру не показываем
        put(crowd.stand, i, x, bob, z, yaw, sc); put(crowd.head, i, x, 1.58 * p.s + bob, z, yaw, sc);
        if (p.sit) put(crowd.sitM, p.si, 0, 0, 0, 0, 0);
      } else if (p.sit) {
        put(crowd.stand, i, 0, 0, 0, 0, 0); put(crowd.sitM, p.si, p.x, 0, p.z, p.ry, p.s);
        put(crowd.head, i, p.x - Math.sin(p.ry) * .03, 1.24 * p.s, p.z - Math.cos(p.ry) * .03, p.ry, p.s);
      } else { put(crowd.stand, i, p.x, 0, p.z, p.ry, p.s); put(crowd.head, i, p.x, 1.58 * p.s, p.z, p.ry, p.s); }
    });
    crowd.stand.instanceMatrix.needsUpdate = crowd.sitM.instanceMatrix.needsUpdate = crowd.head.instanceMatrix.needsUpdate = true;
    if (!moving) { crowd.done = true; onSettled(); }
    return true;
  }
  let onSettled = () => {};

  /* ---------- камера и управление ---------- */
  const st = { p: new THREE.Vector3(), yaw: 0, pitch: 0, fov: 62, plan: false };
  const lookYawPitch = (p, at) => { const dx = at[0] - p[0], dy = at[1] - p[1], dz = at[2] - p[2]; return [Math.atan2(-dx, -dz), Math.atan2(dy, Math.hypot(dx, dz))]; };
  function planPose() {
    const portrait = camera.aspect < 1, vf = THREE.MathUtils.degToRad(50), hf = 2 * Math.atan(Math.tan(vf / 2) * camera.aspect);
    const w = portrait ? D : W, d = portrait ? W : D, dist = Math.max((d / 2 + .8) / Math.tan(vf / 2) / .74, (w / 2 + .8) / Math.tan(hf / 2)) + H;
    const yaw = portrait ? -Math.PI / 2 : 0, down = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw)).multiplyScalar(2 * dist * Math.tan(vf / 2) * .13);  // сдвиг вверх: снизу панель
    return { p: new THREE.Vector3(W / 2, dist, D / 2).add(down), yaw, pitch: -Math.PI / 2 + 1e-4, fov: 50 };
  }
  function poseOf(name) {
    if (name === 'plan') return { ...planPose(), plan: true };
    const v = VIEWS[name], [yaw, pitch] = lookYawPitch(v.p, v.at); return { p: new THREE.Vector3(...v.p), yaw, pitch, fov: name === 'window' ? 55 : 62, plan: false };
  }
  let tween = null, dirty = true, shadowDirty = true, viewName = 'start';
  function apply() {
    camera.position.copy(st.p); camera.rotation.set(st.pitch, st.yaw, 0); if (camera.fov !== st.fov) { camera.fov = st.fov; camera.updateProjectionMatrix(); }
    if (camera.position.y < H + .1) camera.layers.enable(1); else camera.layers.disable(1); sky.position.copy(camera.position);
    dirty = true;
  }
  function go(pose, dur = 1200) {
    if (RM || dur <= 0) { Object.assign(st, { p: pose.p.clone(), yaw: pose.yaw, pitch: pose.pitch, fov: pose.fov, plan: pose.plan }); tween = null; apply(); return; }
    let dy = pose.yaw - st.yaw; dy = Math.atan2(Math.sin(dy), Math.cos(dy));
    tween = { t0: performance.now(), dur, from: { p: st.p.clone(), yaw: st.yaw, pitch: st.pitch, fov: st.fov }, to: { ...pose, yaw: st.yaw + dy }, plan: pose.plan };
    st.plan = false;
  }
  function stepTween(now) {
    if (!tween) return false;
    const k = clamp((now - tween.t0) / tween.dur, 0, 1), e = ease(k), a = tween.from, b = tween.to;
    st.p.lerpVectors(a.p, b.p, e); st.yaw = a.yaw + (b.yaw - a.yaw) * e; st.pitch = a.pitch + (b.pitch - a.pitch) * e; st.fov = a.fov + (b.fov - a.fov) * e;
    // при спуске из плана — дуга, чтобы не проходить сквозь потолок «в лоб»
    if (k >= 1) { st.plan = !!tween.plan; tween = null; }
    apply(); return true;
  }
  function solid(x, z) {
    const r = .3;
    if (COLS.some(([cx, cz]) => Math.abs(x - cx) < COLW / 2 + r && Math.abs(z - cz) < COLW / 2 + r)) return true;
    return Math.abs(x - PLINTH[0]) < PLINTH[2] / 2 + r && z < PLINTH[1] + PLINTH[3] / 2 + r;
  }
  function clampPos(p, prev) {
    p.x = clamp(p.x, .35, W - .35); p.z = clamp(p.z, .4, D - .35);
    if (solid(p.x, p.z)) { if (!solid(p.x, prev.z)) p.z = prev.z; else if (!solid(prev.x, p.z)) p.x = prev.x; else { p.x = prev.x; p.z = prev.z; } }
    return p;
  }
  function walkTo(x, z) {
    const target = clampPos(new THREE.Vector3(x, EYE, z), st.p.clone());
    if (solid(target.x, target.z)) { const c = COLS.find(([cx, cz]) => Math.hypot(target.x - cx, target.z - cz) < 1) || [PLINTH[0], 0]; const dx = target.x - c[0], dz = target.z - c[1], l = Math.hypot(dx, dz) || 1; target.x = c[0] + dx / l * .9; target.z = c[1] + dz / l * .9; clampPos(target, target.clone()); }
    if (st.plan) { go({ p: target, yaw: st.yaw, pitch: -.08, fov: 62, plan: false }, 1500); setView(null); return; }
    const dist = st.p.distanceTo(target); go({ p: target, yaw: st.yaw, pitch: st.pitch, fov: st.fov, plan: false }, clamp(dist / 2.6 * 1000, 450, 2600));
    setView(null);
  }

  /* указатель: перетаскивание = осмотреться, короткий клик по полу = перейти */
  const ray = new THREE.Raycaster(), ndc = new THREE.Vector2(), floorPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0), hit = new THREE.Vector3();
  const reticle = new THREE.Mesh(new THREE.RingGeometry(.16, .22, 40), new THREE.MeshBasicMaterial({ color: '#c9a26a', transparent: true, opacity: .9, depthWrite: false, toneMapped: false }));
  reticle.rotation.x = -Math.PI / 2; reticle.visible = false; reticle.renderOrder = 4; scene.add(reticle);
  function floorAt(ev) {
    const r = canvas.getBoundingClientRect(); ndc.set((ev.clientX - r.left) / r.width * 2 - 1, -(ev.clientY - r.top) / r.height * 2 + 1);
    ray.setFromCamera(ndc, camera); if (!ray.ray.intersectPlane(floorPlane, hit)) return null;
    if (hit.x < 0 || hit.x > W || hit.z < 0 || hit.z > D) return null; return hit.clone();
  }
  let drag = null; const onFirst = opts.onInteract || (() => {});
  canvas.addEventListener('pointerdown', ev => {
    if (drag || (ev.pointerType === 'mouse' && ev.button !== 0)) return;
    drag = { id: ev.pointerId, x: ev.clientX, y: ev.clientY, t: performance.now(), moved: 0 }; canvas.setPointerCapture(ev.pointerId); onFirst();
  });
  canvas.addEventListener('pointermove', ev => {
    if (drag && ev.pointerId === drag.id) {
      const dx = ev.clientX - drag.x, dy = ev.clientY - drag.y; drag.x = ev.clientX; drag.y = ev.clientY; drag.moved += Math.abs(dx) + Math.abs(dy);
      if (drag.moved > 6 && !st.plan) { tween = null; const k = .0042 * st.fov / 62; st.yaw += dx * k; st.pitch = clamp(st.pitch + dy * k, -1.35, 1.35); setView(null); apply(); }
      reticle.visible = false;
    } else if (ev.pointerType === 'mouse') {
      const p = floorAt(ev); reticle.visible = !!p && !solid(p.x, p.z); if (p) reticle.position.set(p.x, .012, p.z); dirty = true;
    }
  });
  const end = ev => {
    if (!drag || ev.pointerId !== drag.id) return;
    const click = drag.moved < 8 && performance.now() - drag.t < 600; drag = null;
    if (click && ev.type === 'pointerup') { const p = floorAt(ev); if (p) walkTo(p.x, p.z); }
  };
  canvas.addEventListener('pointerup', end); canvas.addEventListener('pointercancel', end);
  canvas.addEventListener('pointerleave', () => { reticle.visible = false; dirty = true; });

  /* клавиатура: W/S или ↑/↓ — идти, A/D — шаг вбок, ←/→ — повернуться, Shift — быстрее */
  const keys = new Set();
  canvas.addEventListener('keydown', ev => {
    const k = ev.key.toLowerCase(); if (['w', 'a', 's', 'd', 'ц', 'ф', 'ы', 'в', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright', 'shift'].includes(k)) { keys.add(k); ev.preventDefault(); onFirst(); }
  });
  canvas.addEventListener('keyup', ev => keys.delete(ev.key.toLowerCase()));
  canvas.addEventListener('blur', () => keys.clear());
  function stepKeys(dt) {
    if (!keys.size) return false;
    if (st.plan) { if (['w', 'arrowup', 'ц'].some(k => keys.has(k))) walkTo(st.p.x, st.p.z); keys.clear(); return true; }
    const has = (...k) => k.some(x => keys.has(x));
    let f = (has('w', 'ц', 'arrowup') ? 1 : 0) - (has('s', 'ы', 'arrowdown') ? 1 : 0), s = (has('d', 'в') ? 1 : 0) - (has('a', 'ф') ? 1 : 0), turn = (has('arrowleft') ? 1 : 0) - (has('arrowright') ? 1 : 0);
    if (!f && !s && !turn) return false;
    tween = null; setView(null);
    st.yaw += turn * 1.7 * dt;
    const sp = (keys.has('shift') ? 4.2 : 2.3) * dt, prev = st.p.clone();
    st.p.x += (-Math.sin(st.yaw) * f + Math.cos(st.yaw) * s) * sp; st.p.z += (-Math.cos(st.yaw) * f - Math.sin(st.yaw) * s) * sp; st.p.y = EYE;
    clampPos(st.p, prev); apply(); return true;
  }

  /* ---------- цикл: рисуем только когда что-то меняется ---------- */
  let raf = 0, last = performance.now(), visible = true, modeTween = null, libT = 0, frameN = 0;
  function frame(now) {
    raf = requestAnimationFrame(frame);
    const dt = Math.min(.05, (now - last) / 1000); last = now;
    let busy = stepTween(now) | stepKeys(dt), shade = false;
    for (const a of anims) if (!a.done) { busy |= stepAnim(a, now); shade = true; }
    if (stepCrowd(now)) { busy = 1; if ((frameN = (frameN + 1) % 3) === 0) shade = true; }
    if (modeTween) { const k = clamp((now - modeTween.t0) / 1100, 0, 1); applyMode(modeTween.a, modeTween.b, ease(k)); if (k >= 1) modeTween = null; busy = 1; shade = true; }
    // подсветка Библиотеки вечером меняет цвет медленно: 8 кадров в секунду достаточно
    if (cur.lib > .01 && now - libT > 125) { libT = now; const h = (now / 1000 * .035) % 1; mLib.emissive.setHSL(h, .75, .5 * cur.lib); mLib.emissiveIntensity = 1.6; libEdges.material.color.setHSL((h + .5) % 1, .8, .5 + .3 * cur.lib); busy = 1; }
    else if (cur.lib <= .01 && mLib.emissive.getHex()) { mLib.emissive.set(0); libEdges.material.color.set('#c9d6da'); busy = 1; }
    if (shade || shadowDirty) { renderer.shadowMap.needsUpdate = true; shadowDirty = false; }
    if (busy || dirty) { renderer.render(scene, camera); dirty = false; }
  }
  function run(on) { if (on && !raf && visible) { last = performance.now(); raf = requestAnimationFrame(frame); } else if (!on && raf) { cancelAnimationFrame(raf); raf = 0; } }
  new IntersectionObserver(([e]) => { visible = e.isIntersecting && !document.hidden; run(visible); }).observe(root);
  document.addEventListener('visibilitychange', () => { visible = !document.hidden; run(visible); });
  const resize = () => {
    const w = canvas.clientWidth || root.clientWidth, h = canvas.clientHeight || root.clientHeight; if (!w || !h) return;
    renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
    if (st.plan) { const p = planPose(); Object.assign(st, { p: p.p, yaw: p.yaw, pitch: p.pitch, fov: p.fov }); apply(); }
    dirty = true;
  };
  new ResizeObserver(resize).observe(canvas);

  /* ---------- API для панели ---------- */
  let onChange = opts.onChange || (() => {});
  function setView(name) { viewName = name; onChange(state()); }
  const state = () => ({ layout: layoutName, view: viewName, mode: modeName, people: showPeople, dims: dims.visible, info: LAYOUTS[layoutName] });
  const api = {
    LAYOUTS, state,
    layout(name) { if (!LAYOUTS[name]) return; setLayout(name); onChange(state()); },
    view(name) { if (!VIEWS[name]) return; go(poseOf(name), st.plan || name === 'plan' ? 1600 : 1300); viewName = name; onChange(state()); },
    mode(name) { if (!MODES[name] || name === modeName) return; modeTween = RM ? null : { t0: performance.now(), a: MODES[modeName], b: MODES[name] }; if (RM) applyMode(MODES[name], MODES[name], 1); modeName = name; dirty = true; shadowDirty = true; onChange(state()); },
    people(on) { showPeople = on; setLayout(layoutName); onChange(state()); },
    dims(on) { dims.visible = on; dirty = true; onChange(state()); },
    focus() { canvas.focus({ preventScroll: true }); },
    onSettled(fn) { onSettled = fn || (() => {}); },
  };
  const init = opts.init || {};
  showPeople = init.people !== false;
  if (init.mode === 'evening') { modeName = 'evening'; applyMode(MODES.evening, MODES.evening, 1); }
  resize();
  const v0 = VIEWS[init.view] ? init.view : (LAYOUTS[init.layout] && init.layout !== 'empty' ? 'door' : 'start'); go(poseOf(v0), 0); viewName = v0;
  setLayout(LAYOUTS[init.layout] ? init.layout : 'empty', RM ? 0 : performance.now() + 500);
  if (init.dims) dims.visible = true;
  renderer.shadowMap.needsUpdate = true; renderer.render(scene, camera);
  run(true); onChange(state());
  return api;
}

window.Arka3D = { start };
