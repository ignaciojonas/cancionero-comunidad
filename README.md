# Cancionero · Comunidad

Cancionero litúrgico estático. Costo de hosting: **$0**.

## Estructura

```
cancionero/
├── index.html                       ← App completa (HTML + CSS + JS)
├── canciones.json                   ← Canciones curadas a mano
├── canciones-athenas.json           ← Importadas de PDFs de acordes (generado)
├── canciones-recursoscatolicos.json ← Importadas de recursoscatolicos.com.ar (generado)
├── tools/convert_athenas.py         ← Conversor de PDFs de acordes → JSON
├── tools/scrape_recursoscatolicos.py← Scraper del cancionero web → JSON
├── vercel.json                      ← Config de deploy
└── README.md
```

La app carga y junta **los tres** archivos de canciones (`canciones.json` +
`canciones-athenas.json` + `canciones-recursoscatolicos.json`). El primero es
para canciones cargadas a mano; los otros dos se **generan** (ver más abajo).

## Agregar una canción

Editá `canciones.json` y agregá un objeto al array. Cada canción tiene esta forma:

```json
{
  "id": 9,
  "titulo": "Nombre de la Canción",
  "autor": "Nombre del Autor",
  "categoria": "Vocación",
  "momento": ["Comunión", "Envío"],
  "tono": "G",
  "estrofas": [
    {
      "tipo": "coro",
      "letra": "Texto del coro..."
    },
    {
      "tipo": "estrofa",
      "numero": 1,
      "letra": "Texto de la primera estrofa..."
    }
  ]
}
```

### Acordes de guitarra (opcional)

Los acordes se escriben dentro del campo `letra` con notación **ChordPro**: el
acorde entre corchetes, pegado a la sílaba donde entra.

```json
"letra": "[G]Ven, Espíritu [D]Santo\n[G]Úngeme, [D]lléname"
```

- El acorde se muestra arriba de su sílaba.
- Una letra **sin** corchetes se ve como texto normal (sin acordes).
- Los acordes se muestran por defecto; el botón **"Tono"** del detalle los oculta/muestra. Si la canción no tiene acordes, ese botón queda desactivado.

**Categorías sugeridas:** Vocación, Fraternidad, Salmos, Gloria, Espíritu Santo, Cordero, Pascua, Aclamación, Adviento, Navidad, Cuaresma, Marianas, Envío

**Momentos litúrgicos:** Entrada, Gloria, Salmo Responsorial, Aclamación al Evangelio, Ofertorio, Santo, Cordero, Comunión, Fracción del Pan, Envío, Meditación

**Tipos de sección** (campo `tipo` de cada estrofa): `estrofa` (numerada),
`coro`, `intro`, `precoro`, `puente`, `final`, `instrumental`.

## Importar PDFs de acordes (Athenas)

Las canciones de `canciones-athenas.json` se generan desde hojas de acordes en
PDF (acordes sobre la letra) con el conversor:

```bash
pip install pdfplumber
python3 tools/convert_athenas.py --all "/ruta/a/los/PDFs" \
  --out canciones-athenas.json --start-id 10
```

El conversor detecta columnas, alinea los acordes a la sílaba por posición,
reconoce las secciones y saca la tonalidad del nombre del archivo (ej. `(D)`).

> **Importante:** la alineación de acordes es una **transcripción de base**
> (puede estar corrida ~1 carácter) y las categorías se asignan por palabras
> clave del título. **Conviene revisar/corregir con la guitarra** y reasignar
> categorías/momentos donde haga falta.

## Importar del cancionero web (recursoscatolicos.com.ar)

`canciones-recursoscatolicos.json` se genera scrapeando el cancionero de
[recursoscatolicos.com.ar](https://recursoscatolicos.com.ar/cancionero/). Cada
canción vive en `index.php?q=<id>` con la letra y acordes (notación latina:
DO, RE, MI…) en un `<pre>` monoespaciado, así que la alineación es exacta.

```bash
# 1) bajar el índice a /tmp/rc_index.html y extraer /tmp/rc_list.json (id+título)
# 2) correr el scraper (saltea las que ya existen por título):
python3 tools/scrape_recursoscatolicos.py --all \
  --out canciones-recursoscatolicos.json --start-id 200 --delay 0.3 \
  --exclude-titles canciones.json,canciones-athenas.json
```

Saca título/autor (separa por `" - "`), tono (primer acorde), categoría por
palabras clave, y agrupa estrofas por líneas en blanco. Cada canción guarda su
`fuente` (URL original).

> **Importante:** mismo criterio que arriba — es una **transcripción de base**;
> conviene revisar acordes y reclasificar categorías. El contenido pertenece a
> sus autores / a recursoscatolicos.com.ar; se usa para el cancionero de la
> comunidad.

### Re-clasificar categorías y momentos

`tools/clasificar_tags.py` usa los **tags reales** del sitio (vía
`buscar_ajax.php?s=&tags=<id>`) para reescribir `categoria` y `momento` de las
canciones importadas (recursoscatolicos por `q-id`, Athenas por título). No toca
`canciones.json` (curadas).

```bash
python3 tools/clasificar_tags.py
```

Las que no tienen tags en el sitio (~85, sobre todo Athenas) conservan su
categoría por palabras clave y quedan sin momento.

## Deploy en Vercel

### Opción A — Desde GitHub (recomendado)

1. Subir este proyecto a un repo de GitHub
2. Entrar a [vercel.com](https://vercel.com) → New Project
3. Importar el repo
4. Deploy automático con cada `git push`

Para agregar canciones: editar `canciones.json` → commit → push → Vercel redeploya solo.

### Opción B — Vercel CLI

```bash
npm i -g vercel
cd cancionero/
vercel --prod
```

## Sin costos

- No hay base de datos
- No hay backend
- No hay funciones serverless
- El JSON es un archivo estático cacheado por CDN

El plan gratuito de Vercel soporta proyectos así sin límites prácticos.
