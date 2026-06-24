# Sugerencias por mail (sin backend) · Diseño

**Fecha:** 2026-06-24
**Alcance:** Permitir que la gente sugiera **cambios** en una canción o proponga **canciones nuevas**, sin backend, mediante links `mailto:` prellenados. Sin otras funcionalidades.

## Objetivo

Dar dos puntos de entrada en la app para enviar sugerencias por mail a una casilla fija, con el cuerpo del mail ya prellenado para minimizar el trabajo de quien sugiere y de quien las aplica.

- **Destinatario:** `procesoconfirmacion@gmail.com` (fijo, publicado en los `mailto:`).
- **Canal:** solo email (más privado que WhatsApp; no expone un número personal).

## No incluido (YAGNI)

- Backend, base de datos, formularios de terceros (Formspree, Google Forms).
- Envío por WhatsApp u otros canales.
- Botón "copiar al portapapeles" de respaldo (se puede agregar después si hace falta).
- Aplicar las sugerencias automáticamente: la edición del JSON sigue siendo manual.

## Arquitectura

Todo del lado del cliente, dentro de `index.html`. Dos funciones que arman un link `mailto:` y disparan la apertura del cliente de mail. Cero dependencias; el sitio sigue estático.

`mailto:procesoconfirmacion@gmail.com?subject=<asunto>&body=<cuerpo>`

Asunto y cuerpo se codifican con `encodeURIComponent`. Los saltos de línea (`\n`) viajan como `%0A`.

## Componente 1 — Sugerir un cambio (por canción)

**Disparador:** botón **"Sugerir un cambio"** al final del panel de detalle (`#detailBody`), visible al abrir cualquier canción.

**Función:** `mailtoCambio(cancion)` arma:

- **Asunto:** `[Cancionero] Cambio: <título>`
- **Cuerpo:**

```
¡Hola! Gracias por ayudar a mejorar el cancionero.
Editá abajo lo que quieras corregir (letra, acordes, tono…) y enviá.
No borres la línea "ID" así la encontramos rápido.

ID: <id>
Título: <título>
Autor: <autor>
Categoría: <categoría>
Tono: <tono o "—">

Letra (acordes entre corchetes, ej. [DO]):
<estrofas unidas por \n\n, cada una con su letra ChordPro tal cual está en el JSON>
```

Las estrofas se concatenan con una línea en blanco entre cada una. Si una estrofa tiene `tipo` distinto de `estrofa`/`coro` (ej. `intro`, `puente`), se antepone una etiqueta entre paréntesis para dar contexto (ej. `(Coro)`).

## Componente 2 — Sugerir una canción nueva (global)

**Disparador:** botón **"Sugerir una canción"** en dos lugares: en el hero (al lado de *Playlist Colaborativa*) y en el footer.

**Función:** `mailtoNueva()` (cuerpo fijo, sin datos de canción):

- **Asunto:** `[Cancionero] Nueva canción`
- **Cuerpo:**

```
¡Hola! Gracias por sumar un canto.
Completá los campos. Si sabés los acordes, ponelos entre corchetes antes
de la sílaba, ej.: [DO]Tú has ve[RE]nido a la orilla.

Título:
Autor:
Categoría:
Momento (opcional):
Tono:

Letra:
```

## Estilos

- Reutilizar la paleta actual (`--naranja`, `--azul`, `--borde`, etc.).
- El botón "Sugerir un cambio" del detalle: estilo discreto (borde, texto azul/marrón), separado del cuerpo por un margen y un borde superior suave.
- Los botones "Sugerir una canción" del hero/footer: estilo secundario, sin competir con el botón naranja de *Playlist Colaborativa* (ej. contorno azul o gris).

## Limitaciones conocidas

- **Largo del `mailto:`:** en canciones muy largas, algún cliente de mail podría recortar el cuerpo. Degrada bien: el mail llega con asunto, ID, metadata y la mayor parte de la letra. Aceptable para este alcance.
- **Cliente de mail:** requiere que el dispositivo tenga un cliente de correo configurado (lo habitual en celulares).

## Criterios de éxito

- Al abrir una canción, hay un botón "Sugerir un cambio" que abre el mail prellenado con la canción completa (id, metadata y letra ChordPro) y el asunto correcto.
- Hay un botón "Sugerir una canción" (hero y footer) que abre el mail con la plantilla de canción nueva.
- Ambos van a `procesoconfirmacion@gmail.com` con asunto y cuerpo correctamente codificados.
- Sin dependencias nuevas; el sitio sigue estático.
