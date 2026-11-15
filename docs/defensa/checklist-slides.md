# Checklist de slides

Ocho comprobaciones, atadas a la rúbrica, para revisar el deck antes de la defensa.
Se pasan sobre cada slide del bloque que se toque; las de clásicos + MLP (13-15)
son las que más pesan porque concentran los criterios 6, 7 y 9.

| # | Comprobación | Por qué |
|---|---|---|
| 1 | **Una idea por slide.** Se puede decir en una frase de menos de 15 s. | Criterio 9 (justificar la elección) se pierde si la slide discute cuatro cosas. |
| 2 | **Ninguna métrica se repite** entre dos slides del mismo bloque. | `RMSE train` estaba en la tabla y otra vez en el gráfico: tinta redundante. |
| 3 | **La tabla no pasa de 5 columnas**, y cada columna sostiene el argumento; lo demás, a una nota. | Una tabla de 7 columnas no se lee proyectada. |
| 4 | **Toda jerga tiene glosa en la misma slide** (vecinos, profundidad, α, margen). | El tribunal no tiene por qué saber sklearn. |
| 5 | **El ganador está declarado** con nombre, cifra y criterio. | Criterio 9. "Se elige por `rmse_val`" sin decir quién gana no es una elección. |
| 6 | **Fuente mínima 16 px y capturas legibles** a 1920×1080; si no, fuera. | Una captura de 4 px de texto no es evidencia, es textura. |
| 7 | **Cada cifra coincide con el CSV o artefacto** del que sale. | "45 ajustes por familia" y "12.538 filas" en validación eran falsos y se detectan en la defensa. |
| 8 | **La slide cabe en su tiempo** de `notas-orador.md`. | 20 min y 1.117 s de guion no admiten una slide de 90 s. |

## Cómo se pasó en la revisión del 15 nov

- La reestructuración dejó 28 slides de núcleo y 9 de respaldo: las tablas largas y los mapas se movieron a respaldo, y el núcleo se queda con una idea por slide.
- Slides 13, 14 y 15: clásicos, MLP y techo de fila. Se comprobó que cada cifra sale del CSV y que el ganador está declarado con criterio.
- Slides 18 y 24: OOF/meta/β y pesimista. Se añadió la cobertura empírica 99,7 % y el ancho 25,9 para que la banda no se lea como decoración.
