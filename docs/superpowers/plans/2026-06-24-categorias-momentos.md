# Categorías y momentos — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-clasificar `categoria` y `momento` de las 631 canciones importadas usando los tags reales de recursoscatolicos.com.ar, sin tocar las 11 curadas.

**Architecture:** Un script Python `tools/clasificar_tags.py` baja los tags del sitio (22 requests), arma `q-id → [tags]`, y reescribe `canciones-recursoscatolicos.json` y `canciones-athenas.json` aplicando un mapeo puro tags→categoría/momento. `canciones.json` no se toca.

**Tech Stack:** Python 3 (urllib, stdlib). Verificación: asserts de Python para el mapeo puro + chequeo de distribución; navegador (Claude_Preview) para confirmar que la app sigue funcionando.

## Global Constraints

- No tocar `canciones.json` (curadas).
- Requests gentiles al sitio: delay ≥ 0.8s (rate-limit conocido).
- `momento` ordenado en secuencia litúrgica.
- Canciones sin tags del sitio: se dejan como están (categoría keyword existente, `momento` sin cambios).

---

### Task 1: Funciones puras de mapeo

**Files:**
- Create: `tools/clasificar_tags.py`

**Interfaces:**
- Produces:
  - `momentos_de_tags(tags: iterable[str]) -> list[str]` — momentos en orden litúrgico.
  - `categoria_de_tags(tags: iterable[str]) -> str` — categoría por prioridad, o `'General'`.

- [ ] **Step 1: Crear el script con las constantes y funciones de mapeo**

```python
#!/usr/bin/env python3
"""Re-clasifica categoria/momento de las canciones importadas usando los tags
reales de recursoscatolicos.com.ar. No toca canciones.json (curadas)."""
import sys, re, json, time, ssl, unicodedata
import urllib.request

# id de tag del sitio -> nombre
TAGS = {7:'Adviento',8:'Navidad',9:'Cuaresma',10:'Pascua',11:'Pentecostés',
        12:'Entrada',13:'Ofertorio',14:'Comunión',15:'Meditación',16:'Salida',
        17:'Gloria',18:'Salmo',19:'Aleluya',20:'Santo',21:'Cordero',25:'Adoración',
        33:'Animación/RCC',26:'Espíritu Santo',27:'María',28:'Niños',
        41:'Pascua Joven',24:'Varias'}

# tag del sitio -> momento del cancionero
MOMENTO_MAP = {'Entrada':'Entrada','Gloria':'Gloria','Salmo':'Salmo Responsorial',
               'Aleluya':'Aclamación al Evangelio','Ofertorio':'Ofertorio',
               'Santo':'Santo','Cordero':'Cordero','Comunión':'Comunión',
               'Meditación':'Meditación','Salida':'Envío'}
MOMENTO_ORDER = ['Entrada','Gloria','Salmo Responsorial','Aclamación al Evangelio',
                 'Ofertorio','Santo','Cordero','Comunión','Meditación','Envío']

# prioridad de categoría: (tags del sitio, categoría)
CAT_PRIORITY = [
    ({'María'}, 'Marianas'),
    ({'Adviento'}, 'Adviento'),
    ({'Navidad'}, 'Navidad'),
    ({'Cuaresma'}, 'Cuaresma'),
    ({'Pascua', 'Pascua Joven'}, 'Pascua'),
    ({'Pentecostés', 'Espíritu Santo'}, 'Espíritu Santo'),
    ({'Niños'}, 'Niños'),
    ({'Adoración', 'Animación/RCC'}, 'Adoración'),
]

def momentos_de_tags(tags):
    s = set(tags)
    moms = {MOMENTO_MAP[t] for t in s if t in MOMENTO_MAP}
    return [m for m in MOMENTO_ORDER if m in moms]

def categoria_de_tags(tags):
    s = set(tags)
    for tagset, cat in CAT_PRIORITY:
        if s & tagset:
            return cat
    return 'General'
```

- [ ] **Step 2: Verificar las funciones puras** (test con asserts)

Run:
```bash
python3 -c "
from tools.clasificar_tags import momentos_de_tags, categoria_de_tags
assert categoria_de_tags(['Comunión','Meditación']) == 'General'
assert categoria_de_tags(['María','Comunión']) == 'Marianas'
assert categoria_de_tags(['Pascua Joven']) == 'Pascua'
assert categoria_de_tags(['Animación/RCC']) == 'Adoración'
assert momentos_de_tags(['Comunión','Entrada']) == ['Entrada','Comunión']
assert momentos_de_tags(['Salmo','Aleluya']) == ['Salmo Responsorial','Aclamación al Evangelio']
assert momentos_de_tags(['Varias']) == []
print('OK mapeo')
"
```
Expected: `OK mapeo`

- [ ] **Step 3: Commit**

```bash
git add tools/clasificar_tags.py
git commit -m "Add pure tag->category/momento mapping functions"
```

---

### Task 2: Scraping de tags + aplicación a los JSON

**Files:**
- Modify: `tools/clasificar_tags.py`

**Interfaces:**
- Consumes: `momentos_de_tags`, `categoria_de_tags` (Task 1).
- Produces: función `main()` que reescribe los dos JSON.

- [ ] **Step 1: Agregar scraping, matching y reescritura** al final del script

```python
SSL = ssl.create_default_context(); SSL.check_hostname = False; SSL.verify_mode = ssl.CERT_NONE
BASE = 'https://recursoscatolicos.com.ar/cancionero/'

def fetch(url, retries=4):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    last = None
    for i in range(retries):
        try:
            return urllib.request.urlopen(req, context=SSL, timeout=30).read().decode('utf-8', 'replace')
        except Exception as e:
            last = e; time.sleep(1.5 * (i + 1))
    raise last

def norm(s):
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9 ]', '', s.lower()).strip()

def scrape_tags(delay=0.8):
    """q-id (str) -> set de nombres de tag del sitio."""
    qid_tags = {}
    for tid, name in TAGS.items():
        html = fetch(f'{BASE}buscar_ajax.php?s=&tags={tid}')
        for qid in dict.fromkeys(re.findall(r'\?q=(\d+)', html)):
            qid_tags.setdefault(qid, set()).add(name)
        time.sleep(delay)
    return qid_tags

def title_to_qid():
    """título normalizado -> q-id, desde el índice (para Athenas)."""
    html = fetch(f'{BASE}index.php')
    out = {}
    for qid, raw in re.findall(r'<a[^>]*href=[\'"]\?q=(\d+)[\'"][^>]*>(.*?)</a>', html, re.S):
        t = re.sub(r'<[^>]+>', '', raw).replace('­', '')
        t = re.sub(r'\s*→\s*$', '', t).strip()
        t = re.sub(r'^[A-ZÁÉÍÓÚÑ]\s+', '', t)
        if ' - ' in t:
            t = t.split(' - ')[0]
        out.setdefault(norm(t), qid)
    return out

def qid_de_fuente(song):
    m = re.search(r'q=(\d+)', song.get('fuente', ''))
    return m.group(1) if m else None

def aplicar(song, tags):
    song['categoria'] = categoria_de_tags(tags)
    song['momento'] = momentos_de_tags(tags)

def main():
    qid_tags = scrape_tags()
    t2q = title_to_qid()

    rc = json.load(open('canciones-recursoscatolicos.json', encoding='utf-8'))
    rc_hit = 0
    for s in rc:
        q = qid_de_fuente(s)
        if q in qid_tags:
            aplicar(s, qid_tags[q]); rc_hit += 1
    json.dump(rc, open('canciones-recursoscatolicos.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)

    ath = json.load(open('canciones-athenas.json', encoding='utf-8'))
    ath_hit = 0
    for s in ath:
        q = t2q.get(norm(s['titulo']))
        if q in qid_tags:
            aplicar(s, qid_tags[q]); ath_hit += 1
    json.dump(ath, open('canciones-athenas.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)

    print(f'Recursos: {rc_hit}/{len(rc)} re-clasificadas | Athenas: {ath_hit}/{len(ath)}')
    todas = rc + ath
    cats, moms, sinmom = {}, {}, 0
    for s in todas:
        cats[s['categoria']] = cats.get(s['categoria'], 0) + 1
        if not s['momento']:
            sinmom += 1
        for m in s['momento']:
            moms[m] = moms.get(m, 0) + 1
    print('sin momento:', sinmom, '/', len(todas))
    print('CATEGORÍAS:', json.dumps(dict(sorted(cats.items(), key=lambda x: -x[1])), ensure_ascii=False))
    print('MOMENTOS:', json.dumps(dict(sorted(moms.items(), key=lambda x: -x[1])), ensure_ascii=False))

if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Commit**

```bash
git add tools/clasificar_tags.py
git commit -m "Add tag scraping and JSON re-classification logic"
```

---

### Task 3: Correr el clasificador y verificar

**Files:**
- Modify: `canciones-recursoscatolicos.json`, `canciones-athenas.json` (generados por el script)

**Interfaces:**
- Consumes: `main()` (Task 2).

- [ ] **Step 1: Guardar el estado previo de `canciones.json`** (para probar que no se toca)

Run:
```bash
md5 -q canciones.json > /tmp/canciones_md5_antes.txt; cat /tmp/canciones_md5_antes.txt
```
Expected: un hash (se compara después).

- [ ] **Step 2: Correr el clasificador**

Run: `python3 tools/clasificar_tags.py`
Expected: imprime `Recursos: ~531/559 ...`, `Athenas: ~15/72`, `sin momento: ~85/631`, y los conteos de CATEGORÍAS (General mucho menor que 423) y MOMENTOS (varios cientos repartidos).

- [ ] **Step 3: Validar JSON y que `canciones.json` no cambió**

Run:
```bash
node -e "require('./canciones-recursoscatolicos.json'); require('./canciones-athenas.json'); console.log('JSON OK')"
test "$(md5 -q canciones.json)" = "$(cat /tmp/canciones_md5_antes.txt)" && echo "canciones.json INTACTO" || echo "CAMBIÓ (mal)"
```
Expected: `JSON OK` y `canciones.json INTACTO`.

- [ ] **Step 4: Verificar en el navegador** (la app usa los campos sin cambios de código)

Recargar el preview y `preview_eval`:
```js
(function(){
  var cats = {}, sinMom = 0;
  CANCIONES.forEach(c => { cats[c.categoria]=(cats[c.categoria]||0)+1; if(!(c.momento||[]).length) sinMom++; });
  return { total: CANCIONES.length, sinMomento: sinMom, generales: cats['General'], categorias: Object.keys(cats).length };
})()
```
Expected: `total:642`, `sinMomento` mucho menor que 633 (~85+11 curadas con momento ya puesto), `generales` mucho menor que 423.

Abrir una canción de Comunión y screenshot: debe mostrar la etiqueta de momento "Comunión".

- [ ] **Step 5: Commit**

```bash
git add canciones-recursoscatolicos.json canciones-athenas.json
git commit -m "Re-classify imported songs' categories and momentos from site tags"
```

---

## Self-Review

- **Cobertura del spec:** fuente de datos / scrape de 22 tags (Task 2 `scrape_tags`) · mapeo momento (Task 1 `momentos_de_tags` + MOMENTO_MAP/ORDER) · mapeo categoría por prioridad + General (Task 1 `categoria_de_tags` + CAT_PRIORITY) · recursos por q-id (Task 2 `qid_de_fuente`) · athenas por título (Task 2 `title_to_qid`/`norm`) · fallback deja sin tocar (no se llama `aplicar`) · no tocar `canciones.json` (Task 3 Step 3 verifica md5) · delay ≥0.8s (Task 2 `scrape_tags`). ✔
- **Placeholders:** ninguno; código completo.
- **Consistencia de tipos:** `momentos_de_tags`/`categoria_de_tags` definidas en Task 1 y usadas en `aplicar` (Task 2). `qid_tags` es dict str→set; `qid_de_fuente`/`t2q.get` devuelven str|None y se chequean con `in qid_tags`. ✔
