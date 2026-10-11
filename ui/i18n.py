"""Idioma de la interfaz (español / inglés).

Los textos viven en `ui/textos.py` como pares (español, inglés) bajo una
clave; así no puede existir una clave sin traducir. El idioma elegido se
guarda en `st.session_state["idioma"]`.
"""

import streamlit as st

from agroshift import crops
from agroshift.regions import Region
from ui.textos import MESES_CORTOS, MESES_ES_EN, TEXTOS, TEXTURAS_EN

IDIOMAS = ("es", "en")


def idioma() -> str:
    valor = st.session_state.get("idioma", "es")
    return valor if valor in IDIOMAS else "es"


def t(clave: str, **valores) -> str:
    """Texto de la interfaz en el idioma activo; `valores` rellena {campos}."""
    texto = TEXTOS[clave][IDIOMAS.index(idioma())]
    return texto.format(**valores) if valores else texto


def existe(clave: str) -> bool:
    return clave in TEXTOS


def cultivo(cientifico: str) -> str:
    """'☕ Café' / '☕ Coffee'."""
    return crops.etiqueta(cientifico, idioma())


def nombre_cultivo(cientifico: str) -> str:
    return crops.nombre_comun(cientifico, idioma())


def rotacion(valor: str, con_icono: bool = True) -> str:
    return crops.rotacion_legible(valor, con_icono, idioma())


def meses_cortos() -> list[str]:
    return MESES_CORTOS[idioma()]


def mes(nombre_es: str) -> str:
    """Traduce un nombre de mes completo guardado en español en los datos."""
    return MESES_ES_EN.get(nombre_es, nombre_es) if idioma() == "en" else nombre_es


def textura(nombre_es: str) -> str:
    return TEXTURAS_EN.get(nombre_es, nombre_es) if idioma() == "en" else nombre_es


def region_nombre(region: Region) -> str:
    clave = f"region.{region.slug}.nombre"
    return t(clave) if existe(clave) else region.nombre


def region_corto(region: Region) -> str:
    clave = f"region.{region.slug}.corto"
    return t(clave) if existe(clave) else region.nombre_corto


def region_clima(region: Region) -> str:
    clave = f"region.{region.slug}.clima"
    return t(clave) if existe(clave) else region.clima
