---
title: MIA · n8n con acción propia
course: Reto 1 · SAA+PIA+MIA
block: 09 — MIA decisión
node: D3
indicador: MIA-3
descriptor: 10
spine: true
status: en-curso
tags:
  - mia
  - n8n
  - api
  - rubrica/mia-3
---

# MIA · n8n con acción propia

> [!abstract] En una frase
> El flujo no solo enruta: en la rama de hangar llama a **nuestra** API y registra la decisión.
> Esa es la acción que no se vio en clase y el 10 de MIA-3.

## Qué digo

«El flujo recibe la decisión por webhook con autenticación de cabecera y abre tres ramas: apto,
inspección y hangar. Las dos primeras notifican; la de hangar, además, hace `POST /n8n-decision`
a la API del propio proyecto, que valida un token compartido y registra la decisión con
idempotencia por `fingerprint`. No es un servicio de la lista de clase: es nuestro sistema
cerrando el círculo.»

## Por qué se dice así

- MIA-3 vale el 35 % de MIA, el indicador más pesado del reto. El 10 exige «una acción distinta a
  las vistas en clase»: Postgres, Calendar o Gmail no lo son.
- La idempotencia no es un adorno: evita que un reintento del flujo abra dos registros para la
  misma decisión.

## Lo que es verdad y lo que no

| Afirmación | Estado |
|---|---|
| El flujo está en el repo (`n8n/flujo.json`, 15 nodos) | Verdad |
| La rama hangar llama a nuestra API | Verdad (`app/api.py:262`) |
| El flujo versionado está `active:false` | Verdad, por diseño (un test lo exige) |
| La instancia local lo ejecutó con efectos reales | Verdad: 29 ejecuciones el 2026-11-07 (25 ok / 4 error) |
| Hay una ejecución atribuible a la app | **No la hay**: no lo digo |

## Evidencia

- `n8n/flujo.json` (webhook con `headerAuth`, tres ramas, dos nodos con credencial a sustituir).
- `app/api.py:262` (`POST /n8n-decision`), `_N8N_LOCK` para escritura concurrente.
- `src/n8n.py` (envío desde la app), `app/ui_n8n.py` (`payload_desde_traza`).
- Test que exige la acción novedosa: `tests/test_n8n_propia.py:139`.

## Pregunta probable

**«¿Y si n8n está caído?»**
→ «La app sigue funcionando: el envío es un efecto posterior a la decisión, no parte del cálculo.
Si el webhook falla, la decisión ya está tomada y registrada localmente.»

## Lo que NO digo

- No digo «está en producción»: es una instancia local con ejecuciones reales.
- No digo que la app disparó el flujo: el envío está cableado, pero no hay ejecución atribuible.
- No oculto que el flujo versionado está inactivo: está inactivo por diseño y lo enseño.

## Di esto en el tribunal

> «La rama de hangar no termina en un servicio de terceros: llama a nuestra API, que registra la
> decisión con token e idempotencia. Es el sistema cerrando su propio círculo.»

## Flashcards #flashcards

- ¿Qué hace distinta a la rama de hangar? :: llama a `POST /n8n-decision` de nuestra propia API.
- ¿Cómo se evita duplicar registros? :: con idempotencia por `fingerprint`.
- ¿El flujo versionado está activo? :: no, `active:false` por diseño; la instancia local sí lo ejecutó.
