---
title: NB07 · SHAP y aditividad
course: Reto 1 · SAA+PIA+MIA
block: 07 — NB07 SHAP
node: B7.1
indicador: SAA-9
descriptor: 10
spine: true
status: en-curso
tags:
  - nb07
  - shap
  - rubrica/saa-9
---

# NB07 · SHAP y aditividad

> [!abstract] En una frase
> SHAP no se cree: se comprueba. Si la base más la suma de aportes no reproduce la predicción,
> el gráfico es decoración. Aquí se comprueba con tolerancia 1e-5.

## Qué digo

«Explico el modelo elegido con SHAP, calculado sobre **validación**, no sobre test. Uso la
aditividad como control: base más suma de aportes tiene que dar la predicción, con tolerancia
1e-5, o el assert falla y lo digo. Las variables que más pesan son `cycle` y `T50`; `Nc` y `T30`
aparecen después. Y coinciden con la importancia por permutación, que es otro método: la
conclusión es robusta al método, no causalidad.»

## Por qué la aditividad es la clave

- Es lo que separa «SHAP como imagen bonita» de «SHAP como medición». La rúbrica pide qué
  variables pesan más; el tribunal puede pedir «¿y cómo sabes que está bien?».
- Se calcula en validación porque en test se toca una vez y no se explica con él.

## Evidencia

- `src/clase/shap_clase.py` (`check_aditividad`, `top_shap`); 200 filas de validación, fold-0.
- `resultados/shap_importancia.csv` y `resultados/shap_bundle_C/` (3 CSV + 3 PNG + `metadata.json`).
- Permutación: `resultados/importancia_permutacion.csv` (cycle 20,76 · T50 6,16 · Nc 1,57).
- Bundle: `src/ds02_rul/shap_c.py` (`ejecutar_shap_c`), llamado desde NB07 c3.

## Pregunta probable

**«¿SHAP explica el motor o el modelo?»**
→ «El modelo. Describe qué features empujaron esta predicción, no la física del motor. Sirve para
auditar decisiones y detectar atajos, no para certificar una causa.»

## Lo que NO digo

- No digo «SHAP demuestra causalidad».
- No digo que se calculó en test.
- No presento el gráfico sin haber dicho que la aditividad se comprueba.

## Di esto en el tribunal

> «SHAP sobre validación con control de aditividad a 1e-5: `cycle` y `T50` mandan, y coincide con
> permutación, así que la conclusión es robusta al método.»

## Flashcards #flashcards

- ¿Sobre qué conjunto se calcula SHAP y por qué? :: sobre validación, porque el test se lee una sola vez.
- ¿Qué control demuestra que SHAP está bien calculado? :: la aditividad: base + suma de aportes = predicción, tolerancia 1e-5.
- ¿Qué dos variables mandan? :: `cycle` y `T50`.
