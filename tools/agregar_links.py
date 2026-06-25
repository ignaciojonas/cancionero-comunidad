#!/usr/bin/env python3
"""Agrega campos youtube/spotify a los tres JSON de canciones.

Fuentes:
  1. recursoscatolicos.com.ar: scrapea embedMedia('youtube'/'spotify', URL)
     por cada canción RC. Cachea en /tmp/rc_links.json para reanudar.
  2. Canal YouTube "Canciones y Cantos MPD": matcheo por título contra
     canciones Athenas y curadas (best-effort, ~30 videos).

Uso:
  python3 tools/agregar_links.py            # scrape + aplica + imprime sin-links
  python3 tools/agregar_links.py --dry-run  # no escribe JSONs, solo muestra stats
  python3 tools/agregar_links.py --apply    # salta scraping, aplica cache existente
"""
import sys, os, re, json, time, ssl, unicodedata
import urllib.request

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = '/tmp/rc_links.json'
YT_VIDEOS_FILE = '/tmp/yt_videos.json'

BASE_URL = 'https://recursoscatolicos.com.ar/cancionero/index.php?q='
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

EMBED_RE = re.compile(r"embedMedia\('(youtube|spotify)',\s*'([^']+)'\)")
YT_ID_RE = re.compile(r'youtube\.com/embed/([A-Za-z0-9_-]{11})')
SP_ID_RE = re.compile(r'spotify\.com/embed/track/([A-Za-z0-9]+)')


# ─── HTTP ──────────────────────────────────────────────────────────────────

def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            return urllib.request.urlopen(req, context=SSL_CTX, timeout=15).read().decode('utf-8', errors='replace')
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(2)


def extract_links(html):
    yt = sp = None
    for m in EMBED_RE.finditer(html):
        kind, url = m.group(1), m.group(2)
        if kind == 'youtube':
            vid = YT_ID_RE.search(url)
            if vid:
                yt = f'https://www.youtube.com/watch?v={vid.group(1)}'
        elif kind == 'spotify':
            tid = SP_ID_RE.search(url)
            if tid:
                sp = f'https://open.spotify.com/track/{tid.group(1)}'
    return yt, sp


# ─── Scraping RC ──────────────────────────────────────────────────────────

def scrape_rc(rc_songs, delay=0.9):
    """Devuelve dict {id: {'youtube': url|None, 'spotify': url|None}}."""
    cache = {}
    if os.path.exists(CACHE_FILE):
        cache = json.load(open(CACHE_FILE, encoding='utf-8'))
        print(f'Cache: {len(cache)} entradas previas')

    ids_pendientes = [s['id'] for s in rc_songs if str(s['id']) not in cache]
    total = len(ids_pendientes)
    print(f'A scrapear: {total} canciones RC')

    for i, song_id in enumerate(ids_pendientes):
        try:
            html = fetch(BASE_URL + str(song_id))
            yt, sp = extract_links(html)
            cache[str(song_id)] = {'youtube': yt, 'spotify': sp}
            status = ('▶' if yt else ' ') + ('♫' if sp else ' ')
            print(f'  [{i+1}/{total}] {song_id} {status}', flush=True)
        except Exception as e:
            cache[str(song_id)] = {'youtube': None, 'spotify': None}
            print(f'  [{i+1}/{total}] {song_id} ERROR: {e}', flush=True)

        # Save cache every 20 songs
        if (i + 1) % 20 == 0:
            json.dump(cache, open(CACHE_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        time.sleep(delay)

    json.dump(cache, open(CACHE_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'Cache guardado: {CACHE_FILE}')
    return cache


# ─── Title matching for Athenas/curadas ──────────────────────────────────

def normalizar(s):
    s = s.lower()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')  # remove accents
    s = re.sub(r'[^a-z0-9\s]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def match_yt_channel(songs, yt_videos):
    """
    songs: list of dicts con 'titulo'
    yt_videos: dict {videoId: title}
    Returns dict {titulo_normalizado: youtube_url}
    """
    suffix = re.compile(r'\s*-\s*canciones y cantos mpd\s*$', re.I)
    # Build normalized index of YT videos
    yt_norm = {}
    for vid_id, title in yt_videos.items():
        clean = suffix.sub('', title).strip()
        norm = normalizar(clean)
        yt_norm[norm] = f'https://www.youtube.com/watch?v={vid_id}'

    result = {}
    for song in songs:
        titulo_norm = normalizar(song['titulo'])
        if titulo_norm in yt_norm:
            result[titulo_norm] = yt_norm[titulo_norm]
            continue
        # Partial match: song title is contained in a YT title or vice versa
        for yt_norm_key, url in yt_norm.items():
            if titulo_norm in yt_norm_key or yt_norm_key in titulo_norm:
                result[titulo_norm] = url
                break

    return result


# ─── Apply links to JSON files ────────────────────────────────────────────

def apply_links(rc_cache, yt_matches, dry_run=False):
    files = {
        'canciones-recursoscatolicos.json': 'rc',
        'canciones-athenas.json': 'athenas',
        'canciones.json': 'curadas',
    }
    stats = {'total': 0, 'con_yt': 0, 'con_sp': 0, 'sin_link': []}

    for fname, kind in files.items():
        path = os.path.join(ROOT_DIR, fname)
        data = json.load(open(path, encoding='utf-8'))
        changed = 0

        for song in data:
            stats['total'] += 1
            yt = sp = None

            if kind == 'rc':
                entry = rc_cache.get(str(song['id']), {})
                yt = entry.get('youtube')
                sp = entry.get('spotify')
            else:
                titulo_norm = normalizar(song['titulo'])
                yt = yt_matches.get(titulo_norm)

            # Set or remove fields
            if yt:
                song['youtube'] = yt
                stats['con_yt'] += 1
                changed += 1
            elif 'youtube' in song:
                del song['youtube']

            if sp:
                song['spotify'] = sp
                stats['con_sp'] += 1
                if 'youtube' not in song:
                    pass  # counted below
            elif 'spotify' in song:
                del song['spotify']

            if not yt and not sp:
                stats['sin_link'].append({'fuente': kind, 'id': song['id'], 'titulo': song['titulo']})

        print(f'{fname}: {len(data)} canciones, {changed} con al menos 1 link')
        if not dry_run:
            json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    return stats


# ─── Main ─────────────────────────────────────────────────────────────────

def main():
    dry_run = '--dry-run' in sys.argv
    apply_only = '--apply' in sys.argv

    # Load all JSON files
    rc_songs = json.load(open(os.path.join(ROOT_DIR, 'canciones-recursoscatolicos.json'), encoding='utf-8'))
    ath_songs = json.load(open(os.path.join(ROOT_DIR, 'canciones-athenas.json'), encoding='utf-8'))
    cur_songs = json.load(open(os.path.join(ROOT_DIR, 'canciones.json'), encoding='utf-8'))

    # Step 1: Scrape RC (or load cache)
    if apply_only and os.path.exists(CACHE_FILE):
        rc_cache = json.load(open(CACHE_FILE, encoding='utf-8'))
        print(f'Usando cache existente: {len(rc_cache)} entradas')
    else:
        rc_cache = scrape_rc(rc_songs)

    # Step 2: Match Athenas + curadas against YT channel
    yt_matches = {}
    if os.path.exists(YT_VIDEOS_FILE):
        yt_videos = json.load(open(YT_VIDEOS_FILE, encoding='utf-8'))
        yt_matches = match_yt_channel(ath_songs + cur_songs, yt_videos)
        print(f'YT channel matches: {len(yt_matches)} canciones')
    else:
        print(f'AVISO: {YT_VIDEOS_FILE} no encontrado, sin matches del canal YT')

    # Step 3: Apply
    stats = apply_links(rc_cache, yt_matches, dry_run=dry_run)

    # Step 4: Report
    rc_with_yt = sum(1 for v in rc_cache.values() if v.get('youtube'))
    rc_with_sp = sum(1 for v in rc_cache.values() if v.get('spotify'))
    print(f'\n=== Resumen ===')
    print(f'RC: {rc_with_yt}/{len(rc_songs)} con YouTube | {rc_with_sp}/{len(rc_songs)} con Spotify')
    print(f'Total: {stats["total"]} | con YouTube: {stats["con_yt"]} | con Spotify: {stats["con_sp"]}')
    print(f'Sin ningún link: {len(stats["sin_link"])}')

    if stats['sin_link']:
        print('\n=== Canciones SIN link ===')
        sin_rc = [s for s in stats['sin_link'] if s['fuente'] == 'rc']
        sin_ath = [s for s in stats['sin_link'] if s['fuente'] == 'athenas']
        sin_cur = [s for s in stats['sin_link'] if s['fuente'] == 'curadas']
        if sin_ath:
            print(f'\n-- Athenas ({len(sin_ath)}) --')
            for s in sin_ath:
                print(f"  {s['id']}: {s['titulo']}")
        if sin_cur:
            print(f'\n-- Curadas ({len(sin_cur)}) --')
            for s in sin_cur:
                print(f"  {s['id']}: {s['titulo']}")
        if sin_rc:
            print(f'\n-- RecursosCatolicos ({len(sin_rc)} de {len(rc_songs)}) --')
            for s in sin_rc:
                print(f"  {s['id']}: {s['titulo']}")

    if dry_run:
        print('\n(dry-run: JSONs no modificados)')


if __name__ == '__main__':
    main()
