# Favoritos + Al azar — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Marcar canciones favoritas (persistidas en localStorage), filtrar por favoritos, y un botón 🎲 que abre una canción al azar (favoritos primero).

**Architecture:** Un `Set` `favoritos` en memoria, sincronizado con `localStorage`. Estrella en cada tarjeta y en el detalle. Chip "★ Favoritos" en los filtros. Botón 🎲 en el header. Todo en `index.html`.

**Tech Stack:** JS vanilla + CSS en `index.html`. Verificación con Claude_Preview (`preview_eval` + screenshots).

## Global Constraints

- Todo en `index.html`; sin dependencias.
- `localStorage` en `try/catch`: sin él, los favoritos funcionan en la sesión.
- Centinela `FILTRO_FAVORITOS = '★ Favoritos'` (no colisiona con categorías).

---

### Task 1: Estado de favoritos (storage + helpers)

**Files:**
- Modify: `index.html` — globales + funciones, carga en `init`.

**Interfaces:**
- Produces: `favoritos` (Set), `FILTRO_FAVORITOS`, `esFavorito(id)`, `toggleFavorito(id)`, `guardarFavoritos()`, `cargarFavoritos()`, `pintarEstrella(el, fav)`.

- [ ] **Step 1: Declarar globales** — junto a `let filtroActivo = 'Todas';`

Buscar:
```js
  let filtroActivo = 'Todas';
```
Reemplazar por:
```js
  let filtroActivo = 'Todas';
  const FILTRO_FAVORITOS = '★ Favoritos';
  const FAV_KEY = 'cancionero:favoritos';
  let favoritos = new Set();
```

- [ ] **Step 2: Agregar las funciones** — después de `textoBuscable` (antes de `SECTION_LABELS`)

```js
  // ─── Favoritos (localStorage) ────────────────────────────
  function cargarFavoritos() {
    try {
      const raw = localStorage.getItem(FAV_KEY);
      if (raw) favoritos = new Set(JSON.parse(raw));
    } catch (e) { /* sin localStorage: queda el Set vacío en memoria */ }
  }
  function guardarFavoritos() {
    try { localStorage.setItem(FAV_KEY, JSON.stringify([...favoritos])); } catch (e) {}
  }
  function esFavorito(id) { return favoritos.has(id); }
  function toggleFavorito(id) {
    if (favoritos.has(id)) favoritos.delete(id); else favoritos.add(id);
    guardarFavoritos();
    return favoritos.has(id);
  }
  function pintarEstrella(el, fav) {
    el.textContent = fav ? '★' : '☆';
    el.classList.toggle('fav-activo', fav);
    el.setAttribute('aria-pressed', fav ? 'true' : 'false');
  }
```

- [ ] **Step 3: Cargar al iniciar** — en `init`, antes de `renderFiltros();`

Buscar:
```js
    CANCIONES = base.concat(athenas, recursos);
    renderFiltros();
```
Reemplazar por:
```js
    CANCIONES = base.concat(athenas, recursos);
    cargarFavoritos();
    renderFiltros();
```

- [ ] **Step 4: Verificar** — recargar y `preview_eval`:
```js
(function(){
  favoritos.clear(); guardarFavoritos();
  var a = toggleFavorito(999);            // agrega
  var persistido = JSON.parse(localStorage.getItem('cancionero:favoritos'));
  var b = toggleFavorito(999);            // quita
  return { trasAgregar: a, esFav: esFavorito(999) === false, persistido };
})()
```
Esperado: `trasAgregar:true`, `esFav:true` (ya no es favorito tras el segundo toggle), `persistido:[999]`.

- [ ] **Step 5: Commit**
```bash
git add index.html
git commit -m "Add favorites state backed by localStorage"
```

---

### Task 2: Estrella en las tarjetas + chip de filtro + filtrado

**Files:**
- Modify: `index.html` — CSS, `renderFiltros`, `renderLista`.

**Interfaces:**
- Consumes: `esFavorito`, `toggleFavorito`, `pintarEstrella`, `FILTRO_FAVORITOS` (Task 1).
- Produces: `toggleFavoritoUI(id, el)`; clases CSS `.song-card-actions`, `.star-btn`.

- [ ] **Step 1: Agregar estilos** — después de `.song-arrow:hover` / antes de `.empty-state` (en el bloque Song List)

```css
    .song-card-actions { display: flex; align-items: center; gap: 0.6rem; flex-shrink: 0; }
    .star-btn {
      background: none; border: none; cursor: pointer;
      font-size: 1.3rem; line-height: 1; color: var(--borde);
      padding: 0.15rem; transition: color 0.15s, transform 0.1s;
    }
    .star-btn:hover { transform: scale(1.15); color: var(--oro); }
    .star-btn.fav-activo { color: var(--oro); }
    .btn-icon.fav-activo { color: var(--oro); border-color: var(--oro); background: var(--oro-dim); }
    #btnFav { font-size: 1.15rem; }
```

- [ ] **Step 2: Agregar `toggleFavoritoUI`** — después de `pintarEstrella` (Task 1)

```js
  function toggleFavoritoUI(id, el) {
    const fav = toggleFavorito(id);
    pintarEstrella(el, fav);
    if (filtroActivo === FILTRO_FAVORITOS) renderLista();
  }
```

- [ ] **Step 3: Prepend del chip "Favoritos"** — en `renderFiltros`

Buscar:
```js
  function renderFiltros() {
    const cats = getCategorias();
```
Reemplazar por:
```js
  function renderFiltros() {
    const cats = [FILTRO_FAVORITOS, ...getCategorias()];
```

- [ ] **Step 4: Filtrado por favoritos + estado vacío** — en `renderLista`

Buscar:
```js
    let lista = CANCIONES;
    if (filtroActivo !== 'Todas') lista = lista.filter(c => c.categoria === filtroActivo);
    if (q) {
      const qn = normalizar(q);
      lista = lista.filter(c => textoBuscable(c).includes(qn));
    }

    countEl.textContent = lista.length === 1 ? '1 canción' : `${lista.length} canciones`;
    container.innerHTML = '';

    if (lista.length === 0) {
      container.innerHTML = '<p class="empty-state">No se encontraron canciones.</p>';
      return;
    }
```
Reemplazar por:
```js
    let lista = CANCIONES;
    if (filtroActivo === FILTRO_FAVORITOS) lista = lista.filter(c => esFavorito(c.id));
    else if (filtroActivo !== 'Todas') lista = lista.filter(c => c.categoria === filtroActivo);
    if (q) {
      const qn = normalizar(q);
      lista = lista.filter(c => textoBuscable(c).includes(qn));
    }

    countEl.textContent = lista.length === 1 ? '1 canción' : `${lista.length} canciones`;
    container.innerHTML = '';

    if (lista.length === 0) {
      container.innerHTML = (filtroActivo === FILTRO_FAVORITOS && !q)
        ? '<p class="empty-state">Todavía no marcaste favoritos. Tocá la ☆ en una canción.</p>'
        : '<p class="empty-state">No se encontraron canciones.</p>';
      return;
    }
```

- [ ] **Step 5: Estrella en la tarjeta** — en `renderLista`, reemplazar el `card.innerHTML` completo

Buscar el bloque `card.innerHTML = \`...\`;` (con `song-card-left` y `song-arrow`) y reemplazarlo por:
```js
      const fav = esFavorito(cancion.id);
      card.innerHTML = `
        <div class="song-card-left">
          <div class="song-title">${cancion.titulo}</div>
          <div class="song-meta">
            <span class="tag">${cancion.categoria}</span>
            ${momentoTags}
            <span class="song-autor">${cancion.autor}</span>
          </div>
        </div>
        <div class="song-card-actions">
          <button class="star-btn ${fav ? 'fav-activo' : ''}" title="Favorito"
                  aria-pressed="${fav ? 'true' : 'false'}"
                  onclick="event.stopPropagation(); toggleFavoritoUI(${cancion.id}, this)">${fav ? '★' : '☆'}</button>
          <svg class="song-arrow" width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
            <polyline points="7,4 13,9 7,14"/>
          </svg>
        </div>
      `;
```

- [ ] **Step 6: Verificar con preview**

Recargar y `preview_eval`:
```js
(function(){
  favoritos.clear(); guardarFavoritos();
  var id = CANCIONES[0].id;
  toggleFavorito(id);
  filtroActivo = FILTRO_FAVORITOS; renderFiltros(); renderLista();
  var cards = document.querySelectorAll('.song-card').length;
  var chip = Array.from(document.querySelectorAll('#filterList .filter-btn')).some(b=>b.textContent==='★ Favoritos');
  return { chipPresente: chip, cardsEnFavoritos: cards, esperado1: cards === 1 };
})()
```
Esperado: `chipPresente:true`, `cardsEnFavoritos:1`. Screenshot del filtro Favoritos con 1 canción y su ★.

- [ ] **Step 7: Commit**
```bash
git add index.html
git commit -m "Add favorite star on cards and Favoritos filter chip"
```

---

### Task 3: Estrella en el detalle

**Files:**
- Modify: `index.html` — HTML de `detail-actions` y `abrirDetalle`.

**Interfaces:**
- Consumes: `esFavorito`, `toggleFavorito`, `pintarEstrella`, `toggleFavoritoUI` (Tasks 1-2).

- [ ] **Step 1: Botón estrella en el detalle** — antes de `#btnTono`

Buscar:
```html
      <div class="detail-actions">
        <button class="btn-icon" id="btnTono" title="Mostrar / ocultar acordes" onclick="toggleTono()">
```
Reemplazar por:
```html
      <div class="detail-actions">
        <button class="btn-icon" id="btnFav" title="Favorito" aria-pressed="false"
                onclick="toggleFavoritoUI(cancionActual.id, this)">☆</button>
        <button class="btn-icon" id="btnTono" title="Mostrar / ocultar acordes" onclick="toggleTono()">
```

- [ ] **Step 2: Sincronizar la estrella al abrir** — en `abrirDetalle`, después de `document.getElementById('detailTitulo').textContent = cancion.titulo;`

```js
    pintarEstrella(document.getElementById('btnFav'), esFavorito(cancion.id));
```

- [ ] **Step 3: Verificar con preview**

`preview_eval`:
```js
(function(){
  favoritos.clear(); guardarFavoritos();
  abrirDetalle(CANCIONES[0]);
  var antes = document.getElementById('btnFav').classList.contains('fav-activo');
  document.getElementById('btnFav').click();
  var despues = document.getElementById('btnFav').classList.contains('fav-activo');
  var enSet = esFavorito(CANCIONES[0].id);
  cerrarDetalle();
  return { antes, despues, enSet };
})()
```
Esperado: `{antes:false, despues:true, enSet:true}`. Screenshot del detalle con la ★ dorada activa.

- [ ] **Step 4: Commit**
```bash
git add index.html
git commit -m "Add favorite star in song detail header"
```

---

### Task 4: Botón "Al azar" en el header

**Files:**
- Modify: `index.html` — CSS, HTML del header, función `cancionAlAzar`.

**Interfaces:**
- Consumes: `esFavorito`, `abrirDetalle` (existente).
- Produces: `cancionAlAzar()`; clase `.btn-azar`.

- [ ] **Step 1: Estilo del botón** — después de `#search:focus { ... }`

```css
    .btn-azar {
      flex-shrink: 0;
      background: var(--gris-bg);
      border: 1.5px solid var(--borde);
      border-radius: 6px;
      width: 42px; height: 42px;
      cursor: pointer;
      font-size: 1.15rem;
      display: flex; align-items: center; justify-content: center;
      transition: background 0.15s, border-color 0.15s, transform 0.1s;
    }
    .btn-azar:hover { background: var(--azul-dim); border-color: var(--azul); transform: translateY(-1px); }
```

- [ ] **Step 2: Botón en el header** — después del `</div>` que cierra `.search-wrap`

Buscar:
```html
      <input type="search" id="search" placeholder="Buscar por título, autor o letra…" autocomplete="off" />
    </div>
  </div>
</header>
```
Reemplazar por:
```html
      <input type="search" id="search" placeholder="Buscar por título, autor o letra…" autocomplete="off" />
    </div>
    <button class="btn-azar" title="Canción al azar (de tus favoritos)" onclick="cancionAlAzar()">🎲</button>
  </div>
</header>
```

- [ ] **Step 3: Función `cancionAlAzar`** — después de `cancionAlAzar` no existe aún; agregar después de `cerrarDetalle`

```js
  function cancionAlAzar() {
    let pool = CANCIONES.filter(c => esFavorito(c.id));
    if (pool.length === 0) pool = CANCIONES;
    if (pool.length === 0) return;
    abrirDetalle(pool[Math.floor(Math.random() * pool.length)]);
  }
```

- [ ] **Step 4: Verificar con preview**

`preview_eval`:
```js
(function(){
  favoritos.clear(); guardarFavoritos();
  var soloId = CANCIONES[5].id; toggleFavorito(soloId);
  cerrarDetalle();
  cancionAlAzar();                       // con 1 favorito -> debe abrir ese
  var abierto = cancionActual && cancionActual.id;
  cerrarDetalle();
  favoritos.clear(); guardarFavoritos();
  cancionAlAzar();                       // sin favoritos -> abre cualquiera
  var abiertoSinFav = !!cancionActual;
  cerrarDetalle();
  return { conUnFavoritoAbreEse: abierto === soloId, sinFavoritosAbreAlguna: abiertoSinFav };
})()
```
Esperado: `{conUnFavoritoAbreEse:true, sinFavoritosAbreAlguna:true}`. Screenshot del header con el 🎲.

- [ ] **Step 5: Commit**
```bash
git add index.html
git commit -m "Add random-song button (favorites first) in header"
```

---

## Self-Review

- **Cobertura del spec:** storage/Set + try/catch (Task 1) · esFavorito/toggleFavorito/guardar (Task 1) · estrella en tarjeta sin abrir detalle (Task 2 Step 5, `stopPropagation`) · chip Favoritos primero (Task 2 Step 3) · filtrado + estado vacío (Task 2 Step 4) · re-render al desmarcar en vista Favoritos (Task 2 `toggleFavoritoUI`) · estrella en detalle sincronizada (Task 3) · botón 🎲 en header + pool favoritos→todas (Task 4). ✔
- **Placeholders:** ninguno; código completo.
- **Consistencia:** `pintarEstrella(el, fav)`, `toggleFavorito(id)->bool`, `toggleFavoritoUI(id, el)`, `esFavorito(id)`, `FILTRO_FAVORITOS`, `cancionAlAzar()` usados con nombres/firmas idénticos entre tasks. El botón detalle usa `id="btnFav"` (CSS Task 2 Step 1, HTML Task 3 Step 1, sync Task 3 Step 2). ✔
