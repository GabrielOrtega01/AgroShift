"""Registro de regiones soportadas por AgroShift.

Cada región agrupa lo que el pipeline necesita para correr en un punto
distinto: coordenadas, altitud aproximada (para el cálculo de ETo) y,
si usa NASA SMAP, la celda de la grilla EASE-Grid 2.0 (fila/columna) ya
resuelta — se calculó una vez descargando un gránulo de muestra y
buscando la celda más cercana en sus arreglos cell_lat/cell_lon.

Hay dos orígenes de la humedad del suelo (`fuente_humedad`):
  - "smap":   medición de NASA SMAP L4 (requiere cuenta Earthdata y horas
              de descarga). Son las regiones incluidas en este archivo.
  - "modelo": estimación con un balance hídrico a partir de NASA POWER
              (ver agroshift/hydrology.py). Son las regiones que se
              agregan con `agregar_region.py` y se guardan en
              data/regiones_adicionales.json.

Ver docs/como_agregar_una_region.md.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from agroshift.config import settings

ARCHIVO_ADICIONALES = settings.data_dir / "regiones_adicionales.json"
SENTINELA_RESULTADO = "resumen_etapas_rotacion_v10.csv"


@dataclass(frozen=True)
class Region:
    slug: str
    nombre: str
    clima: str
    latitud: float
    longitud: float
    altitud_m: float
    fila_smap: int | None = None
    columna_smap: int | None = None
    fuente_humedad: str = "smap"
    departamento: str = ""

    @property
    def nombre_corto(self) -> str:
        """'Santander · Chicamocha' para 'Santander · Chicamocha (cañón…)'."""
        return self.nombre.split(" (")[0]

    @property
    def grupo(self) -> str:
        """Departamento al que pertenece (agrupa zonas en el selector)."""
        return self.departamento or self.nombre_corto

    @property
    def zona(self) -> str:
        """'Chicamocha' para 'Santander · Chicamocha'; el nombre corto si no hay zonas."""
        return self.nombre_corto.split(" · ")[-1]

    @property
    def humedad_modelada(self) -> bool:
        return self.fuente_humedad == "modelo"


_REGIONES_SMAP = [
    Region(
        slug="santander",
        nombre="Santander · Bucaramanga (mesa de Bucaramanga)",
        clima="Valle intermedio, cálido-húmedo",
        latitud=7.119,
        longitud=-73.122,
        altitud_m=959.0,
        fila_smap=711,
        columna_smap=1144,
        departamento="Santander",
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


def _cargar_adicionales(ruta: Path = ARCHIVO_ADICIONALES) -> list[Region]:
    if not ruta.exists():
        return []
    return [Region(**r) for r in json.loads(ruta.read_text(encoding="utf-8"))]


REGIONS: dict[str, Region] = {
    r.slug: r for r in _REGIONES_SMAP + _cargar_adicionales()
}


def get_region(slug: str) -> Region:
    try:
        return REGIONS[slug]
    except KeyError:
        disponibles = ", ".join(REGIONS)
        raise ValueError(
            f"Región desconocida: '{slug}'. Disponibles: {disponibles}"
        ) from None


def registrar_region(region: Region, ruta: Path = ARCHIVO_ADICIONALES) -> None:
    """Agrega (o reemplaza) una región con humedad modelada en el JSON."""
    if region.fuente_humedad != "modelo":
        raise ValueError("Sólo se registran regiones con fuente_humedad='modelo'")
    if region.slug in {r.slug for r in _REGIONES_SMAP}:
        raise ValueError(f"'{region.slug}' ya existe como región SMAP")
    actuales = {r.slug: r for r in _cargar_adicionales(ruta)}
    actuales[region.slug] = region
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        json.dumps([asdict(r) for r in actuales.values()], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    REGIONS[region.slug] = region


def regiones_con_resultados() -> list[str]:
    """Slugs cuyo pipeline ya produjo los CSV que lee la app."""
    return [
        slug
        for slug in REGIONS
        if (settings.analysis_dir / slug / SENTINELA_RESULTADO).exists()
    ]
