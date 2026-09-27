"""Punto de entrada del pipeline completo de AgroShift.

Ejecuta, en orden, la descarga de datos crudos y las 12 etapas de análisis
que producen los CSV que consume la app (ver README para el detalle de
cada uno). Requiere credenciales de NASA Earthdata para las etapas de
descarga (ver https://urs.earthdata.nasa.gov/).

Uso:
    python run_pipeline.py            # pipeline completo
    python run_pipeline.py --analysis-only   # omite la descarga, reprocesa
                                              # solo el análisis con los datos
                                              # crudos ya presentes en data/
"""

import argparse

from agroshift.pipeline import Pipeline, PipelineStep

ADQUISICION = [
    PipelineStep("power", "01_descargar_nasa_power.py", "Descarga clima diario NASA POWER"),
    PipelineStep("smap", "02_descargar_nasa_smap.py", "Descarga humedad del suelo NASA SMAP"),
    PipelineStep("smap-fix-enero", "03_corregir_smap_enero.py", "Corrige huecos de enero en SMAP"),
    PipelineStep("smap-fix-faltantes", "04_recuperar_smap_faltantes.py", "Recupera días SMAP faltantes"),
    PipelineStep("ecocrop-catalogo", "05_descargar_catalogo_ecocrop.py", "Descarga catálogo FAO ECOCROP"),
    PipelineStep("ecocrop-caracteristicas", "06_extraer_caracteristicas_ecocrop.py", "Extrae características por cultivo"),
]

ANALISIS = [
    PipelineStep("integrar-ambiental", "07_integrar_datos_ambientales.py", "Integra NASA POWER + SMAP"),
    PipelineStep("clima-2020", "08_analizar_clima_2020.py", "Resumen e indicadores climáticos 2020"),
    PipelineStep("eto", "09_calcular_evapotranspiracion_referencia.py", "Evapotranspiración de referencia (FAO-56)"),
    PipelineStep("etc", "10_calcular_evapotranspiracion_cultivo.py", "Evapotranspiración por cultivo"),
    PipelineStep("balance-hidrico", "11_calcular_balance_hidrico.py", "Balance precipitación vs. demanda"),
    PipelineStep("estado-hidrico", "12_analizar_estado_hidrico.py", "Clasifica estado hídrico por etapa"),
    PipelineStep("compatibilidad", "13_analizar_compatibilidad_cultivos.py", "Compatibilidad climática por cultivo"),
    PipelineStep("escenarios", "14_generar_escenarios_rotacion.py", "Genera escenarios de rotación"),
    PipelineStep("comparar-fechas", "15_comparar_fechas_inicio.py", "Compara escenarios por fecha de inicio"),
    PipelineStep("resumir-etapas", "16_resumir_etapas_rotacion.py", "Resume etapas por rotación"),
    PipelineStep("priorizar", "17_priorizar_escenarios.py", "Prioriza escenarios por criterio"),
    PipelineStep("consolidar", "18_consolidar_resumen_etapas.py", "Consolida el resumen final por etapas"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--analysis-only",
        action="store_true",
        help="omite la descarga de datos crudos (NASA/FAO) y solo corre el análisis",
    )
    args = parser.parse_args()

    steps = ANALISIS if args.analysis_only else ADQUISICION + ANALISIS
    pipeline = Pipeline(steps)
    results = pipeline.run_all()

    if not all(r.ok for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
