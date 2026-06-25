#!/usr/bin/env python3
"""Verifica que los links YouTube/Spotify de las canciones coincidan con el título.

Usa oEmbed (sin API key) para obtener el título real del video/track y lo
compara con el título de la canción. Reporta mismatches.

Uso:
  python3 tools/verificar_links.py                  # verifica todo
  python3 tools/verificar_links.py --json           # output JSON para reprocesar
  python3 tools/verificar_links.py --fix-nulls      # borra links que dieron 404
"""
import sys, os, re, json, time, ssl, unicodedata
import urllib.request, urllib.error

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = '/tmp/verify_links_cache.json'

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

YT_OEMBED  = 'https://www.youtube.com/oembed?format=json&url={}'
SP_OEMBED  = 'https://open.spotify.com/oembed?url={}'


def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            data = urllib.request.urlopen(req, context=SSL_CTX, timeout=10).read()
            return json.loads(data)
        except urllib.error.HTTPError as e:
            if e.code in (400, 404, 403):
                return None  # video/track not found or private
            if attempt == retries - 1:
                return None
            time.sleep(1.5)
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(1.5)
    return None


def normalizar(s):
    s = s.lower()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def similitud(a, b):
    """Porcentaje de palabras de 'a' presentes en 'b' (simple word overlap)."""
    wa = set(normalizar(a).split())
    wb = set(normalizar(b).split())
    if not wa:
        return 0
    return len(wa & wb) / len(wa)


def load_cache():
    if os.path.exists(CACHE_FILE):
        return json.load(open(CACHE_FILE, encoding='utf-8'))
    return {}


def save_cache(cache):
    json.dump(cache, open(CACHE_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)


def verificar_link(song_titulo, link_url, kind, cache):
    cache_key = kind + '|' + link_url
    if cache_key in cache:
        return cache[cache_key]

    if kind == 'youtube':
        data = fetch_json(YT_OEMBED.format(urllib.request.quote(link_url, safe=':/?=&')))
    else:
        data = fetch_json(SP_OEMBED.format(urllib.request.quote(link_url, safe=':/?=&')))

    if data is None:
        result = {'titulo_link': None, 'similitud': 0, 'status': 'ERROR'}
    else:
        titulo_link = data.get('title', '')
        # Spotify oembed a veces agrega " - Single" o artista al final
        titulo_link_limpio = re.sub(r'\s*[-–]\s*(Single|EP|Album).*$', '', titulo_link, flags=re.I).strip()
        sim = max(similitud(song_titulo, titulo_link), similitud(song_titulo, titulo_link_limpio))
        result = {
            'titulo_link': titulo_link,
            'similitud': round(sim, 2),
            'status': 'OK' if sim >= 0.5 else 'MISMATCH',
        }

    cache[cache_key] = result
    return result


def main():
    do_json    = '--json' in sys.argv
    fix_nulls  = '--fix-nulls' in sys.argv
    umbral     = 0.4  # mismatch si similitud < umbral

    files = [
        ('canciones-recursoscatolicos.json', 'rc'),
        ('canciones-athenas.json', 'athenas'),
        ('canciones.json', 'curadas'),
    ]

    cache = load_cache()

    mismatches = []
    errores    = []
    ok_count   = 0
    total      = 0
    modified   = {f: False for f, _ in files}

    for fname, kind in files:
        path = os.path.join(ROOT_DIR, fname)
        data = json.load(open(path, encoding='utf-8'))
        changed = False

        songs_with_links = [(i, s) for i, s in enumerate(data) if s.get('youtube') or s.get('spotify')]
        print(f'\n{fname}: {len(songs_with_links)} canciones con links', flush=True)

        for idx, (i, song) in enumerate(songs_with_links):
            titulo = song['titulo']

            for lkind in ('youtube', 'spotify'):
                url = song.get(lkind)
                if not url:
                    continue

                total += 1
                result = verificar_link(titulo, url, lkind, cache)

                if idx % 20 == 0 or result['status'] != 'OK':
                    print(f"  [{idx+1}/{len(songs_with_links)}] {titulo[:40]:<40} {lkind:8} {result['status']} {result['similitud']:.0%}  {result['titulo_link'] or 'ERROR'}", flush=True)

                if result['status'] == 'ERROR':
                    errores.append({'fuente': fname, 'id': song['id'], 'titulo': titulo, 'tipo': lkind, 'url': url})
                    if fix_nulls:
                        del data[i][lkind]
                        changed = True
                elif result['similitud'] < umbral:
                    mismatches.append({
                        'fuente': fname, 'id': song['id'], 'titulo': titulo,
                        'tipo': lkind, 'url': url,
                        'titulo_link': result['titulo_link'],
                        'similitud': result['similitud'],
                    })

                else:
                    ok_count += 1

            # Save cache every 30 songs
            if (idx + 1) % 30 == 0:
                save_cache(cache)

            time.sleep(0.3)

        if changed and not do_json:
            json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
            print(f'  → {fname} actualizado (links eliminados por error 404)')

    save_cache(cache)

    print(f'\n=== RESUMEN ===')
    print(f'Total links verificados : {total}')
    print(f'OK (similitud >= {umbral:.0%})  : {ok_count}')
    print(f'MISMATCH                : {len(mismatches)}')
    print(f'ERROR (404/privado)     : {len(errores)}')

    if mismatches:
        print(f'\n=== MISMATCHES ({len(mismatches)}) ===')
        for m in sorted(mismatches, key=lambda x: x['similitud']):
            print(f"  [{m['fuente']}] id={m['id']} | cancion: {m['titulo']}")
            print(f"    {m['tipo']:8} → {m['titulo_link']}")
            print(f"    similitud: {m['similitud']:.0%}  url: {m['url']}")

    if errores:
        print(f'\n=== ERRORES 404/privado ({len(errores)}) ===')
        for e in errores:
            print(f"  [{e['fuente']}] id={e['id']} {e['titulo']} | {e['tipo']}: {e['url']}")

    if do_json:
        out = {'mismatches': mismatches, 'errores': errores}
        print('\n=== JSON OUTPUT ===')
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
