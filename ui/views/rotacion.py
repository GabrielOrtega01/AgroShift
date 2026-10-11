"""Pestaña Mi rotación: el recomendador, guiado por las prioridades del agricultor."""

import plotly.graph_objects as go
import streamlit as st

from agroshift.crops import CULTIVOS, etiqueta, nombre_comun, rotacion_legible
from agroshift.recommender import (
    PRIORIDADES,
    cultivos_no_aptos,
    fiabilidad_por_mes,
    rankear_rotaciones,
    sin_permutaciones,
)
from agroshift.regions import Region
from ui import theme
from ui.components import aviso, html, insignia, semaforo

_EXIGENCIA = {"Flexible": 2, "Equilibrado": 3, "Exigente": 4}
_COLORES_ETAPA = [theme.VERDE, theme.SOL, theme.AGUA, theme.TIERRA]
_MEDALLAS = ["🥇", "🥈", "🥉"]


def _meses_recomendados(por_mes) -> list[str]:
    validos = por_mes.dropna(subset=["fiabilidad"])
    if validos.empty:
        return []
    tope = validos["fiabilidad"].max()
    return validos[validos["fiabilidad"] >= tope - 5]["mes"].tolist()


def _controles(data: dict) -> tuple[list[str], int, int | None, list[str], int]:
    with st.container(border=True):
        st.markdown("#### 1 · ¿Qué es lo más importante para ti?")
        prioridades = st.pills(
            "Condiciones que la rotación debe cumplir (puedes elegir varias)",
            options=list(PRIORIDADES),
            format_func=lambda k: f"{PRIORIDADES[k].icono} {PRIORIDADES[k].nombre}",
            selection_mode="multi",
            key="rot_prioridades",
        ) or []
        if prioridades:
            for clave in prioridades:
                p = PRIORIDADES[clave]
                st.caption(f"{p.icono} **{p.nombre}:** {p.explicacion}")
        else:
            st.caption("Sin selección: se muestran las rotaciones más equilibradas en general.")

        st.markdown("#### 2 · Afina tu búsqueda")
        c1, c2 = st.columns(2)
        nivel = c1.select_slider(
            "Nivel de exigencia", options=list(_EXIGENCIA), value="Equilibrado", key="rot_exigencia",
            help="Cuántos de los 4 criterios (agua, balance, humedad, ajuste temporal) debe cumplir. "
                 "Flexible: 2 de 4 · Equilibrado: 3 de 4 · Exigente: 4 de 4.",
        )
        n_cultivos = c2.segmented_control(
            "Cultivos por rotación", options=["Cualquiera", "2", "3"], default="Cualquiera",
            key="rot_ncultivos",
        )
        c3, c4 = st.columns(2)
        compat_min = c3.slider(
            "Adaptación mínima al clima de los cultivos (%)", 0, 80, 50, step=10, key="rot_compat",
            help="Descarta rotaciones que incluyan cultivos poco adaptados a la temperatura y la "
                 "lluvia de tu región (puntaje FAO ECOCROP de la pestaña Cultivos).",
        )
        incluir = c4.multiselect(
            "Quiero que incluya…", options=list(CULTIVOS), format_func=etiqueta, key="rot_incluir",
            placeholder="Cualquier cultivo",
        )
    n = None if n_cultivos in (None, "Cualquiera") else int(n_cultivos)
    return prioridades, _EXIGENCIA[nivel], n, incluir, compat_min


def _tarjeta_podio(posicion: int, fila, mes_txt: str) -> None:
    nivel, color = semaforo(fila["fiabilidad"])
    html(
        f"""
        <div class="as-card as-card-top">
          <div class="as-rank">{_MEDALLAS[posicion]}</div>
          <h4 style="margin-top:.4rem">{rotacion_legible(fila['rotacion'])}</h4>
          <div class="as-big" style="color:{color}">{fila['fiabilidad']:.0f}%</div>
          <div class="as-muted">de las fechas de inicio históricas cumplen lo que pediste</div>
          <p style="margin-top:.6rem">⏱️ ~{fila['duracion_dias']:.0f} días en total · {int(fila['n_etapas'])} cultivos<br>
          🌡️ Adaptación al clima: {fila['compatibilidad_media']:.0f}%<br>
          📅 {mes_txt}</p>
        </div>
        """
    )


def _linea_de_tiempo(etapas) -> go.Figure:
    fig = go.Figure()
    for i, (_, e) in enumerate(etapas.iterrows()):
        fig.add_bar(
            y=["Rotación"], x=[e["duracion_promedio_dias"]], orientation="h",
            name=etiqueta(e["cultivo"]), marker_color=_COLORES_ETAPA[i % len(_COLORES_ETAPA)],
            text=f"{etiqueta(e['cultivo'])}<br>{e['duracion_promedio_dias']:.0f} días",
            textposition="inside", insidetextanchor="middle", textfont=dict(color="#FFFFFF", size=14),
            hovertemplate=f"{etiqueta(e['cultivo'])}: %{{x:.0f}} días<extra></extra>",
        )
    fig.update_layout(barmode="stack", xaxis_title="Días desde el inicio de la rotación")
    fig.update_yaxes(visible=False)
    return theme.estilizar(fig, altura=170, leyenda=False)


def _detalle(data: dict, fila, prioridades, min_criterios) -> None:
    rotacion = fila["rotacion"]
    st.markdown(f"### {rotacion_legible(rotacion)}")

    etapas = data["etapas"]
    etapas = etapas[etapas["rotacion"] == rotacion].sort_values("numero_etapa")
    if not etapas.empty:
        st.markdown("**Así se ve la rotación en el tiempo**")
        st.plotly_chart(_linea_de_tiempo(etapas), width="stretch", config={"displayModeBar": False})

    por_mes = fiabilidad_por_mes(data["escenarios"], rotacion, prioridades, min_criterios)
    recomendados = _meses_recomendados(por_mes)

    izq, der = st.columns([1, 1])
    with izq:
        st.markdown("**¿En qué mes conviene iniciar?**")
        colores = [semaforo(v)[1] if v == v else theme.BORDE for v in por_mes["fiabilidad"]]
        fig = go.Figure(go.Bar(
            x=por_mes["mes"], y=por_mes["fiabilidad"].fillna(0), marker_color=colores,
            hovertemplate="%{x}: %{y:.0f}%<extra></extra>",
        ))
        fig.update_layout(yaxis=dict(range=[0, 100], title="% de fechas que cumplen"))
        st.plotly_chart(theme.estilizar(fig, altura=280, leyenda=False), width="stretch",
                        config={"displayModeBar": False})
        if recomendados:
            st.caption("Mejores meses para iniciar: **" + ", ".join(recomendados) + "**.")

    with der:
        st.markdown("**Cultivo por cultivo**")
        if not etapas.empty:
            tabla = etapas[[
                "numero_etapa", "cultivo", "duracion_promedio_dias",
                "precipitacion_promedio_mm", "ETc_promedio_mm", "cobertura_promedio_pct",
            ]].copy()
            tabla["cultivo"] = tabla["cultivo"].map(etiqueta)
            tabla["cobertura_promedio_pct"] = tabla["cobertura_promedio_pct"].clip(upper=100)
            st.dataframe(
                tabla.rename(columns={
                    "numero_etapa": "Etapa", "cultivo": "Cultivo",
                    "duracion_promedio_dias": "Días", "precipitacion_promedio_mm": "Lluvia (mm)",
                    "ETc_promedio_mm": "Necesita (mm)", "cobertura_promedio_pct": "Lluvia cubre (%)",
                }).round(0),
                hide_index=True, width="stretch",
            )

    cultivos = ", ".join(rotacion_legible(rotacion, con_icono=False).split(" → "))
    cobertura = min(fila["cobertura_media"], 100)
    aviso(
        f"<b>Por qué se recomienda:</b> en el {fila['fiabilidad']:.0f} % de las fechas de inicio "
        f"históricas, esta rotación ({cultivos}) cumplió lo que pediste. En promedio la lluvia cubre "
        f"<b>{cobertura:.0f} %</b> del agua que necesitan los cultivos y la humedad del suelo se "
        f"ubica en el <b>percentil {fila['percentil_humedad']:.0f}</b> de su historial.",
        tipo="info",
    )


def render(data: dict, region: Region) -> None:
    st.subheader("Encuentra tu rotación de cultivos")
    st.caption(
        "Elige qué es importante para ti y AgroShift revisa cientos de combinaciones de cultivos "
        "y fechas de siembra usando el historial de tu región."
    )

    escenarios = data["escenarios"]
    prioridades, min_criterios, n_cultivos, incluir, compat_min = _controles(data)

    compat = data["compatibilidad"]
    descartados = cultivos_no_aptos(compat, compat_min)
    ranking = rankear_rotaciones(
        escenarios, prioridades, min_criterios, incluir, n_cultivos,
        compatibilidad=dict(zip(compat["nombre"], compat["compatibilidad_climatica"])),
        cultivos_excluidos=descartados,
    )
    if descartados:
        st.caption(
            "🌡️ Descartados por no adaptarse al clima de tu región: "
            + ", ".join(etiqueta(c) for c in sorted(descartados, key=nombre_comun))
            + ". Cambia la adaptación mínima para incluirlos."
        )

    st.markdown("#### 3 · Tus mejores opciones")
    if ranking.empty:
        aviso(
            "<b>Ninguna rotación cumple todo lo que pediste.</b> Prueba bajando el nivel de "
            "exigencia, la adaptación mínima al clima, quitando alguna condición o dejando que "
            "el sistema elija los cultivos.",
        )
        return

    distintas = sin_permutaciones(ranking)
    st.caption(
        f"Encontramos **{len(distintas)}** combinaciones de cultivos posibles "
        f"({len(ranking)} si cuentas el orden). Estas son las mejores:"
    )
    top = distintas.head(3)
    columnas = st.columns(len(top))
    for i, (col, (_, fila)) in enumerate(zip(columnas, top.iterrows())):
        por_mes = fiabilidad_por_mes(escenarios, fila["rotacion"], prioridades, min_criterios)
        meses = _meses_recomendados(por_mes)
        with col:
            _tarjeta_podio(i, fila, "Mejores meses: " + ", ".join(meses) if meses else "Sin mes destacado")

    st.write("")
    st.markdown("#### 4 · Mira el detalle")
    candidatas = distintas.head(15)["rotacion"].tolist()
    elegida = st.selectbox(
        "Rotación", candidatas, format_func=rotacion_legible, label_visibility="collapsed",
        key=f"rot_detalle_{region.slug}",
    )
    with st.container(border=True):
        _detalle(data, ranking[ranking["rotacion"] == elegida].iloc[0], prioridades, min_criterios)

    with st.expander(f"Ver las {len(ranking)} rotaciones y descargar"):
        tabla = ranking.assign(rotacion=ranking["rotacion"].map(lambda r: rotacion_legible(r, False)))
        tabla = tabla[["rotacion", "fiabilidad", "compatibilidad_media", "criterios_medios",
                       "duracion_dias", "cobertura_media"]]
        tabla = tabla.rename(columns={
            "rotacion": "Rotación", "fiabilidad": "Fiabilidad (%)",
            "compatibilidad_media": "Adaptación al clima (%)", "criterios_medios": "Criterios (de 4)",
            "duracion_dias": "Duración (días)", "cobertura_media": "Cobertura de agua (%)",
        })
        st.dataframe(tabla.round(1), hide_index=True, width="stretch")
        st.download_button(
            "⬇️ Descargar ranking (CSV)", tabla.round(1).to_csv(index=False).encode("utf-8-sig"),
            file_name=f"agroshift_rotaciones_{region.slug}.csv", mime="text/csv",
        )
