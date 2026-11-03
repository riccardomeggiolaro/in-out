import { esc } from '../ui.js';

export function renderPlaceholder(el, icon, title, text) {
  el.innerHTML = `
    <div class="placeholder">
      <div class="big">${icon}</div>
      <h2>${esc(title)}</h2>
      <p class="muted">${esc(text)}</p>
      <p class="muted" style="margin-top:14px">Sezione in arrivo nella nuova interfaccia. Nel frattempo è disponibile nell'interfaccia attuale.</p>
    </div>`;
}
