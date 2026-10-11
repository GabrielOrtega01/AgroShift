"""Pestaña Mi rotación: el recomendador, guiado por las prioridades del agricultor."""

import plotly.graph_objects as go
import streamlit as st

from agroshift.crops import CULTIVOS, cultivos_de_rotacion
from agroshift.recommender import (
    PRIORIDADES,
    cultivos_no_aptos,
    estado_ph_cultivo,
    fiabilidad_por_mes,
    rankear_rotaciones,
    sin_permutaciones,
)
from agroshift.regions import Region
from ui import theme
from ui.components import aviso, html, semaforo
from ui.i18n import cultivo, meses_cortos, nombre_cultivo, rotacion, t

_EXIGENCIA = {"flexible": 2, "equilibrado": 3, "exigente": 4}
_COLORES_ETAPA = [theme.VERDE, theme.SOL, theme.AGUA, theme.TIERRA]
_MEDALLAS = ["🥇", "🥈", "🥉"]


def _meses_recomendados(por_mes) -> list[str]:
    validos = por_mes.dropna(subset=["fiabilidad"])
    if validos.empty:
        return []
    tope = validos["fiabilidad"].max()
    nombres = meses_cortos()
    return [nombres[int(m) - 1] for m in validos[validos["fiabilidad"] >= tope - 5]["mes_num"]]


def _etiqueta_prioridad(clave: str) -> str:
    return f"{PRIORIDADES[clave].icono} {t(f'prioridad.{clave}.nombre')}"


def _controles() -> tuple[list[str], int, int | None, list[str], int]:
    with st.container(border=True):
        st.markdown(f"#### {t('rot.paso1')}")
        prioridades = st.pills(
            t("rot.prioridades_etiqueta"),
            options=list(PRIORIDADES),
            format_func=_etiqueta_prioridad,
            selection_mode="multi",
            key="rot_prioridades",
        ) or []
        if prioridades:
            for clave in prioridades:
                st.caption(f"{PRIORIDADES[clave].icono} **{t(f'prioridad.{clave}.nombre')}:** "
                           f"{t(f'prioridad.{clave}.explicacion')}")
        else:
            st.caption(t("rot.sin_seleccion"))

        st.markdown(f"#### {t('rot.paso2')}")
        c1, c2 = st.columns(2)
        nivel = c1.select_slider(
            t("rot.exigencia"), options=list(_EXIGENCIA), value="equilibrado",
            format_func=lambda k: t(f"rot.exigencia_{k}"), key="rot_exigencia",
            help=t("rot.exigencia_ayuda"),
        )
        n_cultivos = c2.segmented_control(
            t("rot.n_cultivos"), options=["any", "2", "3"], default="any",
            format_func=lambda k: t("rot.cualquiera") if k == "any" else k, key="rot_ncultivos",
        )
        c3, c4 = st.columns(2)
        compat_min = c3.slider(
            t("rot.adaptacion_min"), 0, 80, 50, step=10, key="rot_compat", help=t("rot.adaptacion_ayuda"),
        )
        incluir = c4.multiselect(
            t("rot.incluir"), options=list(CULTIVOS), format_func=cultivo, key="rot_incluir",
            placeholder=t("rot.incluir_vacio"),
        )
    n = None if n_cultivos in (None, "any") else int(n_cultivos)
    return prioridades, _EXIGENCIA[nivel], n, incluir, compat_min


def _tarjeta_podio(posicion: int, fila, mes_txt: str) -> None:
    _, color = semaforo(fila["fiabilidad"])
    html(
        f"""
        <div class="as-card as-card-top">
          <div class="as-rank">{_MEDALLAS[posicion]}</div>
          <h4 style="margin-top:.4rem">{rotacion(fila['rotacion'])}</h4>
          <div class="as-big" style="color:{color}">{fila['fiabilidad']:.0f}%</div>
          <div class="as-muted">{t('rot.podio_fiabilidad')}</div>
          <p style="margin-top:.6rem">⏱️ {t('rot.podio_duracion', dias=fila['duracion_dias'], n=int(fila['n_etapas']))}<br>
          🌡️ {t('rot.podio_adaptacion', pct=fila['compatibilidad_media'])}<br>
          📅 {mes_txt}</p>
        </div>
        """
    )


def _linea_de_tiempo(etapas) -> go.Figure:
    fig = go.Figure()
    for i, (_, e) in enumerate(etapas.iterrows()):
        fig.add_bar(
            y=["·"], x=[e["duracion_promedio_dias"]], orientation="h",
            name=cultivo(e["cultivo"]), marker_color=_COLORES_ETAPA[i % len(_COLORES_ETAPA)],
            text=f"{cultivo(e['cultivo'])}<br>{e['duracion_promedio_dias']:.0f} {t('rot.dias_abrev')}",
            textposition="inside", insidetextanchor="middle", textfont=dict(color="#FFFFFF", size=14),
            hovertemplate=f"{cultivo(e['cultivo'])}: %{{x:.0f}} {t('rot.dias_abrev')}<extra></extra>",
        )
    fig.update_layout(barmode="stack", xaxis_title=t("rot.eje_dias"))
    fig.update_yaxes(visible=False)
    return theme.estilizar(fig, altura=170, leyenda=False)


def _advertencias_suelo(data: dict, rotacion_id: str) -> list[str]:
    suelo = data["suelo"]
    if suelo is None:
        return []
    compat = data["compatibilidad"].set_index("nombre")
    avisos = []
    for c in cultivos_de_rotacion(rotacion_id):
        if c not in compat.index:
            continue
        fila = compat.loc[c]
        estado = estado_ph_cultivo(suelo.ph, fila)
        if estado == "optimo":
            continue
        avisos.append(t(
            f"rot.ph_{estado}", cultivo=nombre_cultivo(c), ph=suelo.ph,
            pmin=fila["ph_optimo_min"], pmax=fila["ph_optimo_max"],
            amin=fila["ph_absoluto_min"], amax=fila["ph_absoluto_max"],
        ))
    return avisos


def _detalle(data: dict, fila, prioridades, min_criterios) -> None:
    rot = fila["rotacion"]
    st.markdown(f"### {rotacion(rot)}")

    etapas = data["etapas"]
    etapas = etapas[etapas["rotacion"] == rot].sort_values("numero_etapa")
    if not etapas.empty:
        st.markdown(f"**{t('rot.linea_tiempo')}**")
        st.plotly_chart(_linea_de_tiempo(etapas), width="stretch", config={"displayModeBar": False})

    por_mes = fiabilidad_por_mes(data["escenarios"], rot, prioridades, min_criterios)
    recomendados = _meses_recomendados(por_mes)

    izq, der = st.columns([1, 1])
    with izq:
        st.markdown(f"**{t('rot.mes_inicio')}**")
        colores = [semaforo(v)[1] if v == v else theme.BORDE for v in por_mes["fiabilidad"]]
        fig = go.Figure(go.Bar(
            x=meses_cortos(), y=por_mes["fiabilidad"].fillna(0), marker_color=colores,
            hovertemplate="%{x}: %{y:.0f}%<extra></extra>",
        ))
        fig.update_layout(yaxis=dict(range=[0, 100], title=t("rot.eje_fechas_cumplen")))
        st.plotly_chart(theme.estilizar(fig, altura=280, leyenda=False), width="stretch",
                        config={"displayModeBar": False})
        if recomendados:
            st.caption(t("rot.mejores_meses", meses=", ".join(recomendados)))

    with der:
        st.markdown(f"**{t('rot.cultivo_por_cultivo')}**")
        if not etapas.empty:
            tabla = etapas[[
                "numero_etapa", "cultivo", "duracion_promedio_dias",
                "precipitacion_promedio_mm", "ETc_promedio_mm", "cobertura_promedio_pct",
            ]].copy()
            tabla["cultivo"] = tabla["cultivo"].map(cultivo)
            tabla["cobertura_promedio_pct"] = tabla["cobertura_promedio_pct"].clip(upper=100)
            st.dataframe(
                tabla.rename(columns={
                    "numero_etapa": t("col.etapa"), "cultivo": t("col.cultivo"),
                    "duracion_promedio_dias": t("col.dias"), "precipitacion_promedio_mm": t("col.lluvia_mm"),
                    "ETc_promedio_mm": t("col.necesita_mm"), "cobertura_promedio_pct": t("col.cobertura_pct"),
                }).round(0),
                hide_index=True, width="stretch",
            )

    cultivos = ", ".join(rotacion(rot, con_icono=False).split(" → "))
    aviso(
        t("rot.por_que", fiabilidad=fila["fiabilidad"], cultivos=cultivos,
          cobertura=min(fila["cobertura_media"], 100), percentil=fila["percentil_humedad"]),
        tipo="info",
    )
    for texto in _advertencias_suelo(data, rot):
        aviso(texto)


def render(data: dict, region: Region) -> None:
    st.subheader(t("rot.titulo"))
    st.caption(t("rot.intro"))
    if region.humedad_modelada:
        aviso(t("aviso.humedad_modelada"))

    escenarios = data["escenarios"]
    prioridades, min_criterios, n_cultivos, incluir, compat_min = _controles()

    compat = data["compatibilidad"]
    descartados = cultivos_no_aptos(compat, compat_min)
    ranking = rankear_rotaciones(
        escenarios, prioridades, min_criterios, incluir, n_cultivos,
        compatibilidad=dict(zip(compat["nombre"], compat["compatibilidad"])),
        cultivos_excluidos=descartados,
    )
    if descartados:
        nombres = ", ".join(cultivo(c) for c in sorted(descartados, key=nombre_cultivo))
        st.caption(t("rot.descartados", cultivos=nombres))

    st.markdown(f"#### {t('rot.paso3')}")
    if ranking.empty:
        aviso(t("rot.sin_resultados"))
        return

    distintas = sin_permutaciones(ranking)
    st.caption(t("rot.encontramos", n=len(distintas), total=len(ranking)))
    top = distintas.head(3)
    columnas = st.columns(len(top))
    for i, (col, (_, fila)) in enumerate(zip(columnas, top.iterrows())):
        por_mes = fiabilidad_por_mes(escenarios, fila["rotacion"], prioridades, min_criterios)
        meses = _meses_recomendados(por_mes)
        with col:
            _tarjeta_podio(
                i, fila,
                t("rot.podio_meses", meses=", ".join(meses)) if meses else t("rot.podio_sin_mes"),
            )

    st.write("")
    st.markdown(f"#### {t('rot.paso4')}")
    candidatas = distintas.head(15)["rotacion"].tolist()
    elegida = st.selectbox(
        t("rot.selector"), candidatas, format_func=rotacion, label_visibility="collapsed",
        key=f"rot_detalle_{region.slug}",
    )
    with st.container(border=True):
        _detalle(data, ranking[ranking["rotacion"] == elegida].iloc[0], prioridades, min_criterios)

    with st.expander(t("rot.todas", n=len(ranking))):
        tabla = ranking.assign(rotacion=ranking["rotacion"].map(lambda r: rotacion(r, False)))
        tabla = tabla[["rotacion", "fiabilidad", "compatibilidad_media", "criterios_medios",
                       "duracion_dias", "cobertura_media"]]
        tabla = tabla.rename(columns={
            "rotacion": t("col.rotacion"), "fiabilidad": t("col.fiabilidad"),
            "compatibilidad_media": t("col.adaptacion"), "criterios_medios": t("col.criterios"),
            "duracion_dias": t("col.duracion"), "cobertura_media": t("col.cobertura_agua"),
        })
        st.dataframe(tabla.round(1), hide_index=True, width="stretch")
        st.download_button(
            t("rot.descargar"), tabla.round(1).to_csv(index=False).encode("utf-8-sig"),
            file_name=f"agroshift_rotaciones_{region.slug}.csv", mime="text/csv",
        )
