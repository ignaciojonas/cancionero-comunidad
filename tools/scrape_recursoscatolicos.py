#!/usr/bin/env python3
"""Scrapea canciones de recursoscatolicos.com.ar/cancionero a JSON del cancionero.

El sitio sirve cada canción en index.php?q=<id>, con la letra y acordes en un
<pre> monoespaciado (acordes en notación latina sobre la letra). Como es texto
monoespaciado, la alineación de acordes es exacta por columna.

Uso:
  python scrape_recursoscatolicos.py 3 124 512        # imprime JSON (inspección)
  python scrape_recursoscatolicos.py --all --out OUT.json --start-id 200 \
         [--limit N] [--delay 0.4] [--exclude-titles canciones.json,canciones-athenas.json]
"""
import sys, os, re, json, time, ssl, html as HTML, unicodedata
import urllib.request

BASE = 'https://recursoscatolicos.com.ar/cancionero/index.php?q='
SSL = ssl.create_default_context(); SSL.check_hostname = False; SSL.verify_mode = ssl.CERT_NONE

# ─── Acordes (notación latina + inglesa por las dudas) ───────────────────
ROOT = r'(?:DO|RE|MI|FA|SOL|LA|SI|[A-G])'
CHORD_RE = re.compile(
    r'^' + ROOT + r'(?:#|b)?'
    r'(?:m|maj7|maj|sus2|sus4|sus|dim7|dim|aug|add9|add|7M|M7|7|9|6|5|4|2|11|13|M)*'
    r'(?:/' + ROOT + r'(?:#|b)?)?$'
)
MARKER_RE = re.compile(r'^\((?:x?\d+x?|bis)\)$', re.I)

def is_chord_token(t):
    return bool(CHORD_RE.match(t))

def is_chord_line(line):
    toks = line.split()
    if not toks:
        return False
    has = False
    for t in toks:
        if t == '|' or MARKER_RE.match(t):
            continue
        if is_chord_token(t):
            has = True
        else:
            return False
    return has

# ─── Merge acorde+letra por columna (monoespaciado) ──────────────────────
def merge(chord_line, lyric_line):
    inserts = []
    for m in re.finditer(r'\S+', chord_line):
        tok = m.group()
        if tok == '|' or MARKER_RE.match(tok) or not is_chord_token(tok):
            continue
        inserts.append((m.start(), tok))
    s = list(lyric_line)
    for pos, tok in sorted(inserts, reverse=True):
        s.insert(min(pos, len(s)), f'[{tok}]')
    return re.sub(r'[ \t]{2,}', ' ', ''.join(s)).rstrip()

def parse_pre(pre_text):
    lines = [ln.rstrip() for ln in pre_text.split('\n')]
    # recortar líneas en blanco al inicio/fin
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    blocks = []
    cur = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            if cur:
                blocks.append('\n'.join(cur).strip('\n'))
                cur = []
            i += 1
            continue
        if is_chord_line(line):
            nxt = lines[i + 1] if i + 1 < n else ''
            if nxt.strip() and not is_chord_line(nxt):
                cur.append(merge(line, nxt))
                i += 2
                continue
            else:
                cur.append(line.strip())   # acordes instrumentales sueltos
                i += 1
                continue
        cur.append(line)
        i += 1
    if cur:
        blocks.append('\n'.join(cur).strip('\n'))
    return [{'tipo': 'estrofa', 'letra': b} for b in blocks if b.strip()]

def first_chord(estrofas):
    for e in estrofas:
        m = re.search(r'\[([^\]]+)\]', e['letra'])
        if m:
            return m.group(1)
    return None

# ─── Categorías por palabra clave ────────────────────────────────────────
def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn').lower()

CATEGORIES = [
    ('Marianas', ['maria', 'virgen', 'reina', 'madre', 'guadalupe', 'lujan', 'rosario',
                  'ave ', 'inmaculada', 'dolorosa', 'fatima']),
    ('Espíritu Santo', ['espiritu santo', 'ven espiritu', 'pentecost', 'fuego del']),
    ('Adviento', ['adviento', 'ven senor', 'maranatha']),
    ('Navidad', ['navidad', 'belen', 'nino dios', 'noche de paz', 'emmanuel', 'pesebre',
                 'gloria a dios en las alturas']),
    ('Cuaresma', ['cuaresma', 'cruz', 'calvario', 'perdon', 'pecado', 'conviertete',
                  'ceniza', 'pasion']),
    ('Pascua', ['resucito', 'pascua', 'aleluya', 'cristo vive', 'tumba']),
    ('Comunión', ['comunion', 'pan de vida', 'eucarist', 'cuerpo y sangre', 'cordero de dios',
                  'sagrada', 'altar']),
    ('Adoración', ['santo', 'gloria', 'aleluya', 'aclam', 'alab', 'adorar', 'digno',
                   'honor y gloria', 'rey']),
    ('Entrada', ['vengan', 'reunidos', 'entremos', 'juntos como hermanos']),
    ('Envío', ['envia', 'misionero', 'id y ensenad', 'vayan']),
]

def classify(title):
    t = strip_accents(title)
    for cat, kws in CATEGORIES:
        for kw in kws:
            if kw in t:
                return cat
    return 'General'

# ─── Fetch + parse de una canción ────────────────────────────────────────
TITLE_RE = re.compile(r'class="text-3xl md:text-4xl font-bold text-gray-800 mb-2"[^>]*>(.*?)</', re.S)
AUTHOR_RE = re.compile(r'class="text-xl md:text-2xl font-bold text-gray-500"[^>]*>(.*?)</', re.S)
PRE_RE = re.compile(r'<pre[^>]*>(.*?)</pre>', re.S)

def clean(s):
    s = HTML.unescape(s)
    s = s.replace('­', '')  # soft hyphen
    return re.sub(r'\s+', ' ', s).strip()

def fetch(qid, retries=4):
    req = urllib.request.Request(BASE + str(qid), headers={'User-Agent': 'Mozilla/5.0'})
    last = None
    for attempt in range(retries):
        try:
            return urllib.request.urlopen(req, context=SSL, timeout=30).read().decode('utf-8', 'replace')
        except Exception as e:
            last = e
            time.sleep(1.5 * (attempt + 1))  # backoff
    raise last

def parse_song(html, qid, song_id):
    mt = TITLE_RE.search(html)
    titulo = clean(mt.group(1)) if mt else f'Canción {qid}'
    ma = AUTHOR_RE.search(html)
    autor = clean(ma.group(1)) if ma else ''
    # autor a veces va en el título tras " - "
    if not autor and ' - ' in titulo:
        partes = titulo.split(' - ')
        titulo, autor = partes[0].strip(), ' - '.join(partes[1:]).strip()
    pres = PRE_RE.findall(html)
    pre = ''
    for p in pres:
        txt = HTML.unescape(p).replace('­', '')  # quitar guiones suaves invisibles
        if '${' in txt:           # template JS, ignorar
            continue
        pre = txt
        break
    estrofas = parse_pre(pre)
    song = {
        'id': song_id,
        'titulo': titulo,
        'autor': autor or 'Tradicional',
        'categoria': classify(titulo),
        'momento': [],
        'fuente': BASE + str(qid),
    }
    tono = first_chord(estrofas)
    if tono:
        song['tono'] = tono
    song['estrofas'] = estrofas
    for b in song['estrofas']:
        b['letra'] = unicodedata.normalize('NFC', b['letra'])
    song['titulo'] = unicodedata.normalize('NFC', song['titulo'])
    return song

# ─── CLI ─────────────────────────────────────────────────────────────────
def existing_titles(files):
    titles = set()
    for f in files:
        if os.path.exists(f):
            for s in json.load(open(f, encoding='utf-8')):
                titles.add(strip_accents(s['titulo']).strip())
    return titles

def main():
    args = sys.argv[1:]
    if args and args[0] == '--retry':
        # reintenta ids de un archivo y APPENDEA al --out existente
        out = args[args.index('--out') + 1]
        ids_file = args[args.index('--ids-file') + 1]
        delay = float(args[args.index('--delay') + 1]) if '--delay' in args else 1.0
        excl = args[args.index('--exclude-titles') + 1].split(',') if '--exclude-titles' in args else []
        existentes = json.load(open(out, encoding='utf-8'))
        ya = existing_titles(excl)
        for s in existentes:
            ya.add(strip_accents(s['titulo']).strip())
        sid = max((s['id'] for s in existentes), default=199) + 1
        ids = [l.strip() for l in open(ids_file) if l.strip()]
        nuevas, warnings = [], []
        for n, qid in enumerate(ids):
            try:
                song = parse_song(fetch(qid), qid, sid)
                key = strip_accents(song['titulo']).strip()
                if key in ya or not song['estrofas']:
                    continue
                ya.add(key); nuevas.append(song); sid += 1
            except Exception as e:
                warnings.append(f'ERROR q={qid}: {e}')
            time.sleep(delay)
            if (n + 1) % 25 == 0:
                print(f'... {n + 1}/{len(ids)} reintentadas, {len(nuevas)} nuevas', flush=True)
        todas = existentes + nuevas
        json.dump(todas, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'OK retry: +{len(nuevas)} nuevas | total {len(todas)} | {len(warnings)} fallaron')
        for w in warnings:
            print('WARN', w)
        return
    if args and args[0] == '--all':
        out = args[args.index('--out') + 1]
        start = int(args[args.index('--start-id') + 1])
        limit = int(args[args.index('--limit') + 1]) if '--limit' in args else None
        delay = float(args[args.index('--delay') + 1]) if '--delay' in args else 0.4
        excl = args[args.index('--exclude-titles') + 1].split(',') if '--exclude-titles' in args else []
        ya = existing_titles(excl)

        ids = [qid for qid, _ in json.load(open('/tmp/rc_list.json', encoding='utf-8'))]
        if limit:
            ids = ids[:limit]
        songs, warnings, skipped = [], [], 0
        sid = start
        for n, qid in enumerate(ids):
            try:
                song = parse_song(fetch(qid), qid, sid)
                key = strip_accents(song['titulo']).strip()
                if key in ya:
                    skipped += 1
                    continue
                if not song['estrofas']:
                    warnings.append(f'SIN LETRA q={qid} {song["titulo"]}')
                    continue
                ya.add(key)
                songs.append(song)
                sid += 1
            except Exception as e:
                warnings.append(f'ERROR q={qid}: {e}')
            time.sleep(delay)
            if (n + 1) % 50 == 0:
                print(f'... {n + 1}/{len(ids)} procesadas, {len(songs)} guardadas', flush=True)
        json.dump(songs, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'OK: {len(songs)} canciones | {skipped} duplicadas salteadas | {len(warnings)} warnings')
        cats = {}
        for s in songs:
            cats[s['categoria']] = cats.get(s['categoria'], 0) + 1
        print('Categorías:', json.dumps(cats, ensure_ascii=False))
        for w in warnings[:25]:
            print('WARN', w)
    else:
        songs = [parse_song(fetch(q), q, 200 + i) for i, q in enumerate(args)]
        print(json.dumps(songs, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
