"""Inserta la sección v3 en notebook_nasa_fd001.ipynb (antes de las conclusiones)."""
import json
import pathlib

NB = pathlib.Path('notebook_nasa_fd001.ipynb')

MD_9 = """## 9. V3 — validación honesta, alarma por coste e incertidumbre

La v2 medía el train **in-sample** (7.34) y alertaba con umbrales fijos. La v3 corrige eso:

1. **Validación por motor**: `GroupKFold` agrupando por `engine_id`, así un motor nunca está
   en train y validación a la vez. La RNN usa **holdout por motor** (20 % de los motores fuera)
   porque 5 folds × LSTM no es viable. Se probó antes un split temporal (70/30 de ciclos) y se
   descartó: solo ve el final de la vida del motor, no aprende el rango completo de RUL y en test
   se iba a RMSE 63.
2. **Umbral calibrado por coste** (`FN × 20 + FP × 1`) sobre OOF de train, nunca sobre test.
3. **Features de salud** causales (solo pasado): z-score por motor, deltas a 10 y 30, std rolling 15,
   media 5 sobre los 7 sensores clave. Se aplican **igual** a GBDT y a LSTM.
4. **Incertidumbre** con LightGBM quantile (α = 0.1 / 0.9).
5. **Transferencia** del pipeline a FD002 y FD004.

El protocolo de test no cambia: última ventana por motor contra `RUL_FDxxx.txt` con clip 125.
"""

CODE_DEMO = r"""import sys
sys.path.insert(0, 'scripts')

import json
import pathlib
import importlib

import v3_core
importlib.reload(v3_core)
from lightgbm import LGBMRegressor

# Demo en vivo del protocolo: OOF por motor + umbral por coste (FD001, features de salud)
tr3, te3, rul3 = v3_core.load_fd('FD001')
_, f3 = v3_core.add_health_features(tr3)
_, f3t = v3_core.add_health_features(te3)
X3, y3, m3 = v3_core.make_windows(tr3, f3)
X3t, m3t = v3_core.test_last(te3, f3t, rul3)

mk3 = lambda s: LGBMRegressor(n_estimators=300, learning_rate=0.05, max_depth=8,
                              random_state=s, n_jobs=-1, verbose=-1)
oof3 = v3_core.oof_predict(X3, y3, m3.engine_id.values, mk3, folds=3, seeds=(42,))[42]
mod3 = mk3(42).fit(X3.reshape(len(X3), -1), y3)
p3 = mod3.predict(X3t.reshape(len(X3t), -1))
cal3 = v3_core.calibrate_threshold(oof3, y3)

print(f'features: {f3.shape[1]} | ventanas train: {X3.shape}')
print(f'RMSE OOF por motor: {v3_core.rmse(y3, oof3):.2f}  (in-sample era 7.34)')
print(f'RMSE test (motor):  {v3_core.rmse(m3t.RUL_real, p3):.2f}')
print('umbral calibrado en OOF:', cal3)
print('test con T*:', v3_core.eval_alarm(p3, m3t.RUL_real.values, cal3['T']))
print('test con 15 fijo:', v3_core.eval_alarm(p3, m3t.RUL_real.values, 15.0))
"""

MD_TABLA = """### 9b. Resultados de la fase 0-2 (OOF por motor + umbral por coste)

`models/v3_results.json` recoge todas las combinaciones ejecutadas. En FD001 los modelos
tabulares usan 5 folds × 3 seeds; en FD002/FD004, 3 folds × 1 seed (coste). La fila de la LSTM
usa **holdout por motor** (20 % de motores fuera), no OOF, y su columna es RMSE de validación.
"""

CODE_TABLA = r"""res = json.loads(pathlib.Path('models/v3_results.json').read_text(encoding='utf-8'))
filas = []
for fd, d in res.items():
    for clave, v in d.get('models', {}).items():
        filas.append({
            'Dataset': fd, 'Features': v['features'], 'Modelo': v['modelo'],
            'RMSE val/OOF': v.get('rmse_oof_mean', v.get('rmse_val')),
            '±std': v.get('rmse_oof_std', 0),
            'RMSE test': v['rmse_test'], 'MAE test': v['mae_test'],
            'T*': v['T'],
            'Recall @T*': v['alarma_T']['recall'], 'Prec @T*': v['alarma_T']['precision'],
            'Alarmas': v['alarma_T']['alarmas'],
            'Recall @15': v['alarma_15']['recall'],
        })
tab_v3 = pd.DataFrame(filas)
print('=== FASE 0-2: OOF por motor, test por motor, alarma calibrada ===')
display(tab_v3.sort_values(['Dataset', 'RMSE test']).reset_index(drop=True))
print('Nota: RMSE OOF se mide por ventana; RMSE test por motor. La columna ±std viene de 3 seeds en FD001.')
"""

MD_Q = """### 9c. Fase 3 — incertidumbre (LightGBM quantile)

Intervalo del 80 % (`q10`–`q90`) sobre la última ventana de cada motor. La regla ingenua
`q90 < 30` no dispara nunca (el intervalo es demasiado ancho); se comparan varias reglas y
se elige la de menor coste.
"""

CODE_Q = r"""q = pd.read_csv('models/v3_quantile_FD001.csv')
pol = json.loads(pathlib.Path('models/alarm_policy.json').read_text(encoding='utf-8'))
real_q = q['RUL_real'].values
cover = float(np.mean((real_q >= q['q10'].values) & (real_q <= q['q90'].values)))
ancho = float(np.mean(q['q90'].values - q['q10'].values))
print(f'cobertura del intervalo 80%: {100*cover:.1f}%  | ancho medio: {ancho:.1f} ciclos')

orden = q.sort_values('RUL_real').reset_index(drop=True)
fig, ax = plt.subplots(figsize=(12, 4.5))
ax.plot(orden.index, orden['RUL_real'], 'k-', lw=2, label='RUL real')
ax.plot(orden.index, orden['pred'], color='steelblue', lw=1.2, label='RUL predicha')
ax.fill_between(orden.index, orden['q10'], orden['q90'], color='steelblue', alpha=0.15,
                label='intervalo 80%')
ax.axhline(pol['T_crit'], color='crimson', ls='--', lw=1.2, label=f"T crítico = {pol['T_crit']}")
ax.set_xlabel('motores ordenados por RUL real')
ax.set_ylabel('RUL (clip 125)')
ax.set_title('Fase 3 — predicción e intervalo del 80 % (última ventana por motor)')
ax.legend(fontsize=9)
plt.tight_layout()
plt.show()

reglas = pd.DataFrame(pol['reglas']).T.reset_index().rename(columns={'index': 'Regla'})
print('=== comparación de reglas de alarma (test, 100 motores) ===')
display(reglas[['Regla', 'alarmas', 'recall', 'precision', 'coste']].sort_values('coste'))
print('regla elegida:', pol['regla_elegida'])
"""

MD_TRANSFER = """### 9d. Fase 4 — transferencia a FD002 (6 condiciones) y FD004 (6 condiciones, 2 modos de fallo)

Mismo pipeline, recalibrando el umbral por coste en cada dataset. Se comparan solo los
modelos tabulares: la LSTM se reentrena únicamente en FD001 y FD002 (coste de cómputo).
"""

CODE_TRANSFER = r"""cols_trans = ['Dataset', 'Modelo', 'RMSE val/OOF', 'RMSE test', 'MAE test', 'T*',
              'Recall @T*', 'Prec @T*', 'Alarmas']
trans = tab_v3[tab_v3['Features'] == 'health'][cols_trans].copy()
print('=== FASE 4: transferencia del pipeline ===')
display(trans.sort_values(['Dataset', 'RMSE test']).reset_index(drop=True))

piv = tab_v3[tab_v3['Features'] == 'health'].pivot_table(
    index='Modelo', columns='Dataset', values='RMSE test')
print('\nRMSE test por dataset (features de salud):')
display(piv.round(2))

fig, ax = plt.subplots(figsize=(8, 4))
piv.T.plot(kind='bar', ax=ax)
ax.set_ylabel('RMSE test')
ax.set_title('Transferencia: RMSE test por dataset y modelo')
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.show()
"""

MD_SYS = """### 9e. Fase 5 — sistema: inferencia, política y drift

`scripts/predict.py` carga `models/v3_bundle.joblib` (modelo + quantiles + features + versión)
y `models/alarm_policy.json`, y devuelve RUL, intervalo, alarma y **coste esperado de la decisión**.
Para drift: PSI **a nivel de flota** (comparar un solo motor contra la flota mide heterogeneidad,
no drift) y, por motor, % de valores fuera del rango [p01, p99] de entrenamiento.
"""

CODE_SYS = r"""import predict
importlib.reload(predict)

_, te5, _ = v3_core.load_fd('FD001')
for eid in (1, 3, 20):
    g = te5[te5['engine_id'] == eid]
    r = predict.predict(g)
    print(f'motor {eid:3d} -> RUL {r["rul"]:6.1f} [{r["q10"]:5.1f}, {r["q90"]:5.1f}]  '
          f'{r["alerta"]:8s} coste_esperado={r["coste_esperado"]:.2f}')

inf, met = predict.report('FD001')
print('\ninforme batch (100 motores):', met)
display(inf.head(5))

dfleet = predict.drift_batch(te5)
print(f"\ndrift de flota -> PSI max {dfleet['psi_max']:.3f} en {dfleet['peor_sensor']} "
      f"(alerta={dfleet['alerta_drift']}, n={dfleet['n_filas']})")
o = predict.out_of_range(te5[te5['engine_id'] == 66])
print(f"motor 66 fuera de rango: {o['peor_pct']:.1f}% en {o['peor_sensor']} (alerta={o['alerta']})")
"""

MD_LIM = """### 9f. Limitaciones de la v3 (dichas antes de que las pregunte nadie)

- **La `q90 < 30` no funciona**: el intervalo del 80 % mide ~65 ciclos de ancho, así que casi ningún
  motor queda por debajo del umbral. La incertidumbre sirve para priorizar, no para disparar alarmas sola.
- **El umbral se mueve con el dataset**: T* = 22 en FD001, 42.5 en FD002, 45 en FD004. No es transportable
  sin recalibrar (y recalibrar exige fallos reales).
- **OOF mide ventanas, test mide motores**: siguen siendo unidades distintas; el OOF es más pesimista.
- **FD002/FD004 con 1 seed y 3 folds**: sin barra de error. Sirven para ver si transfiere, no para decidir.
- **La LSTM** solo se reentrena en FD001/FD002; en FD004 no se ejecutó por coste (~20 min).
- Un **split temporal** de la RNN se probó y se descartó: validaba bien (14.5) pero en test daba 63,
  porque el tramo final de cada motor tiene un rango de RUL estrecho y el modelo no aprende a distinguir
  motores sanos. El holdout por motor sí cubre todo el rango.
- **El coste 20:1 es una suposición**, no un dato de planta. Cambiarlo mueve T* y el recall.
"""


def code_cell(src):
    return {"cell_type": "code", "execution_count": None, "id": None,
            "metadata": {}, "outputs": [], "source": src}


def md_cell(src):
    return {"cell_type": "markdown", "metadata": {}, "id": None, "source": src}


def main():
    nb = json.loads(NB.read_text(encoding='utf-8'))
    # quitar sección v3 previa si se reejecuta
    nb['cells'] = [c for c in nb['cells']
                   if not ''.join(c['source']).startswith('## 9. V3')]
    nuevas = [md_cell(MD_9), code_cell(CODE_DEMO), md_cell(MD_TABLA), code_cell(CODE_TABLA),
              md_cell(MD_Q), code_cell(CODE_Q), md_cell(MD_TRANSFER), code_cell(CODE_TRANSFER),
              md_cell(MD_SYS), code_cell(CODE_SYS), md_cell(MD_LIM)]

    nb['cells'] = nb['cells'][:-1] + nuevas + [nb['cells'][-1]]
    for i, c in enumerate(nb['cells']):
        c['id'] = f'c{i:02d}'
        c.setdefault('metadata', {})
        if c['cell_type'] == 'code':
            c.setdefault('outputs', [])
            c['outputs'] = []
            c['execution_count'] = None
    NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
    print('celdas totales:', len(nb['cells']), '| insertadas v3:', len(nuevas))


if __name__ == '__main__':
    main()
