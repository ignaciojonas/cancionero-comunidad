# Cancionero · Comunidad

Cancionero litúrgico estático. Costo de hosting: **$0**.

## Estructura

```
cancionero/
├── index.html        ← App completa (HTML + CSS + JS)
├── canciones.json    ← Base de datos de canciones
├── vercel.json       ← Config de deploy
└── README.md
```

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
