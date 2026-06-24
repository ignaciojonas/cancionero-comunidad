# Acordes de guitarra en el Cancionero · Diseño

**Fecha:** 2026-06-23
**Alcance:** Agregar acordes de guitarra a las canciones, alineados a la sílaba, mostrados por defecto y ocultables. Cargar 1 canción real de prueba (desde los PDFs de Athenas) como plantilla, manteniendo las 8 canciones demo. Sin otras mejoras en este ciclo.

## Objetivo

Que cada canción pueda mostrar los acordes de guitarra encima de la sílaba exacta donde se cambia, para poder tocar mientras se lee la letra. Los acordes se ven por defecto y se pueden ocultar con el botón "Tono" que ya existe.

## No incluido (YAGNI)

- Transposición de tono / cambio de cejilla.
- Diagramas de digitación (grillas de acordes).
- Editor visual de acordes.
- Cualquier otra mejora de la app fuera de los acordes.

## Modelo de datos

Se mantiene el archivo `canciones.json` y el campo `letra` de cada estrofa. Se permite **notación ChordPro embebida**: el acorde entre corchetes, pegado a la sílaba donde entra.

Antes:
```json
{ "tipo": "estrofa", "numero": 1, "letra": "Tú has venido a la orilla,\n..." }
```

Después:
```json
{ "tipo": "estrofa", "numero": 1, "letra": "[G]Tú has venido a la o[D]rilla,\n[C]no has buscado ni a [G]sabios ni a ricos..." }
```

Propiedades:

- **Retrocompatible:** una letra sin `[...]` se renderiza exactamente igual que hoy. Las canciones sin acordes no se rompen.
- **Un solo campo:** acorde y sílaba viven juntos en `letra`; no se pueden desalinear.
- El campo `tono` de cada canción se mantiene sin cambios (es metadato informativo, no afecta el render).
- El JSON sigue siendo válido y estático.

Aplica por igual a estrofas (`tipo: "estrofa"`) y coros (`tipo: "coro"`).

## Renderizado

Al dibujar la letra de una canción:

1. **Parser:** se recorre el texto de `letra` y se separa en unidades. Cada `[Acorde]texto` produce una unidad con dos partes: el acorde y el segmento de texto que le sigue (hasta el próximo `[` o el fin de línea). El texto antes del primer acorde es una unidad sin acorde.
2. **Salto de línea:** los `\n` se respetan como hoy (cada renglón es una línea lógica).
3. **Markup:** cada unidad se renderiza como un `inline-block` que apila el acorde arriba y la sílaba/segmento abajo. Así el acorde queda fijo sobre su sílaba y el texto corta de renglón naturalmente al llegar al borde.

Estado **con acordes visibles**:
```
   G                    D
Tú has venido a la o rilla,
   C                G
no has buscado ni a sabios ni a ricos...
```

Estado **con acordes ocultos** (idéntico a hoy):
```
Tú has venido a la orilla,
no has buscado ni a sabios ni a ricos...
```

### Estilo

- El acorde usa un color de acento (dorado `--gold` o granate) y tamaño chico; el texto mantiene la tipografía serif (`--font-serif`) y el tamaño actual de la letra.
- Cuando los acordes están ocultos, se renderiza solo el texto (sin reservar el espacio vertical del acorde), de modo que el layout queda igual al actual.

## Toggle (mostrar / ocultar acordes)

- Se reutiliza el botón **"Tono"** existente (`btnTono`) y la función `toggleTono()` (hoy reservada para esto).
- **Por defecto los acordes se muestran.** Al abrir una canción con acordes, el botón arranca en estado `active` (estilo ya presente en el CSS).
- Tocar el botón **oculta** los acordes (solo letra); volver a tocarlo los muestra de nuevo. El re-render usa el mismo parser con un flag de visibilidad.
- El estado es **por canción** y se resetea al cerrar el detalle (comportamiento ya existente vía `mostrandoTono`).
- Si la canción **no tiene acordes** (ningún `[...]` en sus estrofas), el botón aparece **atenuado/desactivado** y no hace nada.

## Contenido

### Las 8 canciones demo

Se **mantienen tal cual están**, sin acordes. Al abrir cualquiera de ellas, el botón "Tono" queda atenuado/desactivado (no tienen `[...]` en sus estrofas). Sirven para demostrar el estado "sin acordes".

### 1 canción de prueba (plantilla real)

Se agrega **una** canción nueva tomada de los PDFs de Athenas, con sus acordes en notación ChordPro, como ejemplo funcional y plantilla para futuras cargas.

- **Canción elegida:** "Ven, Espíritu Santo" (tono D). Es corta y limpia, y mapea directo al modelo `estrofa`/`coro` actual sin necesidad de tipos de sección nuevos.
- Fuente: `Ven, Espíritu Santo (D).pdf` (acordes sobre la letra). Se traduce la posición de cada acorde a la sílaba correspondiente en notación ChordPro inline.
- Se le asignan `categoria`, `momento` y `tono` coherentes con el resto del catálogo.

> **Advertencia:** la conversión de la posición de acordes desde el PDF es una transcripción de base. **Conviene verificarla con la guitarra antes de usarla en comunidad.**

### Fuera de alcance de este ciclo

- Importar los otros ~71 PDFs de la carpeta.
- Modelar secciones más ricas presentes en muchas hojas de Athenas (`INTRO`, `PRE CORO`, `PUENTE`, líneas instrumentales como `| F#m | C#m B |`). Eso requeriría ampliar el modelo de datos y se decidirá si/ cuando se importe el resto del repertorio.

## Implementación

- Todo se resuelve dentro de `index.html` (parser de ChordPro + CSS de apilado + ajuste de `toggleTono()` y del estado inicial) y en `canciones.json` (acordes embebidos).
- **Cero dependencias nuevas.** Sigue siendo un sitio estático, sin backend, hosteable gratis.

## Documentación

- Actualizar el `README.md` para documentar la notación ChordPro en el campo `letra` (cómo cargar acordes en una canción nueva) y el comportamiento del toggle.

## Criterios de éxito

- Una canción con acordes los muestra alineados a la sílaba al abrir el detalle.
- El botón "Tono" oculta y vuelve a mostrar los acordes.
- Una canción sin acordes se ve igual que hoy y su botón "Tono" queda desactivado.
- Las 8 canciones demo se mantienen sin cambios (sin acordes, botón "Tono" desactivado).
- Se agrega "Ven, Espíritu Santo" con acordes en ChordPro, que se muestran alineados al abrirla.
- No se agregan dependencias ni backend.
