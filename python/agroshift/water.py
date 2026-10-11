"""Balance de agua por cultivo, coherente con el recomendador de rotaciones.

El resumen por etapas agrupa los escenarios de todas las fechas de inicio
del historial. Promediarlo por cultivo (ponderando por número de
escenarios) da el balance típico de un ciclo, que es la misma base que
usa el ranking; un ciclo único (el del primer año) lo contradiría.
"""

import pandas as pd

COLUMNAS = {
    "duracion_promedio_dias": "dias",
    "precipitacion_promedio_mm": "lluvia_mm",
    "ETc_promedio_mm": "necesidad_mm",
    "balance_promedio_mm": "saldo_mm",
    "cobertura_promedio_pct": "cobertura_pct",
}


def balance_por_cultivo(etapas: pd.DataFrame) -> pd.DataFrame:
    """Una fila por cultivo con el promedio de un ciclo en el historial.

    Columnas: cultivo, dias, lluvia_mm, necesidad_mm, saldo_mm,
    cobertura_pct (tope 100) y escenarios.
    """
    peso = etapas["cantidad_registros"]
    agrupado = {}
    for origen, destino in COLUMNAS.items():
        ponderado = (etapas[origen] * peso).groupby(etapas["cultivo"]).sum()
        agrupado[destino] = ponderado / peso.groupby(etapas["cultivo"]).sum()
    resultado = pd.DataFrame(agrupado)
    resultado["cobertura_pct"] = resultado["cobertura_pct"].clip(upper=100)
    resultado["escenarios"] = peso.groupby(etapas["cultivo"]).sum()
    return resultado.reset_index()
