---
title: Checklist del día D
course: Reto 1 · SAA+PIA+MIA
block: 00 — Arranque
node: A3
spine: false
status: en-curso
tags:
  - checklist
  - demo
---

# Checklist del día D

> [!abstract] En una frase
> El día de la defensa no se investiga: se comprueba. Todo lo que sigue se verifica en menos
> de 10 minutos y evita el 90 % de los fallos de demo.

## Antes de salir

- [ ] Portátil cargado + cargador. La demo consume batería.
- [ ] `results/` y capturas en local: **la demo no depende de la red**.
- [ ] PDF de la presentación y este vault exportados (por si el portátil falla).

## Al llegar, en este orden

```bash
# 1. El repo está en el árbol esperado
git -C . status --short | wc -l

# 2. Los artefactos existen y cuadran
python -c "import json;d=json.load(open('models/ds02_manifest.json'));print(d['metrics']['reference_row']['rmse'], d['macro_rmse'])"

# 3. La app arranca (deja la terminal visible, no minimizada)
streamlit run app/dashboard_ds02.py --server.port 8501

# 4. La API de MIA-3 escucha
uvicorn app.api:app --port 8000
curl -s localhost:8000/healthz

# 5. n8n arriba
curl -s localhost:5678/healthz
```

## Pestañas abiertas, en este orden

1. **App** (`localhost:8501`) en la pestaña del motor.
2. **n8n** (`localhost:5678`) en el flujo, vista de ejecuciones.
3. **README** en el apartado «Resultados» (captura de MLflow).
4. **NB07** abierto en la celda de SHAP (por si piden verlo).
5. Este vault en [[00-guion-15-min]].

## Si algo no arranca

| Fallo | Qué hago |
|---|---|
| Streamlit no carga | Enseño las capturas de `docs/assets/` y sigo el guion; no reinicio en vivo. |
| API caída | Digo «la API es local, la enseño en código» y abro `app/api.py:262`. |
| n8n caído | Enseño `n8n/flujo.json` y la vista de ejecuciones ya capturada. |
| Sin red | Todo el material está en local; MLflow se enseña con el export CSV. |

## Lo que no se hace en vivo

- No se reentrena nada (8–40 minutos y mueve cifras).
- No se `pip install` nada.
- No se abre un notebook y se pulsa «Run all».

## Di esto en el tribunal

> «La demo es local: modelo congelado, banda calibrada y reglas; si algo cae, enseño la captura
> y sigo, porque lo que importa es la cadena, no el clic.»

## Flashcards #flashcards

- ¿Qué se comprueba primero el día D? :: que los artefactos existen y cuadran con el manifiesto.
- ¿Qué se hace si Streamlit no arranca? :: enseñar capturas y seguir el guion, sin reiniciar en vivo.
