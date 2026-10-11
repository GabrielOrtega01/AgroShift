"""Identidad visual: paleta, estilos globales y plantilla de gráficos."""

import plotly.graph_objects as go
import streamlit as st

VERDE = "#2E7D32"
VERDE_OSCURO = "#1B5E20"
VERDE_CLARO = "#A5D6A7"
LIMA = "#7CB342"
AGUA = "#1E88E5"
SOL = "#F9A825"
TIERRA = "#8D6E63"
ALERTA = "#E53935"
TEXTO = "#1F2A1F"
TEXTO_SUAVE = "#5B6B5B"
BORDE = "#DCE6D6"

COLORES_SERIE = [VERDE, AGUA, SOL, TIERRA, LIMA, ALERTA]

_CSS = f"""
<style>
#MainMenu, footer {{ visibility: hidden; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1180px; }}

h1, h2, h3 {{ color: {VERDE_OSCURO}; letter-spacing: -0.01em; }}
h2 {{ font-size: 1.45rem; margin-top: 0.4rem; }}
h3 {{ font-size: 1.15rem; }}

/* Barra lateral */
[data-testid="stSidebar"] {{ background: #EEF4EA; border-right: 1px solid {BORDE}; }}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{ color: {VERDE_OSCURO}; }}

/* Pestañas */
.stTabs [data-baseweb="tab-list"] {{ gap: 0.25rem; border-bottom: 2px solid {BORDE}; flex-wrap: wrap; }}
.stTabs [data-baseweb="tab"] {{
  height: 3rem; padding: 0 1rem; border-radius: 10px 10px 0 0;
  font-weight: 600; color: {TEXTO_SUAVE};
}}
.stTabs [aria-selected="true"] {{ color: {VERDE_OSCURO}; background: #FFFFFF; }}

/* Métricas como tarjetas */
[data-testid="stMetric"] {{
  background: #FFFFFF; border: 1px solid {BORDE}; border-radius: 14px;
  padding: 0.9rem 1.1rem; box-shadow: 0 1px 2px rgba(31,42,31,.05);
}}
[data-testid="stMetricLabel"] {{ color: {TEXTO_SUAVE}; }}
[data-testid="stMetricValue"] {{ color: {VERDE_OSCURO}; font-weight: 700; }}

/* Contenedores con borde */
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 14px; }}

/* Héroe */
.as-hero {{
  background: linear-gradient(120deg, {VERDE_OSCURO} 0%, {VERDE} 55%, {LIMA} 100%);
  color: #FFFFFF; border-radius: 18px; padding: 1.6rem 1.8rem; margin-bottom: 1.2rem;
}}
.as-hero h1 {{ color: #FFFFFF; margin: 0 0 .25rem 0; font-size: 2rem; }}
.as-hero p {{ margin: 0; font-size: 1.05rem; opacity: .95; }}
.as-hero .as-chip {{
  display: inline-block; margin: .8rem .4rem 0 0; padding: .2rem .75rem;
  background: rgba(255,255,255,.18); border-radius: 999px; font-size: .85rem;
}}

@media (max-width: 640px) {{
  .as-hero {{ padding: 1.1rem 1.1rem; }}
  .as-hero h1 {{ font-size: 1.6rem; }}
  .as-hero p {{ font-size: .95rem; }}
  .as-hero .as-chip {{ font-size: .75rem; margin-top: .5rem; }}
  .as-big {{ font-size: 1.7rem; }}
}}

/* Tarjetas */
.as-card {{
  background: #FFFFFF; border: 1px solid {BORDE}; border-radius: 14px;
  padding: 1rem 1.15rem; height: 100%; box-shadow: 0 1px 2px rgba(31,42,31,.05);
}}
.as-card h4 {{ margin: 0 0 .35rem 0; color: {VERDE_OSCURO}; font-size: 1.05rem; }}
.as-card p {{ margin: 0; color: {TEXTO_SUAVE}; font-size: .95rem; line-height: 1.45; }}
.as-step-num {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 1.9rem; height: 1.9rem; border-radius: 50%; margin-bottom: .5rem;
  background: {VERDE}; color: #FFFFFF; font-weight: 700;
}}
.as-card-top {{ border-top: 4px solid {VERDE}; min-height: 9.5rem; }}

/* Insignias */
.as-badge {{
  display: inline-block; padding: .12rem .6rem; border-radius: 999px;
  font-size: .8rem; font-weight: 600; margin: 0 .3rem .3rem 0;
}}
.as-ok {{ background: #E3F2E1; color: {VERDE_OSCURO}; }}
.as-no {{ background: #F1F1EE; color: #8A948A; text-decoration: line-through; }}

/* Avisos */
.as-callout {{
  background: #FFF8E1; border-left: 5px solid {SOL}; border-radius: 10px;
  padding: .8rem 1rem; color: {TEXTO}; font-size: .95rem; line-height: 1.5;
}}
.as-callout.as-info {{ background: #E8F1FB; border-left-color: {AGUA}; }}

/* Línea de lectura rápida */
.as-insight {{ display: flex; gap: .7rem; align-items: flex-start; margin: .5rem 0; line-height: 1.45; }}
.as-insight span.as-ico {{ font-size: 1.35rem; line-height: 1.2; }}

/* Ranking */
.as-rank {{ font-size: 2rem; line-height: 1; }}
.as-big {{ font-size: 2.1rem; font-weight: 800; color: {VERDE_OSCURO}; line-height: 1.1; }}
.as-muted {{ color: {TEXTO_SUAVE}; font-size: .9rem; }}
.as-unit {{ font-size: 1rem; font-weight: 600; color: {TEXTO_SUAVE}; }}
</style>
"""


def aplicar_tema() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def estilizar(fig: go.Figure, altura: int = 360, leyenda: bool = True) -> go.Figure:
    """Aplica la plantilla visual común a un gráfico de Plotly."""
    fig.update_layout(
        height=altura,
        margin=dict(l=8, r=8, t=48, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Source Sans Pro, sans-serif", size=14, color=TEXTO),
        title=dict(font=dict(size=16, color=VERDE_OSCURO), x=0, xanchor="left"),
        colorway=COLORES_SERIE,
        showlegend=leyenda,
        legend=dict(orientation="h", y=-0.18, x=0, title_text=""),
        hoverlabel=dict(bgcolor="#FFFFFF", font_color=TEXTO),
    )
    fig.update_xaxes(showgrid=False, linecolor=BORDE, title_text=None)
    fig.update_yaxes(gridcolor="#E9EFE5", zeroline=False)
    return fig
