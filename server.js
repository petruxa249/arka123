/* АРКА 123: сервер сайта без зависимостей. Запуск: node server.js
   Переменные окружения:
     PORT (3000), ADMIN_KEY (ключ входа в /admin; без него создаётся data/admin-key.txt),
     TRUST_PROXY=1 (сервер стоит за nginx/Cloudflare: адрес гостя берётся из X-Forwarded-For, cookie получает Secure),
     TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID (уведомления), WEBHOOK_URL и WEBHOOK_SECRET (вебхук в календарь/Zapier/Make),
     NODE_ENV=production (не печатать ключ в консоль). */
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const zlib = require('zlib');

const PORT = +process.env.PORT || 3000;
const ROOT = __dirname;
const DATA_DIR = path.join(ROOT, 'data');
const DB_FILE = path.join(DATA_DIR, 'requests.json');
const KEY_FILE = path.join(DATA_DIR, 'admin-key.txt');
const CAL_FILE = path.join(DATA_DIR, 'calendar-stub.json');
const TZ = 'Europe/Minsk';
const OPEN = 9, CLOSE = 21, MIN_DUR = 2, HOLD_MS = 24 * 3600e3, HORIZON_DAYS = 180;
const MAX_HOLDS = 3; /* неподтверждённых броней одновременно с одного адреса или одного контакта */
const CHANNELS = ['Telegram', 'WhatsApp', 'Viber', 'звонок', 'E-mail'];
const TRUST_PROXY = process.env.TRUST_PROXY === '1';
const PROD = process.env.NODE_ENV === 'production';

fs.mkdirSync(DATA_DIR, { recursive: true });
if (!fs.existsSync(DB_FILE)) fs.writeFileSync(DB_FILE, '[]', { mode: 0o600 });
let ADMIN_KEY = process.env.ADMIN_KEY;
if (!ADMIN_KEY) {
  if (!fs.existsSync(KEY_FILE)) fs.writeFileSync(KEY_FILE, crypto.randomBytes(18).toString('base64url'), { mode: 0o600 });
  ADMIN_KEY = fs.readFileSync(KEY_FILE, 'utf8').trim();
}
const hmac = (k, s) => crypto.createHmac('sha256', k).update(s).digest();
/* отдельный токен для подписки .ics: адрес календаря попадает в Google/Apple, поэтому в нём не главный ключ */
const ICS_TOKEN = hmac(ADMIN_KEY, 'arka-ics').toString('base64url').slice(0, 32);
const ipSalt = hmac(ADMIN_KEY, 'arka-ip');

const load = () => JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
const save = (list) => { const tmp = DB_FILE + '.tmp'; fs.writeFileSync(tmp, JSON.stringify(list, null, 2), { mode: 0o600 }); fs.renameSync(tmp, DB_FILE); };
const safely = (fn) => { try { fn(); } catch (e) { console.error('[ошибка побочного действия]', e.message); } };

/* дата и час в Минске */
function minskNow() {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-GB', { timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', hour12: false })
    .formatToParts(new Date()).map(x => [x.type, x.value]));
  return { date: `${p.year}-${p.month}-${p.day}`, hour: +p.hour % 24 };
}
const addDays = (iso, n) => { const d = new Date(iso + 'T00:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
const validDate = (s) => typeof s === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(s) && new Date(s + 'T00:00:00Z').toISOString().slice(0, 10) === s;
const isActive = (r) => r.booking && (r.status === 'confirmed' || (r.status === 'new' && Date.now() - r.createdAt < HOLD_MS));

function busyMap(list, from, to) {
  const busy = {};
  for (const r of list) {
    if (!isActive(r)) continue;
    const { date, start, dur } = r.booking;
    if (date < from || date > to) continue;
    for (let h = start; h < start + dur; h++) (busy[date] = busy[date] || []).push(h);
  }
  return busy;
}
const price = (start, dur) => { let s = 0; for (let h = start; h < start + dur; h++) s += h >= 17 ? 120 : 90; return s; };

/* ограничение частоты: окно 10 минут, отдельно для заявок и для входа в админку */
const buckets = { req: new Map(), login: new Map() };
function limited(kind, ip, max) {
  const m = buckets[kind], now = Date.now(), arr = (m.get(ip) || []).filter(t => now - t < 600e3);
  arr.push(now); m.set(ip, arr); return arr.length > max;
}
setInterval(() => { const now = Date.now(); for (const m of Object.values(buckets)) for (const [k, a] of m) if (!a.some(t => now - t < 600e3)) m.delete(k); }, 600e3).unref();

const clientIp = (req) => (TRUST_PROXY && String(req.headers['x-forwarded-for'] || '').split(',')[0].trim()) || req.socket.remoteAddress || '';
const ipHash = (ip) => hmac(ipSalt, ip).toString('hex').slice(0, 16); /* в базе хранится не адрес, а его хэш */
const contactKey = (c) => { const d = String(c || '').replace(/\D/g, ''); return d.length >= 7 ? d.slice(-9) : String(c || '').toLowerCase().replace(/^@/, ''); };

const clean = (v, max) => String(v == null ? '' : v).replace(/[\u0000-\u001f\u007f\u2028\u2029]/g, ' ').trim().slice(0, max);

function validate(body) {
  const err = (m) => ({ error: m });
  if (!body || typeof body !== 'object' || Array.isArray(body)) return err('Неверный запрос');
  if (clean(body.website, 50)) return err('Спам-фильтр');
  const name = clean(body.name, 80), contact = clean(body.contact, 120);
  if (name.length < 2) return err('Введите имя');
  if (contact.length < 3) return err('Укажите, как с вами связаться');
  const channel = CHANNELS.includes(body.channel) ? body.channel : 'Telegram';
  if (channel === 'E-mail' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contact)) return err('Проверьте адрес почты');
  if (['WhatsApp', 'Viber', 'звонок'].includes(channel) && contact.replace(/\D/g, '').length < 7) return err('Проверьте номер телефона');
  const guests = Math.max(0, Math.min(500, parseInt(body.guests, 10) || 0));
  const rec = { name, contact, channel, format: clean(body.format, 40), guests, message: clean(body.message, 500) };
  if (body.booking) {
    const b = body.booking, now = minskNow();
    if (typeof b !== 'object') return err('Недопустимая дата');
    const date = String(b.date), start = b.start, dur = b.dur;
    if (!validDate(date) || date < now.date || date > addDays(now.date, HORIZON_DAYS)) return err('Недопустимая дата');
    if (!Number.isInteger(start) || !Number.isInteger(dur) || start < OPEN || dur < MIN_DUR || start + dur > CLOSE) return err('Недопустимое время');
    if (date === now.date && start <= now.hour) return err('Это время уже прошло');
    rec.booking = { date, start, dur, price: price(start, dur) };
  }
  return { rec };
}

const post = (url, body, headers = {}) => fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json', ...headers }, body, signal: AbortSignal.timeout(5000) })
  .catch((e) => console.error('[уведомление не ушло]', new URL(url).host, e.name));

function notify(r) {
  const token = process.env.TELEGRAM_BOT_TOKEN, chat = process.env.TELEGRAM_CHAT_ID;
  if (!token || !chat) return;
  const b = r.booking;
  const text = `Новая заявка АРКА 123\n${r.name} · ${r.channel}: ${r.contact}\n` + (b ? `Бронь: ${b.date}, ${b.start}:00–${b.start + b.dur}:00, ${b.price} BYN\n` : '') +
    `Формат: ${r.format || '—'}, гостей: ${r.guests || '—'}` + (r.message ? `\n${r.message}` : '');
  post(`https://api.telegram.org/bot${token}/sendMessage`, JSON.stringify({ chat_id: chat, text }));
}

/* вебхук: WEBHOOK_URL получает JSON при создании, подтверждении и отмене заявки (Zapier, Make, n8n, Google Apps Script).
   Подпись: X-Arka-Signature = sha256=HMAC(WEBHOOK_SECRET, X-Arka-Timestamp + "." + тело). Проверяйте её и возраст метки (не старше 5 минут).
   X-Arka-Secret оставлен для простых сервисов, которые умеют только сравнить заголовок (только по HTTPS). */
const iso = (date, h) => `${date}T${String(h).padStart(2, '0')}:00:00+03:00`;
function hook(event, r) {
  const url = process.env.WEBHOOK_URL;
  if (!url) return;
  const b = r.booking;
  const body = JSON.stringify({ event, id: r.id, status: r.status, name: r.name, channel: r.channel, contact: r.contact, format: r.format, guests: r.guests, message: r.message,
    booking: b ? { ...b, startISO: iso(b.date, b.start), endISO: iso(b.date, b.start + b.dur), summary: `АРКА 123: ${r.name} (${r.format || 'аренда'})` } : null });
  const secret = process.env.WEBHOOK_SECRET || '', ts = String(Math.floor(Date.now() / 1000));
  const headers = { 'X-Arka-Event': event, 'X-Arka-Timestamp': ts };
  if (secret) Object.assign(headers, { 'X-Arka-Signature': 'sha256=' + hmac(secret, ts + '.' + body).toString('hex'), 'X-Arka-Secret': secret });
  post(url, body, headers);
}
/* Запись в календарь: ЗАГЛУШКА для тестового задания. Событие собирается в формате Google Calendar API (events.insert)
   и сохраняется в data/calendar-stub.json. Чтобы писать в настоящий календарь, замените тело calendarWrite на вызов
   calendar.events.insert({ calendarId, requestBody: event }) с сервисным аккаунтом Google. */
function calendarWrite(action, r) {
  let cal = []; try { cal = JSON.parse(fs.readFileSync(CAL_FILE, 'utf8')); } catch (e) {}
  const b = r.booking; if (!b) return;
  cal = cal.filter(x => x.id !== r.id);
  if (action !== 'remove') cal.push({ id: r.id, calendarId: 'arka123@stub.calendar', event: {
    summary: `АРКА 123: ${r.name} (${r.format || 'аренда'})`, status: action === 'confirm' ? 'confirmed' : 'tentative',
    description: `${r.channel}: ${r.contact}\nГостей: ${r.guests || '—'}\n${b.price} BYN\n${r.message || ''}`,
    start: { dateTime: iso(b.date, b.start), timeZone: TZ }, end: { dateTime: iso(b.date, b.start + b.dur), timeZone: TZ } } });
  fs.writeFileSync(CAL_FILE, JSON.stringify(cal, null, 2), { mode: 0o600 });
  console.log(`[календарь-заглушка] ${action}: ${b.date} ${b.start}:00`);
}
/* календарь-подписка (.ics): Google Календарь, Apple, Outlook. Строки длиннее 75 байт переносятся по RFC 5545. */
function ics(list) {
  const stamp = (d) => d.toISOString().replace(/[-:]/g, '').replace(/\.\d+/, '');
  const esc2 = (t) => String(t || '').replace(/[\\;,]/g, m => '\\' + m).replace(/\n/g, '\\n');
  const fold = (line) => { const out = []; let cur = '', n = 0;
    for (const ch of line) { const len = Buffer.byteLength(ch); if (n + len > 74) { out.push(cur); cur = ' '; n = 1; } cur += ch; n += len; }
    out.push(cur); return out.join('\r\n'); };
  const ev = list.filter(isActive).map(r => { const b = r.booking;
    return ['BEGIN:VEVENT', `UID:${r.id}@arka123`, `DTSTAMP:${stamp(new Date())}`, `DTSTART:${stamp(new Date(iso(b.date, b.start)))}`, `DTEND:${stamp(new Date(iso(b.date, b.start + b.dur)))}`,
      `SUMMARY:${esc2('АРКА 123: ' + r.name + (r.status === 'new' ? ' (не подтверждено)' : ''))}`,
      `DESCRIPTION:${esc2(`${r.channel}: ${r.contact}\n${r.format || ''}, гостей: ${r.guests || '—'}\n${b.price} BYN\n${r.message || ''}`)}`, 'END:VEVENT'].map(fold).join('\r\n'); });
  return ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//ARKA123//RU', 'CALSCALE:GREGORIAN', fold('X-WR-CALNAME:АРКА 123 · брони'), ...ev, 'END:VCALENDAR'].join('\r\n') + '\r\n';
}

/* ---------- заголовки безопасности ---------- */
const BASE_HEADERS = {
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
  'Cross-Origin-Opener-Policy': 'same-origin',
};
const SITE_CSP = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; " +
  "font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; " +
  "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'self'";
const ADMIN_CSP = "default-src 'none'; style-src 'unsafe-inline'; img-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'";
const head = (res, code, extra = {}) => res.writeHead(code, { ...BASE_HEADERS, ...(TRUST_PROXY ? { 'Strict-Transport-Security': 'max-age=31536000' } : {}), ...extra });

const send = (res, code, obj) => { head(res, code, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' }); res.end(JSON.stringify(obj)); };
const readBody = (req, max) => new Promise((ok, no) => {
  const parts = []; let n = 0;
  req.on('data', c => { n += c.length; if (n > max) { no(Object.assign(new Error('big'), { code: 413 })); req.destroy(); } else parts.push(c); });
  req.on('end', () => ok(Buffer.concat(parts).toString('utf8')));
  req.on('error', no);
});
const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
/* сравнение секретов за постоянное время и без утечки длины */
const same = (a, b) => crypto.timingSafeEqual(hmac('cmp', String(a || '')), hmac('cmp', String(b || '')));

/* ---------- вход в админку: ключ меняется на cookie, в адресе ключа больше нет ---------- */
const SESS = new Map(); const SESS_MS = 12 * 3600e3;
const cookies = (req) => Object.fromEntries(String(req.headers.cookie || '').split(';').map(s => s.trim().split('=')).filter(p => p[0]).map(([k, ...v]) => [k, v.join('=')]));
function session(req) { const t = cookies(req).arka_admin; const exp = t && SESS.get(t); if (!exp) return null; if (exp < Date.now()) { SESS.delete(t); return null; } return t; }
function startSession(req) {
  const t = crypto.randomBytes(24).toString('base64url'); SESS.set(t, Date.now() + SESS_MS);
  const secure = TRUST_PROXY && /https/i.test(String(req.headers['x-forwarded-proto'] || '')) ? '; Secure' : '';
  return `arka_admin=${t}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${SESS_MS / 1000}${secure}`;
}
/* запросы, меняющие данные админки, принимаются только со своего сайта */
const sameOrigin = (req) => { const o = req.headers.origin || req.headers.referer; if (!o || o === 'null') return !req.headers.origin; try { return new URL(o).host === req.headers.host; } catch (e) { return false; } };

const PAGE = (title, body) => `<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>${title}</title>` +
  `<style>body{font:14px system-ui;margin:24px;color:#1a1f23}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ddd;padding:8px;text-align:left;vertical-align:top}input{font:inherit;padding:6px 8px}button{font:inherit;padding:6px 12px;cursor:pointer}.top{display:flex;gap:12px;align-items:center;justify-content:space-between}code{background:#f3f3f3;padding:2px 6px;word-break:break-all}.err{color:#a3261a}</style>${body}</html>`;
const loginPage = (msg = '') => PAGE('Вход · АРКА 123', `<h1>Заявки АРКА 123</h1>${msg ? `<p class="err">${esc(msg)}</p>` : ''}<form method="post" action="/admin/login"><label>Ключ администратора <input type="password" name="key" autocomplete="current-password" required autofocus></label> <button>Войти</button></form><p>Ключ лежит в data/admin-key.txt или в переменной ADMIN_KEY.</p>`);

function adminPage(req) {
  const list = load().slice().reverse();
  const rows = list.map(r => {
    const b = r.booking;
    const st = !b ? r.status : (isActive(r) ? r.status : (r.status === 'new' ? 'истекла' : r.status));
    return `<tr><td>${esc(new Date(r.createdAt).toLocaleString('ru-RU', { timeZone: TZ }))}</td><td>${esc(r.name)}</td><td>${esc(r.channel)}: ${esc(r.contact)}</td><td>${b ? esc(`${b.date} ${b.start}:00–${b.start + b.dur}:00, ${b.price} BYN`) : '—'}</td><td>${esc(r.format)} · ${esc(r.guests || '')}</td><td>${esc(r.message)}</td><td>${esc(st)}</td>` +
      `<td>${['confirm', 'cancel'].map(a => `<form method="post" action="/api/admin/${a}" style="display:inline"><input type="hidden" name="id" value="${esc(r.id)}"><button>${a === 'confirm' ? 'Подтвердить' : 'Отменить'}</button></form>`).join(' ')}</td></tr>`;
  }).join('');
  const host = /^[\w.\-]+(:\d+)?$/.test(req.headers.host || '') ? req.headers.host : 'localhost:' + PORT;
  const icsUrl = `${TRUST_PROXY ? 'https' : 'http'}://${host}/calendar.ics?token=${ICS_TOKEN}`;
  return PAGE('Заявки АРКА 123', `<div class="top"><h1>Заявки (${list.length})</h1><form method="post" action="/admin/logout"><button>Выйти</button></form></div>` +
    `<p>Подписка на календарь броней (Google, Apple, Outlook), адрес секретный: <code>${esc(icsUrl)}</code></p>` +
    `<table><tr><th>Когда<th>Имя<th>Связь<th>Бронь<th>Формат<th>Комментарий<th>Статус<th></tr>${rows}</table>` +
    `<h2>Календарь (заглушка записи)</h2><pre>${esc(fs.existsSync(CAL_FILE) ? fs.readFileSync(CAL_FILE, 'utf8') : '[]')}</pre>`);
}
const html = (res, code, body, extra = {}) => { head(res, code, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store', 'Content-Security-Policy': ADMIN_CSP, 'X-Frame-Options': 'DENY', ...extra }); res.end(body); };
const redirect = (res, to, extra = {}) => { head(res, 303, { Location: to, 'Cache-Control': 'no-store', ...extra }); res.end(); };

/* ---------- статика: отдаются только файлы сайта из белого списка расширений ---------- */
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.avif': 'image/avif',
  '.svg': 'image/svg+xml', '.mp4': 'video/mp4', '.webm': 'video/webm', '.ico': 'image/x-icon', '.woff2': 'font/woff2' };
const PRIVATE = new Set(['server.js']);
const ZIP = /^(text\/|image\/svg)/;
const gzCache = new Map();

function serveStatic(req, res, url) {
  let p;
  try { p = decodeURIComponent(url.pathname); } catch (e) { head(res, 400); return res.end(); }
  if (p.endsWith('/')) p += 'index.html';
  const rel = p.replace(/^\/+/, '');
  const segs = rel.split('/');
  /* без обратных слэшей, двоеточий (потоки NTFS), точек в начале и пробелов/точек в конце имени: на Windows «DATA/» и «data./» это тоже data */
  const bad = !rel || /[\\:\0]/.test(rel) || segs.some(s => !s || s.startsWith('.') || /[. ]$/.test(s)) ||
    ['data', 'node_modules'].includes(segs[0].toLowerCase()) || PRIVATE.has(rel.toLowerCase());
  const ext = path.extname(rel).toLowerCase(), type = MIME[ext];
  const file = path.resolve(ROOT, rel);
  if (bad || !type || !file.startsWith(ROOT + path.sep)) { head(res, 404, { 'Content-Type': 'text/plain; charset=utf-8' }); return res.end('Not found'); }
  fs.stat(file, (e, st) => {
    if (e || !st.isFile()) { head(res, 404, { 'Content-Type': 'text/plain; charset=utf-8' }); return res.end('Not found'); }
    const isHtml = ext === '.html';
    const etag = `W/"${st.size.toString(36)}-${Math.floor(st.mtimeMs).toString(36)}"`;
    const cache = isHtml ? 'no-cache' : (url.searchParams.has('v') ? 'public, max-age=31536000, immutable' : (/^(image|video|font)\//.test(type) ? 'public, max-age=604800' : 'public, max-age=3600'));
    const h = { 'Content-Type': type, 'Cache-Control': cache, ETag: etag, 'Last-Modified': st.mtime.toUTCString(), 'Accept-Ranges': 'bytes', Vary: 'Accept-Encoding' };
    if (isHtml) Object.assign(h, { 'Content-Security-Policy': SITE_CSP, 'X-Frame-Options': 'SAMEORIGIN' });
    if (req.headers['if-none-match'] === etag) { head(res, 304, h); return res.end(); }
    const range = req.headers.range;
    if (range && /^bytes=(\d+-\d*|-\d+)$/.test(range)) { /* Range нужен браузерам для видео */
      let [a, b] = range.slice(6).split('-');
      if (a === '') { a = Math.max(0, st.size - +b); b = st.size - 1; } else { a = +a; b = b ? Math.min(+b, st.size - 1) : st.size - 1; }
      if (a > b || a >= st.size) { head(res, 416, { 'Content-Range': `bytes */${st.size}` }); return res.end(); }
      head(res, 206, { ...h, 'Content-Range': `bytes ${a}-${b}/${st.size}`, 'Content-Length': b - a + 1 });
      return req.method === 'HEAD' ? res.end() : fs.createReadStream(file, { start: a, end: b }).pipe(res);
    }
    if (ZIP.test(type) && /\bgzip\b/.test(req.headers['accept-encoding'] || '') && st.size > 1024) {
      const key = file + ':' + etag; let gz = gzCache.get(key);
      if (!gz) { gz = zlib.gzipSync(fs.readFileSync(file), { level: 9 }); gzCache.set(key, gz); }
      head(res, 200, { ...h, 'Content-Encoding': 'gzip', 'Content-Length': gz.length });
      return res.end(req.method === 'HEAD' ? undefined : gz);
    }
    head(res, 200, { ...h, 'Content-Length': st.size });
    if (req.method === 'HEAD') return res.end();
    fs.createReadStream(file).pipe(res);
  });
}

http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  const ip = clientIp(req);
  try {
    if (req.method === 'GET' && url.pathname === '/api/availability') {
      const now = minskNow();
      let from = url.searchParams.get('from') || now.date, to = url.searchParams.get('to') || addDays(now.date, HORIZON_DAYS);
      if (!validDate(from) || !validDate(to)) return send(res, 400, { error: 'Неверные даты' });
      if (from < now.date) from = now.date;
      return send(res, 200, { today: now.date, hour: now.hour, open: OPEN, close: CLOSE, busy: busyMap(load(), from, to) });
    }
    if (req.method === 'POST' && url.pathname === '/api/requests') {
      if (!/^application\/json\b/i.test(req.headers['content-type'] || '')) return send(res, 415, { error: 'Нужен JSON' });
      if (limited('req', ip, 8)) return send(res, 429, { error: 'Слишком много заявок, попробуйте через несколько минут' });
      let body; try { body = JSON.parse((await readBody(req, 20000)) || '{}'); } catch (e) { return send(res, e.code === 413 ? 413 : 400, { error: 'Неверный запрос' }); }
      const v = validate(body);
      if (v.error) return send(res, 400, { error: v.error });
      const list = load(), r = v.rec;
      r.ipHash = ipHash(ip);
      if (r.booking) { /* проверка и запись в одном синхронном шаге: гонки нет */
        const ck = contactKey(r.contact);
        const holds = list.filter(x => x.status === 'new' && isActive(x) && (x.ipHash === r.ipHash || contactKey(x.contact) === ck)).length;
        if (holds >= MAX_HOLDS) return send(res, 429, { error: 'У вас уже есть неподтверждённые брони. Дождитесь ответа менеджера или позвоните нам' });
        const busy = busyMap(list, r.booking.date, r.booking.date)[r.booking.date] || [];
        for (let h = r.booking.start; h < r.booking.start + r.booking.dur; h++) if (busy.includes(h)) return send(res, 409, { error: 'Это время уже заняли, выберите другое' });
      }
      r.id = crypto.randomBytes(8).toString('hex'); r.createdAt = Date.now(); r.status = 'new';
      list.push(r); save(list);
      safely(() => notify(r)); safely(() => hook('request.created', r)); safely(() => calendarWrite('insert', r));
      return send(res, 201, { ok: true, id: r.id, booking: r.booking || null });
    }
    if (url.pathname === '/admin' && req.method === 'GET') {
      const k = url.searchParams.get('key');
      if (k !== null) { /* старые ссылки /admin?key=... : ключ меняется на cookie и сразу убирается из адреса */
        if (limited('login', ip, 10)) return html(res, 429, loginPage('Слишком много попыток, подождите 10 минут'));
        return same(k, ADMIN_KEY) ? redirect(res, '/admin', { 'Set-Cookie': startSession(req) }) : html(res, 401, loginPage('Неверный ключ'));
      }
      return session(req) ? html(res, 200, adminPage(req)) : html(res, 401, loginPage());
    }
    if (url.pathname === '/admin/login' && req.method === 'POST') {
      if (!sameOrigin(req)) return html(res, 403, loginPage('Запрос с чужого сайта'));
      if (limited('login', ip, 10)) return html(res, 429, loginPage('Слишком много попыток, подождите 10 минут'));
      const f = new URLSearchParams(await readBody(req, 2000));
      return same(f.get('key'), ADMIN_KEY) ? redirect(res, '/admin', { 'Set-Cookie': startSession(req) }) : html(res, 401, loginPage('Неверный ключ'));
    }
    if (url.pathname === '/admin/logout' && req.method === 'POST') {
      const t = session(req); if (t) SESS.delete(t);
      return redirect(res, '/admin', { 'Set-Cookie': 'arka_admin=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0' });
    }
    if (url.pathname === '/calendar.ics' && req.method === 'GET') {
      if (!same(url.searchParams.get('token'), ICS_TOKEN)) { head(res, 401, { 'Content-Type': 'text/plain; charset=utf-8' }); return res.end('Нужен токен календаря: адрес подписки есть на странице /admin'); }
      head(res, 200, { 'Content-Type': 'text/calendar; charset=utf-8', 'Cache-Control': 'no-store' }); return res.end(ics(load()));
    }
    const m = url.pathname.match(/^\/api\/admin\/(confirm|cancel)$/);
    if (m && req.method === 'POST') {
      if (!session(req) || !sameOrigin(req)) return send(res, 401, { error: 'Нет доступа' });
      const f = new URLSearchParams(await readBody(req, 2000));
      const list = load(), r = list.find(x => x.id === f.get('id'));
      if (r) {
        r.status = m[1] === 'confirm' ? 'confirmed' : 'cancelled'; save(list);
        safely(() => hook(r.status === 'confirmed' ? 'request.confirmed' : 'request.cancelled', r));
        safely(() => calendarWrite(r.status === 'confirmed' ? 'confirm' : 'remove', r));
      }
      return redirect(res, '/admin');
    }
    if (url.pathname.startsWith('/api/')) return send(res, 404, { error: 'Нет такого метода' });
    if (req.method !== 'GET' && req.method !== 'HEAD') { head(res, 405, { Allow: 'GET, HEAD' }); return res.end(); }
    serveStatic(req, res, url);
  } catch (e) {
    if (!res.headersSent) send(res, e.code === 413 ? 413 : 400, { error: 'Неверный запрос' }); else res.destroy();
  }
}).listen(PORT, () => {
  console.log(`АРКА 123: http://localhost:${PORT}`);
  console.log(`Заявки: http://localhost:${PORT}/admin` + (PROD ? ' (ключ в data/admin-key.txt или ADMIN_KEY)' : `?key=${ADMIN_KEY}`));
});
