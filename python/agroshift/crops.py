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
    "Musa acuminata": ("Plátano", "🍌"),
    "Glycine max": ("Soya", "🌱"),
    "Gossypium hirsutum": ("Algodón", "☁️"),
    "Pisum sativum": ("Arveja", "🫛"),
}

NOMBRES_EN: dict[str, str] = {
    "Coffea arabica": "Coffee",
    "Lycopersicon esculentum": "Tomato",
    "Manihot esculenta": "Cassava",
    "Oryza sativa": "Rice",
    "Phaseolus vulgaris": "Beans",
    "Saccharum officinarum": "Sugarcane",
    "Solanum tuberosum": "Potato",
    "Zea mays": "Maize",
    "Musa acuminata": "Plantain",
    "Glycine max": "Soybean",
    "Gossypium hirsutum": "Cotton",
    "Pisum sativum": "Peas",
}

SEPARADOR_ROTACION = " → "


def nombre_comun(cientifico: str, idioma: str = "es") -> str:
    if idioma == "en" and cientifico in NOMBRES_EN:
        return NOMBRES_EN[cientifico]
    return CULTIVOS.get(cientifico, (cientifico, ""))[0]


def icono(cientifico: str) -> str:
    return CULTIVOS.get(cientifico, ("", "🌱"))[1] or "🌱"


def etiqueta(cientifico: str, idioma: str = "es") -> str:
    """'☕ Café' — nombre común con su ícono."""
    return f"{icono(cientifico)} {nombre_comun(cientifico, idioma)}"


def cultivos_de_rotacion(rotacion: str) -> list[str]:
    return rotacion.split(SEPARADOR_ROTACION)


def rotacion_legible(rotacion: str, con_icono: bool = True, idioma: str = "es") -> str:
    """'Coffea arabica → Zea mays' -> '☕ Café → 🌽 Maíz'."""
    formato = etiqueta if con_icono else nombre_comun
    return SEPARADOR_ROTACION.join(
        formato(c, idioma) for c in cultivos_de_rotacion(rotacion)
    )
