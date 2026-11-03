// Stato dell'impianto: configurazione + un websocket realtime per ogni pesa.
// Le schermate si iscrivono agli eventi con plant.on(nome, fn) e ricevono
// { weigher, data } per ogni messaggio.

import { api, wsUrl } from './api.js';

// Stati del realtime mandati dai terminali durante la diagnostica
const DIAGNOSTIC_STATUSES = ['D', 'diagnostic in progress'];

class Plant extends EventTarget {
  constructor() {
    super();
    this.config = null;
    this.weighers = []; // [{ id, instanceName, name, node, realtime, data, connected, relays }]
  }

  on(type, fn) {
    const handler = e => fn(e.detail);
    this.addEventListener(type, handler);
    return () => this.removeEventListener(type, handler);
  }
  emit(type, detail) { this.dispatchEvent(new CustomEvent(type, { detail })); }

  get mode() { return String(this.config?.mode || '').toUpperCase(); }
  get isAutomatic() { return ['AUTOMATIC', 'SEMIAUTOMATIC'].includes(this.mode); }

  async load() {
    this.config = await api('/api/config-weigher/configuration');
    this.weighers = [];
    for (const [instanceName, inst] of Object.entries(this.config.weighers || {})) {
      for (const [name, node] of Object.entries(inst.nodes || {})) {
        this.weighers.push({
          id: `${instanceName}/${name}`,
          instanceName, name, node, instance: inst,
          realtime: null,
          data: null,
          connected: false,
          relays: { ...(node.rele || {}) },
          lastPicture: null,
        });
      }
    }
    this.weighers.forEach(w => this.connect(w));
    this.emit('loaded', {});
  }

  query(w) { return { instance_name: w.instanceName, weigher_name: w.name }; }
  path(w) { return `?instance_name=${encodeURIComponent(w.instanceName)}&weigher_name=${encodeURIComponent(w.name)}`; }

  connect(w) {
    const url = wsUrl(`/api/command-weigher/realtime${this.path(w)}`);
    let ping = null;
    const open = () => {
      const ws = new WebSocket(url);
      w.ws = ws;
      ws.onopen = () => {
        w.connected = true;
        this.emit('connection', { weigher: w });
        ping = setInterval(() => { if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: 'ping' })); }, 20000);
      };
      ws.onclose = () => {
        w.connected = false;
        clearInterval(ping);
        this.emit('connection', { weigher: w });
        setTimeout(open, 3000);
      };
      ws.onerror = () => ws.close();
      ws.onmessage = ev => {
        let data;
        try { data = JSON.parse(ev.data); } catch (_) { return; }
        if (!data || typeof data !== 'object' || data.type === 'pong') return;
        this.dispatch(w, data);
      };
    };
    open();
  }

  // Smista i messaggi del server in eventi con un nome chiaro
  dispatch(w, data) {
    if ('gross_weight' in data && 'status' in data) {
      w.realtime = { ...data, diagnostic: DIAGNOSTIC_STATUSES.includes(data.status) };
      this.emit('realtime', { weigher: w, data: w.realtime });
    }
    if ('data_in_execution' in data && 'id_selected' in data) {
      w.data = data;
      this.emit('data', { weigher: w, data });
    }
    if (data.weight_executed) this.emit('weighing', { weigher: w, data });
    if ('command_executed' in data) this.emit('command', { weigher: w, data });
    if (typeof data.cam_message === 'string') this.emit('message', { weigher: w, text: data.cam_message, error: !!data.cam_is_error });
    if (typeof data.message === 'string') this.emit('message', { weigher: w, text: data.message, error: false });
    if (typeof data.error_message === 'string') this.emit('message', { weigher: w, text: data.error_message, error: true });
    if (data.weighing_picture) {
      w.lastPicture = { ...data.weighing_picture, at: new Date() };
      this.emit('picture', { weigher: w, data: w.lastPicture });
    }
    if (data.weighing_flash) this.emit('flash', { weigher: w, data: data.weighing_flash });
    if (data.weighing_report) this.emit('report', { weigher: w, data: data.weighing_report });
    if ('access' in data) this.emit('access', { weigher: w, data });
    // Stato relè: { "<nome>": 0|1 }
    let relayChanged = false;
    for (const [k, v] of Object.entries(data)) {
      if (k in w.relays && (v === 0 || v === 1)) { w.relays[k] = v; relayChanged = true; }
    }
    if (relayChanged) this.emit('relays', { weigher: w, relays: w.relays });
  }

  async refreshData(w) {
    try {
      w.data = await api('/api/data', { query: this.query(w) });
      this.emit('data', { weigher: w, data: w.data });
    } catch (_) {}
    return w.data;
  }
}

export const plant = new Plant();

/** Stato sintetico di una pesa per colori ed etichette. */
export function weightState(w) {
  const rt = w.realtime;
  const min = Number(w.node.min_weight) || 0;
  if (!w.connected) return { kind: 'err', label: 'Non collegata' };
  if (!rt) return { kind: 'idle', label: 'In attesa' };
  if (rt.diagnostic) return { kind: 'warn', label: 'Diagnostica' };
  if (rt.gross_weight === '' || rt.gross_weight === undefined) return { kind: 'err', label: 'Nessun dato' };
  const g = Number(rt.gross_weight);
  if (!Number.isFinite(g)) return { kind: 'err', label: 'Errore lettura' };
  if (rt.over_max_theshold) return { kind: 'err', label: 'Oltre il massimo' };
  if (rt.status !== 'ST') return { kind: 'warn', label: 'Instabile' };
  if (g < min) return { kind: 'idle', label: 'Pesa scarica' };
  return { kind: 'ok', label: 'Stabile' };
}
