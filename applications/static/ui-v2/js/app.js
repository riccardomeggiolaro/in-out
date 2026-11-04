// Avvio dell'applicazione: menu e navigazione, barra di stato, tema.

import { getToken, logout } from './api.js';
import { plant, weightState } from './plant.js';
import { esc, formatKg, toast } from './ui.js';
import { renderPesa } from './views/pesa.js';
import { renderImpianto } from './views/impianto.js';
import { renderPlaceholder } from './views/placeholder.js';

if (!getToken()) logout();

const ROUTES = {
  pesa:         { title: 'Pesa',         render: renderPesa },
  accessi:      { title: 'Accessi',      render: el => renderPlaceholder(el, '📋', 'Accessi e prenotazioni', 'Mezzi in impianto, prenotazioni e storico delle pesate.') },
  anagrafiche:  { title: 'Anagrafiche',  render: el => renderPlaceholder(el, '👥', 'Anagrafiche', 'Clienti e fornitori, vettori, autisti, mezzi, materiali e badge.') },
  impianto:     { title: 'Impianto',     render: renderImpianto },
  report:       { title: 'Report',       render: el => renderPlaceholder(el, '📊', 'Report', 'Statistiche, esportazioni e modelli di stampa.') },
  impostazioni: { title: 'Impostazioni', render: el => renderPlaceholder(el, '⚙️', 'Impostazioni', 'Configurazione guidata di pese, terminali, relè, fotocamere, stampanti e utenti.') },
};

const view = document.getElementById('view');
const title = document.getElementById('page-title');
let cleanup = null;

function currentRoute() {
  const name = location.hash.replace(/^#\/?/, '').split('/')[0];
  return ROUTES[name] ? name : 'pesa';
}

function navigate() {
  const name = currentRoute();
  if (typeof cleanup === 'function') cleanup();
  cleanup = null;
  view.innerHTML = '';
  document.querySelectorAll('.nav-item').forEach(a => {
    if (a.dataset.route === name) a.setAttribute('aria-current', 'page');
    else a.removeAttribute('aria-current');
  });
  title.textContent = ROUTES[name].title;
  document.title = `${ROUTES[name].title} · Pesa`;
  cleanup = ROUTES[name].render(view);
}

// ── Barra di stato dell'impianto ─────────────────────────────
const strip = document.getElementById('status-strip');
function renderStatus() {
  const chips = plant.weighers.map(w => {
    const st = weightState(w);
    const g = w.realtime?.gross_weight;
    const kg = st.kind === 'ok' || st.kind === 'idle' || st.kind === 'warn' ? `${formatKg(g)} kg` : st.label;
    return `<span class="chip ${st.kind}" title="${esc(w.name)}: ${esc(st.label)}"><span class="dot"></span>${esc(w.name)} · ${esc(kg)}</span>`;
  });
  const relays = plant.weighers.flatMap(w => Object.entries(w.relays).map(([n, v]) =>
    `<span class="chip ${v === 1 ? 'ok' : 'err'}" title="Relè ${esc(n)} di ${esc(w.name)}"><span class="dot"></span>Sbarra ${esc(n)} ${v === 1 ? 'aperta' : 'chiusa'}</span>`));
  const mode = plant.config ? `<span class="chip ${plant.isAutomatic ? 'ok' : ''}"><span class="dot"></span>${plant.isAutomatic ? 'Automatico' : 'Manuale'}</span>` : '';
  strip.innerHTML = mode + chips.join('') + relays.join('');
}
let statusQueued = false;
function queueStatus() {
  if (statusQueued) return;
  statusQueued = true;
  requestAnimationFrame(() => { statusQueued = false; renderStatus(); });
}
['loaded', 'realtime', 'connection', 'relays'].forEach(t => plant.on(t, queueStatus));

// ── Tema ─────────────────────────────────────────────────────
const THEME_KEY = 'ui-v2.theme';
function applyTheme(t) { if (t) document.documentElement.dataset.theme = t; else delete document.documentElement.dataset.theme; }
try { applyTheme(localStorage.getItem(THEME_KEY)); } catch (_) {}
document.getElementById('theme-toggle').addEventListener('click', () => {
  const dark = document.documentElement.dataset.theme === 'dark' ||
    (!document.documentElement.dataset.theme && matchMedia('(prefers-color-scheme: dark)').matches);
  const next = dark ? 'light' : 'dark';
  applyTheme(next);
  try { localStorage.setItem(THEME_KEY, next); } catch (_) {}
});
document.getElementById('logout').addEventListener('click', logout);

// ── Avvio ────────────────────────────────────────────────────
window.addEventListener('hashchange', navigate);
plant.load()
  .then(() => navigate())
  .catch(err => {
    view.innerHTML = `<div class="placeholder"><div class="big">⚠️</div><h2>Impossibile caricare la configurazione</h2><p class="muted">${esc(err.message)}</p></div>`;
    toast('Impossibile caricare la configurazione: ' + err.message, 'err');
  });
