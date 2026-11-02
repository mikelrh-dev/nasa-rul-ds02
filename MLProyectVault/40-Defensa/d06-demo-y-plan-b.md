---
tipo: defensa
status: sin-estudiar
tags:
  - demo
  - plan-b
  - pantalla
---

# Demo y plan B — qué muestras y si falla

> [!abstract] En una frase
> Enseñas en orden recarga, predicción y decisión, y si algo falla cuentas sin pantalla.

## Qué muestras en pantalla (orden)

1. `models/ds02_manifest.json`: referencia 4.251 y macro 4.8433. Prueba que lo defendido es lo de disco.
2. NB01 celda 6: ventanas `(17450, 50, 19)` y `(6196, 50, 19)`. Prueba el terreno.
3. NB02 celda 11: tabla titular con híbrido 4.276 en esa ejecución. Prueba que combina.
4. NB03 celda 16: `[RELOAD OK] 60.40 vs 58.00`. Prueba que servir es recargar.
5. Estado por motor con `L_inf`: APTO, INSPECCIÓN o HANGAR. Prueba que decides.

Cinco paradas, cinco minutos de apoyo a [[d02-guion-5min]]. Nada más: si abres más pestañas, pierdes al tribunal.

## Qué dices en cada parada

En el manifiesto lees exacto y redondeas en voz. En ventanas dices «0,44 ciclos, no 50». En la tabla dices «en esa ejecución» y remites al bundle. En el reload dices «recargado igual que en memoria».

Cada parada termina con su frase: terreno listo, bases sueltas, combinación que gana, cota calibrada, decisión operativa.

## Plan B si algo no carga

Si no abre el HDF5, enseñas [[e00-cifras-autoritativas]] impresa y cuentas el reparto de memoria. Si no recarga el `.keras`, cuentas `LastStepPooling` y la guarda de forma ([[s12-persistencia-y-contrato]]).

Si los decimales se mueven en ±0.1, dices: «TensorFlow en CPU, documentado en el README; el orden se mantiene» ([[c14-ruido-y-reproducibilidad]]).

Plan B no es improvisar: es contar sin pantalla lo mismo que mostrarías con ella.

## Errores de demo que te hunden

Abrir el cuaderno entero y hacer scroll sin rumbo. Recitar hashes de memoria en vez de leerlos. Decir «aquí se ve que funciona» sin leer el número exacto.

La demo se ensaya con cronómetro igual que el guion: cinco paradas, un minuto por parada como máximo.

## Di esto en el tribunal

> [!quote]
> «Te enseño manifiesto, ventanas, tabla, reload y estado. Si algo no carga, te lo cuento igual: 4.25 en disco, beta 1.0 y banda 100 con 26.4.»

## Flashcards

> [!question]- ¿Qué cinco paradas muestras?
> Manifiesto, ventanas, tabla, reload y estado por L_inf.

> [!question]- ¿Qué haces si falla el HDF5?
> Enseñas e00 y cuentas el reparto de memoria.

> [!question]- ¿Qué dices si se mueven los decimales?
> TF en CPU ±0.1, documentado y sin cambiar el orden.

> [!question]- ¿Qué afirma esta nota en una frase?
> Enseñas en orden recarga, predicción y decisión, y si algo falla cuentas sin pantalla.

> [!question]- ¿Cómo la contarías en el tribunal?
> «Te enseño manifiesto, ventanas, tabla, reload y estado. Si algo no carga, te lo cuento igual: 4.25 en disco, beta 1.0 y banda 100 con 26.4.»

> [!question]- ¿Qué archivo respalda esta nota?
`models/ds02_manifest.json`

> [!question]- ¿A qué nota vas si fallas esta idea?
[[d02-guion-5min]]

> [!question]- ¿A qué nota vas si fallas esta idea?
[[e00-cifras-autoritativas]]

> [!question]- ¿A qué nota vas si fallas esta idea?
[[s12-persistencia-y-contrato]]

> [!question]- ¿A qué nota vas si fallas esta idea?
[[c14-ruido-y-reproducibilidad]]

> [!question]- ¿Qué afirma esta nota en una frase?
> Enseñas en orden recarga, predicción y decisión, y si algo falla cuentas sin pantalla.

