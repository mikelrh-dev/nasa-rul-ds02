"""Fase 5: bundle de producción (modelo + quantiles + política + drift).

Entrena el LGBM definitivo con features de salud sobre todo train y guarda:
  models/v3_bundle.joblib      -> modelo, q10/q90, features, ventana, versión
  models/alarm_policy.json     -> umbrales por coste y métricas medidas
  models/psi_reference.json    -> deciles de referencia por sensor (drift)
  models/v3_quantile_FD001.csv -> q10/q50/q90 en test (para el gráfico del notebook)
"""
import json
import pathlib

import joblib
import numpy as np
import pandas as pd

import v3_core as c
from lightgbm import LGBMRegressor

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERSION = 'v3.0.0'


def main():
    tr, te, rul = c.load_fd('FD001')
    _, f_tr = c.add_health_features(tr)
    _, f_te = c.add_health_features(te)
    X, y, _ = c.make_windows(tr, f_tr)
    Xt, mt = c.test_last(te, f_te, rul)
    F = list(f_tr.columns)
    Xf, Xtf = X.reshape(len(X), -1), Xt.reshape(len(Xt), -1)
    real = mt['RUL_real'].values

    def mk(alpha=None):
        kw = {'objective': 'quantile', 'alpha': alpha} if alpha is not None else {}
        return LGBMRegressor(n_estimators=300, learning_rate=0.05, max_depth=8,
                             random_state=42, n_jobs=-1, verbose=-1, **kw)

    model, q10, q90 = mk(), mk(0.1), mk(0.9)
    for m in (model, q10, q90):
        m.fit(Xf, y)
    p, lo, hi = model.predict(Xtf), q10.predict(Xtf), q90.predict(Xtf)

    res = json.loads((ROOT / 'models' / 'v3_results.json').read_text(encoding='utf-8'))
    lgb = next(v for k, v in res['FD001']['models'].items()
               if k.endswith('LightGBM') and v['features'] == 'health')
    T_crit = lgb['T']
    T_warn = round(T_crit + 6.0, 1)

    # --- comparación de reglas de alarma (cuantiles vs media) ---
    pos = real < 15
    reglas = {
        'media < T*': p < T_crit,
        'media < 15 (fijo)': p < 15,
        'q90 < 30': hi < 30,
        'q10 < 15': lo < 15,
        'q10 < T*': lo < T_crit,
        'media < T* o q10 < 15': (p < T_crit) | (lo < 15),
    }
    reglas_met = {}
    for nombre, alarma in reglas.items():
        tp = int((alarma & pos).sum())
        fp = int((alarma & ~pos).sum())
        fn = int((~alarma & pos).sum())
        reglas_met[nombre] = {'alarmas': int(alarma.sum()), 'tp': tp, 'fp': fp, 'fn': fn,
                              'recall': round(100 * tp / max(1, tp + fn), 1),
                              'precision': round(100 * tp / max(1, tp + fp), 1),
                              'coste': int(20 * fn + fp)}
    elegida = min(reglas_met, key=lambda k: reglas_met[k]['coste'])

    cobertura = float(np.mean((real >= lo) & (real <= hi)))
    pd.DataFrame({'engine_id': mt['engine_id'], 'RUL_real': real, 'pred': p,
                  'q10': lo, 'q90': hi, 'alerta': ['ROJO' if v < T_crit else
                                                   ('AMARILLO' if v < T_warn else 'VERDE') for v in p]}
                 ).to_csv(ROOT / 'models' / 'v3_quantile_FD001.csv', index=False)

    bundle = {'version': VERSION, 'dataset': 'FD001', 'window': c.WINDOW, 'features': F,
              'model': model, 'q10': q10, 'q90': q90, 'T_crit': T_crit, 'T_warn': T_warn,
              'regla_alarma': elegida,
              'rmse_test': c.rmse(real, p), 'mae_test': c.mae(real, p)}
    joblib.dump(bundle, ROOT / 'models' / 'v3_bundle.joblib')

    policy = {
        'version': VERSION, 'modelo': 'LightGBM + features de salud',
        'dataset_calibracion': 'FD001', 'metodo': 'coste FN*20 + FP*1 sobre OOF por motor',
        'T_crit': T_crit, 'T_warn': T_warn, 'evento': 'RUL real < 15',
        'regla_elegida': elegida, 'reglas': reglas_met,
        'metricas_test': lgb['alarma_T'], 'metricas_fijo_15': lgb['alarma_15'],
        'cobertura_80': round(100 * cobertura, 1),
        'rmse_test': lgb['rmse_test'], 'mae_test': lgb['mae_test'],
    }
    (ROOT / 'models' / 'alarm_policy.json').write_text(
        json.dumps(policy, ensure_ascii=False, indent=1), encoding='utf-8')

    # referencia de drift: bordes (deciles únicos) + proporciones reales por bin
    ref = {}
    for s in c.SENSORS:
        vals = tr[s].values
        qs = np.unique(np.quantile(vals, np.linspace(0, 1, 11)))
        if len(qs) < 4:  # sensor casi constante: PSI no es informativo
            ref[s] = {'skip': True}
            continue
        edges = qs[1:-1]
        counts, _ = np.histogram(vals, bins=np.concatenate([[-np.inf], edges, [np.inf]]))
        ref[s] = {'edges': [float(e) for e in edges],
                  'props': [float(p) for p in counts / counts.sum()],
                  'p01': float(np.quantile(vals, 0.01)),
                  'p99': float(np.quantile(vals, 0.99))}
    (ROOT / 'models' / 'psi_reference.json').write_text(
        json.dumps({'version': VERSION, 'sensors': ref}, ensure_ascii=False), encoding='utf-8')

    print(f'bundle {VERSION} | RMSE test {bundle["rmse_test"]:.2f} | T_crit={T_crit} T_warn={T_warn}')
    print('cobertura 80%:', round(100 * cobertura, 1))
    for k, v in reglas_met.items():
        print(f'  {k:28s} recall {v["recall"]:5.1f}%  prec {v["precision"]:5.1f}%  '
              f'{v["alarmas"]:3d} alarmas  coste {v["coste"]}')
    print('regla elegida:', elegida)


if __name__ == '__main__':
    main()
