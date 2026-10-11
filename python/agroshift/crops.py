"""Presentación de cultivos: ECOCROP los nombra por su especie científica.

El agricultor reconoce "Café" y no "Coffea arabica"; este módulo traduce
los nombres científicos del pipeline a nombres comunes con un ícono.
"""

CULTIVOS: dict[str, tuple[str, str]] = {
    "Coffea arabica": ("Café", "☕"),
    "Lycopersicon esculentum": ("Tomate", "🍅"),
    "Manihot esculenta": ("Yuca", "🌿"),
    "Oryza sativa": ("Arroz", "🌾"),
    "Phaseolus vulgaris": ("Frijol", "🫘"),
    "Saccharum officinarum": ("Caña de azúcar", "🎋"),
    "Solanum tuberosum": ("Papa", "🥔"),
    "Zea mays": ("Maíz", "🌽"),
}

SEPARADOR_ROTACION = " → "


def nombre_comun(cientifico: str) -> str:
    return CULTIVOS.get(cientifico, (cientifico, ""))[0]


def icono(cientifico: str) -> str:
    return CULTIVOS.get(cientifico, ("", "🌱"))[1] or "🌱"


def etiqueta(cientifico: str) -> str:
    """'☕ Café' — nombre común con su ícono."""
    return f"{icono(cientifico)} {nombre_comun(cientifico)}"


def cultivos_de_rotacion(rotacion: str) -> list[str]:
    return rotacion.split(SEPARADOR_ROTACION)


def rotacion_legible(rotacion: str, con_icono: bool = True) -> str:
    """'Coffea arabica → Zea mays' -> '☕ Café → 🌽 Maíz'."""
    formato = etiqueta if con_icono else nombre_comun
    return SEPARADOR_ROTACION.join(
        formato(c) for c in cultivos_de_rotacion(rotacion)
    )
