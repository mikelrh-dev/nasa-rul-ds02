---
tipo: concepto
status: consolidado
tags:
  - seguridad
  - api
  - contrato
---

# Seguridad de API y contrato — servir sin regalar el bundle

> [!abstract] En una frase
> Quien escribe se autentica, quien abusa se frena, quien manipula el artefacto no carga.

## La idea

Tres guardas en capas:

1. **Auth (`app/api.py`)**: escrituras exigen API key comparada con `hmac.compare_digest` (no `==`). Fallo = 401, nunca 200/429. Lecturas `/health` abiertas para sonda.
2. **Rate-limit**: ventana fija también en escrituras autenticadas. Evita reintento masivo y test `test_security_api.py` lo pinnea.
3. **Contrato artefacto**: `assert_ds02_artifact` aborta si `scaler n_features != 18` o `n_op != 4` (un FD001 colado puntuaría sin avisar). `load_ensemble` verifica SHA-256 contra `models/ds02_manifest.json` / `app/cache/cache_manifest.json` antes de deserializar. Si caché y bundle discrepan, manda bundle y la caché se invalida.

## Dónde aparece en este proyecto

- `app/api.py:208 predict`, `tests/test_security_api.py`, `tests/test_artifact_contract.py`
- `src/ds02_rul/persistence.py:187 assert_ds02_artifact`, `:207 load_ensemble`
- `s12-persistencia-y-contrato`, `s14-app-y-despliegue`

> [!warning] La trampa
> «401 o 429 da igual»: no. 401 es sin llave, 429 es con llave pero abusando. Devolver 429 a un atacante le dice que la llave vale.

## Di esto en el tribunal

> [!quote]
> «Escribes con llave comparada en tiempo constante, abusas y te freno igual, manipulas el bundle y no carga: el hash manda.»

## Flashcards

> [!question]- ¿Qué pasa sin llave, con abuso y con bundle tocado?
> Sin llave 401; abuso rate-limit; bundle tocado no carga por SHA y guarda de forma.
