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
