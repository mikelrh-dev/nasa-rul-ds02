# Delta for ds02-dss-ui

## ADDED Requirements

### Requirement: Auditoría no rompe con un manifiesto sin bilstm_sha256

La pestaña Auditoría MUST NOT lanzar excepción cuando el manifiesto de
procedencia no registre `bilstm_sha256`: MUST leer el hash esperado de
`models/ds02_manifest.json` y MUST mostrar un aviso si falta, sin truncar la
pestaña.

#### Scenario: Manifiesto sin bilstm_sha256

- GIVEN el botón «Auditar hashes del artefacto» y un manifiesto sin la clave
- WHEN se pulsa
- THEN no hay excepción AND la pestaña sigue mostrando reglas e informe

### Requirement: Umbral inválido mantiene la app operable

Un par de umbrales con `hangar >= apto` MUST mostrar un error y restaurar el
preset, sin `st.stop()`: la app MUST seguir renderizando sidebar y pestañas para
poder corregirlo.

#### Scenario: Umbral invertido

- GIVEN Hangar=30 y Apto=25
- WHEN se aplica
- THEN hay un error visible AND siguen existiendo sidebar y pestañas

### Requirement: «Ver gemelo» abre la ficha de un gemelo registrado

Pulsar «Ver gemelo» en la tarjeta de un gemelo registrado MUST abrir su ficha
(seleccionando el detalle del gemelo), no solo cambiar de pestaña.

#### Scenario: Gemelo registrado

- GIVEN un gemelo registrado
- WHEN se pulsa «Ver gemelo»
- THEN la ficha del gemelo queda seleccionada

### Requirement: Test del panel n8n con huella única

El test del panel n8n MUST usar una huella única por pulsación, de modo que no
acumule notificaciones duplicadas en la sesión.

#### Scenario: Dos pulsaciones

- GIVEN dos pulsaciones del test
- WHEN se envían
- THEN cada envío tiene un `fingerprint` distinto

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
