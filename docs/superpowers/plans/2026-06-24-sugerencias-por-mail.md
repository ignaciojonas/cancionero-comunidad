# Sugerencias por mail — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar botones que abren un mail prellenado para sugerir un cambio en una canción o proponer una canción nueva, sin backend.

**Architecture:** Links `mailto:` nativos (`<a href>`). Funciones puras arman el `href` con `encodeURIComponent`; el href del botón "Sugerir un cambio" se setea al abrir cada canción, y los de "Sugerir una canción" (hero + footer) se setean al cargar. Todo en `index.html`.

**Tech Stack:** HTML + CSS + JS vanilla. Sin dependencias. Verificación con Claude_Preview (`preview_eval` leyendo y decodificando el `href`, + screenshots).

## Global Constraints

- Destinatario fijo: `procesoconfirmacion@gmail.com`.
- Cero dependencias nuevas; sigue siendo estático.
- Todo el código vive en `index.html`.
- Asunto y cuerpo codificados con `encodeURIComponent`.
- Asuntos exactos: `[Cancionero] Cambio: <título>` y `[Cancionero] Nueva canción`.

---

### Task 1: Funciones que arman los `mailto:`

**Files:**
- Modify: `index.html` (bloque `<script>`, después de `SECTION_LABELS`)

**Interfaces:**
- Produces:
  - `buildMailtoHref(asunto: string, cuerpo: string) -> string` — devuelve `mailto:...?subject=...&body=...`.
  - `cuerpoEstrofas(cancion) -> string` — estrofas unidas por línea en blanco, con etiqueta `(Coro)`/`(Intro)`… para tipos que no sean `estrofa`.
  - `hrefCambio(cancion) -> string`
  - `hrefNueva() -> string`

- [ ] **Step 1: Agregar las funciones** después de la constante `SECTION_LABELS`

```js
const MAIL_DESTINO = 'procesoconfirmacion@gmail.com';

function buildMailtoHref(asunto, cuerpo) {
  return 'mailto:' + MAIL_DESTINO +
    '?subject=' + encodeURIComponent(asunto) +
    '&body=' + encodeURIComponent(cuerpo);
}

function cuerpoEstrofas(cancion) {
  return (cancion.estrofas || []).map(e => {
    let label = '';
    if (e.tipo === 'coro') label = '(Coro)\n';
    else if (e.tipo && e.tipo !== 'estrofa') label = '(' + (SECTION_LABELS[e.tipo] || e.tipo) + ')\n';
    return label + e.letra;
  }).join('\n\n');
}

function hrefCambio(cancion) {
  const cuerpo =
`¡Hola! Gracias por ayudar a mejorar el cancionero.
Editá abajo lo que quieras corregir (letra, acordes, tono…) y enviá.
No borres la línea "ID" así la encontramos rápido.

ID: ${cancion.id}
Título: ${cancion.titulo}
Autor: ${cancion.autor}
Categoría: ${cancion.categoria}
Tono: ${cancion.tono || '—'}

Letra (acordes entre corchetes, ej. [DO]):
${cuerpoEstrofas(cancion)}`;
  return buildMailtoHref('[Cancionero] Cambio: ' + cancion.titulo, cuerpo);
}

function hrefNueva() {
  const cuerpo =
`¡Hola! Gracias por sumar un canto.
Completá los campos. Si sabés los acordes, ponelos entre corchetes antes
de la sílaba, ej.: [DO]Tú has ve[RE]nido a la orilla.

Título:
Autor:
Categoría:
Momento (opcional):
Tono:

Letra:
`;
  return buildMailtoHref('[Cancionero] Nueva canción', cuerpo);
}
```

- [ ] **Step 2: Verificar con preview** (tras recargar)

`preview_eval`:
```js
(function(){
  var c = CANCIONES.find(x => x.titulo === 'Alfa y Omega');
  var href = hrefCambio(c);
  var body = decodeURIComponent(href.split('&body=')[1]);
  return {
    empiezaMailto: href.startsWith('mailto:procesoconfirmacion@gmail.com?subject='),
    asuntoOk: href.includes('subject=' + encodeURIComponent('[Cancionero] Cambio: Alfa y Omega')),
    bodyTieneId: body.includes('ID: ' + c.id),
    bodyTieneAcorde: body.includes('[DO]'),
    nuevaAsunto: decodeURIComponent(hrefNueva().split('subject=')[1].split('&')[0])
  };
})()
```
Esperado: `empiezaMailto:true, asuntoOk:true, bodyTieneId:true, bodyTieneAcorde:true, nuevaAsunto:"[Cancionero] Nueva canción"`.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "Add mailto builders for change/new-song suggestions"
```

---

### Task 2: Estilos de los botones de sugerencia

**Files:**
- Modify: `index.html` (bloque `<style>`, después de la sección `Footer`)

**Interfaces:**
- Produces: clases `.detail-footer`, `.btn-sugerir`, `.btn-sugerir-nueva`.

- [ ] **Step 1: Agregar estilos** (después del bloque `footer { … }` / `.footer-text strong`)

```css
/* ─── Botones de sugerencia (mailto) ─────────────────── */
.detail-footer {
  padding: 1rem 1.75rem 1.5rem;
  border-top: 1px solid var(--borde-soft);
  background: var(--blanco);
  flex-shrink: 0;
}
.btn-sugerir {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: none;
  border: 1.5px solid var(--borde);
  border-radius: 7px;
  padding: 0.5rem 1rem;
  font-family: var(--font);
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--azul-dk);
  text-decoration: none;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.btn-sugerir:hover { background: var(--azul-dim); border-color: var(--azul); }

.btn-sugerir-nueva {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border: 1.5px solid var(--azul);
  color: var(--azul-dk);
  background: var(--blanco);
  text-decoration: none;
  font-weight: 600;
  font-size: 0.88rem;
  padding: 0.55rem 1.1rem;
  border-radius: 7px;
  transition: background 0.15s, transform 0.1s;
}
.btn-sugerir-nueva:hover { background: var(--azul-dim); transform: translateY(-1px); }
.hero-cta { display: flex; flex-wrap: wrap; gap: 0.6rem; align-items: center; }
.footer-yt + .footer-sugerir, .footer-sugerir { margin-left: 0.75rem; }
```

- [ ] **Step 2: Commit**

```bash
git add index.html
git commit -m "Add styles for suggestion buttons"
```

---

### Task 3: Botón "Sugerir un cambio" en el detalle

**Files:**
- Modify: `index.html` — HTML del panel de detalle (después de `#detailBody`) y función `abrirDetalle`.

**Interfaces:**
- Consumes: `hrefCambio` (Task 1), `.detail-footer`/`.btn-sugerir` (Task 2).

- [ ] **Step 1: Agregar el footer del panel** justo después de `<div class="detail-body" id="detailBody"></div>`

```html
    <div class="detail-footer">
      <a class="btn-sugerir" id="btnSugerirCambio" href="#" target="_blank" rel="noopener">
        ✎ Sugerir un cambio
      </a>
    </div>
```

- [ ] **Step 2: Setear el href al abrir la canción** — en `abrirDetalle`, después de `renderLetra(cancion);`

```js
    document.getElementById('btnSugerirCambio').href = hrefCambio(cancion);
```

- [ ] **Step 3: Verificar con preview**

Abrir una canción y `preview_eval`:
```js
(function(){
  abrirDetalle(CANCIONES.find(c => c.titulo === 'Alianza'));
  var a = document.getElementById('btnSugerirCambio');
  return {
    visible: a.offsetHeight > 0,
    hrefOk: a.href.startsWith('mailto:procesoconfirmacion@gmail.com'),
    bodyTieneTitulo: decodeURIComponent(a.href).includes('Título: Alianza')
  };
})()
```
Esperado: `{visible:true, hrefOk:true, bodyTieneTitulo:true}`. Screenshot del detalle mostrando el botón.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "Add 'Sugerir un cambio' button to song detail"
```

---

### Task 4: Botones "Sugerir una canción" en hero y footer

**Files:**
- Modify: `index.html` — HTML del hero (al lado de `.yt-link`) y del footer; función `init`.

**Interfaces:**
- Consumes: `hrefNueva` (Task 1), `.btn-sugerir-nueva` (Task 2).

- [ ] **Step 1: Envolver el botón del hero y agregar el de sugerir** — reemplazar el `<a class="yt-link">…</a>` por un contenedor con los dos:

Buscar en el hero:
```html
    <a class="yt-link" href="https://www.youtube.com/@cancionesycantosmpd" target="_blank" rel="noopener">
```
y envolver ese `<a>…</a>` completo en:
```html
    <div class="hero-cta">
      <a class="yt-link" href="https://www.youtube.com/@cancionesycantosmpd" target="_blank" rel="noopener">
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M23 7.5a3 3 0 0 0-2.1-2.1C19.1 5 12 5 12 5s-7.1 0-8.9.4A3 3 0 0 0 1 7.5 31 31 0 0 0 .6 12 31 31 0 0 0 1 16.5a3 3 0 0 0 2.1 2.1C4.9 19 12 19 12 19s7.1 0 8.9-.4a3 3 0 0 0 2.1-2.1A31 31 0 0 0 23.4 12 31 31 0 0 0 23 7.5zM9.8 15.5v-7l6 3.5z"/>
        </svg>
        Playlist Colaborativa
      </a>
      <a class="btn-sugerir-nueva" id="btnSugerirNuevaHero" href="#">✎ Sugerir una canción</a>
    </div>
```

- [ ] **Step 2: Agregar el link en el footer** — después del `<a class="footer-yt">…</a>`:

```html
    <a class="footer-yt footer-sugerir" id="btnSugerirNuevaFooter" href="#">✎ Sugerir una canción</a>
```

- [ ] **Step 3: Setear los href en `init`** — al final de `init`, después de `renderLista();`

```js
    document.querySelectorAll('#btnSugerirNuevaHero, #btnSugerirNuevaFooter')
      .forEach(a => a.href = hrefNueva());
```

- [ ] **Step 4: Verificar con preview**

`preview_eval`:
```js
(function(){
  var h = document.getElementById('btnSugerirNuevaHero');
  var f = document.getElementById('btnSugerirNuevaFooter');
  return {
    heroHref: h.href.startsWith('mailto:procesoconfirmacion@gmail.com'),
    footerHref: f.href.startsWith('mailto:procesoconfirmacion@gmail.com'),
    asunto: decodeURIComponent(h.href.split('subject=')[1].split('&')[0]),
    bodyTienePlantilla: decodeURIComponent(h.href).includes('Título:')
  };
})()
```
Esperado: `{heroHref:true, footerHref:true, asunto:"[Cancionero] Nueva canción", bodyTienePlantilla:true}`. Screenshot del hero mostrando los dos botones.

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "Add 'Sugerir una canción' buttons in hero and footer"
```

---

## Self-Review

- **Cobertura del spec:** Componente 1 cambio (Tasks 1, 3) · Componente 2 nueva (Tasks 1, 4) · destinatario fijo y asuntos exactos (Task 1, Global Constraints) · estilos (Task 2) · etiquetas de sección en estrofas (`cuerpoEstrofas`, Task 1). ✔
- **Placeholders:** ninguno; todo el código está completo.
- **Consistencia de tipos:** `hrefCambio`/`hrefNueva`/`buildMailtoHref`/`cuerpoEstrofas` definidos en Task 1 y usados con esos nombres en Tasks 3-4. IDs `btnSugerirCambio`, `btnSugerirNuevaHero`, `btnSugerirNuevaFooter` consistentes entre HTML y JS. ✔
