"""Pestaña Cómo funciona: metodología, fuentes y límites, en lenguaje claro."""

import streamlit as st

from agroshift.recommender import PRIORIDADES
from ui.components import aviso, tarjeta

REPOSITORIO = "https://github.com/GabrielOrtega01/AgroShift"


def render() -> None:
    st.subheader("¿Cómo llega AgroShift a sus recomendaciones?")
    st.markdown(
        "AgroShift **no adivina**: combina datos medidos por satélite con las necesidades "
        "conocidas de cada cultivo. Estos son los pasos."
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tarjeta("Medimos el clima", "Temperatura, lluvia, viento y radiación diaria desde 2020 (NASA POWER).", numero=1)
    with c2:
        tarjeta("Medimos el suelo", "Humedad de la superficie y de la zona de raíces (NASA SMAP).", numero=2)
    with c3:
        tarjeta("Calculamos el agua", "Estimamos cuánta agua pierde y pide cada cultivo etapa por etapa (método FAO‑56).", numero=3)
    with c4:
        tarjeta("Probamos rotaciones", "Simulamos cada rotación en muchas fechas de inicio del historial y las comparamos.", numero=4)

    st.write("")
    st.markdown("### Los 4 criterios de evaluación")
    st.caption("Una rotación suma un punto por cada criterio que cumple. El máximo es 4.")
    columnas = st.columns(2)
    for i, p in enumerate(PRIORIDADES.values()):
        with columnas[i % 2]:
            tarjeta(p.nombre, p.explicacion, icono=p.icono)
            st.write("")

    st.markdown("### ¿Qué significa «fiabilidad»?")
    st.markdown(
        "Nadie puede predecir exactamente el clima del próximo año. Por eso AgroShift prueba cada "
        "rotación en **todas las fechas de inicio del historial (2020–2025)** y te dice en qué "
        "porcentaje de ellas se cumplió lo que pediste. Un **90 %** significa que la rotación "
        "funcionó casi siempre; un **30 %**, que depende mucho del año."
    )

    st.markdown("### ¿Y si un cultivo no se da bien en mi clima?")
    st.markdown(
        "El cálculo de agua por sí solo no sabe si hace demasiado frío o calor para un cultivo. "
        "Por eso AgroShift cruza cada rotación con la **adaptación al clima** de la pestaña "
        "Cultivos y, por defecto, descarta las que incluyen cultivos con menos de **50 %**, "
        "tanto en adaptación general como en temperatura (la lluvia que falta se puede suplir "
        "con riego; el frío o el calor excesivo, no). Puedes cambiar ese mínimo en **Mi rotación**."
    )

    st.markdown("### De dónde salen los datos")
    st.dataframe(
        [
            {"Fuente": "NASA POWER", "Qué aporta": "Clima diario: temperatura, lluvia, humedad relativa, viento, radiación",
             "Resolución": "~50 km, diaria"},
            {"Fuente": "NASA SMAP L4", "Qué aporta": "Humedad del suelo (superficie y zona de raíces)",
             "Resolución": "9 km, una muestra al día"},
            {"Fuente": "FAO ECOCROP", "Qué aporta": "Temperatura, lluvia, pH y ciclo que necesita cada cultivo",
             "Resolución": "Por especie"},
        ],
        hide_index=True, width="stretch",
    )

    st.markdown("### Glosario")
    with st.expander("Ver términos técnicos"):
        st.markdown(
            "- **ETo (evapotranspiración de referencia):** agua que pierde un cultivo de referencia por evaporación y transpiración.\n"
            "- **ETc:** agua que realmente necesita *tu* cultivo en cada etapa (ETo × coeficiente del cultivo).\n"
            "- **Balance hídrico:** lluvia menos ETc. Positivo = sobra agua; negativo = falta.\n"
            "- **Percentil de humedad:** compara la humedad del suelo con su propio historial. P25 significa que "
            "el suelo está más húmedo que el 25 % de los días registrados.\n"
            "- **m³/m³:** volumen de agua por volumen de suelo (0,30 = 30 % del suelo es agua)."
        )

    st.markdown("### Límites que debes conocer")
    aviso(
        "<ul style='margin:0;padding-left:1.2rem'>"
        "<li>Los datos representan un <b>punto de referencia por región</b>, no tu finca exacta; "
        "el microclima y la pendiente pueden variar.</li>"
        "<li>La humedad del suelo viene de un satélite con celdas de <b>9 km</b>.</li>"
        "<li><b>No usa análisis de suelo local</b> (textura, pH, fertilidad). Confírmalos aparte.</li>"
        "<li>Hoy cubre <b>4 regiones</b> y <b>8 cultivos</b>.</li>"
        "<li>Es una <b>herramienta de apoyo</b>: no reemplaza la asesoría de un técnico agropecuario.</li>"
        "</ul>"
    )

    st.write("")
    st.caption(
        f"Proyecto desarrollado para el NASA Space Apps Challenge 2026 — «Field Shift: Adapting "
        f"Farms with NASA Data». Código abierto: [{REPOSITORIO}]({REPOSITORIO})"
    )
