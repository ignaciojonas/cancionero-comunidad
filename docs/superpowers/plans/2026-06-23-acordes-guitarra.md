# Acordes de guitarra — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mostrar acordes de guitarra alineados a la sílaba sobre la letra de cada canción, visibles por defecto y ocultables con el botón "Tono".

**Architecture:** Notación ChordPro embebida en el campo `letra` del JSON (`[G]Ven, Espíritu [D]Santo`). Un parser puro convierte cada línea en una secuencia de segmentos `{acorde, texto}`. El render apila acorde sobre texto con `inline-block`. El botón "Tono" alterna un flag de visibilidad y re-renderiza. Todo dentro de `index.html`.

**Tech Stack:** HTML + CSS + JavaScript vanilla. Sin dependencias, sin build. Datos en `canciones.json`. Verificación con Claude_Preview (`preview_eval` + screenshots).

## Global Constraints

- Cero dependencias nuevas; sitio estático hosteable gratis.
- Todo el código vive en `index.html`; los datos en `canciones.json`.
- Retrocompatibilidad: una letra sin `[...]` se renderiza igual que hoy.
- Color del acorde: variable `--gold`. Letra: `--font-serif`, tamaño actual.
- Acordes visibles por defecto; el botón "Tono" los oculta/muestra.
- Canción sin acordes → botón "Tono" desactivado (atenuado, sin acción).

---

### Task 1: Parser ChordPro (`parseChordPro`)

**Files:**
- Modify: `index.html` (bloque `<script>`)

**Interfaces:**
- Produces: `parseChordPro(linea: string) -> Array<{chord: string|null, text: string}>`
  - Divide una línea en segmentos. El texto antes del primer `[acorde]` es `{chord:null, text:"..."}`. Cada `[X]abc` produce `{chord:"X", text:"abc"}` (texto hasta el próximo `[` o fin de línea).
  - `lineaTieneAcordes(linea)` y `cancionTieneAcordes(cancion)` helpers.
  - `cancionTieneAcordes(cancion) -> boolean`: true si alguna estrofa tiene `[` en su `letra`.

- [ ] **Step 1: Agregar el parser al `<script>`** (después de las variables globales, antes de `init`)

```js
// ─── Parser ChordPro ─────────────────────────────────────
// "[G]Ven, Espíritu [D]Santo" -> [{chord:'G',text:'Ven, Espíritu '},{chord:'D',text:'Santo'}]
function parseChordPro(linea) {
  const segmentos = [];
  const re = /\[([^\]]+)\]/g;
  let lastIndex = 0;
  let pendingChord = null;
  let m;
  while ((m = re.exec(linea)) !== null) {
    const texto = linea.slice(lastIndex, m.index);
    if (texto.length > 0 || segmentos.length === 0) {
      segmentos.push({ chord: pendingChord, text: texto });
    } else if (pendingChord !== null) {
      // acordes consecutivos sin texto entre medio
      segmentos.push({ chord: pendingChord, text: '' });
    }
    pendingChord = m[1];
    lastIndex = re.lastIndex;
  }
  segmentos.push({ chord: pendingChord, text: linea.slice(lastIndex) });
  return segmentos;
}

function lineaTieneAcordes(linea) {
  return /\[[^\]]+\]/.test(linea);
}

function cancionTieneAcordes(cancion) {
  return cancion.estrofas.some(e => lineaTieneAcordes(e.letra));
}
```

- [ ] **Step 2: Verificar el parser en el navegador**

Arrancar preview sobre `index.html`, luego `preview_eval`:
```js
JSON.stringify(parseChordPro('[G]Ven, Espíritu [D]Santo'))
```
Esperado: `[{"chord":"G","text":"Ven, Espíritu "},{"chord":"D","text":"Santo"}]`

Y línea sin acordes:
```js
JSON.stringify(parseChordPro('Tú has venido a la orilla'))
```
Esperado: `[{"chord":null,"text":"Tú has venido a la orilla"}]`

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "Add ChordPro parser helpers"
```

---

### Task 2: CSS para acordes apilados

**Files:**
- Modify: `index.html` (bloque `<style>`)

**Interfaces:**
- Produces: clases `.linea`, `.cseg`, `.cseg-chord`, `.cseg-text`, y modificador `.detail-body.hide-chords`.

- [ ] **Step 1: Agregar estilos** (después del bloque `.coro-letra`)

```css
/* ─── Acordes (ChordPro) ─────────────────────────────── */
.linea { display: block; }
.cseg {
  display: inline-flex;
  flex-direction: column;
  vertical-align: bottom;
  white-space: pre-wrap;
}
.cseg-chord {
  font-family: var(--font-sans);
  font-size: 0.72rem;
  font-weight: 600;
  line-height: 1.3;
  color: var(--gold);
  white-space: pre;
  min-height: 1.1em;
}
.cseg-text { white-space: pre-wrap; }

/* Modo "ocultar acordes": colapsa la fila del acorde */
.detail-body.hide-chords .cseg-chord { display: none; }

/* Botón Tono desactivado (canción sin acordes) */
.btn-icon:disabled { opacity: 0.35; cursor: default; }
.btn-icon:disabled:hover { background: var(--bg-hover); color: var(--cream-dim); }
```

- [ ] **Step 2: Commit**

```bash
git add index.html
git commit -m "Add CSS for stacked chord rendering"
```

---

### Task 3: Render de letra con acordes (`renderLetra`)

**Files:**
- Modify: `index.html` — reescribir `renderLetra(cancion)` y agregar `renderLineas(letra)`.

**Interfaces:**
- Consumes: `parseChordPro` (Task 1), clases CSS (Task 2).
- Produces: `renderLineas(letra: string) -> string` (HTML). Reemplaza el render directo de `e.letra`.

- [ ] **Step 1: Agregar `renderLineas` y actualizar `renderLetra`**

Reemplazar la función `renderLetra` actual por:
```js
function escapeHtml(s) {
  return s.replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
}

function renderLineas(letra) {
  return letra.split('\n').map(linea => {
    const segs = parseChordPro(linea).map(seg => {
      const chord = seg.chord ? `<span class="cseg-chord">${escapeHtml(seg.chord)}</span>` : '';
      return `<span class="cseg">${chord}<span class="cseg-text">${escapeHtml(seg.text)}</span></span>`;
    }).join('');
    return `<span class="linea">${segs}</span>`;
  }).join('');
}

function renderLetra(cancion) {
  const body = document.getElementById('detailBody');
  body.innerHTML = '';

  let estrofaNum = 0;
  cancion.estrofas.forEach(e => {
    const block = document.createElement('div');
    if (e.tipo === 'coro') {
      block.className = 'coro-block';
      block.innerHTML = `
        <span class="coro-label">Coro</span>
        <span class="coro-letra">${renderLineas(e.letra)}</span>
      `;
    } else {
      estrofaNum++;
      block.className = 'estrofa';
      block.innerHTML = `
        <span class="estrofa-num">${estrofaNum}</span>
        <span class="estrofa-letra">${renderLineas(e.letra)}</span>
      `;
    }
    body.appendChild(block);
  });
}
```

Nota: `.estrofa-letra`/`.coro-letra` tienen `white-space: pre-line`. Como ahora los renglones son `<span class="linea">` (display:block), se quita la dependencia del `pre-line` para saltos, pero `pre-line` no molesta. Dejarlo.

- [ ] **Step 2: Verificar render con preview**

`preview_eval` que abra una canción con acordes (ver Task 5) y compruebe que existe `.cseg-chord` con texto `G`:
```js
(function(){ var el=document.querySelector('.cseg-chord'); return el ? el.textContent : 'NO CHORD'; })()
```
Esperado: `G` (tras tener la canción cargada). Si Task 5 aún no está, probar inyectando: `document.getElementById('detailBody').innerHTML = renderLineas('[G]Hola [D]mundo'); document.querySelector('.cseg-chord').textContent` → Esperado `G`.

Screenshot del detalle para confirmar que el acorde queda arriba de la sílaba.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "Render lyrics with stacked ChordPro chords"
```

---

### Task 4: Toggle "Tono" — visible por defecto + estado desactivado

**Files:**
- Modify: `index.html` — `abrirDetalle`, `toggleTono`, y estado inicial del botón.

**Interfaces:**
- Consumes: `cancionTieneAcordes` (Task 1), clase `.hide-chords` y `:disabled` (Task 2).
- Produces: comportamiento del toggle.

- [ ] **Step 1: Actualizar `abrirDetalle`** — fijar estado del botón al abrir

Dentro de `abrirDetalle`, después de `renderLetra(cancion);`, agregar:
```js
const btnTono = document.getElementById('btnTono');
const body = document.getElementById('detailBody');
const tieneAcordes = cancionTieneAcordes(cancion);
mostrandoTono = tieneAcordes;            // visibles por defecto si los hay
btnTono.disabled = !tieneAcordes;
btnTono.classList.toggle('active', tieneAcordes);
body.classList.toggle('hide-chords', !tieneAcordes);
```

- [ ] **Step 2: Reescribir `toggleTono`**

```js
function toggleTono() {
  if (!cancionActual || !cancionTieneAcordes(cancionActual)) return;
  mostrandoTono = !mostrandoTono;
  const btn = document.getElementById('btnTono');
  const body = document.getElementById('detailBody');
  btn.classList.toggle('active', mostrandoTono);
  body.classList.toggle('hide-chords', !mostrandoTono);
}
```

- [ ] **Step 3: Verificar con preview**

Abrir canción con acordes → `preview_eval`:
```js
({ active: document.getElementById('btnTono').classList.contains('active'),
   disabled: document.getElementById('btnTono').disabled,
   hidden: document.getElementById('detailBody').classList.contains('hide-chords') })
```
Esperado al abrir: `{active:true, disabled:false, hidden:false}`.
Click en el botón (`preview_click` sobre `#btnTono`) → repetir eval → Esperado: `{active:false, disabled:false, hidden:true}` y screenshot mostrando solo letra.
Abrir una de las 8 demo (sin acordes) → Esperado: `{active:false, disabled:true, hidden:true}`.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "Toggle chords via Tono button, on by default, disabled when none"
```

---

### Task 5: Agregar "Ven, Espíritu Santo" con acordes a `canciones.json`

**Files:**
- Modify: `canciones.json`

**Interfaces:**
- Consumes: notación ChordPro (Task 1).

- [ ] **Step 1: Agregar el objeto al final del array** (id 9)

```json
{
  "id": 9,
  "titulo": "Ven, Espíritu Santo",
  "autor": "Athenas",
  "categoria": "Espíritu Santo",
  "momento": ["Entrada", "Pentecostés"],
  "tono": "D",
  "estrofas": [
    {
      "tipo": "coro",
      "letra": "[G]Ven, Espíritu [D]Santo\n[G]Ven, Espíritu [D]Santo\n[G]Úngeme, [D]lléname\nY [G]enciende el fuego de [A]tu amor"
    }
  ]
}
```

(Recordar agregar la coma después del objeto id 8 anterior.)

- [ ] **Step 2: Validar JSON**

Run: `node -e "JSON.parse(require('fs').readFileSync('canciones.json','utf8')); console.log('OK')"`
Expected: `OK`

- [ ] **Step 3: Verificación end-to-end con preview**

Recargar preview, buscar "Ven, Espíritu Santo" de Athenas, abrirla, screenshot: acordes G/D/A arriba de las sílabas. Click "Tono": se ocultan. Confirmar que el badge "Tono D" aparece en la meta.

- [ ] **Step 4: Commit**

```bash
git add canciones.json
git commit -m "Add 'Ven, Espíritu Santo' (Athenas) with chords as template"
```

---

### Task 6: Documentar la notación ChordPro en el README

**Files:**
- Modify: `README.md` — sección "Agregar una canción".

**Interfaces:** ninguna.

- [ ] **Step 1: Agregar subsección sobre acordes** después del ejemplo JSON existente

```markdown
### Acordes de guitarra (opcional)

Los acordes se escriben dentro del campo `letra` con notación **ChordPro**: el
acorde entre corchetes, pegado a la sílaba donde entra.

```json
"letra": "[G]Ven, Espíritu [D]Santo\n[G]Úngeme, [D]lléname"
```

- El acorde se muestra arriba de su sílaba.
- Una letra **sin** corchetes se ve como texto normal (sin acordes).
- Los acordes se muestran por defecto; el botón **"Tono"** del detalle los oculta/muestra. Si la canción no tiene acordes, ese botón queda desactivado.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "Document ChordPro chord notation in README"
```

---

## Self-Review

- **Cobertura del spec:** modelo de datos (Task 5) · render apilado (Tasks 2-3) · toggle default-on + disabled (Task 4) · retrocompatibilidad (Task 1 parser + Task 3 maneja `chord:null`) · 8 demo intactas (no se tocan) · 1 canción real (Task 5) · README (Task 6). ✔
- **Placeholders:** ninguno; todo el código está completo.
- **Consistencia de tipos:** `parseChordPro` devuelve `{chord, text}` y `renderLineas` consume `seg.chord`/`seg.text`. `cancionTieneAcordes` usado en Task 4 definido en Task 1. ✔
