# Acordes de guitarra en el Cancionero · Diseño

**Fecha:** 2026-06-23
**Alcance:** Agregar acordes de guitarra a las canciones, alineados a la sílaba, mostrados por defecto y ocultables. Sin otras mejoras en este ciclo.

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

## Contenido: acordes de las 8 canciones existentes

Se cargan acordes de base para las 8 canciones ya presentes, en el tono que cada una ya declara (`tono`). Son piezas litúrgicas conocidas (Pescador de Hombres, El Señor es mi Pastor, etc.).

> **Advertencia:** los acordes son una propuesta de base generada sin una fuente autorizada. **Conviene verificarlos con la guitarra antes de usarlos en comunidad.** El usuario revisa/corrige lo que no le cierre.

## Implementación

- Todo se resuelve dentro de `index.html` (parser de ChordPro + CSS de apilado + ajuste de `toggleTono()` y del estado inicial) y en `canciones.json` (acordes embebidos).
- **Cero dependencias nuevas.** Sigue siendo un sitio estático, sin backend, hosteable gratis.

## Documentación

- Actualizar el `README.md` para documentar la notación ChordPro en el campo `letra` (cómo cargar acordes en una canción nueva) y el comportamiento del toggle.

## Criterios de éxito

- Una canción con acordes los muestra alineados a la sílaba al abrir el detalle.
- El botón "Tono" oculta y vuelve a mostrar los acordes.
- Una canción sin acordes se ve igual que hoy y su botón "Tono" queda desactivado.
- Las 8 canciones existentes tienen acordes de base cargados.
- No se agregan dependencias ni backend.
