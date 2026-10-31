"""Presentacion estilo clase para los notebooks DS02.

Solo formato y dibujo: ninguna funcion entrena ni cambia metricas.
Extraido verbatim de la celda de utilidades de `01_datos_y_bases.ipynb`
para que los 3 cuadernos hagan `from ds02_rul.viz import *` en una linea,
como en clase (`from sklearn... import ...`).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .metrics import evaluate_predictions

try:
    from IPython.display import display
except ImportError:  # pragma: no cover
    def display(x):  # fallback fuera del notebook
        print(x)

# --- utilidades de presentación: importaciones ---
# `plt` se importa aquí, no en la celda de persistencia: las funciones
# de abajo lo usan y esa celda se ejecuta después de todos los gráficos.

# --- paleta y etiquetas -----------------------------------------------------
# Un color por modelo, el mismo en todos los gráficos. Así el lector reconoce
# la serie sin volver a leer la leyenda.
PALETA = {
    'LightGBM solo': '#8C8C8C',
    'BiLSTM solo': '#4C72B0',
    'Híbrido + EMA5': '#1FA098',
}
COLORES_ABLACION = {'LGBM': '#8C8C8C', 'BiLSTM': '#4C72B0', 'BiLSTM+EMA': '#1FA098'}
NOMBRE_CORTO = {'LightGBM solo': 'LightGBM', 'BiLSTM solo': 'BiLSTM'}


def nombre_corto(modelo):
    """Etiqueta corta para los ejes; no toca el nombre que usan las tablas."""
    return NOMBRE_CORTO.get(modelo, modelo)


# --- tablas -----------------------------------------------------------------
def tabla_modelos(summary, metricas=('RMSE', 'MAE', 'R2', 'NASA_Score')):
    """Una fila por modelo con 'media ± desviación' en cada métrica.

    Ordena por RMSE medio y devuelve strings: es una tabla para leer, no para
    volver a calcular. Los decimales se eligen por métrica para que el ruido de
    las últimas cifras no se confunda con una diferencia.
    """
    orden = summary.sort_values('RMSE_mean')
    filas = []
    for _, fila in orden.iterrows():
        registro = {'Modelo': fila['Modelo']}
        for metrica in metricas:
            decimales = {'R2': 4, 'NASA_Score': 1}.get(metrica, 3)
            registro[metrica] = (f"{fila[f'{metrica}_mean']:.{decimales}f}"
                                 f" ± {fila[f'{metrica}_std']:.{decimales}f}")
        filas.append(registro)
    return pd.DataFrame(filas)


def comparar_con_base(summary, base, metricas=('RMSE', 'MAE')):
    """Cuánto mejora (o empeora) cada modelo frente a la base indicada.

    El delta es la diferencia directa de medias: negativo en RMSE/MAE significa
    que se equivoca menos. La columna 'mejora %' ya viene en positivo cuando
    mejora, para poder decirla en voz alta sin cambiar de signo.
    """
    fila_base = summary.loc[summary['Modelo'] == base].iloc[0]
    filas = []
    for _, fila in summary.sort_values('RMSE_mean').iterrows():
        registro = {'Modelo': fila['Modelo'], 'frente a': base}
        for metrica in metricas:
            delta = fila[f'{metrica}_mean'] - fila_base[f'{metrica}_mean']
            registro[f'delta {metrica}'] = round(float(delta), 3)
            registro[f'mejora {metrica} %'] = round(-100 * float(delta) / float(fila_base[f'{metrica}_mean']), 1)
        filas.append(registro)
    return pd.DataFrame(filas)


def tabla_por_motor(y_real, y_pred, unidades):
    """RMSE, MAE y sesgo de cada motor de test, por separado.

    Un promedio bueno puede esconder un motor malo: si un motor concentra el
    error, el número global no describe al modelo.
    """
    y_real = np.asarray(y_real, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    unidades = np.asarray(unidades)
    filas = []
    for unidad in sorted(np.unique(unidades).tolist()):
        mask = unidades == unidad
        error = y_pred[mask] - y_real[mask]
        filas.append({
            'Motor': int(unidad),
            'Ventanas': int(mask.sum()),
            'RMSE': round(float(np.sqrt(np.mean(error ** 2))), 3),
            'MAE': round(float(np.mean(np.abs(error))), 3),
            'Sesgo': round(float(error.mean()), 3),
        })
    return pd.DataFrame(filas)


# --- gráficos ---------------------------------------------------------------
def barras_metricas(summary, metricas=('RMSE', 'MAE', 'R2', 'NASA_Score'), figsize=(11, 7)):
    """Barras horizontales de la media, con la desviación entre semillas como error.

    La rayita es la desviación: si dos barras se diferencian menos que eso, es
    un empate y no hay que elegir por el tercer decimal.
    """
    orden = summary.sort_values('RMSE_mean')
    etiquetas = [nombre_corto(m) for m in orden['Modelo']]
    colores = [PALETA.get(m, '#999999') for m in orden['Modelo']]

    fig, axes = plt.subplots(2, 2, figsize=figsize)
    for ax, metrica in zip(axes.ravel(), metricas):
        ax.barh(etiquetas, orden[f'{metrica}_mean'].values,
                xerr=orden[f'{metrica}_std'].values, color=colores, capsize=5)
        ax.set_title(metrica)
        ax.set_xlabel('media ± desviación entre semillas')
        ax.grid(True, axis='x', ls='--', alpha=0.5)
        ax.invert_yaxis()
    fig.suptitle('Comparación de modelos sobre los motores 11/14/15', y=1.01)
    plt.tight_layout()
    plt.show()


def dispersion_por_semilla(seed_rows, metrica='RMSE', figsize=(9, 4)):
    """Un punto por semilla y una línea con la media.

    Si los puntos se abren mucho, el promedio no alcanza: hay que decir cuánto
    varía el modelo antes de declararlo ganador.
    """
    df = pd.DataFrame(seed_rows)
    modelos = [m for m in PALETA if m in set(df['Modelo'])]
    fig, ax = plt.subplots(figsize=figsize)
    for i, modelo in enumerate(modelos):
        valores = df.loc[df['Modelo'] == modelo, metrica].values
        if len(valores) == 0:
            continue
        x = np.full(len(valores), i) + np.linspace(-0.06, 0.06, len(valores))
        ax.scatter(x, valores, s=80, color=PALETA[modelo], zorder=3)
        ax.hlines(valores.mean(), i - 0.22, i + 0.22, color='black', lw=1.8)
        ax.annotate(f'{valores.mean():.3f}', (i, valores.mean()),
                    textcoords='offset points', xytext=(0, 12), ha='center')
    ax.set_xticks(range(len(modelos)))
    ax.set_xticklabels([nombre_corto(m) for m in modelos])
    ax.set_ylabel(metrica)
    ax.set_title(f'{metrica} por semilla — cada punto es una semilla, la línea es la media')
    ax.grid(True, axis='y', ls='--', alpha=0.5)
    plt.tight_layout()
    plt.show()


def barras_ablacion(abl, metrica='RMSE', figsize=(11, 4.5)):
    """Barras agrupadas: una variante de la ablación por grupo, un modelo por barra.

    Responde una sola pregunta: cuánto cambia la métrica al quitar el contador
    de ciclos o al usar la línea base por motor.
    """
    tabla = abl.pivot(index='variant', columns='model', values=metrica)
    modelos = list(tabla.columns)
    posiciones = np.arange(len(tabla.index))
    ancho = 0.8 / len(modelos)

    fig, ax = plt.subplots(figsize=figsize)
    for i, modelo in enumerate(modelos):
        ax.bar(posiciones + i * ancho - 0.4 + ancho / 2, tabla[modelo].values,
               width=ancho, label=modelo,
               color=COLORES_ABLACION.get(modelo, '#999999'))
    ax.set_xticks(posiciones)
    ax.set_xticklabels([v.replace('  ', ' ') for v in tabla.index], rotation=12, ha='right')
    ax.set_ylabel(metrica)
    ax.set_title(f'{metrica} por variante de la ablación (más corta es mejor)')
    ax.grid(True, axis='y', ls='--', alpha=0.5)
    ax.legend(title='modelo')
    plt.tight_layout()
    plt.show()
    return tabla


def real_vs_predicho(y_real, y_pred, titulo, figsize=(6.5, 6)):
    """Dispersión predicción frente a realidad, con la diagonal identidad.

    Un modelo perfecto pone todos los puntos sobre la diagonal. Lo que importa
    no es el punto individual sino la forma de la nube: si se abre en abanico
    hacia la derecha, el error crece con la RUL.
    """
    y_real = np.asarray(y_real, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    error = y_pred - y_real
    rmse = float(np.sqrt(np.mean(error ** 2)))
    mae = float(np.mean(np.abs(error)))
    r2 = float(1 - np.sum(error ** 2) / np.sum((y_real - y_real.mean()) ** 2))
    limite = float(max(y_real.max(), y_pred.max()) * 1.05)

    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(y_real, y_pred, s=10, alpha=0.35, color='#1FA098', edgecolors='none')
    ax.plot([0, limite], [0, limite], 'k--', lw=1.4, label='predicción perfecta')
    ax.set_xlim(0, limite)
    ax.set_ylim(0, limite)
    ax.set_xlabel('RUL real (ciclos)')
    ax.set_ylabel('RUL predicha (ciclos)')
    ax.set_title(titulo)
    ax.text(0.03, 0.97, f'RMSE {rmse:.2f}\nMAE {mae:.2f}\nR² {r2:.3f}',
            transform=ax.transAxes, va='top',
            bbox=dict(boxstyle='round', fc='white', ec='#cccccc'))
    ax.grid(True, ls='--', alpha=0.4)
    ax.legend(loc='lower right')
    plt.tight_layout()
    plt.show()


def residuos(y_real, y_pred, titulo='Residuos', figsize=(9, 4)):
    """Error (predicho − real) frente a la predicción, con la banda de ±1 desviación.

    Si la nube está centrada en cero, el modelo no tiene sesgo global. Si se
    abre a un lado, el error depende del nivel de RUL.
    """
    y_real = np.asarray(y_real, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    residuo = y_pred - y_real

    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(y_pred, residuo, s=9, alpha=0.3, color='#4C72B0', edgecolors='none')
    ax.axhline(0, color='black', lw=1.2)
    ax.axhline(residuo.mean(), color='#C44E52', lw=1.3, ls='--',
               label=f'sesgo {residuo.mean():+.2f}')
    ax.fill_between([0, float(y_pred.max())], -residuo.std(), residuo.std(),
                    color='#4C72B0', alpha=0.10, label=f'±1 desv ({residuo.std():.2f})')
    ax.set_xlabel('RUL predicha (ciclos)')
    ax.set_ylabel('predicho − real')
    ax.set_title(titulo)
    ax.grid(True, ls='--', alpha=0.4)
    ax.legend(loc='upper right')
    plt.tight_layout()
    plt.show()


def error_por_tramo(y_real, y_pred, tramos=(0, 25, 50, 75, 100, 500), figsize=(9, 4)):
    """MAE en cada tramo de RUL real: dice dónde duele el error.

    Cada barra es un rango de RUL real. Si el MAE crece hacia la derecha, el
    modelo acierta cerca del fallo y se pierde cuando al motor le queda vida.
    """
    y_real = np.asarray(y_real, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    filas = []
    for bajo, alto in zip(tramos[:-1], tramos[1:]):
        mask = (y_real >= bajo) & (y_real < alto)
        if mask.sum() == 0:
            continue
        filas.append({
            'tramo de RUL': f'[{bajo}, {alto})',
            'ventanas': int(mask.sum()),
            'MAE': round(float(np.mean(np.abs(y_real[mask] - y_pred[mask]))), 3),
        })
    tabla = pd.DataFrame(filas)

    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(tabla['tramo de RUL'], tabla['MAE'], color='#1FA098')
    for i, valor in enumerate(tabla['MAE']):
        ax.annotate(f'{valor:.2f}', (i, valor), textcoords='offset points',
                    xytext=(0, 4), ha='center')
    ax.set_xlabel('RUL real (ciclos)')
    ax.set_ylabel('MAE del tramo')
    ax.set_title('¿Dónde falla el modelo? MAE por tramo de RUL real')
    ax.grid(True, axis='y', ls='--', alpha=0.5)
    plt.tight_layout()
    plt.show()
    return tabla


def curva_entrenamiento(historial, figsize=(8, 4)):
    """Pérdida de entrenamiento y de validación por época.

    Si la de validación deja de bajar mientras la de entrenamiento sigue
    cayendo, el modelo empieza a memorizar; el early stopping corta ahí.
    """
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(historial['loss'], marker='o', label='entrenamiento', color='#4C72B0')
    ax.plot(historial['val_loss'], marker='s', label='validación (motor 16)', color='#C44E52')
    mejor = int(np.argmin(historial['val_loss']))
    ax.scatter([mejor], [historial['val_loss'][mejor]], s=150, facecolors='none',
               edgecolors='black', zorder=3, label=f'mejor época ({mejor + 1})')
    ax.set_xlabel('época')
    ax.set_ylabel('pérdida (MSE)')
    ax.set_title('Curva de entrenamiento del BiLSTM')
    ax.grid(True, ls='--', alpha=0.5)
    ax.legend()
    plt.tight_layout()
    plt.show()


def beta_por_fold(selection, figsize=(7, 4)):
    """El beta elegido en cada fold, con la mediana como línea de referencia.

    Si los folds no coinciden, el beta no está bien determinado: conviene decirlo
    en vez de informar un único número como si fuera estable.
    """
    folds = selection['folds']
    fig, ax = plt.subplots(figsize=figsize)
    ax.bar([f"fold {f['fold']}" for f in folds], [f['beta'] for f in folds], color='#1FA098')
    ax.axhline(selection['beta'], color='black', ls='--', lw=1.4,
               label=f"mediana {selection['beta']:.2f}")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel('beta elegido')
    ax.set_title('beta fuera de fold: ¿coinciden los folds?')
    ax.grid(True, axis='y', ls='--', alpha=0.5)
    ax.legend()
    plt.tight_layout()
    plt.show()


# Fase A — envoltorios estilo clase (SOLO presentacion: no re-entrena, no cambia metricas)
def evaluar_clase(nombre, y_true, y_pred):
    """Alias de evaluate_predictions: misma fila, nombre estilo clase."""
    return evaluate_predictions(np.asarray(y_true), np.asarray(y_pred), nombre)

def mostrar_clase(filas, orden_por="RMSE"):
    """Ordena la tabla como en clase (mejor arriba) y la redondea. Solo lectura."""
    t = pd.DataFrame(filas).sort_values(orden_por, ascending=True).reset_index(drop=True)
    display(t.round(3))
    return t
