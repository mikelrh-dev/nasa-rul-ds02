---
source: learn-teacher
mode: vault
vault: vault-defensa
created: 2026-11-10
updated: 2026-11-10
---

# LEARNING_LOG — vault-defensa

Vault de **defensa** del Reto 1 (SAA · PIA · MIA). No enseña cómo funciona el sistema: ordena
**qué se dice, en qué orden y por qué se eligió**. El mecanismo vive en el repo y en
`MLProyectVault`; aquí solo entra lo que se dice en voz alta o se consulta en 10 segundos.

## Estado actual

| | |
|---|---|
| Defensa | 15 min con corte seco + 3 preguntas individuales (una por asignatura) |
| Notas | 42 + este log · 16 en el spine |
| Repaso | 16 esquemas con flashcards (uno por nota del spine) |
| Rúbrica | 19 indicadores · 18 en 10 · **PIA-4 en 7** |
| Ensayo | cronometrado con [[00-guion-15-min]] |

### Cómo se usa

1. **Ensayar** → [[00-guion-15-min]] de arriba abajo, cronómetro en mano. No se lee otra nota
   que la que enlaza cada fila.
2. **Entender una decisión** → [[95-catalogo-de-12-decisiones]] y luego la nota del cuaderno
   donde se ve.
3. **Preparar preguntas** → [[100-tres-preguntas-individuales]] y [[101-banco-de-preguntas]].
4. **Comprobar que cubres la rúbrica** → [[110-mapa-indicador-evidencia]].
5. **Saber qué no decir** → [[103-cifras-y-lista-negra]] y [[104-frases-prohibidas]].

### Reglas del vault

1. **Una nota = un minuto de voz.** Si no se dice o no se consulta en vivo, no entra.
2. **Cada nota declara indicador y descriptor** (`indicador:`, `descriptor:` en el frontmatter).
3. **Toda cifra sale del manifiesto o de `resultados/`.** Los decimales viven en
   [[103-cifras-y-lista-negra]]; el resto redondea.
4. **El repo manda.** Si una nota y el código discrepan, se corrige la nota.
5. **Espina = orden de los cuadernos.** Se explica en el orden en que se construyó:
   NB01 → NB02 → NB03 → NB04 → NB05 → NB06 → NB07.

## Índice

### 00 — Arranque

- [[00-guion-15-min]] ★ guion maestro, minuto a minuto
- [[01-guion-3-min]] versión si recortan el tiempo
- [[02-apertura-30s]] ★ negocio con dato + IA débil
- [[03-checklist-dia-D]] qué abrir y en qué orden

### 01 — NB01 · EDA (SAA-3, SAA-4, SAA-5)

- [[10-nb01-dataset-y-tabla-de-campos]]
- [[11-nb01-cinco-graficos-comentados]] ★
- [[12-nb01-nulos-mar-y-variable-nueva]]

### 02 — NB02 · cinco modelos y MLP (SAA-6, SAA-7, SAA-8, SAA-9)

- [[20-nb02-cinco-modelos-y-tiempos]] ★
- [[21-nb02-mlp-base-y-tres-experimentos]] ★
- [[22-nb02-metricas-y-error-de-negocio]]
- [[23-nb02-eleccion-y-desempate]] ★

### 03 — NB03 · ablación (SAA-6 → 10)

- [[30-nb03-ablacion-cyc-norm]] ★

### 04 — NB04 · BiLSTM, ventana y OOF

- [[40-nb04-ventana-y-fuga]]
- [[41-nb04-bilstm-y-pooling]]
- [[42-nb04-oof-y-beta]] ★

### 05 — NB05 · meta, multisemilla y banda

- [[50-nb05-stacking-y-holdout-16]]
- [[51-nb05-multisemilla]]
- [[52-nb05-banda-conformal]] ★

### 06 — NB06 · producción

- [[60-nb06-cascada-bundle-c]] ★
- [[61-nb06-dos-ligas-y-tabla-final]]
- [[62-nb06-macro-y-motor-14]]

### 07 — NB07 · SHAP (SAA-9 → 10)

- [[70-nb07-shap-aditividad]] ★

### 08 — PIA · código

- [[80-pia-readme-y-funciones]] · [[81-pia-estructura-de-carpetas]]
- [[82-pia-pipeline-sklearn]] · [[83-pia-mlflow]] ★ · [[84-pia-streamlit-test-y-caso-nuevo]]

### 09 — MIA · decisión y acción

- [[90-mia-negocio-con-dato-y-objetivo]] · [[91-mia-seis-reglas]] ★
- [[92-mia-n8n-rama-propia]] ★ · [[93-mia-demo-de-la-accion]]

### 10 — Decisiones

- [[94-como-contar-una-decision]] · [[95-catalogo-de-12-decisiones]] · [[96-lo-que-descartamos]]

### 11 — Tribunal

- [[100-tres-preguntas-individuales]] ★ · [[101-banco-de-preguntas]]
- [[102-objeciones-duras]] · [[103-cifras-y-lista-negra]] · [[104-frases-prohibidas]]

### 12 — Rúbrica

- [[110-mapa-indicador-evidencia]] ★ · [[111-huecos-declarados]] · [[112-como-subir-de-7-a-10]]

## Perfil y nivel

- `preferencia_quiz: solo_al_final` · `formato: expositivo` · `ritmo: normal` · idioma: español.
- `nivel: sin calibrar` · evidencia 0/0. Se recalcula con los ensayos, no con impresiones.

## Bitácora

- **2026-11-10** — vault creado con la rúbrica v5 leída del PDF (19 indicadores, 15 min,
  3 preguntas individuales). Estructura ordenada por cuadernos, a petición.
