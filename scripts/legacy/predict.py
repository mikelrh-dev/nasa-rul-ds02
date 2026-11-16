"""Inferencia v3: RUL + incertidumbre + alarma por coste + drift.

No es una API web: es el módulo de inferencia que usaría un servicio.

    python scripts/predict.py --fd FD001 --engine 12 --cut 80
    python scripts/predict.py --fd FD001 --report
"""
import argparse
import json
import os
import pathlib

import joblib
import numpy as np
import pandas as pd

from ds02_rul.persistence import verify_artifact_sha256  # noqa: E402

import v3_core as c

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'models' / 'v3_bundle.joblib'
POLICY = ROOT / 'models' / 'alarm_policy.json'
PSI_REF = ROOT / 'models' / 'psi_reference.json'

COSTE_FALLO = 20.0     # coste relativo de un fallo no detectado
COSTE_INSPECCION = 1.0  # coste relativo de una inspección


def _load():
    """Carga el bundle FD001; hoy fuera de servicio (archivado y no versionado)."""
    if not os.path.exists(str(BUNDLE)):
        raise RuntimeError(
            "FD001 v3 bundle no esta en models/ (archivado en "
            "archive/fd001-legacy-20261107/ y no versionado). El repo sirve DS02 "
            "en models/ensemble.joblib; este CLI queda fuera de servicio."
        )
    # SEC-JOBLIB-01: checksum verificado ANTES de deserializar.
    verify_artifact_sha256(str(BUNDLE), "v3_bundle_sha256")
    b = joblib.load(BUNDLE)
    b['policy'] = json.loads(POLICY.read_text(encoding='utf-8'))
    b['psi'] = json.loads(PSI_REF.read_text(encoding='utf-8'))
    return b


def out_of_range(history):
    """Porcentaje de valores del motor fuera del rango [p01, p99] de train."""
    b = _load()
    df = history.sort_values('cycle').tail(30)
    out = {}
    for s in c.SENSORS:
        ref = b['psi']['sensors'][s]
        if ref.get('skip'):
            continue
        lo, hi = ref['p01'], ref['p99']
        out[s] = round(100 * float(np.mean((df[s].values < lo) | (df[s].values > hi))), 1)
    peor = max(out, key=out.get)
    return {'pct_fuera': out, 'peor_sensor': peor, 'peor_pct': out[peor],
            'alerta': out[peor] > 20}


def predict(history, bundle=None):
    """history: DataFrame con columnas del dataset (solo sensores + cycle).

    Devuelve RUL puntual, intervalo 80 %, alarma y coste esperado de la decisión.
    """
    b = bundle or _load()
    df = history.copy()
    if 'engine_id' not in df.columns:
        df['engine_id'] = 0
    df = df.sort_values('cycle')
    _, feats = c.add_health_features(df)
    if len(feats) < b['window']:
        raise ValueError(f'historial insuficiente: {len(feats)} < {b["window"]} ciclos')
    x = feats[b['features']].values[-b['window']:].reshape(1, -1)

    rul = float(b['model'].predict(x)[0])
    lo = float(b['q10'].predict(x)[0])
    hi = float(b['q90'].predict(x)[0])
    T_crit, T_warn = b['policy']['T_crit'], b['policy']['T_warn']

    if rul < T_crit:
        alerta = 'ROJO'
    elif rul < T_warn:
        alerta = 'AMARILLO'
    else:
        alerta = 'VERDE'

    # probabilidad heurística de fallo inminente a partir del cuantil alto
    p_fallo = 0.9 if hi < T_crit else (0.5 if rul < T_crit else (0.1 if lo < T_crit else 0.02))
    coste = min(COSTE_INSPECCION, p_fallo * COSTE_FALLO)
    if alerta == 'ROJO':
        coste = COSTE_INSPECCION

    return {'version': b['version'], 'rul': round(rul, 1), 'q10': round(lo, 1), 'q90': round(hi, 1),
            'alerta': alerta, 'p_fallo': round(p_fallo, 2), 'coste_esperado': round(coste, 2),
            'T_crit': T_crit, 'T_warn': T_warn}


def report(fd='FD001'):
    """Informe batch FD001: RUL, alerta y coste por motor; escribe el CSV."""
    b = _load()
    tr, te, rul = c.load_fd(fd)
    rows = []
    for eid, g in te.groupby('engine_id', sort=True):
        r = predict(g, b)
        rows.append({'engine_id': int(eid), 'cycle': int(g['cycle'].max()),
                     'RUL_real': float(rul.loc[rul.engine_id == eid, 'RUL'].iloc[0]),
                     'RUL_pred': r['rul'], 'q10': r['q10'], 'q90': r['q90'],
                     'alerta': r['alerta'], 'coste_esperado': r['coste_esperado']})
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / 'models' / 'informe_batch.csv', index=False)
    real = df['RUL_real'].values
    pos = real < 15
    al = (df['alerta'] == 'ROJO').values
    tp = int((al & pos).sum())
    return df, {'n': len(df), 'ROJO': int(al.sum()),
                'rojo_reales': int(pos.sum()), 'tp': tp,
                'recall': round(100 * tp / max(1, int(pos.sum())), 1),
                'precision': round(100 * tp / max(1, int(al.sum())), 1)}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--fd', default='FD001')
    ap.add_argument('--engine', type=int)
    ap.add_argument('--cut', type=int, default=0)
    ap.add_argument('--report', action='store_true')
    a = ap.parse_args()

    if not os.path.exists(str(BUNDLE)):
        raise SystemExit(
            "FD001 v3 bundle no esta en models/ (archivado en "
            "archive/fd001-legacy-20261107/ y no versionado). El repo sirve DS02 "
            "en models/ensemble.joblib; este CLI queda fuera de servicio."
        )

    if a.report:
        df, m = report(a.fd)
        print('informe batch:', m)
        print(df.head().to_string(index=False))
    else:
        _, te, _ = c.load_fd(a.fd)
        g = te[te.engine_id == a.engine]
        if a.cut:
            g = g[g.cycle <= a.cut]
        print('prediccion:', predict(g))
        print('fuera de rango:', out_of_range(g))
