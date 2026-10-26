# Verify report: DS02 pre-defense hardening

**Change:** `2026-10-26-ds02-pre-defense-hardening`
**Status:** Passed
**Date:** 2026-10-26
**Commit range:** `46c7872` (deploy) → `d91982f` (data robustness), on top of the
four SDD authoring commits `59aaf25`…`62cad2b`.

Every line below was produced by a command run against the working tree, not
read from a document. Where a claim could only be read from the code, it says so.

---

## 1. Full gate

```
$ .venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider
217 passed in 208.68s (0:03:28)
```

Baseline before the change: `211 passed in 196.76s`. Six tests were added (three
for the seal check, one for the deciding window, two for the non-finite
rejection) and none was removed.

`python scripts/verify_gate.py` is the repository's executable gate and wraps the
same command; the direct invocation above is what was run, with the cache
provider disabled so nothing is written to `.pytest_cache`.

## 2. Evidence gate

```
$ .venv/Scripts/python.exe scripts/freeze_rules_evidence.py
beta (median of 3 folds): 1.0
check                                      expected       observed  verdict
baseline OOF RMSE                             9.491       9.490728  ok
baseline OOF NASA                           19257.1   19257.147705  ok
R2 OOF RMSE                                  10.737      10.737296  ok
R2 OOF NASA                                   21053   21052.967180  ok
R2 rows changed                               13000   13000.000000  ok
R2b OOF RMSE                                  9.623       9.622750  ok
R2b OOF NASA                                18713.9   18713.886835  ok
R2b rows changed                              10715   10715.000000  ok
R2b max positive increment                  1.32885       1.328848  ok
envelope max positive increment                   0       0.000000  ok
OOF coverage (corrected point)               0.9012       0.901240  ok
pure OOF rows                                 14915   14915.000000  ok
exit 0
```

No drift. The rules layer, its calibration and its figures are untouched by this
change.

## 3. Per phase

### Phase 1 — Deployment

```
$ docker compose config -q
exit 0
```

The Dockerfile parses. The fix itself is one line, `COPY mia/ ./mia/`.

**Verified by execution, not by a real build.** The tree the Dockerfile produces
was copied to the Hermes scratch directory (`src/`, `app/`, `scripts/`, the four
files under `models/`) and the dashboard entrypoint was imported from it:

```
without mia/   -> ModuleNotFoundError: No module named 'motor'
                   File ".../app/ui_rules.py", line 33
with mia/      -> IMPORT OK
```

A real `docker build` was **not** run: Docker is not exercised in this
environment. This is the one item in the change that remains verified by
reproduction rather than by the artifact itself.

### Phase 2 — Documentary coherence

```
$ grep -rn "cada 2 filas" docs/
(no output)

$ grep -n "fifth tab" README.md
(no output)

$ grep -n "dashboard" README.md
196:streamlit run app/dashboard_ds02.py   # fleet hangar + conformal band

$ git ls-files | grep bak_pestanas
(no output)

$ grep -rn "bak_pestanas" app/ tests/ scripts/
(no output)

$ grep -n "211 passed\|41 passed" docs/defensa_ds02_explicacion_logica_negocio.md
124:| 211 tests del paquete `mia/` + `hangar()`/`flota()` + reglas pasan | Ejecutados 2026-10-25: `211 passed in 196.76s` |
```

One correction to the task wording, recorded here because it affects how the
acceptance is read: `grep -n "dashboard.py" README.md` can never match
`app/dashboard_ds02.py`, because the `2` sits between `dashboard_` and `.py`. The
check passed vacuously; the meaningful form is `grep -n "dashboard" README.md`,
which returns exactly one line and it is the ds02 board.

### Phase 3 — The window that decided

RED before the fix, then green:

```
>       assert reportada == decidida.name == 1177
E       assert 1218 == np.int64(1177)
FAILED tests/test_engine_flow.py::test_la_ventana_que_decide_es_la_de_menor_limite_inferior
1 failed, 9 passed in 27.38s

$ .venv/Scripts/python.exe -m pytest tests/test_engine_flow.py -q
10 passed in 22.53s
```

Value change for the U11/ciclo 22 alta: `1218 -> 1177`. The deciding row carries
`start_row` 2354 and `2354 // 2 = 1177`. U14/ciclo 29 stays at 285, because
there the deciding window is the last row and both expressions agree — which is
why the defect was not visible on every engine.

### Phase 4 — Data robustness and provenance

RED before the fix:

```
>       with pytest.raises(ValueError, match=r"no finito.*`T48`, fila 4"):
E       Failed: DID NOT RAISE ValueError
FAILED tests/test_live_eval.py::test_non_finite_values_are_rejected_with_column_and_row
1 failed, 41 deselected in 3.20s

$ .venv/Scripts/python.exe -m pytest tests/test_live_eval.py tests/test_dss_ui.py -q
73 passed in 98.54s
```

The seal check, on the real provenance and on the three outcomes:

```
real cache vs real bundle : checked= True ok= True esperado= 0acd795b0906 leido= 0acd795b0906
=> nothing must render on the green path: True
mismatched bundle         : checked= True ok= False esperado= 0acd795b0906 leido= f27262dbc0e3
missing bundle            : {'checked': False, 'ok': False, 'esperado': '0acd795b0906…', 'leido': None}
provenance not a dict     : {'checked': False, 'ok': False, 'esperado': None, 'leido': None}
```

The recorded seal and the bundle on disk agree, so the warning is not rendered
today and the green path is unchanged.

## 4. Headless render

```
$ .venv/Scripts/python.exe <scratch>/probe_final_render.py
excepciones: 0
avisos: ['La banda es la serie guardada: **no se recalibra** al mover los …']
pestanias: [':material/factory: Flota · qué pasa hoy',
            ':material/precision_manufacturing: Motor · qué le pasa a este',
            ':material/library_add: Casos nuevos · trae un motor',
            ':material/science: Auditoría · cómo se calculó']
¿aparece el aviso del sello? False
```

Zero exceptions, four tabs, and the one warning present is the pre-existing
"the band does not recalibrate" note, not the seal warning. The
`use_container_width` deprecation line printed by Streamlit is pre-existing and
unrelated.

## 5. Frozen artifacts untouched

```
$ git status --porcelain models/ src/ mia/ app/cache/ 02_DS02_ensemble_RUL.ipynb
(empty)
```

No weight was retrained, no rule or threshold was edited, no calibration moved,
no cache row was rewritten. `mia/` was copied into the image and never modified.

## 6. Repository state

```
$ git status --porcelain
(empty)
```

Every file this change owns is committed. The tree is clean.

## 7. What this change does not prove

1. **A real Docker build.** The image was reproduced by copying the tree the
   Dockerfile produces, not by running `docker build`. The one-line fix is
   verified in both directions, but the image itself was never built here.
2. **The seal check against a cache rebuilt from a different bundle whose hash
   was also rewritten into the manifest.** It compares the manifest with the
   artifact; an edited manifest passes. Closing that needs the cache builder to
   sign its own output.
3. **The dataset window index for twins saved before the change.** Those keep a
   position in their own series, which is what the fix reports and what the
   caption now says. No persisted data was rewritten.
4. **Archive.** The repository has no `openspec/changes/archive/` directory and
   no OpenSpec CLI, and the loop skill forbids running the merge by hand. The
   deployed specs were not modified; the deltas in `specs/` are the record, and
   the archive step is left to the next change that has the tooling for it.

## 8. Deliverable

Four defects closed, none of them in the model:

| # | Defect | Fix | Evidence |
| --- | --- | --- | --- |
| 1 | Image cannot serve the dashboard | `COPY mia/ ./mia/` | import fails without it, succeeds with it |
| 2 | Panel cites a window that did not decide | `vista_resultado` reports the deciding position | 1218 → 1177, RED then green |
| 3 | `validate_table` accepts `±inf` | same loop, same message format | RED then green |
| 4 | Seal displayed, never checked | `artifact_hash_check` + warning on mismatch only | three outcomes measured |
