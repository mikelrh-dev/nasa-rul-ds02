"""Barra lateral de la app: seleccion de unidad y altas de flota.

Extraida de `dashboard_ds02.py` (B3). Devuelve `SidebarState` en vez de
definir globales; los callbacks del dashboard entran como parametros.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone

import streamlit as st

from app.lib import dashboard_helpers as DH
from app.lib import flota as F
from app.lib import twin as T
from app.lib import alta as A
from app.lib import ui_data_loader as L
from app.lib import ui_inference as INF


@dataclass
class SidebarState:
    unit: int


def _sidebar(windows, provenance, units, max_life, altas_fn, etiqueta_unidad,
             registro, guardar_registros, log) -> SidebarState:
    with st.sidebar:
        st.header("Guardia operativa", icon=":material/radar:")
        # Qué ve cada audiencia: el tribunal necesita todo; el operario, solo su turno.
        st.segmented_control(
            "Vista",
            ["Tribunal", "Turno"],
            default="Tribunal",
            key="vista_modo",
            help="Tribunal muestra la evidencia de sesión y la traza de reglas; Turno "
                 "deja solo lo que un operario usa en su guardia.",
        )
        _vistas = sorted(set(int(u) for u in units) | {int(a["unit_id"]) for a in altas_fn()})
        _default = _vistas[0] if int(st.session_state.get("unit", _vistas[0])) not in _vistas else int(st.session_state.get("unit", _vistas[0]))
        unit = st.segmented_control(
            "Unidad de test",
            _vistas,
            default=_default,
            required=True,
            format_func=lambda u: etiqueta_unidad(float(u)),
            key="unit",
            help="Motores del conjunto de test DS02 (partición fija [11, 14, 15]).",
        )
        st.caption(etiqueta_unidad(float(unit)))

        # El reloj de flota va aquí, junto a la unidad: son los dos controles que se
        # usan juntos. El «ciclo del alta» de más abajo es otro concepto.
        st.slider(
            "Ciclo de vuelo simulado",
            min_value=1,
            max_value=max_life,
            value=1,
            step=1,
            key="cycle",
            help=(
                "Reloj de flota: se aplica a todas las unidades. Las que terminaron "
                "su vida registrada se muestran en su último ciclo evaluado (vida "
                f"máxima: {max_life})."
            ),
        )
        st.divider()

        # Sin `st.form`: la matrícula se deriva de la unidad y tiene que refrescarse
        # al cambiarla. En un form el valor no viaja hasta enviar y quedaría obsoleto.
        unidad_libre = st.selectbox(
            "Unidad base (caché)", sorted(int(u) for u in units), key="alta_unidad",
            format_func=lambda u: L.UNIT_LABELS.get(int(u), f"Unidad {int(u)}"),
            help="Motor del test del que se toma la historia ya puntuada.",
        )
        ciclo_libre = st.number_input(
            "Ciclo hasta el que tomar historia",
            min_value=int(windows["cycle"].min()),
            max_value=int(windows["cycle"].max()),
            value=int(min(max(int(windows["cycle"].min()), 20), int(windows["cycle"].max()))),
            step=1, key="alta_ciclo",
            help="El mismo motor en otro ciclo es otro caso de prueba: cambia su estado de triaje.",
        )
        matricula = st.text_input(
            "Matrícula (etiqueta de visualización, auto-generada)",
            value=f"MTTT{int(unidad_libre)}", disabled=True,
            help="No es un identificador real de aeronave: es la etiqueta con la que "
                 "el motor aparece en el muro y en el hangar.",
        )
        enviar = st.button("Incorporar unidad",
                           icon=":material/add_circle:", type="primary")
        if enviar:
            try:
                limpia = T.normalizar_id(matricula)
            except ValueError as exc:
                st.error(str(exc), icon=":material/rule:")
            else:
                unidad_p, ciclo_p = int(unidad_libre), int(ciclo_libre)
                registro = {F.ALTAS_KEY: st.session_state.get(F.ALTAS_KEY) or {}}
                try:
                    registro = F.registrar_alta(registro, limpia, unidad_p, ciclo_p)
                except ValueError as exc:
                    st.error(str(exc), icon=":material/rule:")
                else:
                    st.session_state[F.ALTAS_KEY] = registro[F.ALTAS_KEY]
                    guardar_registros()
                    _uid = registro[F.ALTAS_KEY][limpia]["unit_id"]
                    st.session_state["_alta_pendiente"] = int(_uid)
                    # El alta crea su gemelo: el motor aparece en "Gemelos
                    # registrados" con su serie guardada. No llama al modelo, toma
                    # las ventanas ya puntuadas de la caché.
                    _umb = {"apto": float(st.session_state.get("th_apto_Normal", L.DEFAULT_AIRWORTHY)),
                            "hangar": float(st.session_state.get("th_aog_Normal", L.DEFAULT_AOG))}
                    _ventanas_alta = A.ventanas_de_alta(windows, unidad_p, ciclo_p, _uid)
                    _gemelo = T.make_twin(
                        limpia,
                        {"windows": _ventanas_alta,
                         "contract": {"unidad_simulada": _uid,
                                      "motor": limpia,
                                      "canales": INF.channel_order(),
                                      "window": INF.window_size(),
                                      "step": 2,
                                      "artefacto_sha256": L.get_provenance()["artifact"]["ensemble_sha256"],
                                      "filas": int(len(_ventanas_alta)),
                                      "ventanas": int(len(_ventanas_alta))}},
                        source="alta del sidebar",
                        banda=L.UNIT_LABELS.get(unidad_p, f"U{unidad_p} (caché)"),
                        correccion="ninguna (ventanas ya puntuadas de la caché)",
                        umbrales=_umb,
                    )
                    st.session_state["twins"] = T.registrar(
                        st.session_state.get("twins", {}), _gemelo)
                    guardar_registros()
                    # El aviso dice donde va a aparecer el motor: la matricula, que
                    # es la clave del hangar. Antes prometia la matricula y el
                    # hangar la claveaba como U-1000.
                    st.session_state["twin_flash"] = (
                        f"Aeronave `{limpia}` incorporada (U{unidad_p} hasta el ciclo {ciclo_p}). "
                        f"Aparece en el muro y en «Gemelos registrados» con la matrícula "
                        f"`{limpia}`. Para derivarla, ábrela en «Hangar · ciclo de vida»."
                    )
                    log(f"Alta de la unidad {limpia} (U{unidad_p} hasta el ciclo {ciclo_p}).")
                    st.rerun()
        with st.expander("Reset de flota (quitar unidades de alta)",
                         icon=":material/restart_alt:"):
            st.caption(
                "Deshace las altas de esta sesión. La flota de la caché no se toca."
            )
            altas = altas_fn()
            if not altas:
                st.caption("Ninguna aeronave de alta en esta sesión.")
            else:
                a_quitar = st.selectbox(
                    "Aeronave", [a["matricula"] for a in altas], key="alta_quitar",
                    help="Aeronave de alta a quitar de esta sesión. La flota de la caché no se toca.",
                )
                if st.button("Quitar", icon=":material/delete:", key="alta_quitar_btn"):
                    registro = registro()
                    registro = F.quitar_alta(registro, a_quitar)
                    st.session_state[F.ALTAS_KEY] = registro[F.ALTAS_KEY]
                    st.session_state["twins"] = registro.get("twins") or {}
                    st.session_state["hangar"] = registro.get("hangar") or {}
                    guardar_registros()
                    st.rerun()
        st.caption(
            f"Caché con {L.fmt_miles(provenance['counts']['windows'])} ventanas y "
            f"{L.fmt_miles(provenance['counts']['rows'])} filas de telemetría · "
            f"generada {provenance['generated_at'][:16].replace('T', ' ')}"
        )

        with st.expander("Cómo leer esta pantalla", icon=":material/help:"):
            st.markdown(
                """- **RUL**: ciclos que le quedan al motor (estimación, no medida).
    - **L_inf / objetivo nominal 90 % · cobertura medida empíricamente**: cota inferior conformal; gobierna la decisión (APTO · INSPECCIÓN · HANGAR/AOG).
    - **Ciclo de vuelo / Ventana**: reloj simulado; 50 muestras remuestreadas (~0,4 ciclos) por ventana.
    - **Orden de trabajo**: JSON/CSV de las unidades bloqueadas con banda y acción."""
            )

        # Panel n8n visible (app-ux-bundle-fix): estado del webhook, último envío y
        # botón de prueba. Nunca rompe la app si falta la URL (ver src/n8n.py).
        with st.expander("n8n · webhook de decisión", icon=":material/webhook:"):
            _url_n8n = os.environ.get("N8N_WEBHOOK_URL", "")
            if _url_n8n:
                st.caption(f"Webhook configurado: `{_url_n8n}`")
            else:
                st.caption(
                    "Webhook no configurado (`N8N_WEBHOOK_URL` vacío): los envíos "
                    "quedan en log local y el test devuelve ok=False."
                )
            _ult_n8n = st.session_state.get("n8n_ultimo") or {}
            if _ult_n8n:
                st.caption(
                    f"Último envío: {_ult_n8n.get('decision', '?')} · "
                    f"ok={_ult_n8n.get('ok')} · status={_ult_n8n.get('status')} · "
                    f"en {_ult_n8n.get('en', '?')}"
                )
            else:
                st.caption("Último envío: ninguno en esta sesión.")
            if st.button("Probar envío n8n", key="n8n_prueba", icon=":material/send:"):
                _res_prueba = DH.probar_n8n()
                st.session_state["n8n_ultimo"] = {
                    "decision": "APTO (test)",
                    "ok": bool(isinstance(_res_prueba, dict) and _res_prueba.get("ok") is True),
                    "status": (_res_prueba.get("status") if isinstance(_res_prueba, dict) else None),
                    "en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                }
                # El caption de arriba se emite ANTES que este boton en la misma
                # pasada: Streamlit no re-ejecuta el script al terminar, asi que sin
                # rerun el caption seguiria mostrando el envio anterior (o "ninguno").
                st.rerun()
    return SidebarState(unit=int(unit))
