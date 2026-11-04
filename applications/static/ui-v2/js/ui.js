// Piccole utilità per l'interfaccia: escape HTML, avvisi, formattazione.

export function esc(v) {
  return String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

/** Avviso in basso a destra. kind: '' | 'ok' | 'warn' | 'err'. action: { label, run } opzionale. */
export function toast(text, kind = '', { action, timeout = 6000 } = {}) {
  const box = document.getElementById('toasts');
  // lo stesso messaggio può arrivare sia dalla risposta che dal websocket: lo mostro una volta
  if ([...box.children].some(c => c.dataset.text === text)) return;
  const el = document.createElement('div');
  el.className = `toast ${kind}`;
  el.dataset.text = text;
  el.setAttribute('role', kind === 'err' ? 'alert' : 'status');
  const span = document.createElement('span');
  span.textContent = text;
  el.appendChild(span);
  if (action) {
    const a = document.createElement('a');
    a.href = '#';
    a.textContent = action.label;
    a.addEventListener('click', e => { e.preventDefault(); action.run(); });
    el.appendChild(a);
  }
  box.appendChild(el);
  while (box.children.length > 5) box.firstChild.remove();
  setTimeout(() => { el.classList.add('hide'); setTimeout(() => el.remove(), 350); }, timeout);
}

export function formatKg(value) {
  if (value === null || value === undefined || value === '') return '—';
  const n = Number(value);
  return Number.isFinite(n) ? n.toLocaleString('it-IT') : String(value);
}

export function formatTime(date = new Date()) {
  return date.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
