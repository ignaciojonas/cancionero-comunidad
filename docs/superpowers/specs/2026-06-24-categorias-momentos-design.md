# Mejorar categorías y momentos · Diseño

**Fecha:** 2026-06-24
**Alcance:** Re-clasificar `categoria` y `momento` de las **631 canciones importadas automáticamente** (559 de recursoscatolicos + 72 de Athenas), usando los **tags reales** del sitio recursoscatolicos.com.ar. Las **11 curadas a mano** (`canciones.json`) **no se tocan**.

## Problema

Estado actual (642 canciones): **423 en "General"** (66%) y **633 sin ningún momento**. Las categorías de lo importado se asignaron por palabras clave y los momentos quedaron vacíos.

## Fuente de datos

El cancionero de recursoscatolicos expone un sistema de tags reales vía
`buscar_ajax.php?s=&tags=<id>`, que devuelve las canciones (`?q=<id>`) de cada tag.
Con ~22 requests (uno por tag) se arma el mapa `q-id → [tags]`. Cobertura: 552 de
559 canciones del sitio tienen ≥1 tag.

Tags del sitio (id → nombre): 7 Adviento, 8 Navidad, 9 Cuaresma, 10 Pascua,
11 Pentecostés, 12 Entrada, 13 Ofertorio, 14 Comunión, 15 Meditación, 16 Salida,
17 Gloria, 18 Salmo, 19 Aleluya, 20 Santo, 21 Cordero, 25 Adoración,
33 Animación/RCC, 26 Espíritu Santo, 27 María, 28 Niños, 41 Pascua Joven, 24 Varias.

## Mapeo (dos ejes)

### `momento` (array) ← tags de momento litúrgico

| Tag sitio | momento |
|---|---|
| Entrada | Entrada |
| Gloria | Gloria |
| Salmo | Salmo Responsorial |
| Aleluya | Aclamación al Evangelio |
| Ofertorio | Ofertorio |
| Santo | Santo |
| Cordero | Cordero |
| Comunión | Comunión |
| Meditación | Meditación |
| Salida | Envío |

Los momentos se ordenan en secuencia litúrgica: Entrada, Gloria, Salmo Responsorial,
Aclamación al Evangelio, Ofertorio, Santo, Cordero, Comunión, Meditación, Envío.

### `categoria` (única) ← tag de tema/tiempo, por prioridad

Primer match gana, en este orden:

1. María → **Marianas**
2. Adviento → **Adviento**
3. Navidad → **Navidad**
4. Cuaresma → **Cuaresma**
5. Pascua / Pascua Joven → **Pascua**
6. Pentecostés / Espíritu Santo → **Espíritu Santo**
7. Niños → **Niños**
8. Adoración / Animación/RCC → **Adoración**
9. (ningún tag de tema) → **General**

Los tags "Varias" y "Meditación" no aportan a `categoria` (Meditación sí va a `momento`).
Una canción sin tag de tema queda en **General** pero **con sus momentos cargados**
si tiene tags de momento.

## Asignación por canción

- **Recursos (559):** se identifica la canción por el `q-id` de su campo `fuente`.
  531 tienen tags → se aplica el mapeo. Las 28 sin tags caen en el fallback.
- **Athenas (72):** se matchea por título normalizado contra las canciones del sitio;
  15 matchean y heredan sus tags. Las 57 sin match caen en el fallback.
- **Fallback (~85 canciones sin tags del sitio):** se mantiene la `categoria` por
  palabras clave (clasificador existente) y `momento` queda vacío. No se inventan
  momentos. Quedan marcadas para revisión opcional posterior.
- **Curadas (`canciones.json`, 11):** intactas.

## Implementación

Un script `tools/clasificar_tags.py` que:

1. Baja los 22 tags (`buscar_ajax.php`) y arma `q-id → [tags del sitio]`.
2. Baja el índice una vez para armar `título normalizado → q-id` (para Athenas).
3. Reescribe **en su lugar** `canciones-recursoscatolicos.json` y
   `canciones-athenas.json`, actualizando `categoria` y `momento` según el mapeo;
   conserva el resto de cada objeto (id, título, autor, tono, estrofas, fuente).
4. No toca `canciones.json`.
5. Imprime un resumen (cobertura, conteo por categoría y por momento, cuántas
   quedaron en fallback).

Requests gentiles (delay ≥0.8s) por el rate-limit conocido del sitio.

## No incluido (YAGNI)

- Clasificar con IA las ~85 huérfanas (se ofrece como paso posterior opcional).
- Cambiar la UI (la sidebar y los tags de momento ya renderizan estos campos).
- Tocar las 11 curadas.

## Criterios de éxito

- Las 546 canciones con tags del sitio quedan con `categoria` de tema/tiempo (o General)
  y `momento` cargado según sus tags litúrgicos.
- Los momentos cargados pasan de 9 a ~546 canciones.
- "General" baja drásticamente (de 423 a las genuinamente genéricas + las ~85 de fallback).
- `canciones.json` (curadas) sin cambios.
- La app sigue funcionando sin cambios de código (solo datos).
