"""Piezas visuales reutilizables (tarjetas, insignias, avisos)."""

from html import escape

import streamlit as st

from ui.i18n import t


def html(contenido: str) -> None:
    """Renderiza HTML. Se quita la sangría de cada línea: Markdown trata
    cuatro espacios iniciales como bloque de código."""
    limpio = "\n".join(linea.strip() for linea in contenido.splitlines())
    st.markdown(limpio, unsafe_allow_html=True)


def hero(titulo: str, subtitulo: str, chips: list[str]) -> None:
    chips_html = "".join(f'<span class="as-chip">{escape(c)}</span>' for c in chips)
    html(
        f"""
        <div class="as-hero">
          <h1>{escape(titulo)}</h1>
          <p>{escape(subtitulo)}</p>
          {chips_html}
        </div>
        """
    )


def tarjeta(titulo: str, texto: str, numero: int | None = None, icono: str = "") -> None:
    num = f'<div class="as-step-num">{numero}</div>' if numero else ""
    ico = f"{icono} " if icono else ""
    html(
        f"""
        <div class="as-card as-card-top">
          {num}
          <h4>{ico}{escape(titulo)}</h4>
          <p>{texto}</p>
        </div>
        """
    )


def kpi(etiqueta: str, valor: str, unidad: str = "", ayuda: str = "") -> None:
    """Indicador grande; a diferencia de st.metric, no trunca el texto."""
    unidad_html = f'<span class="as-unit">{escape(unidad)}</span>' if unidad else ""
    ayuda_html = f'<div class="as-muted">{escape(ayuda)}</div>' if ayuda else ""
    html(
        f"""
        <div class="as-card">
          <div class="as-muted">{escape(etiqueta)}</div>
          <div class="as-big">{escape(valor)} {unidad_html}</div>
          {ayuda_html}
        </div>
        """
    )


def insignia(texto: str, activa: bool = True) -> str:
    clase = "as-ok" if activa else "as-no"
    return f'<span class="as-badge {clase}">{escape(texto)}</span>'


def aviso(texto: str, tipo: str = "aviso") -> None:
    clase = "as-callout as-info" if tipo == "info" else "as-callout"
    html(f'<div class="{clase}">{texto}</div>')


def lectura(icono: str, texto: str) -> None:
    html(
        f"""
        <div class="as-insight"><span class="as-ico">{icono}</span>
        <div>{texto}</div></div>
        """
    )


NIVELES = [(80, "nivel.excelente", "#2E7D32"), (60, "nivel.buena", "#7CB342"),
           (40, "nivel.regular", "#F9A825"), (0, "nivel.baja", "#E53935")]


def semaforo(porcentaje: float) -> tuple[str, str]:
    """(etiqueta, color) para un puntaje de 0 a 100."""
    for minimo, clave, color in NIVELES:
        if porcentaje >= minimo:
            return t(clave), color
    return t("nivel.baja"), "#E53935"
