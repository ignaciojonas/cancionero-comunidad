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
