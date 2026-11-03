"""Anade a 05 la celda 'el meta por dentro' (alpha + pesos del RidgeCV).

El meta del bundle C versionado se lee con joblib (bilstm_model va desprendido,
asi que no hace falta TF). La celda se ejecuta aqui mismo para guardar sus
outputs reales; el notebook queda listo para defensa sin reentrenar nada.
"""
import contextlib
import io
import json
import os
import pathlib

NB = pathlib.Path('notebooks/05_ensemble_adaptado.ipynb')
ROOT = pathlib.Path('.').resolve()

MD = """### El meta por dentro (no es una caja negra)

El meta no se queda en "un modelo que mezcla": tiene dos piezas y una decision
que se puede leer.

1. **RidgeCV** sobre `[p_lstm, p_lgb]`. Prueba una rejilla de `alpha` (fuerza de
   la regularizacion) y se queda con la que mejor generaliza en el propio
   holdout. Ridge y no regresion lineal normal porque dos predictores muy
   correlacionados (las dos ramas ven el mismo motor) desestabilizan los pesos.
2. **LightGBM** sobre el mismo diseno. Captura lo no lineal: cuando una rama se
   desvia mucho, el arbol corrige; el Ridge promedia.
3. **Reconciliacion fija 50/50**: `p_meta = 0.5·ridge + 0.5·lgbm`. No se aprende
   un tercer peso: con 2.535 filas de holdout un tercer ajuste solo anadiria
   varianza.

Lo que sigue es el meta **del bundle C versionado**, leido del artefacto (no
reentrenado): su `alpha`, sus pesos y cuanto confia en cada rama."""

CELL = '''import joblib
import numpy as np
_meta = joblib.load('../track_clase/models/ensemble.joblib')
_ridge = _meta.ridge_meta
_w = np.asarray(_ridge.coef_, dtype=float).ravel()
print('features del meta :', int(_ridge.n_features_in_), '(2 = [p_lstm, p_lgb]; sin reloj)')
print('alpha elegido     :', float(_ridge.alpha_))
print('peso -> p_lstm    : %+.3f' % _w[0])
print('peso -> p_lgb     : %+.3f' % _w[1])
print('intercepto        : %+.2f ciclos' % float(np.ravel(_ridge.intercept_)[0]))
_total = float(np.abs(_w).sum())
print('reparto del Ridge : p_lstm %.0f%% | p_lgb %.0f%%' % (100 * abs(_w[0]) / _total,
                                                        100 * abs(_w[1]) / _total))
print()
print('meta final        : 0.5 * Ridge + 0.5 * LightGBM (meta_predict)')
print('beta              : %.2f  (1.00 = el meta sustituye a la red)' % float(_meta.beta))
print('EMA               : span %d, causal por motor' % int(_meta.ema_span))
print()
print('COMO LEERLO: pesos que suman ~1 con intercepto pequeno = el meta')
print('reparte la prediccion entre las dos ramas, no anade un nivel propio.')
print('Un intercepto grande seria la senal de que esta aprendiendo un prior')
print('de RUL en vez de reconciliar (el fallo medido en el diseno OOF-pooled).')'''


def read_text(p):
    return p.read_bytes().decode('utf-8', 'replace')


nb = json.loads(NB.read_text(encoding='utf-8'))
cells = nb['cells']

# Idempotencia.
cells = [c for c in cells
         if not (c['cell_type'] == 'markdown'
                 and 'El meta por dentro' in ''.join(c.get('source', [])))]
cells = [c for c in cells
         if not (c['cell_type'] == 'code'
                 and "'../track_clase/models/ensemble.joblib'" in ''.join(c.get('source', []))
                 and '_ridge' in ''.join(c.get('source', [])))]

# Punto de insercion: tras el markdown 'Que acaba de pasar'.
anchor = next(i for i, c in enumerate(cells)
              if c['cell_type'] == 'markdown'
              and 'Qué acaba de pasar' in ''.join(c.get('source', [])))

# Ejecuta la celda con cwd=notebooks para capturar stdout real.
ns = {'__name__': '__main__'}
cwd = os.getcwd()
os.chdir(ROOT / 'notebooks')
buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        exec(compile(CELL, 'meta_cell', 'exec'), ns)
finally:
    os.chdir(cwd)
out = buf.getvalue()
print(out)

new = [
    {'cell_type': 'markdown', 'metadata': {}, 'source': [MD]},
    {'cell_type': 'code', 'execution_count': 6, 'metadata': {},
     'outputs': [{'name': 'stdout', 'output_type': 'stream',
                  'text': out.splitlines(keepends=True)}],
     'source': [CELL]},
]
for k, cell in enumerate(new):
    cells.insert(anchor + 1 + k, cell)

nb['cells'] = cells
NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

code = [c for c in cells if c['cell_type'] == 'code']
print('05: %d celdas | %d de codigo | %d con output | %d imagenes'
      % (len(cells), len(code),
         sum(1 for c in code if c.get('outputs')),
         sum(1 for c in code for o in c.get('outputs', []) if 'image/png' in o.get('data', {}))))
