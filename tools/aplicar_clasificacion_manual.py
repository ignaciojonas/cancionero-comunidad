#!/usr/bin/env python3
"""Aplica la clasificación manual (por contenido) de Athenas a canciones-athenas.json.

Lee tools/athenas_clasificacion_manual.json (id -> {categoria, momento}) y setea
esos campos en las canciones correspondientes. Solo toca las que están en el mapeo.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_PATH = os.path.join(ROOT, 'tools', 'athenas_clasificacion_manual.json')
ATH_PATH = os.path.join(ROOT, 'canciones-athenas.json')

def main():
    mapa = {k: v for k, v in json.load(open(MAP_PATH, encoding='utf-8')).items()
            if not k.startswith('_')}
    ath = json.load(open(ATH_PATH, encoding='utf-8'))
    aplicadas = 0
    for s in ath:
        m = mapa.get(str(s['id']))
        if m:
            s['categoria'] = m['categoria']
            s['momento'] = m['momento']
            aplicadas += 1
    json.dump(ath, open(ATH_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    sin = sum(1 for s in ath if not s.get('momento'))
    print(f'Aplicadas: {aplicadas}/{len(mapa)} del mapeo | Athenas sin momento ahora: {sin}/{len(ath)}')

if __name__ == '__main__':
    main()
