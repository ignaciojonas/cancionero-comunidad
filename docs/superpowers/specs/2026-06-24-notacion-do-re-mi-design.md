# Unificar notación de acordes a DO/RE/MI · Diseño

**Fecha:** 2026-06-24
**Alcance:** Convertir todos los acordes en notación inglesa (C, D, E…) a notación latina (DO, RE, MI…) en los tres archivos de canciones, incluyendo el campo `tono`. Sin cambios en el código de la app.

## Motivación

La data tiene notación mezclada: las de Athenas (71 canciones) usan inglés (C, D, G…), y quedan residuos en las curadas (1 canción + 11 tonos) y recursoscatolicos (5 canciones). El objetivo es que **todo** esté en DO/RE/MI, lo que además simplifica el transporte de acordes futuro.

## Mapeo

Raíz: `C→DO, D→RE, E→MI, F→FA, G→SOL, A→LA, B→SI`.

Se conserva todo lo demás del acorde:
- **Alteraciones** pegadas a la raíz: `C#→DO#`, `Bb→SIb`, `F#→FA#`.
- **Sufijos / cualidad**: `m`, `7`, `maj7`, `sus2`, `sus4`, `dim`, `aug`, `add9`, `9`, `6`, etc. → intactos. Ej.: `Am→LAm`, `G7→SOL7`, `Cmaj7→DOmaj7`, `Dsus4→REsus4`.
- **Bajo (slash)**: se convierte raíz **y** bajo. Ej.: `G/B→SOL/SI`, `D/F#→RE/FA#`.

Notas que ya están en latín (DO, RE…) se dejan igual (idempotente).

## Qué se convierte

1. **Acordes entre corchetes** dentro de `letra`: `[G]` → `[SOL]`. (~1815 ocurrencias.)
2. **Líneas instrumentales sueltas** (sin corchetes), tipo `| F#m | C#m B |` (~121, todas en Athenas): se tokeniza por espacios y se convierte **solo** los tokens que matchean el patrón de acorde; las barras `|` y cualquier otro token quedan intactos. No se toca texto de letra normal (las líneas con letra no entran porque no son "líneas de solo acordes").
3. **Campo `tono`**: `"G"` → `"SOL"` (~81 tonos en inglés).

## Componentes

- `acorde_a_espanol(acorde: str) -> str` (función pura): aplica el mapeo a un acorde individual (raíz + alteración + sufijo + bajo). Es la unidad testeable.
- `convertir_letra(letra: str) -> str`: convierte los `[...]` y las líneas instrumentales.
- Script `tools/normalizar_notacion.py`: reescribe los 3 JSON aplicando lo anterior a cada `letra` y a cada `tono`. No toca `canciones.json` de forma distinta — los tres se procesan igual.

## Detección de "línea instrumental suelta"

Una línea sin `[` se trata como línea de acordes (y por tanto se convierte token a token) **solo si** todos sus tokens (ignorando `|`) matchean el patrón de acorde. Si algún token no es acorde (es letra), la línea se deja intacta. Así una línea de letra sin acordes nunca se modifica.

## No incluido (YAGNI)

- Transporte de acordes (es la feature siguiente; esto la habilita).
- Cambios en el render de la app (ya muestra DO/RE/MI).
- Convertir notación alemana (H) u otras (no existen en la data).

## Verificación

- Tests de `acorde_a_espanol` con asserts: `C→DO`, `Am→LAm`, `F#m→FA#m`, `Bb→SIb`, `G/B→SOL/SI`, `Csus4→DOsus4`, `DO→DO` (idempotente), `G7→SOL7`.
- Correr el script y comprobar que **no queda ningún acorde inglés** entre corchetes ni en tonos (re-correr el análisis: inglés = 0).
- Mostrar antes/después de un par de Athenas con líneas instrumentales para confirmar que la letra no se rompió.
- Verificación en el navegador: una canción de Athenas muestra los acordes en DO/RE/MI y el badge "Tono …" en latín.

## Criterios de éxito

- Cero acordes en notación inglesa entre corchetes en los tres archivos.
- Cero tonos en inglés.
- Líneas instrumentales convertidas sin romper texto de letra.
- La app renderiza igual, ahora todo en DO/RE/MI.
