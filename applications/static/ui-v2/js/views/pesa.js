// Schermata "Pesa": peso grande, mezzo sulla pesa, azioni principali,
// ultima foto, sbarre e attività recente. Usa le API esistenti del server.

import { api, openProtectedFile } from '../api.js';
import { plant, weightState } from '../plant.js';
import { esc, formatKg, formatTime, toast } from '../ui.js';

const SELECTED_KEY = 'ui-v2.selectedWeigher';
const activity = new Map(); // id pesa → [{ time, text, kind }]

function logActivity(w, text, kind = '') {
  const list = activity.get(w.id) || [];
  list.unshift({ time: new Date(), text, kind });
  activity.set(w.id, list.slice(0, 30));
}

// L'attività si registra anche quando la schermata non è aperta
plant.on('message', ({ weigher, text, error }) => logActivity(weigher, text, error ? 'err' : ''));
plant.on('weighing', ({ weigher, data }) => {
  const we = data.weight_executed || {};
  if (we.executed === false) logActivity(weigher, 'Pesata non riuscita', 'err');
  else logActivity(weigher, `Pesata eseguita${we.pid ? ' · PID ' + we.pid : ''} · ${formatKg(we.gross_weight)} kg`, 'ok');
});
plant.on('report', ({ weigher, data }) => logActivity(weigher, `Report ${String(data.event_type || '').toUpperCase()} ${data.printed === false ? 'non stampato' : 'inviato a ' + (data.printer_name || 'stampante')}`, data.printed === false ? 'err' : 'ok'));
plant.on('picture', ({ weigher }) => logActivity(weigher, 'Foto scattata'));

export function renderPesa(el) {
  if (!plant.weighers.length) {
    el.innerHTML = `<div class="placeholder"><div class="big">⚖️</div><h2>Nessuna pesa configurata</h2><p class="muted">Aggiungi una pesa nelle impostazioni.</p></div>`;
    return;
  }

  let current = plant.weighers.find(w => w.id === safeGet(SELECTED_KEY)) || plant.weighers[0];
  let accesses = [];
  let filter = '';
  let busy = false;

  el.innerHTML = `
    <div class="weigher-tabs" role="tablist" aria-label="Pese" ${plant.weighers.length > 1 ? '' : 'hidden'}></div>
    <div class="pesa-grid">
      <section class="card area-vehicle" aria-labelledby="h-vehicle">
        <div class="card-h"><h2 id="h-vehicle">Mezzo sulla pesa</h2><button class="btn" data-act="clear" title="Togli il mezzo selezionato" style="padding:4px 10px;font-size:13px">Svuota</button></div>
        <div class="card-b">
          <form class="vehicle-search" data-form="plate" autocomplete="off">
            <input class="input" name="q" placeholder="Targa, badge o cerca…" aria-label="Targa o ricerca">
            <button class="btn primary" type="submit" title="Usa questa targa">OK</button>
          </form>
          <div class="selected-box" data-slot="selected"></div>
          <ul class="access-list" data-slot="accesses" aria-label="Mezzi in impianto"></ul>
        </div>
      </section>

      <div class="area-weight">
        <section class="card weight-card" data-slot="weight" aria-live="polite"></section>
        <div data-slot="auto"></div>
        <section class="actions" aria-label="Azioni">
          <button class="btn big" data-act="in">Pesata entrata <span class="kbd">F1</span></button>
          <button class="btn big" data-act="out">Pesata uscita <span class="kbd">F2</span></button>
          <div class="small-row">
            <button class="btn" data-act="tare">Tara <span class="kbd">F3</span></button>
            <button class="btn" data-act="zero">Zero <span class="kbd">F4</span></button>
            <button class="btn" data-act="reprint">Ristampa</button>
          </div>
        </section>
      </div>

      <div class="area-side">
        <section class="card" aria-labelledby="h-photo">
          <div class="card-h"><h2 id="h-photo">Ultima foto</h2><span class="muted" data-slot="photo-time" style="font-size:12px"></span></div>
          <div class="card-b" data-slot="photo"></div>
        </section>
        <section class="card" aria-labelledby="h-relays">
          <div class="card-h"><h2 id="h-relays">Sbarre</h2></div>
          <div class="card-b" data-slot="relays"></div>
        </section>
        <section class="card" aria-labelledby="h-activity">
          <div class="card-h"><h2 id="h-activity">Attività</h2></div>
          <div class="card-b"><ul class="activity" data-slot="activity"></ul></div>
        </section>
      </div>
    </div>`;

  const $ = s => el.querySelector(s);
  const slot = name => el.querySelector(`[data-slot="${name}"]`);

  // ── Rendering ──────────────────────────────────────────────
  function renderTabs() {
    const tabs = $('.weigher-tabs');
    tabs.innerHTML = plant.weighers.map(w => {
      const st = weightState(w);
      return `<button class="weigher-tab" role="tab" data-weigher="${esc(w.id)}" aria-selected="${w === current}">
        <span class="dot ${st.kind}"></span>${esc(w.name)}<span class="w">${esc(formatKg(w.realtime?.gross_weight))} kg</span></button>`;
    }).join('');
  }

  function renderWeight() {
    const w = current, rt = w.realtime || {}, st = weightState(w);
    const card = slot('weight');
    card.className = `card weight-card ${st.kind}`;
    const showWeight = rt.gross_weight !== '' && rt.gross_weight !== undefined && !rt.diagnostic;
    const unit = rt.unite_measure || 'kg';
    card.innerHTML = `
      <div class="weight-top">
        <span class="weight-name">${esc(w.name)}${w.node.terminal ? ` <span class="muted" style="font-weight:500">· ${esc(w.node.terminal)}</span>` : ''}</span>
        <span class="weight-status ${st.kind}">${esc(st.label)}</span>
      </div>
      <div class="weight-value">${showWeight ? esc(formatKg(rt.gross_weight)) : '—'}<span class="unit">${esc(unit)}</span></div>
      <div class="weight-sub">
        <span>Tara <b>${esc(formatKg(rt.tare === '' ? null : String(rt.tare ?? '').replace(/PT|\s/g, '')))}</b></span>
        <span>Netto <b>${esc(formatKg(rt.net_weight))}</b></span>
        <span>Min <b>${esc(formatKg(w.node.min_weight))}</b></span>
      </div>`;
  }

  function selectedInfo() {
    const d = current.data;
    const die = d?.data_in_execution || {};
    const ids = d?.id_selected || {};
    return { die, ids, hasSelection: !!(ids.id || die.vehicle?.plate) };
  }

  function renderSelected() {
    const { die, ids, hasSelection } = selectedInfo();
    const box = slot('selected');
    box.classList.toggle('has', hasSelection);
    if (!hasSelection) {
      box.innerHTML = `<div class="empty">Nessun mezzo selezionato. Scrivi la targa o scegli dalla lista.</div>`;
      return;
    }
    const rows = [
      ['Cliente/Forn.', die.subject?.social_reason],
      ['Vettore', die.vector?.social_reason],
      ['Autista', die.driver?.social_reason || die.driver?.name],
      ['Materiale', die.material?.description],
      ['1ª pesata', ids.weight1 ? `${formatKg(ids.weight1.weight ?? ids.weight1)} kg` : null],
    ].filter(([, v]) => v);
    box.innerHTML = `
      <div class="plate">${esc(die.vehicle?.plate || (ids.id ? 'Accesso #' + ids.id : '—'))}</div>
      ${rows.length ? `<dl class="kv">${rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')}</dl>` : ''}`;
    // Suggerisce l'azione giusta: uscita se c'è già la prima pesata o una tara
    const suggestOut = !!ids.weight1 || (current.realtime && current.realtime.tare && String(current.realtime.tare).replace(/PT|\s/g, '') !== '0');
    $('[data-act="in"]').classList.toggle('primary', !suggestOut);
    $('[data-act="out"]').classList.toggle('primary', suggestOut);
  }

  function renderAccesses() {
    const list = slot('accesses');
    const selectedId = current.data?.id_selected?.id;
    const q = filter.trim().toUpperCase();
    const items = accesses.filter(a => !q || accessLabel(a).toUpperCase().includes(q) || accessInfo(a).toUpperCase().includes(q));
    if (!items.length) {
      list.innerHTML = `<li class="empty">${accesses.length ? 'Nessun mezzo trovato' : 'Nessun mezzo in impianto'}</li>`;
      return;
    }
    list.innerHTML = items.slice(0, 50).map(a => `
      <li><button class="access-item" data-access="${a.id}" aria-pressed="${a.id === selectedId}">
        <span class="p">${esc(accessLabel(a))}${a.type === 'RESERVATION' ? '<span class="tag">Prenotato</span>' : ''}${a.in_out?.some(io => io.idWeight1) ? '<span class="tag" style="background:var(--ok-bg);color:var(--ok)">Dentro</span>' : ''}</span>
        <span class="s">${esc(accessInfo(a)) || '&nbsp;'}</span>
      </button></li>`).join('');
  }

  function renderPhoto(flash = false) {
    const p = current.lastPicture;
    const box = slot('photo');
    slot('photo-time').textContent = p ? formatTime(p.at) : '';
    if (!p) {
      const cams = current.node.events?.weighing?.cams?.filter(c => c.active).length || 0;
      box.innerHTML = `<div class="photo-empty">${cams ? 'Nessuna foto in questa sessione.<br>Comparirà alla prossima pesata.' : 'Nessuna fotocamera attiva su questa pesa.'}</div>`;
    } else {
      const src = '/images' + (p.path_name.startsWith('/') ? '' : '/') + p.path_name;
      box.innerHTML = `<img class="photo" src="${esc(src)}" alt="Ultima foto della pesa ${esc(current.name)}">`;
      box.querySelector('img').addEventListener('click', () => window.open(src, '_blank'));
    }
    if (flash) { box.classList.remove('flash'); void box.offsetWidth; box.classList.add('flash'); }
  }

  function renderRelays() {
    const box = slot('relays');
    const entries = Object.entries(current.relays);
    if (!entries.length) { box.innerHTML = '<div class="empty">Nessuna sbarra configurata.</div>'; return; }
    box.innerHTML = entries.map(([n, v]) => `
      <div class="relay-row">
        <span class="light ${v === 1 ? 'open' : ''}" aria-hidden="true"></span>
        <span class="name">Sbarra ${esc(n)}</span>
        <span class="muted">${v === 1 ? 'aperta' : 'chiusa'}</span>
        <button class="btn" data-relay="${esc(n)}">${v === 1 ? 'Chiudi' : 'Apri'}</button>
      </div>`).join('');
  }

  function renderAuto() {
    const box = slot('auto');
    box.innerHTML = plant.isAutomatic
      ? `<div class="auto-banner">● Modalità ${plant.mode === 'SEMIAUTOMATIC' ? 'semiautomatica' : 'automatica'}: le pesate partono da sole quando viene letta una targa o un badge. I comandi qui sotto restano disponibili per intervenire.</div>`
      : '';
  }

  function renderActivity() {
    const list = activity.get(current.id) || [];
    slot('activity').innerHTML = list.length
      ? list.map(a => `<li><time>${formatTime(a.time)}</time><span class="${a.kind}">${esc(a.text)}</span></li>`).join('')
      : '<li class="empty">Nessuna attività in questa sessione.</li>';
  }

  function renderAll() {
    renderTabs(); renderWeight(); renderSelected(); renderAccesses();
    renderPhoto(); renderRelays(); renderAuto(); renderActivity();
  }

  // ── Dati ───────────────────────────────────────────────────
  async function loadAccesses() {
    try {
      const res = await api('/api/anagrafic/access/list', { query: { status: 'NOT_CLOSED', permanentIfWeight1: true } });
      accesses = res?.data || [];
    } catch (_) { accesses = []; }
    renderAccesses();
  }

  async function selectAccess(id) {
    const already = current.data?.id_selected?.id === id;
    try {
      await api('/api/data', { method: 'PATCH', query: plant.query(current), body: { data_in_execution: {}, id_selected: { id: already ? -1 : id } } });
    } catch (err) { toast(err.message, 'err'); }
    await plant.refreshData(current);
  }

  async function usePlate(text) {
    const plate = text.trim().toUpperCase();
    if (!plate) return;
    // Se corrisponde a un mezzo in impianto lo seleziono, altrimenti imposto la targa
    const match = accesses.find(a => (a.vehicle?.plate || '').toUpperCase() === plate);
    if (match) return selectAccess(match.id);
    try {
      await api('/api/data', { method: 'PATCH', query: { ...plant.query(current), auto_select: true }, body: { data_in_execution: { vehicle: { plate } }, id_selected: {} } });
    } catch (err) { toast(err.message, 'err'); }
    await plant.refreshData(current);
  }

  async function clearSelection() {
    try { await api('/api/data', { method: 'DELETE', query: plant.query(current) }); }
    catch (err) { toast(err.message, 'err'); }
    await plant.refreshData(current);
  }

  async function command(act) {
    if (busy) return;
    const routes = {
      in:      { path: '/api/command-weigher/in',  method: 'POST', label: 'Pesata entrata' },
      out:     { path: '/api/command-weigher/out', method: 'POST', label: 'Pesata uscita' },
      tare:    { path: '/api/command-weigher/tare', label: 'Tara' },
      zero:    { path: '/api/command-weigher/zero', label: 'Zero' },
      reprint: { path: '/api/anagrafic/access/in-out/print-last', label: 'Ristampa' },
    };
    const r = routes[act];
    if (!r) return;
    busy = true;
    el.querySelectorAll('.actions .btn').forEach(b => b.disabled = true);
    try {
      const res = await api(r.path, { method: r.method || 'GET', query: plant.query(current) });
      const err = res?.command_details?.error_message;
      if (err) { toast(`${r.label}: ${err}`, 'err'); logActivity(current, `${r.label}: ${err}`, 'err'); }
      else {
        const msg = act === 'in' || act === 'out' ? `${r.label} in corso…` : `${r.label} eseguita`;
        toast(msg, 'ok'); logActivity(current, msg);
      }
    } catch (e) {
      toast(`${r.label}: ${e.message}`, 'err'); logActivity(current, `${r.label}: ${e.message}`, 'err');
    } finally {
      busy = false;
      el.querySelectorAll('.actions .btn').forEach(b => b.disabled = false);
      renderActivity();
    }
  }

  async function toggleRelay(name) {
    try {
      const res = await api('/api/command-weigher/rele', { query: { ...plant.query(current), rele: name } });
      const err = res?.command_details?.error_message;
      if (err) toast(`Sbarra ${name}: ${err}`, 'err');
    } catch (e) { toast(`Sbarra ${name}: ${e.message}`, 'err'); }
  }

  // ── Eventi interfaccia ─────────────────────────────────────
  el.addEventListener('click', e => {
    const tab = e.target.closest('[data-weigher]');
    if (tab) {
      current = plant.weighers.find(w => w.id === tab.dataset.weigher) || current;
      safeSet(SELECTED_KEY, current.id);
      plant.refreshData(current);
      renderAll();
      return;
    }
    const acc = e.target.closest('[data-access]');
    if (acc) return selectAccess(Number(acc.dataset.access));
    const relay = e.target.closest('[data-relay]');
    if (relay) return toggleRelay(relay.dataset.relay);
    const act = e.target.closest('[data-act]');
    if (act) return act.dataset.act === 'clear' ? clearSelection() : command(act.dataset.act);
  });
  const form = el.querySelector('[data-form="plate"]');
  form.addEventListener('submit', e => { e.preventDefault(); usePlate(form.q.value); form.q.value = ''; filter = ''; renderAccesses(); });
  form.q.addEventListener('input', () => { filter = form.q.value; renderAccesses(); });

  const onKey = e => {
    const map = { F1: 'in', F2: 'out', F3: 'tare', F4: 'zero' };
    if (map[e.key]) { e.preventDefault(); command(map[e.key]); }
  };
  window.addEventListener('keydown', onKey);

  // ── Eventi dal server ──────────────────────────────────────
  let queued = false;
  const queueWeight = () => {
    if (queued) return; queued = true;
    requestAnimationFrame(() => { queued = false; renderWeight(); renderTabs(); });
  };
  const offs = [
    plant.on('realtime', ({ weigher }) => { if (weigher === current) queueWeight(); else renderTabs(); }),
    plant.on('connection', () => { renderTabs(); renderWeight(); }),
    plant.on('data', ({ weigher }) => { if (weigher === current) { renderSelected(); renderAccesses(); } }),
    plant.on('relays', ({ weigher }) => { if (weigher === current) renderRelays(); }),
    plant.on('picture', ({ weigher }) => { if (weigher === current) { renderPhoto(true); renderActivity(); } }),
    plant.on('flash', ({ weigher }) => { if (weigher === current) renderPhoto(true); }),
    plant.on('message', ({ weigher, text, error }) => { if (weigher === current) { toast(`${weigher.name}: ${text}`, error ? 'err' : ''); renderActivity(); } }),
    plant.on('weighing', ({ weigher, data }) => {
      const we = data.weight_executed || {};
      if (we.executed !== false) toast(`${weigher.name}: pesata eseguita · ${formatKg(we.gross_weight)} kg`, 'ok');
      if (weigher === current) renderActivity();
      loadAccesses();
    }),
    plant.on('report', ({ weigher, data }) => {
      if (data.in_out_id != null) {
        toast(`${weigher.name}: report ${String(data.event_type || '').toUpperCase()} pronto`, data.printed === false ? 'warn' : 'ok', {
          timeout: 12000,
          action: { label: 'Apri PDF', run: () => openProtectedFile(`/api/anagrafic/access/in-out/pdf/${encodeURIComponent(data.in_out_id)}`).catch(e => toast(e.message, 'err')) },
        });
      }
      if (weigher === current) renderActivity();
    }),
    plant.on('access', () => loadAccesses()),
  ];
  const poll = setInterval(loadAccesses, 30000);

  renderAll();
  plant.refreshData(current);
  loadAccesses();

  return () => {
    offs.forEach(off => off());
    clearInterval(poll);
    window.removeEventListener('keydown', onKey);
  };
}

function accessLabel(a) {
  if (a.vehicle?.plate) return a.vehicle.plate;
  const io = a.in_out?.[0];
  return io?.weight1?.pid || io?.weight2?.pid || `Accesso #${a.id}`;
}
function accessInfo(a) {
  const last = a.in_out?.length ? (a.in_out.find(io => io.is_last) || a.in_out[a.in_out.length - 1]) : null;
  const open = last && last.net_weight == null;
  const subject = (open && last.subject?.social_reason) || a.subject?.social_reason;
  const material = (open && last.material?.description) || a.material?.description;
  return [subject, material].filter(Boolean).join(' · ');
}
function safeGet(k) { try { return localStorage.getItem(k); } catch (_) { return null; } }
function safeSet(k, v) { try { localStorage.setItem(k, v); } catch (_) {} }
