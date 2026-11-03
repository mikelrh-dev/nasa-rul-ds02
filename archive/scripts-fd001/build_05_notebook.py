"""Genera notebooks/05_ensemble_adaptado.ipynb (cáscara de reporte, estilo NB04).

El entrenamiento pesado vive en `track_clase/train_ensemble_adaptado.py`; el
notebook solo lee `resultados/comparativa_bundle_c.csv`,
`resultados/bundle_c_por_motor.csv` y el PNG, e imprime el veredicto de la
puerta D11. Sin re-entrenar en el notebook.
"""

import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.cells = [
    nbf.v4.new_markdown_cell(
        "# 05 — Bundle C: ensemble sobre base adaptada (grano ventana)\n"
        "\n"
        "Mismo protocolo que B sobre ventanas adaptadas (MAR T30 + ffill con "
        "medianas de fit-units, contrato 93 intacto, sin `fase_vuelo`). Grano "
        "**ventana**: la tabla SAA de filas (SVM 9.06, MLP 7.70) va aparte — "
        "prohibido el ranking mixto. La decisión se toma contra la puerta D11 "
        "en las mismas 6.196 ventanas test."
    ),
    nbf.v4.new_code_cell(
        "import pandas as pd\n"
        "comp = pd.read_csv('../resultados/comparativa_bundle_c.csv')\n"
        "print(comp.to_string(index=False))"
    ),
    nbf.v4.new_markdown_cell(
        "## Real vs predicho + análisis por motor (bundle C, test)"
    ),
    nbf.v4.new_code_cell(
        "from IPython.display import Image, display\n"
        "import pandas as pd\n"
        "pm = pd.read_csv('../resultados/bundle_c_por_motor.csv')\n"
        "print(pm.to_string(index=False))\n"
        "print()\n"
        "display(Image('../resultados/real_vs_predicho_bundle_c.png'))\n"
        "print()\n"
        "print('QUÉ VEO: el patrón por motor debe replicar al de B (U14 concentra el error).')\n"
        "print('CONCLUSIÓN: si se replica, el ventaneo honesto funciona también para el ensemble.')"
    ),
    nbf.v4.new_markdown_cell(
        "## Cierre — veredicto de la puerta D11\n"
        "\n"
        "Se adopta C solo si `RMSE_C <= 4.251` **y** `NASA_C <= 2305.1` "
        "(B-histórico, mismas ventanas). Si no, C queda como experimento y B "
        "sigue en producción. SIN re-freeze en este change (requiere otra "
        "autorización)."
    ),
    nbf.v4.new_code_cell(
        "import pandas as pd\n"
        "comp = pd.read_csv('../resultados/comparativa_bundle_c.csv')\n"
        "c = comp.loc[comp['Modelo'].str.startswith('Híbrido-C')].iloc[0]\n"
        "ok_rmse = c['RMSE'] <= 4.251\n"
        "ok_nasa = c['NASA_Score'] <= 2305.1\n"
        "print(f\"bundle C: RMSE {c['RMSE']:.3f} (<=4.251? {ok_rmse}) | \"\n"
        "      f\"NASA {c['NASA_Score']:.1f} (<=2305.1? {ok_nasa})\")\n"
        "print('ADOPTAR (pendiente re-freeze autorizado)' if ok_rmse and ok_nasa\n"
        "      else 'C queda como experimento, B sigue en producción')"
    ),
    nbf.v4.new_markdown_cell(
        "## Multiseed (7, 123) — media ± desv\n"
        "\n"
        "B publica sus titulares como media ± desv sobre [42, 7, 123]. Para comparar "
        "en la misma liga, este bloque repite el protocolo C en las seeds 7 y 123 "
        "reutilizando beta=1.00 (igual que el notebook 02 reutiliza BETA). Sin "
        "ablación: el diseño ya está decidido."
    ),
    nbf.v4.new_code_cell(
        "import sys; sys.path.insert(0, '..')\n"
        "import numpy as np\n"
        "import pandas as pd\n"
        "from track_clase.train_ensemble_adaptado import (\n"
        "    construir_raw_adaptado, FIT_UNITS, HOLDOUT_UNITS, TEST_UNITS)\n"
        "from ds02_rul import HybridStackingEnsemble\n"
        "from ds02_rul.metrics import evaluate_predictions\n"
        "from ds02_rul.pipeline import run_seed\n"
        "from ds02_rul.stacking import fit_meta_learners\n"
        "raw = construir_raw_adaptado()\n"
        "filas = []\n"
        "for seed in (7, 123):\n"
        "    out = run_seed(raw, seed=seed, fit_units=FIT_UNITS,\n"
        "                   holdout_units=HOLDOUT_UNITS, test_units=TEST_UNITS,\n"
        "                   window=50, step_train=3, step_test=2, epochs=22)\n"
        "    Z = np.column_stack([out['p_lstm_hold'], out['p_lgb_hold']])\n"
        "    ridge_s, lgbm_s = fit_meta_learners(\n"
        "        Z, out['dev']['y'][out['hold_idx']], seed=seed)\n"
        "    ens = HybridStackingEnsemble(\n"
        "        bilstm_model=out['bilstm'], lgb_standalone=out['lgbm'],\n"
        "        ridge_meta=ridge_s, lgb_meta=lgbm_s,\n"
        "        residualizer=out['prep']['residualizer'],\n"
        "        scaler=out['prep']['scaler'], scaler_w=out['prep']['scaler_w'],\n"
        "        n_op=4, window_size=50, beta=1.00, ema_span=5)\n"
        "    t = out['test']\n"
        "    pe = ens.predict(t['X_raw'], t['meta']['cycle'].values,\n"
        "                     t['meta']['unit'].values)\n"
        "    m = evaluate_predictions(t['y'], pe, f'Híbrido-C seed {seed}')\n"
        "    filas.append({'seed': seed, 'RMSE': m['RMSE'], 'MAE': m['MAE'],\n"
        "                  'R2': m['R2'], 'NASA_Score': m['NASA_Score']})\n"
        "    print(f\"seed {seed}: RMSE {m['RMSE']:.3f} | NASA {m['NASA_Score']:.1f}\")\n"
        "ms = pd.DataFrame(filas)\n"
        "ms.to_csv('../resultados/bundle_c_multiseed.csv', index=False)\n"
        "print(ms.to_string(index=False))"
    ),
    nbf.v4.new_code_cell(
        "import numpy as np\n"
        "import pandas as pd\n"
        "base = pd.read_csv('../resultados/comparativa_bundle_c.csv')\n"
        "ms = pd.read_csv('../resultados/bundle_c_multiseed.csv')\n"
        "r42 = base.loc[base['Modelo'].str.startswith('Híbrido-C')].iloc[0]\n"
        "rmse = [float(r42['RMSE'])] + ms['RMSE'].tolist()\n"
        "nasa = [float(r42['NASA_Score'])] + ms['NASA_Score'].tolist()\n"
        "print(f\"C (42,7,123): RMSE {np.mean(rmse):.3f} +- {np.std(rmse, ddof=1):.3f} | \"\n"
        "      f\"NASA {np.mean(nasa):.1f} +- {np.std(nasa, ddof=1):.1f}\")\n"
        "print('B histórico: RMSE 4.251 | NASA 2305.1 (media multiseed congelada)')\n"
        "print('Veredicto: ' + ('ADOPTAR (pendiente re-freeze autorizado)'\n"
        "      if np.mean(rmse) <= 4.251 and np.mean(nasa) <= 2305.1\n"
        "      else 'C queda como experimento, B sigue en producción'))"
    ),
]

with open("notebooks/05_ensemble_adaptado.ipynb", "w", encoding="utf-8") as fh:
    nbf.write(nb, fh)
print("notebooks/05_ensemble_adaptado.ipynb escrito")
