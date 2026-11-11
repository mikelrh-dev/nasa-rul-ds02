"""Librerías de `app/`: estado, datos, inferencia, reglas y helpers.

No son puras en su totalidad: `ui_data_loader`, `ui_inference` y `ui_shap`
importan Streamlit para cachear lecturas y el modelo; el resto de la lógica de
estado (flota, hangar, twin, alta, simulacion) no escribe y solo arrastra
Streamlit de forma transitiva. Ningún módulo de aquí inserta rutas en
`sys.path`: la raíz del repositorio la añade el entrypoint. Los imports entre
módulos son de paquete.
"""
