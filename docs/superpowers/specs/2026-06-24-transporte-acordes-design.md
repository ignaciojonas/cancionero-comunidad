# Transporte de acordes · Diseño

**Fecha:** 2026-06-24
**Alcance:** Permitir transponer los acordes de una canción por semitonos en el detalle, con botones − / +, mostrando el tono resultante, recordando el transporte por canción. Solo notación latina (DO/RE/MI), siempre con sostenidos.

## Lógica de transporte

- Escala cromática (sostenidos): `['DO','DO#','RE','RE#','MI','FA','FA#','SOL','SOL#','LA','LA#','SI']`.
- Mapa nota→índice que también acepta bemoles de entrada: `DOb→SI(11)`-equiv no aplica; se cubren `REb=1, MIb=3, SOLb=6, LAb=8, SIb=10` además de los naturales y sostenidos.
- `transponerAcorde(acorde, semitonos) -> string`:
  - Separa raíz (`DO|RE|MI|FA|SOL|LA|SI` + `#`/`b` opcional), sufijo (resto), y bajo opcional tras `/`.
  - Convierte la raíz: índice = mapa[raíz]; nueva = `cromatica[(índice + semitonos) % 12]` (siempre sostenido).
  - Reescribe: `nueva + sufijo` y, si hay bajo, `+ '/' + transponerNota(bajo)`.
  - Si la raíz no se reconoce (no es acorde), devuelve el texto igual.
- `transponerNota(nota)`: helper que transpone solo la raíz+alteración (para el bajo y para el tono).

## Render

- En `renderLineas`, cada acorde se transpone por el offset actual (`transporte`):
  - **Acordes entre corchetes**: se transpone `seg.chord`.
  - **Líneas instrumentales** (sin corchetes, tipo `| FA#m | DO#m SI |`): se detecta con un `esLineaAcordes(linea)` (estricto, igual criterio que el normalizador) y se transpone cada token de acorde; barras y demás quedan igual.
- Con `transporte === 0`, el render es idéntico al actual.

## Estado y persistencia

- Global `transporte` (entero, semitonos de la canción abierta).
- Mapa `transportes` (objeto `{ id: semitonos }`) persistido en `localStorage`, clave `cancionero:transporte`. `try/catch` (sin localStorage funciona en memoria).
- `cargarTransportes()` en `init`. `guardarTransporte(id, semitonos)` actualiza el mapa y persiste (borra la entrada si vuelve a 0).
- `abrirDetalle`: `transporte = transportes[cancion.id] || 0`.

## UI (línea de meta del detalle)

- Control compacto reemplazando/junto al badge de tono:
  `[ − ]  Tono <strong>RE</strong>  [ + ]`, donde el tono es el **resultante** del transporte.
  Si `transporte !== 0`, se muestra el offset (ej. `MI (+2)`).
- Tocar el texto del tono → `resetTransporte()` (offset 0).
- El control aparece solo si la canción tiene acordes (`cancionTieneAcordes`).
- Funciones: `transponer(delta)` (suma delta al offset, re-renderiza letra, actualiza control, persiste), `resetTransporte()`.
- Si la canción no tiene `tono` declarado pero sí acordes, el control muestra el offset (ej. `Transporte +2`) en vez de una tonalidad.

## No incluido (YAGNI)

- Sugerencia de cejilla (capo).
- Preferencia de bemoles (siempre sostenidos, por decisión del usuario).
- Transporte desde la lista (solo en el detalle).

## Verificación

- `transponerAcorde`: `DO,2→RE`; `LA#m,1→SIm`; `SOL/SI,2→LA/DO#`; `SIb,0→SIb`(entrada bemol se respeta a 0 semitonos → idealmente queda igual; ver nota); `MI,1→FA`; `DO,-1→SI`; `SOLsus4,2→LAsus4`.
- En el navegador: `+` re-renderiza acordes y líneas instrumentales al nuevo tono; el badge muestra el tono resultante con offset; persiste al cerrar y reabrir; reset vuelve al original.

**Nota sobre entrada bemol a 0 semitonos:** como la salida siempre es en sostenidos, `transponerAcorde('SIb', 0)` devuelve `LA#`. Es consistente con "siempre sostenidos"; los pocos acordes con bemol del repertorio quedarán como sostenidos al interactuar con el transporte (a 0, el render normal no llama al transpositor, así que sin tocar nada se ven igual que hoy).

## Criterios de éxito

- Botones − / + transponen todos los acordes (corchetes + instrumentales) de a un semitono.
- El tono mostrado refleja el transporte; tocar el tono resetea.
- El transporte se recuerda por canción entre recargas.
- Con offset 0, todo se ve igual que hoy.
- Sin dependencias nuevas.
