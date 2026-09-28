"""Registro de regiones soportadas por AgroShift.

Cada región agrupa lo que el pipeline necesita para correr en un punto
distinto: coordenadas, altitud aproximada (para el cálculo de ETo) y la
celda de la grilla SMAP EASE-Grid 2.0 (fila/columna) ya resuelta — se
calculó una vez descargando un gránulo de muestra y buscando la celda
más cercana en sus arreglos cell_lat/cell_lon (ver
docs/como_agregar_una_region.md si se agrega una región nueva).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    slug: str
    nombre: str
    clima: str
    latitud: float
    longitud: float
    altitud_m: float
    fila_smap: int
    columna_smap: int


REGIONS: dict[str, Region] = {
    r.slug: r
    for r in [
        Region(
            slug="santander",
            nombre="Santander (valle del Magdalena medio)",
            clima="Valle intermedio, cálido-húmedo",
            latitud=7.119,
            longitud=-73.122,
            altitud_m=959.0,
            fila_smap=711,
            columna_smap=1144,
        ),
        Region(
            slug="quindio",
            nombre="Quindío (eje cafetero)",
            clima="Templado de montaña, zona cafetera",
            latitud=4.533,
            longitud=-75.681,
            altitud_m=1483.0,
            fila_smap=747,
            columna_smap=1117,
        ),
        Region(
            slug="cordoba",
            nombre="Córdoba (Caribe seco)",
            clima="Tropical seco, ganadería y cultivos de secano",
            latitud=8.748,
            longitud=-75.878,
            altitud_m=13.0,
            fila_smap=688,
            columna_smap=1115,
        ),
        Region(
            slug="boyaca",
            nombre="Boyacá (altiplano cundiboyacense)",
            clima="Frío de altiplano andino, papa y cereales",
            latitud=5.535,
            longitud=-73.367,
            altitud_m=2782.0,
            fila_smap=733,
            columna_smap=1142,
        ),
    ]
}


def get_region(slug: str) -> Region:
    try:
        return REGIONS[slug]
    except KeyError:
        disponibles = ", ".join(REGIONS)
        raise ValueError(
            f"Región desconocida: '{slug}'. Disponibles: {disponibles}"
        ) from None
