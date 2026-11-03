// Vista 3D dell'impianto: per ora riusa la pagina 3D esistente.
export function renderImpianto(el) {
  el.innerHTML = `<iframe class="plant-frame" src="/static/config3d.html" title="Vista 3D dell'impianto"></iframe>`;
}
