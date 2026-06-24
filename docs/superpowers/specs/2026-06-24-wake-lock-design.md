# Wake Lock — pantalla activa al leer una canción · Diseño

**Fecha:** 2026-06-24
**Alcance:** Evitar que la pantalla del celular se apague mientras se está leyendo/cantando una canción (con el panel de detalle abierto), usando la Screen Wake Lock API. Sin app nativa, sin UI nueva.

## Objetivo

Cuando alguien abre una canción para cantarla desde el teléfono, la pantalla no debe apagarse sola. Al cerrar la canción, vuelve el comportamiento normal del dispositivo.

## Arquitectura

Screen Wake Lock API del navegador (`navigator.wakeLock`). Todo dentro de `index.html`, sin dependencias. Se adquiere el lock al abrir el detalle de una canción y se libera al cerrarlo.

## Componentes

- `solicitarWakeLock()` (async): si `navigator.wakeLock` existe, pide `navigator.wakeLock.request('screen')` y guarda el sentinel en una variable de módulo `wakeLock`. Envuelto en `try/catch`: si falla (batería baja, permiso denegado, etc.), no rompe nada.
- `liberarWakeLock()` (async): si hay sentinel, llama `wakeLock.release()` y lo limpia.
- Enganches:
  - `abrirDetalle(cancion)` → `solicitarWakeLock()`.
  - `cerrarDetalle()` → `liberarWakeLock()`.
- Listener `visibilitychange`: el SO libera el lock cuando la pestaña pasa a segundo plano. Al volver a `document.visibilityState === 'visible'`, si hay una canción abierta (`cancionActual` no es null) y no hay sentinel activo, re-pedir el lock.

## Compatibilidad y errores

- **Feature-detection:** si `'wakeLock' in navigator` es falso (iOS < 16.4, Android viejo), todas las funciones son no-op. La app funciona igual.
- La adquisición se hace en respuesta a un gesto del usuario (click que abre la canción) y con la página visible, que es lo que requieren los navegadores.
- Cualquier error queda atrapado y silenciado: es una mejora, no una función crítica.

## No incluido (YAGNI)

- Botón/indicador de UI (es automático; el usuario eligió "simplemente funciona").
- Mantener la pantalla activa fuera del detalle (en la lista).

## Verificación

- En el preview: confirmar que al abrir una canción se intenta adquirir el lock y al cerrarla se libera (estado del sentinel), y que sin soporte no hay errores en consola.
- Prueba real ("no se apaga la pantalla") la hace el usuario en un celular.

## Criterios de éxito

- Con `navigator.wakeLock` disponible: al abrir una canción se adquiere el wake lock; al cerrarla se libera; al volver a la app con una canción abierta, se vuelve a adquirir.
- Sin soporte: la app funciona exactamente igual que antes, sin errores.
- Sin dependencias ni UI nueva.
