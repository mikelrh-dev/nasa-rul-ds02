"""Fases 0-2 sobre un dataset FDxxx: OOF por motor, umbral por coste, quantiles.

Uso:  python scripts/v3_run.py --fd FD001 --folds 5 --seeds 3 --rf
      python scripts/v3_run.py --fd FD002 --folds 3 --seeds 1
"""
import argparse
import json
import pathlib
import time

import numpy as np
import v3_core as c
from lightgbm import LGBMRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

OUT = pathlib.Path(__file__).resolve().parents[1] / 'models' / 'v3_results.json'
SEEDS = (42, 7, 2024)


def lgb_maker(seed):
    return LGBMRegressor(n_estimators=300, learning_rate=0.05, max_depth=8,
                         random_state=seed, n_jobs=-1, verbose=-1)


def rf_maker(seed):
    return RandomForestRegressor(n_estimators=200, max_depth=12, max_features='sqrt',
                                 random_state=seed, n_jobs=-1)


def lr_maker(seed):
    return make_pipeline(StandardScaler(), LinearRegression())


def run(fd, folds, n_seeds, with_rf, feats_list, cfn=20):
    tr, te, rul = c.load_fd(fd)
    _, f_all_tr = c.add_health_features(tr)
    _, f_all_te = c.add_health_features(te)

    variants = {}
    if 'health' in feats_list:
        variants['health'] = (f_all_tr, f_all_te)
    if 'raw' in feats_list:
        variants['raw'] = (tr[c.SENSORS], te[c.SENSORS])

    out = {'fd': fd, 'n_train_engines': int(tr.engine_id.nunique()),
           'n_test_engines': int(rul.engine_id.nunique()), 'models': {}}
    seeds = SEEDS[:n_seeds]

    for fname, (ftr, fte) in variants.items():
        X, y, m = c.make_windows(tr, ftr)
        Xt, mt = c.test_last(te, fte, rul)
        groups = m.engine_id.values
        print(f'\n== {fd} / features={fname}  X={X.shape} test={Xt.shape}')

        makers = [('LightGBM', lgb_maker), ('LinearRegression', lr_maker)]
        if with_rf:
            makers.append(('RandomForest', rf_maker))

        for name, maker in makers:
            t0 = time.time()
            oofs = c.oof_predict(X, y, groups, maker, folds=folds, seeds=seeds)
            rm = [c.rmse(y, oofs[s]) for s in seeds]
            mt_ = [c.mae(y, oofs[s]) for s in seeds]
            model = maker(seeds[0])
            model.fit(X.reshape(len(X), -1), y)
            pred = model.predict(Xt.reshape(len(Xt), -1))
            oof0 = oofs[seeds[0]]
            cal = c.calibrate_threshold(oof0, y, cfn=cfn)
            rec = {
                'features': fname, 'modelo': name, 'n_seeds': len(seeds), 'folds': folds,
                'rmse_oof_mean': round(float(np.mean(rm)), 2),
                'rmse_oof_std': round(float(np.std(rm)), 2),
                'mae_oof_mean': round(float(np.mean(mt_)), 2),
                'rmse_test': round(c.rmse(mt.RUL_real, pred), 2),
                'mae_test': round(c.mae(mt.RUL_real, pred), 2),
                'sesgo': round(float(np.mean(pred - mt.RUL_real)), 2),
                'T': cal['T'], 'alarma_T': c.eval_alarm(pred, mt.RUL_real.values, cal['T'], cfn=cfn),
                'alarma_15': c.eval_alarm(pred, mt.RUL_real.values, 15.0, cfn=cfn),
                'segundos': round(time.time() - t0, 1),
            }
            print(f"  {name:16s} OOF {rec['rmse_oof_mean']:.2f}±{rec['rmse_oof_std']:.2f} | "
                  f"test {rec['rmse_test']:.2f} / MAE {rec['mae_test']:.2f} | "
                  f"T*={cal['T']:.1f} recall {rec['alarma_T']['recall']:.0f}% "
                  f"({rec['alarma_T']['alarmas']} alarmas) | {rec['segundos']:.0f}s")
            out['models'][f'{fname}/{name}'] = rec

            if name == 'LightGBM' and fname == 'health':
                # Fase 3: incertidumbre con quantile
                q = {}
                for alpha in (0.1, 0.9):
                    mq = LGBMRegressor(objective='quantile', alpha=alpha, n_estimators=300,
                                       learning_rate=0.05, max_depth=8, random_state=42,
                                       n_jobs=-1, verbose=-1)
                    mq.fit(X.reshape(len(X), -1), y)
                    q[alpha] = mq.predict(Xt.reshape(len(Xt), -1))
                lo, hi = q[0.1], q[0.9]
                real = mt.RUL_real.values
                cover = float(np.mean((real >= lo) & (real <= hi)))
                alarma_q = hi < 30
                pos = real < 15
                tp = int((alarma_q & pos).sum())
                fp = int((alarma_q & ~pos).sum())
                fn = int((~alarma_q & pos).sum())
                out['quantile'] = {
                    'cobertura_80': round(100 * cover, 1),
                    'ancho_medio': round(float(np.mean(hi - lo)), 1),
                    'alarma_q90_lt_30': {'alarmas': int(alarma_q.sum()), 'tp': tp, 'fp': fp, 'fn': fn,
                                         'recall': round(100 * tp / max(1, tp + fn), 1),
                                         'precision': round(100 * tp / max(1, tp + fp), 1),
                                         'coste': int(cfn * fn + fp)},
                    'alarma_media_T': rec['alarma_T'],
                }
                print(f"  quantile: cobertura {out['quantile']['cobertura_80']}% "
                      f"| q90<30 -> recall {out['quantile']['alarma_q90_lt_30']['recall']}% "
                      f"({out['quantile']['alarma_q90_lt_30']['alarmas']} alarmas)")

    # guardar/mergear
    data = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    data[fd] = out
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    print('\nguardado en', OUT)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--fd', default='FD001')
    ap.add_argument('--folds', type=int, default=5)
    ap.add_argument('--seeds', type=int, default=3)
    ap.add_argument('--rf', action='store_true')
    ap.add_argument('--features', default='health,raw')
    a = ap.parse_args()
    run(a.fd, a.folds, a.seeds, a.rf, a.features.split(','))
