# DS02 Ensamble RUL — 3 cuadernos (mismo código que `02_DS02_ensemble_RUL.ipynb`)

> Fuente de verdad para presentación: esta secuencia 01 → 02 → 03. El `02_DS02_ensemble_RUL.ipynb` de la raíz es el artefacto generado congelado de referencia (vía `scripts/build_02_notebook.py`) y **no debe re-ejecutarse**: su celda de persistencia reescribe `models/` y la re-ejecución cambia las cifras por no-determinismo CPU de TensorFlow (ver `EVALUACION_EJECUCION.md`).

El original de 77 celdas se partió **sin cambiar ningún cálculo**, solo por tiempo y lectura.

| Cuaderno | Contenido original | Tiempo aprox | Requisito |
|---|---|---|---|
| `01_datos_y_bases.ipynb` | Sec. 0–5: entorno, reparto, preproceso, ventanas, LGBM + BiLSTM `run_seed(42)` | Lento (1ª parte ~10 min) | ninguno |
| `02_decision_ablacion_oof_ensamble.ipynb` | Sec. 6–8: ablación `cyc_norm`, OOF + `beta`, metas, `HybridStackingEnsemble`, conformal | Lento (ablación + OOF) | haber corrido 01 |
| `03_evidencia_multisemilla_diagnostico.ipynb` | Sec. 9–14: 2 semillas extra, comparativa, diagnósticos, persistencia `models/` | Lento (2 semillas) | haber corrido 01 y 02 |

Cómo funciona el paso de estado (lo único nuevo):
- `01` guarda en `artifacts/`: `nb1_dev/test.npz`, `nb1_aux.joblib`, `nb1_result_arrays.joblib`, `bilstm_seed42.keras`.
- `02` lo recarga (celda Puente), no re-entrena la 42; al final guarda `nb2_selection/conformal/eval.joblib` + `nb2_p_ens.npy`.
- `03` recarga `artifacts/` de 01+02, reconstruye el mismo `ensemble` (mismo beta, mismos objetos) y sigue con multisemilla y `save_ensemble`.

Reglas: correr cada cuaderno de arriba abajo, en orden 01→02→03. El original de raíz se deja intacto como referencia.

## Guía estilo clase (cómo leer estos cuadernos)

Igual que en RequisitosClase (plantilla `00` y ejercicios 01–05):

1. **Una tabla manda.** `mostrar_clase()` ordena la tabla con el mejor arriba. La columna de decisión es `RMSE val` (en clase `F1/MAE/AUC val`); `±` es la desviación entre semillas/trozos.
2. **Baseline tonto primero.** `Baseline (media train)` está solo como referencia, como el `Baseline (siempre 'no')` de clase. Cualquier modelo útil tiene que ganarle. No entra en la elección.
3. **`evaluar_clase` no entrena.** Es un alias de `evaluate_predictions`: pone la nota y tira el cálculo, igual que `evaluar()` en clase mide con `cross_validate` y no deja modelo entrenado.
4. **Extras aparte.** La tabla `extra` (EMA 3/5/10) es para curiosear, como el sec. 7 de clase. La decisión solo usa la tabla titular.
5. **Gráficos mínimos.** Cada `barh` tiene una frase `Cómo leerlo` + una `Fíjate`. Si el gráfico necesita más de dos frases para entenderse, no es el gráfico final.

## Regla de empate (la que decide)

Copiada de clase, con tus métricas:

- Resta el `RMSE` del 1º y del 2º de la tabla ordenada.
- Si la diferencia es **menor que el `±`** (desviación entre semillas), es **empate**: elige el más simple (BiLSTM solo antes que híbrido, RF antes que XGBoost ajustado).
- Solo hay victoria si la diferencia supera el `±` **y** se mantiene en las 4 métricas (RMSE, MAE, R², NASA_Score).
- El test (motores 11/14/15) no elige: solo comprueba que la validación dijo la verdad, como en clase sec. 9/test.

Ejemplo con tus números: híbrido 4.23 ± 0.14 frente a BiLSTM 6.07 ± 0.57 → diferencia 1.85, mayor que ambos `±` → victoria, no empate.

## Para entenderlo (lo que en clase va en `details`)

- **OOF agrupado:** cada ventana la puntúa un meta ajustado en *otros* motores. Medir sobre el propio ajuste (protocolo legado de un motor) da un cociente falsamente bueno y por eso solo se publica como diagnóstico.
- **beta:** mediana de los 3 folds. `beta=0` degrada al campeón sin riesgo; `beta=1` es `p_meta` puro.
- **Conformal:** banda calibrada sobre residuales fuera de fold, asimétrica por tramo (la NASA tampoco es simétrica). Nominal 90 %: si cubre de más, se publica el trade-off en vez de estrecharla eligiendo sobre test.
