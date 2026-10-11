"""Contrasta la humedad del suelo modelada con la medida por NASA SMAP.

Las regiones sin descarga SMAP usan un balance hídrico de balde
(agroshift/hydrology.py). Aquí se aplica ese mismo modelo a las regiones
que sí tienen SMAP y se mide qué tan bien reproduce su comportamiento:

  - correlación de rangos (Spearman) diaria: lo que importa para el
    pipeline, que trabaja con percentiles de humedad;
  - correlación de la climatología mensual (ciclo estacional).

Salida: data/validation/humedad_modelo_vs_smap.csv

Uso:
    python validar_humedad_modelo.py
"""

from pathlib import Path

import pandas as pd

from agroshift.config import settings
from agroshift.hydrology import eto_penman_monteith, humedad_suelo_modelada
from agroshift.regions import REGIONS

SALIDA = settings.data_dir / "validation" / "humedad_modelo_vs_smap.csv"


def _spearman(a: pd.Series, b: pd.Series) -> float:
    return float(a.rank().corr(b.rank()))


def main() -> None:
    filas = []
    for region in REGIONS.values():
        if region.humedad_modelada:
            continue
        ruta = settings.analysis_dir / region.slug / "agroshift_environmental.csv"
        if not ruta.exists():
            continue
        datos = pd.read_csv(ruta, parse_dates=["fecha"])
        eto = eto_penman_monteith(datos, region.latitud, region.altitud_m)
        modelo = humedad_suelo_modelada(datos, eto).set_index(datos["fecha"])
        smap = datos.set_index("fecha")
        validos = smap["sm_rootzone"].notna()

        clim_modelo = modelo["sm_rootzone"].groupby(modelo.index.month).mean()
        clim_smap = smap["sm_rootzone"].groupby(smap.index.month).mean()
        filas.append(
            {
                "region": region.slug,
                "dias": int(validos.sum()),
                "spearman_diario_raiz": round(_spearman(modelo["sm_rootzone"][validos], smap["sm_rootzone"][validos]), 2),
                "spearman_diario_superficie": round(
                    _spearman(modelo["sm_surface"][validos], smap["sm_surface"][validos]), 2
                ),
                "correlacion_climatologia_mensual": round(float(clim_modelo.corr(clim_smap)), 2),
            }
        )

    resultado = pd.DataFrame(filas)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(SALIDA, index=False)
    print(resultado.to_string(index=False))
    print(f"\nGuardado en {SALIDA}")


if __name__ == "__main__":
    main()
