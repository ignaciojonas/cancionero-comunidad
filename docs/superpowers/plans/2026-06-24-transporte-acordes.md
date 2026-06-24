# Transporte de acordes — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transponer los acordes de una canción por semitonos con botones − / + en el detalle, mostrando el tono resultante y recordando el transporte por canción.

**Architecture:** Funciones puras JS (`transponerNota`, `transponerAcorde`, `esLineaAcordes`) + `renderLineas` que aplica el offset global `transporte`. Estado por canción en `localStorage`. Control − / + en la línea de meta del detalle. Todo en `index.html`.

**Tech Stack:** JS + CSS en `index.html`. Verificación con Claude_Preview (`preview_eval` + screenshots).

## Global Constraints

- Salida siempre en sostenidos (`#`).
- Con `transporte === 0`, el render es idéntico al actual (no se llama al transpositor).
- Datos ya normalizados a notación latina (DO/RE/MI).
- `localStorage` en `try/catch`.

---

### Task 1: Funciones de transporte (puras)

**Files:**
- Modify: `index.html` — agregar funciones junto a `parseChordPro`.

**Interfaces:**
- Produces: `transponerNota(nota, semis)`, `transponerAcorde(acorde, semis)`, `esLineaAcordes(linea)`.

- [ ] **Step 1: Agregar las funciones** después de `cancionTieneAcordes`

```js
  // ─── Transporte de acordes ───────────────────────────────
  const CROMATICA = ['DO','DO#','RE','RE#','MI','FA','FA#','SOL','SOL#','LA','LA#','SI'];
  const NOTA_IDX = { 'DO':0,'DO#':1,'REb':1,'RE':2,'RE#':3,'MIb':3,'MI':4,'FA':5,
                     'FA#':6,'SOLb':6,'SOL':7,'SOL#':8,'LAb':8,'LA':9,'LA#':10,'SIb':10,'SI':11 };
  const RAIZ_RE = /^(DO|RE|MI|FA|SOL|LA|SI)(#|b)?/;
  const SUF_JS = '(?:maj7|maj|min7|min|sus2|sus4|sus|dim7|dim|aug|add9|add|m7|m9|m6|m|7M|M7|7|9|6|5|4|2|11|13|°)*';
  const RAIZ_JS = '(?:DO|RE|MI|FA|SOL|LA|SI)';
  const ACORDE_STRICT = new RegExp('^' + RAIZ_JS + '(#|b)?' + SUF_JS + '(?:/' + RAIZ_JS + '(#|b)?)?$');
  const MARKER_JS = /^\(.*\)$|^x\d+$/i;

  function transponerNota(nota, semis) {
    const m = RAIZ_RE.exec(nota);
    if (!m) return nota;
    const base = m[1] + (m[2] || '');
    const idx = NOTA_IDX[base];
    if (idx === undefined) return nota;
    return CROMATICA[(((idx + semis) % 12) + 12) % 12];
  }

  function transponerAcorde(acorde, semis) {
    const m = RAIZ_RE.exec(acorde);
    if (!m || NOTA_IDX[m[1] + (m[2] || '')] === undefined) return acorde;
    const nuevaRaiz = transponerNota(m[1] + (m[2] || ''), semis);
    let resto = acorde.slice(m[0].length);
    const slash = resto.indexOf('/');
    if (slash !== -1) {
      return nuevaRaiz + resto.slice(0, slash) + '/' + transponerNota(resto.slice(slash + 1), semis);
    }
    return nuevaRaiz + resto;
  }

  function esLineaAcordes(linea) {
    const toks = linea.split(/\s+/).filter(t => t && t !== '|');
    if (!toks.length) return false;
    let hay = false;
    for (const t of toks) {
      if (MARKER_JS.test(t)) continue;
      if (ACORDE_STRICT.test(t)) hay = true;
      else return false;
    }
    return hay;
  }
```

- [ ] **Step 2: Verificar con preview** (recargar y `preview_eval`)

```js
(function(){
  return {
    DO2: transponerAcorde('DO', 2),
    LAsm1: transponerAcorde('LA#m', 1),
    slash: transponerAcorde('SOL/SI', 2),
    sus: transponerAcorde('SOLsus4', 2),
    bajada: transponerAcorde('DO', -1),
    noAcorde: transponerAcorde('Aleluya', 2),
    linea: esLineaAcordes('| FA#m | DO#m SI |'),
    noLinea: esLineaAcordes('Gloria a Dios')
  };
})()
```
Esperado: `DO2:"RE"`, `LAsm1:"SIm"`, `slash:"LA/DO#"`, `sus:"LAsus4"`, `bajada:"SI"`, `noAcorde:"Aleluya"`, `linea:true`, `noLinea:false`.

- [ ] **Step 3: Commit**
```bash
git add index.html
git commit -m "Add chord transposition helper functions"
```

---

### Task 2: Estado y persistencia del transporte

**Files:**
- Modify: `index.html` — globales, carga en `init`.

**Interfaces:**
- Produces: `transporte` (int), `transportes` (obj), `cargarTransportes()`, `guardarTransporte(id, semis)`.

- [ ] **Step 1: Declarar globales** — junto a `let favoritos = new Set();`

```js
  let transporte = 0;
  let transportes = {};
  const TRANS_KEY = 'cancionero:transporte';
```

- [ ] **Step 2: Funciones de persistencia** — después de `toggleFavoritoUI`

```js
  function cargarTransportes() {
    try { const r = localStorage.getItem(TRANS_KEY); if (r) transportes = JSON.parse(r) || {}; }
    catch (e) {}
  }
  function guardarTransporte(id, semis) {
    if (semis === 0) delete transportes[id]; else transportes[id] = semis;
    try { localStorage.setItem(TRANS_KEY, JSON.stringify(transportes)); } catch (e) {}
  }
```

- [ ] **Step 3: Cargar en `init`** — junto a `cargarFavoritos();`

Buscar:
```js
    cargarFavoritos();
    renderFiltros();
```
Reemplazar por:
```js
    cargarFavoritos();
    cargarTransportes();
    renderFiltros();
```

- [ ] **Step 4: Verificar** (`preview_eval`)
```js
(function(){
  transportes = {}; guardarTransporte(5, 3);
  var p = JSON.parse(localStorage.getItem('cancionero:transporte'));
  guardarTransporte(5, 0);                 // 0 borra la entrada
  var q = JSON.parse(localStorage.getItem('cancionero:transporte'));
  return { trasGuardar: p, trasReset: q };
})()
```
Esperado: `trasGuardar:{"5":3}`, `trasReset:{}`.

- [ ] **Step 5: Commit**
```bash
git add index.html
git commit -m "Add per-song transpose state persisted in localStorage"
```

---

### Task 3: Aplicar el transporte en el render

**Files:**
- Modify: `index.html` — `renderLineas`.

**Interfaces:**
- Consumes: `parseChordPro`, `transponerAcorde`, `esLineaAcordes`, `transporte` (Tasks 1-2).

- [ ] **Step 1: Reescribir `renderLineas`** para transponer

Buscar:
```js
  function renderLineas(letra) {
    return letra.split('\n').map(linea => {
      const segs = parseChordPro(linea).map(seg => {
        const chord = seg.chord ? `<span class="cseg-chord">${escapeHtml(seg.chord)}</span>` : '';
        return `<span class="cseg">${chord}<span class="cseg-text">${escapeHtml(seg.text)}</span></span>`;
      }).join('');
      return `<span class="linea">${segs}</span>`;
    }).join('');
  }
```
Reemplazar por:
```js
  function renderLineas(letra) {
    return letra.split('\n').map(linea => {
      let segs = parseChordPro(linea);
      if (transporte !== 0) {
        const tieneCorchetes = segs.some(s => s.chord !== null);
        if (tieneCorchetes) {
          segs = segs.map(s => ({ chord: s.chord ? transponerAcorde(s.chord, transporte) : null, text: s.text }));
        } else if (esLineaAcordes(linea)) {
          const t = linea.split(/(\s+)/)
            .map(tok => /\S/.test(tok) ? transponerAcorde(tok, transporte) : tok).join('');
          segs = [{ chord: null, text: t }];
        }
      }
      const html = segs.map(seg => {
        const chord = seg.chord ? `<span class="cseg-chord">${escapeHtml(seg.chord)}</span>` : '';
        return `<span class="cseg">${chord}<span class="cseg-text">${escapeHtml(seg.text)}</span></span>`;
      }).join('');
      return `<span class="linea">${html}</span>`;
    }).join('');
  }
```

- [ ] **Step 2: Verificar** (`preview_eval`)
```js
(function(){
  var c = CANCIONES.find(c => c.autor === 'Athenas' && cancionTieneAcordes(c));
  transporte = 0; abrirDetalle(c);
  var orig = Array.from(document.querySelectorAll('.cseg-chord')).map(e=>e.textContent);
  transporte = 2; renderLetra(c);
  var trans = Array.from(document.querySelectorAll('.cseg-chord')).map(e=>e.textContent);
  transporte = 0; cerrarDetalle();
  return { orig: orig.slice(0,4), trans: trans.slice(0,4), cambio: JSON.stringify(orig)!==JSON.stringify(trans) };
})()
```
Esperado: `cambio:true`, y `trans` = `orig` subido 2 semitonos (ej. SOL→LA, RE→MI).

- [ ] **Step 3: Commit**
```bash
git add index.html
git commit -m "Apply transpose offset when rendering chords and instrumental lines"
```

---

### Task 4: Control − / + en el detalle

**Files:**
- Modify: `index.html` — CSS, `detailMeta` en `abrirDetalle`, funciones de control.

**Interfaces:**
- Consumes: `transponerAcorde`, `transporte`, `transportes`, `guardarTransporte`, `cancionTieneAcordes`, `renderLetra` (existente).
- Produces: `actualizarControlTransporte()`, `transponer(delta)`, `resetTransporte()`.

- [ ] **Step 1: Estilos** — después de `.tono-badge strong { ... }`

```css
    .transporte-control { display: inline-flex; align-items: center; gap: 0.35rem; }
    .btn-trans {
      width: 22px; height: 22px; padding: 0;
      border: 1px solid var(--borde); background: var(--blanco);
      border-radius: 5px; cursor: pointer; font-size: 0.95rem; line-height: 1;
      color: var(--azul-dk); display: inline-flex; align-items: center; justify-content: center;
      transition: background 0.15s, border-color 0.15s;
    }
    .btn-trans:hover { background: var(--azul-dim); border-color: var(--azul); }
    .trans-tono { cursor: pointer; white-space: nowrap; }
    .trans-tono strong { color: var(--azul); font-weight: 700; }
    .trans-tono:hover strong { color: var(--naranja-dk); }
```

- [ ] **Step 2: Reemplazar el badge de tono por el contenedor del control** — en `abrirDetalle`

Buscar:
```js
      ${cancion.tono ? `<span class="sep">·</span><span class="tono-badge">Tono <strong>${cancion.tono}</strong></span>` : ''}
    `;
```
Reemplazar por:
```js
      <span class="transporte-control" id="transposeControl"></span>
    `;
```

- [ ] **Step 3: Setear el transporte guardado antes de renderizar** — en `abrirDetalle`, después de `cancionActual = cancion;`

```js
    transporte = transportes[cancion.id] || 0;
```

- [ ] **Step 4: Llamar al control después de configurar el detalle** — en `abrirDetalle`, después de `body.classList.toggle('hide-chords', !tieneAcordes);`

```js
    actualizarControlTransporte();
```

- [ ] **Step 5: Agregar las funciones del control** — después de `cancionAlAzar`

```js
  function actualizarControlTransporte() {
    const cont = document.getElementById('transposeControl');
    if (!cont) return;
    if (!cancionActual || !cancionTieneAcordes(cancionActual)) { cont.innerHTML = ''; return; }
    const base = cancionActual.tono;
    let label;
    if (base) {
      const actual = transporte === 0 ? base : transponerAcorde(base, transporte);
      const off = transporte === 0 ? '' : ` (${transporte > 0 ? '+' : ''}${transporte})`;
      label = `Tono <strong>${actual}</strong>${off}`;
    } else {
      label = transporte === 0 ? 'Transporte'
        : `Transporte <strong>${transporte > 0 ? '+' : ''}${transporte}</strong>`;
    }
    cont.innerHTML = `
      <span class="sep">·</span>
      <button class="btn-trans" title="Bajar medio tono" onclick="transponer(-1)">−</button>
      <span class="trans-tono" title="Volver al tono original" onclick="resetTransporte()">${label}</span>
      <button class="btn-trans" title="Subir medio tono" onclick="transponer(1)">+</button>
    `;
  }

  function transponer(delta) {
    if (!cancionActual) return;
    transporte = ((((transporte + delta) % 12) + 12) % 12);
    if (transporte > 6) transporte -= 12;     // rango -5..6
    guardarTransporte(cancionActual.id, transporte);
    renderLetra(cancionActual);
    actualizarControlTransporte();
  }

  function resetTransporte() {
    if (!cancionActual) return;
    transporte = 0;
    guardarTransporte(cancionActual.id, 0);
    renderLetra(cancionActual);
    actualizarControlTransporte();
  }
```

- [ ] **Step 6: Verificar con preview**

```js
(function(){
  var c = CANCIONES.find(c => c.autor === 'Athenas' && cancionTieneAcordes(c) && c.tono);
  transportes = {}; abrirDetalle(c);
  transponer(2);
  var tonoMostrado = document.querySelector('.trans-tono strong').textContent;
  var persistido = JSON.parse(localStorage.getItem('cancionero:transporte'))[c.id];
  cerrarDetalle(); abrirDetalle(c);          // reabrir: debe recordar +2
  var recordado = transporte;
  resetTransporte();
  var trasReset = transporte;
  cerrarDetalle();
  return { tonoMostrado, persistido, recordado, trasReset };
})()
```
Esperado: `tonoMostrado` = tono base +2 (ej. base RE → "MI"), `persistido:2`, `recordado:2`, `trasReset:0`. Screenshot del detalle con el control `− Tono MI (+2) +`.

- [ ] **Step 7: Commit**
```bash
git add index.html
git commit -m "Add transpose control (- / +) in song detail"
```

---

## Self-Review

- **Cobertura del spec:** escala/índices con bemoles de entrada (Task 1 `NOTA_IDX`) · `transponerAcorde` con sufijo + bajo (Task 1) · render de corchetes + líneas instrumentales (Task 3) · offset 0 = sin transponer (Task 3 `if (transporte !== 0)`) · estado + persistencia por canción (Task 2) · control − / + + tono resultante + offset + reset (Task 4) · solo si tiene acordes (Task 4 `cancionTieneAcordes`) · canción sin tono muestra offset (Task 4). ✔
- **Placeholders:** ninguno; código completo.
- **Consistencia:** `transponerNota`/`transponerAcorde`/`esLineaAcordes` (Task 1) usados en `renderLineas` (Task 3) y el control (Task 4). `transporte`/`transportes`/`guardarTransporte` (Task 2) usados en Tasks 3-4. `actualizarControlTransporte`/`transponer`/`resetTransporte` (Task 4) referenciados desde `abrirDetalle` y el HTML del control. ✔
