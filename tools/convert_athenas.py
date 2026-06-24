#!/usr/bin/env python3
"""Convierte PDFs de acordes (Athenas) a objetos de canción para canciones.json.

Maneja: detección de columnas, alineación de acordes a la sílaba por posición x,
secciones (INTRO/VERSO/PRE CORO/CORO/PUENTE/FINAL), y líneas instrumentales.

Uso:
  python convert_athenas.py FILE.pdf [FILE2.pdf ...]      # imprime JSON (inspección)
  python convert_athenas.py --all DIR --out OUT.json --start-id 10
"""
import sys, os, re, json, glob, unicodedata
import pdfplumber

# ─── Detección de acordes ────────────────────────────────────────────────
CHORD_RE = re.compile(
    r'^[A-G][#b]?'
    r'(?:maj7|maj|min7|min|m7|m9|m6|m|sus2|sus4|sus|dim7|dim|aug|add9|add'
    r'|7|9|6|5|4|2|11|13|°)*'
    r'(?:/[A-G][#b]?)?$'
)
MARKER_RE = re.compile(r'^\((?:x\d+|X\d+|bis|\d+x)\)$', re.I)

def is_chord_token(t):
    return bool(CHORD_RE.match(t))

def is_chord_line(words):
    """words: lista de dicts con 'text'. True si todos los tokens son acordes/barras."""
    if not words:
        return False
    has_chord = False
    for w in words:
        t = w['text']
        if t == '|' or MARKER_RE.match(t):
            continue
        if is_chord_token(t):
            has_chord = True
        else:
            return False
    return has_chord

# ─── Secciones ───────────────────────────────────────────────────────────
# El encabezado debe ser la línea ENTERA (etiqueta corta): "CORO", "VERSO 2",
# "PRE CORO 1". No debe matchear el comienzo de una frase ("Solo puedo...").
SECTION_RE = re.compile(
    r'^(INTRO|INTERLUDIO|VERSO|VERSOS|ESTROFA|PRE\s*-?\s*CORO|PRECORO|CORO|'
    r'ESTRIBILLO|PUENTE|FINAL|CODA|TAG|SOLO)\s*\d*\s*:?\s*$', re.I)

def section_type(line):
    m = SECTION_RE.match(line.strip())
    if not m:
        return None
    key = re.sub(r'\s+', ' ', m.group(1).upper())
    return {
        'INTRO': 'intro', 'INTERLUDIO': 'instrumental', 'SOLO': 'instrumental',
        'VERSO': 'estrofa', 'VERSOS': 'estrofa', 'ESTROFA': 'estrofa',
        'PRE CORO': 'precoro', 'PRE-CORO': 'precoro', 'PRECORO': 'precoro',
        'CORO': 'coro', 'ESTRIBILLO': 'coro',
        'PUENTE': 'puente', 'FINAL': 'final', 'CODA': 'final', 'TAG': 'final',
    }.get(key, 'estrofa')

# ─── Reconstrucción de líneas con posición (geometría real de palabras) ──
def page_columns(page):
    """Devuelve lista de columnas; cada columna es lista de words.
    Detecta 2 columnas buscando un hueco vertical ancho en el centro."""
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    if not words:
        return []
    W = page.width
    occupied = [False] * (int(W) + 2)
    for w in words:
        for x in range(int(w['x0']), int(w['x1']) + 1):
            if 0 <= x < len(occupied):
                occupied[x] = True
    best_gap = (0, None)
    x = int(W * 0.30)
    while x < int(W * 0.70):
        if not occupied[x]:
            start = x
            while x < int(W * 0.70) and not occupied[x]:
                x += 1
            gap = x - start
            if gap > best_gap[0]:
                best_gap = (gap, (start + x) // 2)
        x += 1
    if best_gap[0] >= 35 and best_gap[1] is not None:
        split = best_gap[1]
        left = [w for w in words if w['x0'] < split]
        right = [w for w in words if w['x0'] >= split]
        return [c for c in (left, right) if c]
    return [words]

def group_lines(words):
    """Agrupa words en líneas por 'top' (clusters dentro de ~5pt). Inserta ''
    como línea en blanco solo cuando el salto vertical supera ~1.6x la altura
    de línea típica (separación de párrafo), no entre acorde y su letra."""
    rows = []
    for w in sorted(words, key=lambda w: w['top']):
        if rows and abs(w['top'] - rows[-1]['top0']) <= 5:
            rows[-1]['words'].append(w)
        else:
            rows.append({'top0': w['top'], 'words': [w]})
    tops = [r['top0'] for r in rows]
    deltas = sorted(tops[i + 1] - tops[i] for i in range(len(tops) - 1))
    med = deltas[len(deltas) // 2] if deltas else 0
    lines = []
    for i, r in enumerate(rows):
        if i > 0 and med and (r['top0'] - rows[i - 1]['top0']) > med * 1.6:
            lines.append('')
        lines.append(sorted(r['words'], key=lambda w: w['x0']))
    return lines

def line_text(words):
    return ' '.join(w['text'] for w in words)

# ─── Merge acorde+letra → ChordPro (alineación por posición x) ────────────
def merge_chord_lyric(chord_words, lyric_words):
    # construir string de letra con espacios simples y, en paralelo, una lista
    # de "límites de carácter" (x, índice) para ubicar cada acorde por posición.
    parts = []
    boundaries = []  # (x, char_index)
    idx = 0
    for i, w in enumerate(lyric_words):
        if i > 0:
            parts.append(' ')
            idx += 1
        L = max(1, len(w['text']))
        span = w['x1'] - w['x0']
        for p in range(L + 1):
            boundaries.append((w['x0'] + (p / L) * span, idx + p))
        parts.append(w['text'])
        idx += len(w['text'])
    full = ''.join(parts)

    # ancho de carácter típico de la letra (para sesgo de alineación)
    cws = [(w['x1'] - w['x0']) / max(1, len(w['text'])) for w in lyric_words]
    cws.sort()
    cw = cws[len(cws) // 2] if cws else 6.0
    bias = 0.6 * cw  # los acordes se tipean ~medio carácter a la derecha

    def find_index(xc):
        if not boundaries:
            return len(full)
        best = min(boundaries, key=lambda b: abs(b[0] - xc))
        return best[1]

    inserts = []
    for w in chord_words:
        t = w['text']
        if t == '|' or MARKER_RE.match(t) or not is_chord_token(t):
            continue
        inserts.append((find_index(w['x0'] - bias), t))
    chars = list(full)
    for pos, tok in sorted(inserts, key=lambda p: p[0], reverse=True):
        chars.insert(min(pos, len(chars)), f'[{tok}]')
    return ''.join(chars)

def chordline_to_inline(chord_words):
    """Línea instrumental: barras y acordes con espacio simple."""
    return ' '.join(w['text'] for w in chord_words)

# ─── Procesar un PDF ─────────────────────────────────────────────────────
def parse_pdf(path):
    all_lines = []  # cada elemento: '' (blanco) o lista de words
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for col_words in page_columns(page):
                all_lines.extend(group_lines(col_words))
                all_lines.append('')  # separador entre columnas

    def is_blank(ln):
        return ln == '' or (isinstance(ln, list) and not ln)

    def header_of(ln):
        return None if is_blank(ln) else section_type(line_text(ln))

    # quitar primera línea no vacía (título en la hoja)
    started = False
    cleaned = []
    for ln in all_lines:
        if not started and not is_blank(ln):
            started = True
            continue  # drop title line
        cleaned.append(ln)

    blocks = []
    cur_type = 'estrofa'
    cur = []

    def flush():
        nonlocal cur
        text = '\n'.join(cur).strip('\n')
        if text.strip():
            blocks.append({'tipo': cur_type, 'letra': text})
        cur = []

    i = 0
    n = len(cleaned)
    while i < n:
        line = cleaned[i]
        if is_blank(line):
            if cur:
                cur.append('')
            i += 1
            continue
        st = section_type(line_text(line))
        if st is not None:
            flush()
            cur_type = st
            i += 1
            continue
        if is_chord_line(line):
            nxt = cleaned[i + 1] if i + 1 < n else ''
            if not is_blank(nxt) and not is_chord_line(nxt) and header_of(nxt) is None:
                cur.append(merge_chord_lyric(line, nxt))
                i += 2
                continue
            else:
                cur.append(chordline_to_inline(line))
                i += 1
                continue
        cur.append(line_text(line))
        i += 1
    flush()

    for b in blocks:
        b['letra'] = re.sub(r'\n{2,}', '\n', b['letra']).strip('\n')
    return blocks

# ─── Metadatos desde el nombre de archivo ────────────────────────────────
KEY_RE = re.compile(r'\(([A-G][#b]?m?)\)')

def title_and_tono(filename):
    stem = os.path.splitext(os.path.basename(filename))[0]
    tono = None
    m = KEY_RE.search(stem)
    if m:
        tono = m.group(1)
    title = KEY_RE.sub('', stem)
    title = re.sub(r'\bacordes\b', '', title, flags=re.I)
    title = re.sub(r'^\s*\d+\s*[.\-]\s*', '', title)  # "6. " / "8. "
    title = re.sub(r'\s{2,}', ' ', title).strip(' -·.')
    return title, tono

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn').lower()

CATEGORIES = [
    ('Marianas', ['maria', 'reina', 'madre', 'esclava', 'pieta', 'fuiste llevada',
                  'he aqui', 'contigo', 'dulce madre', 'coronada', 'esa cruz, maria']),
    ('Espíritu Santo', ['espiritu', 'inundame', 'fuego nuevo', 'brisa', 'desciende',
                        'el mismo espiritu']),
    ('Pascua', ['resucito', 'tumba esta vacia', 'cristo reina', 'vida en ti']),
    ('Navidad', ['nino dios', 'emmanuel', 'navidad', 'sagrada familia']),
    ('Cuaresma', ['cruz', 'espinas', 'al morir', 'glorioso rey', 'contemplarte',
                  'me amo y se entrego', 'para salvarnos']),
    ('Adoración', ['santo', 'gloria', 'digno', 'alabar', 'adoramos', 'alfa y omega',
                   'eternamente dios', 'adonai', 'cristo']),
    ('Comunión', ['es el senor', 'cuando estas en el altar', 'pan']),
    ('Misericordia', ['misericordia', 'fuente de vida', 'consuelo']),
    ('Confianza', ['nada puede separarte', 'me basta tu gracia', 'aumenta mi fe',
                   'creo', 'cada dia', 'mirad las aves', 'si tu lo quieres',
                   'cuando miro atras', 'todo es tuyo', 'todo lo haces nuevo']),
]

def classify(title):
    t = strip_accents(title)
    for cat, kws in CATEGORIES:
        for kw in kws:
            if kw in t:
                return cat
    return 'Adoración'

def song_from_pdf(path, song_id):
    title, tono = title_and_tono(path)
    estrofas = parse_pdf(path)
    song = {
        'id': song_id,
        'titulo': title,
        'autor': 'Athenas',
        'categoria': classify(title),
        'momento': [],
    }
    if tono:
        song['tono'] = tono
    song['estrofas'] = estrofas
    # acentos compuestos (NFC) en todo el contenido textual
    song['titulo'] = unicodedata.normalize('NFC', song['titulo'])
    for b in song['estrofas']:
        b['letra'] = unicodedata.normalize('NFC', b['letra'])
    return song

# ─── CLI ─────────────────────────────────────────────────────────────────
def main():
    args = sys.argv[1:]
    if args and args[0] == '--all':
        d = args[1]
        out = args[args.index('--out') + 1]
        start = int(args[args.index('--start-id') + 1])
        # ya curadas en canciones.json → no reimportar (NFC: macOS usa NFD en nombres)
        SKIP = {unicodedata.normalize('NFC', 'Ven, Espíritu Santo (D)')}
        def stem_nfc(f):
            return unicodedata.normalize('NFC', os.path.splitext(os.path.basename(f))[0])
        files = [f for f in sorted(glob.glob(os.path.join(d, '*.pdf')))
                 if stem_nfc(f) not in SKIP]
        songs = []
        warnings = []
        for i, f in enumerate(files):
            try:
                s = song_from_pdf(f, start + i)
                if not s['estrofas']:
                    warnings.append(f'SIN ESTROFAS: {os.path.basename(f)}')
                if 'tono' not in s:
                    warnings.append(f'SIN TONO: {os.path.basename(f)}')
                songs.append(s)
            except Exception as e:
                warnings.append(f'ERROR {os.path.basename(f)}: {e}')
        with open(out, 'w', encoding='utf-8') as fh:
            json.dump(songs, fh, ensure_ascii=False, indent=2)
        print(f'Procesados: {len(songs)} / {len(files)} archivos')
        print(f'Bloques totales: {sum(len(s["estrofas"]) for s in songs)}')
        print('Categorías:', json.dumps({c: sum(1 for s in songs if s["categoria"]==c)
              for c in sorted(set(s["categoria"] for s in songs))}, ensure_ascii=False))
        if warnings:
            print('\n'.join(['WARN ' + w for w in warnings]))
    else:
        songs = [song_from_pdf(f, 100 + i) for i, f in enumerate(args)]
        print(json.dumps(songs, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
