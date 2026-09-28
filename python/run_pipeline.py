"""Punto de entrada del pipeline completo de AgroShift.

Ejecuta, en orden, la descarga de datos crudos y las 11 etapas de análisis
que producen los CSV que consume la app (ver README para el detalle de
cada uno). Requiere credenciales de NASA Earthdata para las etapas de
descarga (ver https://urs.earthdata.nasa.gov/).

El pipeline es multi-región y multi-año: --region elige el punto (ver
agroshift/regions.py) y --fecha-inicio/--fecha-fin el rango histórico.
Cada corrida escribe en su propia carpeta: data/analysis/<region>/.

Uso:
    python run_pipeline.py --region quindio
    python run_pipeline.py --region cordoba --fecha-inicio 2020-01-01 --fecha-fin 2025-12-31
    python run_pipeline.py --analysis-only   # omite la descarga, reprocesa
                                              # solo el análisis con los datos
                                              # crudos ya presentes en data/
"""

import argparse
import os

from agroshift.pipeline import Pipeline, PipelineStep
from agroshift.regions import REGIONS

ADQUISICION = [
    PipelineStep("power", "01_descargar_nasa_power.py", "Descarga clima diario NASA POWER"),
    PipelineStep("smap", "02_descargar_nasa_smap.py", "Descarga humedad del suelo NASA SMAP"),
    PipelineStep("smap-recuperar", "03_recuperar_smap_faltantes.py", "Recupera días SMAP incompletos"),
    PipelineStep("ecocrop-catalogo", "04_descargar_catalogo_ecocrop.py", "Descarga catálogo FAO ECOCROP"),
    PipelineStep("ecocrop-caracteristicas", "05_extraer_caracteristicas_ecocrop.py", "Extrae características por cultivo"),
]

ANALISIS = [
    PipelineStep("integrar-ambiental", "06_integrar_datos_ambientales.py", "Integra NASA POWER + SMAP"),
    PipelineStep("clima", "07_analizar_clima_2020.py", "Resumen e indicadores climáticos"),
    PipelineStep("eto", "08_calcular_evapotranspiracion_referencia.py", "Evapotranspiración de referencia (FAO-56)"),
    PipelineStep("etc", "09_calcular_evapotranspiracion_cultivo.py", "Evapotranspiración por cultivo"),
    PipelineStep("balance-hidrico", "10_calcular_balance_hidrico.py", "Balance precipitación vs. demanda"),
    PipelineStep("estado-hidrico", "11_analizar_estado_hidrico.py", "Clasifica estado hídrico por etapa"),
    PipelineStep("compatibilidad", "12_analizar_compatibilidad_cultivos.py", "Compatibilidad climática por cultivo"),
    PipelineStep("escenarios", "13_generar_escenarios_rotacion.py", "Genera escenarios de rotación"),
    PipelineStep("comparar-fechas", "14_comparar_fechas_inicio.py", "Compara escenarios por fecha de inicio"),
    PipelineStep("resumir-etapas", "15_resumir_etapas_rotacion.py", "Resume etapas por rotación"),
    PipelineStep("priorizar", "16_priorizar_escenarios.py", "Prioriza escenarios por criterio"),
    PipelineStep("consolidar", "17_consolidar_resumen_etapas.py", "Consolida el resumen final por etapas"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--region",
        choices=sorted(REGIONS),
        default="santander",
        help="región a procesar (default: santander)",
    )
    parser.add_argument(
        "--fecha-inicio",
        default="2020-01-01",
        help="inicio del rango histórico (default: 2020-01-01)",
    )
    parser.add_argument(
        "--fecha-fin",
        default="2025-12-31",
        help="fin del rango histórico (default: 2025-12-31)",
    )
    parser.add_argument(
        "--analysis-only",
        action="store_true",
        help="omite la descarga de datos crudos (NASA/FAO) y solo corre el análisis",
    )
    args = parser.parse_args()

    os.environ["AGROSHIFT_REGION"] = args.region
    os.environ["AGROSHIFT_FECHA_INICIO"] = args.fecha_inicio
    os.environ["AGROSHIFT_FECHA_FIN"] = args.fecha_fin

    steps = ANALISIS if args.analysis_only else ADQUISICION + ANALISIS
    pipeline = Pipeline(steps)
    results = pipeline.run_all()

    if not all(r.ok for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
