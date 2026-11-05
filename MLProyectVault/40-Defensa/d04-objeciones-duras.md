---
tipo: defensa
status: sin-estudiar
tags:
  - objeciones
  - tribunal
  - honestidad
---

# Objeciones duras — 10 con respuesta honesta

> [!abstract] En una frase
> Aquí no te escondes: cada objeción incómoda tiene respuesta con número y límite.

## 1. «Beta 1.0 significa que el BiLSTM sobra»

No. Beta 1.0 elige el meta completo en esta partición, pero un fold pide 0. El meta sin el campeón no existe: necesita sus predicciones. Y la mejor rama sola da 5.654; el híbrido da 4.338 en disco ([[e00-cifras-autoritativas]]).

## 2. «Banda 100 % con 26 ciclos es inútil»

Es cota, no promesa. Cubre porque es ancha donde el error es grande. Estrecharla a 3.35 colapsa a 31 % de cobertura: se midió y se rechazó ([[s11-banda-conformal]]). Prefiero cota honesta a intervalo falso.

## 3. «La unidad 16 es un holdout de juguete»

Cierto que es una sola unidad con RUL hasta 62. Por eso el meta aprende techo corto y por eso enseño el experimento OOF que no transfiere (media 39.9 vs real 31.5). El protocolo es honesto, no omnipotente ([[s01-protocolo-honesto]]).

## 4. «0,44 ciclos por ventana es ridículo»

Es el horizonte real con stride 100. La ventana no pretende ver la vida entera: ve medio ciclo con mucho detalle y el ciclo normalizado aporta la posición ([[c02-ventanas-y-horizonte]]).

## 5. «El BiLSTM varía medio punto entre semillas»

Sí: ±0.1 en el híbrido final por no-determinismo de TensorFlow en CPU (±0.5 en el BiLSTM suelto de la base original). Por eso cito media y dispersión, no una corrida. El orden se mantiene en las tres: el híbrido siempre gana ([[c14-ruido-y-reproducibilidad]], [[c20-multisemilla-y-ruido]]).

## 6. «LightGBM 7.07 no aporta nada»

Sola no, pero combinada sí: el salto de 5.654 a 4.338 viene de errores complementarios, no de magia. Blending fijo daba 8.09 y 7.18 y se rechazó; stacking aprendido sí supera ([[s10-stacking-hibrido]]).

## 7. «Esto no decide nada, solo predice»

La RUL sola no decide: decide `L_inf` con 30 y 25. Lead time 9/23/17 en media y saturación en 60.6. La decisión vive en [[s13-capa-de-reglas-y-decision]], no en el RMSE.

## 8. «Macro 5.0153 contra 4.338: ¿cuál es la verdad?»

Ambas: 4.338 pondera por ventana y esconde al motor 14; 5.0153 pesa cada motor igual (bundle C). El 14 da 8.5761 con 760 filas. Enseño las dos para no halagar la flota ([[e00-cifras-autoritativas]], [[c26-deriva-y-limites]]).

## 9. «¿Por qué no reentrenar en producción?»

Porque movería ±0.1 sin mejorar y rompería la trazabilidad. Defiendo lo de disco con hashes d6c70142 y bf9620a7 y reload idéntico ([[s12-persistencia-y-contrato]]).

## 10. «¿Y la deriva de distribución?»

No hay monitor de deriva: si llega un régimen no visto, el modelo predice igual sin avisar. Es el límite declarado de [[s14-app-y-despliegue]] y la próxima frontera.

## Di esto en el tribunal

> [!quote]
> «Cada objeción que me pones tiene número y límite en mi vault. Beta con disenso, banda como cota, holdout de una unidad y deriva sin monitor: lo enseño yo antes de que lo encuentres tú.»

## Flashcards

> [!question]- ¿Qué respondes a banda inútil?
> Es cota honesta: 100 % con 26.4; estrecharla a 3.35 la rompe.

> [!question]- ¿Qué respondes a beta 1.0?
> Dos folds piden 1.0 y uno pide 0; hay disenso y el meta necesita al campeón.

> [!question]- ¿Qué respondes a deriva?
> No hay monitor: es el límite declarado, no una prestación.

> [!question]- ¿Qué afirma esta nota en una frase?
> Aquí no te escondes: cada objeción incómoda tiene respuesta con número y límite.

> [!question]- ¿Cómo la contarías en el tribunal?
> «Cada objeción que me pones tiene número y límite en mi vault. Beta con disenso, banda como cota, holdout de una unidad y deriva sin monitor: lo enseño yo antes de que lo encuentres tú.»

> [!question]- ¿A qué nota vas si fallas esta idea?
[[e00-cifras-autoritativas]]

> [!question]- ¿A qué nota vas si fallas esta idea?
[[s11-banda-conformal]]

