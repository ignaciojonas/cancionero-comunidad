# Favoritos locales + Canción al azar · Diseño

**Fecha:** 2026-06-24
**Alcance:** Permitir marcar canciones como favoritas (guardadas en el navegador), filtrar por favoritos, y un botón que abre una canción al azar (priorizando favoritos). Sin backend.

## Favoritos

### Almacenamiento
- `localStorage`, clave `cancionero:favoritos` = array JSON de ids de canción.
- Al iniciar se carga a un `Set` en memoria (`favoritos`).
- Toda lectura/escritura de `localStorage` va en `try/catch`: si no está disponible
  (modo incógnito, permisos), la app sigue funcionando con el `Set` en memoria por la sesión.

### Funciones
- `esFavorito(id) -> boolean`
- `toggleFavorito(id)` — agrega/quita del `Set`, persiste, y actualiza la UI.
- `guardarFavoritos()` — escribe el `Set` a `localStorage` (try/catch).

### UI de la estrella
- Botón estrella en **cada tarjeta** de la lista: `★` si es favorita, `☆` si no.
  Al tocarla, marca/desmarca **sin abrir** el detalle (`stopPropagation`).
- Botón estrella en el **header del detalle** (junto a Tono/Cerrar), sincronizado.
- Al togglear: se actualiza la estrella tocada; si la vista activa es "Favoritos",
  se re-renderiza la lista (para que un desmarcado desaparezca).

### Filtro "Favoritos"
- Constante centinela `FILTRO_FAVORITOS = '★ Favoritos'` (no colisiona con categorías reales).
- Se antepone como **primer chip** de filtros, antes de "Todas" (sidebar + barra mobile).
- Con el filtro activo, `renderLista` muestra solo las canciones cuyo id está en `favoritos`.
- Si no hay favoritos, mensaje de estado vacío: *"Todavía no marcaste favoritos. Tocá la ★ en una canción."*

## Canción al azar

- Botón `🎲` en el header, al lado del buscador.
- `cancionAlAzar()`: arma `pool` = canciones favoritas; si está vacío, `pool` = todas (`CANCIONES`).
  Elige una al azar y llama `abrirDetalle(cancion)`.

## Integración con lo existente

- `renderFiltros`: antepone el chip de favoritos a la lista de categorías.
- `renderLista`: si `filtroActivo === FILTRO_FAVORITOS`, filtra por el `Set`; el resto del
  filtrado (búsqueda) se sigue aplicando.
- Las tarjetas (`renderLista`) suman el botón estrella; `abrirDetalle` sincroniza la estrella del detalle.

## No incluido (YAGNI)

- Sincronización entre dispositivos / cuentas (es local por diseño).
- Exportar/importar favoritos.
- Que "Al azar" respete la categoría/búsqueda activa (queda favoritos→todas; se puede sumar después).

## Verificación

- En el preview: marcar una canción persiste en `localStorage`; recargar la mantiene.
- El filtro "★ Favoritos" muestra solo las marcadas; vacío muestra el mensaje.
- `🎲` con favoritos abre una de favoritos; sin favoritos abre una de las 642.
- Sin `localStorage` disponible, no hay errores y los favoritos funcionan en la sesión.

## Criterios de éxito

- Marcar/desmarcar desde la tarjeta y desde el detalle, persistente entre recargas.
- Chip "★ Favoritos" filtra correctamente y muestra estado vacío cuando corresponde.
- `🎲` abre una canción del pool correcto (favoritos, o todas si no hay).
- Sin dependencias nuevas; sigue estático.
