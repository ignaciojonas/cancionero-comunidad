# Notación DO/RE/MI — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir todos los acordes y tonos en notación inglesa (C, D, E…) a latina (DO, RE, MI…) en los tres archivos de canciones.

**Architecture:** Script `tools/normalizar_notacion.py` con una función pura `acorde_a_espanol` (convierte un acorde) y `convertir_letra` (corchetes + líneas instrumentales). Detección **estricta** de acordes para no confundir palabras de letra (ej. "Aleluya") con acordes. Reescribe los 3 JSON.

**Tech Stack:** Python 3 (stdlib). Verificación: asserts de las funciones puras + re-análisis (cero inglés) + navegador.

## Global Constraints

- Mapeo raíz: C→DO, D→RE, E→MI, F→FA, G→SOL, A→LA, B→SI; alteraciones y sufijos intactos; bajo (slash) convierte raíz y bajo.
- Idempotente: lo que ya está en latín queda igual.
- Líneas de letra (no-acordes) nunca se modifican.

---

### Task 1: `acorde_a_espanol` (conversión de un acorde)

**Files:**
- Create: `tools/normalizar_notacion.py`

**Interfaces:**
- Produces: `acorde_a_espanol(ac: str) -> str`.

- [ ] **Step 1: Crear el script con constantes y la función de conversión**

```python
#!/usr/bin/env python3
"""Convierte acordes/tonos de notación inglesa (C,D,E…) a latina (DO,RE,MI…)
en los tres JSON de canciones."""
import re, json, os

ROOT = {'C': 'DO', 'D': 'RE', 'E': 'MI', 'F': 'FA', 'G': 'SOL', 'A': 'LA', 'B': 'SI'}
LATIN = re.compile(r'^(DO|RE|MI|FA|SOL|LA|SI)')
# conversión: raíz + alteración + sufijo (preservado) + bajo opcional
ENG = re.compile(r'^([A-G])(#|b)?([^/\s]*)(?:/([A-G])(#|b)?)?$')

def acorde_a_espanol(ac):
    if LATIN.match(ac):
        return ac                      # ya está en latín
    m = ENG.match(ac)
    if not m:
        return ac                      # no es un acorde inglés reconocible
    r, acc, suf, br, bacc = m.groups()
    out = ROOT[r] + (acc or '') + (suf or '')
    if br:
        out += '/' + ROOT[br] + (bacc or '')
    return out
```

- [ ] **Step 2: Verificar la conversión** (asserts)

Run:
```bash
python3 -c "
from tools.normalizar_notacion import acorde_a_espanol as f
assert f('C') == 'DO', f('C')
assert f('Am') == 'LAm'
assert f('F#m') == 'FA#m'
assert f('Bb') == 'SIb'
assert f('G/B') == 'SOL/SI'
assert f('D/F#') == 'RE/FA#'
assert f('Csus4') == 'DOsus4'
assert f('G7') == 'SOL7'
assert f('DO') == 'DO'        # idempotente
assert f('FA') == 'FA'        # latino que empieza con F no se rompe
assert f('REm') == 'REm'
print('OK acorde')
"
```
Expected: `OK acorde`

- [ ] **Step 3: Commit**
```bash
git add tools/normalizar_notacion.py
git commit -m "Add acorde_a_espanol chord notation converter"
```

---

### Task 2: Detección de líneas de acordes y `convertir_letra`

**Files:**
- Modify: `tools/normalizar_notacion.py`

**Interfaces:**
- Consumes: `acorde_a_espanol`, `LATIN` (Task 1).
- Produces: `es_linea_acordes(linea: str) -> bool`, `convertir_letra(letra: str) -> str`.

- [ ] **Step 1: Agregar detección estricta + `convertir_letra`** después de `acorde_a_espanol`

```python
# detección ESTRICTA (sufijos conocidos) para no confundir letra con acordes
SUF = (r'(?:maj7|maj|min7|min|sus2|sus4|sus|dim7|dim|aug|add9|add|m7|m9|m6|m'
       r'|7M|M7|7|9|6|5|4|2|11|13|°)*')
RAIZ = r'(?:[A-G]|DO|RE|MI|FA|SOL|LA|SI)'
STRICT = re.compile(r'^' + RAIZ + r'(#|b)?' + SUF + r'(?:/' + RAIZ + r'(#|b)?)?$')
MARKER = re.compile(r'^\(.*\)$|^x\d+$', re.I)

def es_linea_acordes(linea):
    toks = [t for t in linea.split() if t and t != '|']
    if not toks:
        return False
    hay = False
    for t in toks:
        if MARKER.match(t):
            continue
        if STRICT.match(t):
            hay = True
        else:
            return False
    return hay

def convertir_letra(letra):
    out = []
    for linea in letra.split('\n'):
        if '[' in linea:
            linea = re.sub(r'\[([^\]]+)\]', lambda m: '[' + acorde_a_espanol(m.group(1)) + ']', linea)
        elif es_linea_acordes(linea):
            linea = ' '.join('|' if t == '|' else acorde_a_espanol(t) for t in linea.split())
        out.append(linea)
    return '\n'.join(out)
```

- [ ] **Step 2: Verificar detección y conversión de letra** (asserts)

Run:
```bash
python3 -c "
from tools.normalizar_notacion import es_linea_acordes as L, convertir_letra as C
assert L('| F#m | C#m B |') is True
assert L('| E | E |') is True
assert L('Aleluya') is False
assert L('Gloria a Dios') is False
assert L('Amen') is False
assert C('[G]Ven, Espíritu [D]Santo') == '[SOL]Ven, Espíritu [RE]Santo'
assert C('| F#m | C#m B |') == '| FA#m | DO#m SI |'
assert C('Aleluya, aleluya.') == 'Aleluya, aleluya.'
assert C('[Am]No has [G/B]buscado') == '[LAm]No has [SOL/SI]buscado'
print('OK letra')
"
```
Expected: `OK letra`

- [ ] **Step 3: Commit**
```bash
git add tools/normalizar_notacion.py
git commit -m "Add strict chord-line detection and lyric converter"
```

---

### Task 3: Aplicar a los 3 JSON y verificar

**Files:**
- Modify: `tools/normalizar_notacion.py`, `canciones.json`, `canciones-athenas.json`, `canciones-recursoscatolicos.json`

**Interfaces:**
- Consumes: `convertir_letra`, `acorde_a_espanol` (Tasks 1-2).

- [ ] **Step 1: Agregar `main()` que reescribe los archivos** al final del script

```python
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ['canciones.json', 'canciones-athenas.json', 'canciones-recursoscatolicos.json']

def main():
    total = 0
    for f in FILES:
        path = os.path.join(ROOT_DIR, f)
        data = json.load(open(path, encoding='utf-8'))
        for s in data:
            if s.get('tono'):
                s['tono'] = acorde_a_espanol(s['tono'])
            for e in s['estrofas']:
                e['letra'] = convertir_letra(e['letra'])
        json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        total += len(data)
    print(f'Convertidos: {total} canciones en {len(FILES)} archivos')

if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Correr el script**

Run: `python3 tools/normalizar_notacion.py`
Expected: `Convertidos: 642 canciones en 3 archivos`

- [ ] **Step 3: Verificar que no queda notación inglesa**

Run:
```bash
python3 -c "
import json, re
ENG = re.compile(r'^[A-G](#|b)?')
LAT = re.compile(r'^(DO|RE|MI|FA|SOL|LA|SI)')
def es_ingles(ac): return bool(ENG.match(ac)) and not bool(LAT.match(ac))
tot_brk = tot_tono = 0
for f in ['canciones.json','canciones-athenas.json','canciones-recursoscatolicos.json']:
    for s in json.load(open(f,encoding='utf-8')):
        if s.get('tono') and es_ingles(s['tono']): tot_tono += 1
        for e in s['estrofas']:
            for m in re.findall(r'\[([^\]]+)\]', e['letra']):
                if es_ingles(m): tot_brk += 1
print('acordes ingleses en corchetes:', tot_brk, '| tonos ingleses:', tot_tono)
"
```
Expected: `acordes ingleses en corchetes: 0 | tonos ingleses: 0`

- [ ] **Step 4: Validar JSON**

Run: `node -e "['canciones.json','canciones-athenas.json','canciones-recursoscatolicos.json'].forEach(f=>require('./'+f)); console.log('JSON OK')"`
Expected: `JSON OK`

- [ ] **Step 5: Verificar en el navegador**

Recargar el preview, abrir una canción de Athenas (autor "Athenas") con acordes y `preview_eval`:
```js
(function(){
  var c = CANCIONES.find(c => c.autor === 'Athenas' && cancionTieneAcordes(c));
  abrirDetalle(c);
  var acordes = Array.from(document.querySelectorAll('.cseg-chord')).map(e=>e.textContent);
  var hayIngles = acordes.some(a => /^[A-G](#|b)?($|[^a-zA-Z])/.test(a) && !/^(DO|RE|MI|FA|SOL|LA|SI)/.test(a));
  var r = { titulo: c.titulo, tono: c.tono, primerosAcordes: acordes.slice(0,6), hayIngles };
  cerrarDetalle();
  return r;
})()
```
Expected: `tono` en latín (ej. "RE"), `primerosAcordes` en DO/RE/MI, `hayIngles:false`. Screenshot del detalle.

- [ ] **Step 6: Commit**
```bash
git add tools/normalizar_notacion.py canciones.json canciones-athenas.json canciones-recursoscatolicos.json
git commit -m "Convert all chord notation to DO/RE/MI (Latin)"
```

---

## Self-Review

- **Cobertura del spec:** mapeo raíz + alteraciones + sufijos + bajo (Task 1 `acorde_a_espanol`) · corchetes (Task 2 `convertir_letra`) · líneas instrumentales sueltas con detección estricta (Task 2 `es_linea_acordes`) · campo tono (Task 3 `main`) · idempotencia (Task 1 LATIN check) · verificación cero-inglés (Task 3 Step 3) · navegador (Task 3 Step 5). ✔
- **Placeholders:** ninguno; código completo.
- **Consistencia:** `acorde_a_espanol` (Task 1) usado por `convertir_letra` (Task 2) y `main` (Task 3); `es_linea_acordes`/`convertir_letra` con firmas estables; `STRICT`/`LATIN`/`ENG` definidos antes de su uso. ✔
