"""Recomendador de rotaciones: convierte las prioridades del agricultor en
un ranking de rotaciones.

Cada rotación se evalúa en muchas fechas de inicio históricas (2020-2025).
En lugar de premiar la mejor fecha puntual — que no se puede predecir —
se premia la *fiabilidad*: en qué porcentaje de esas fechas la rotación
cumple lo que el agricultor pidió.
"""

from dataclasses import dataclass

import pandas as pd

from agroshift.crops import cultivos_de_rotacion
from agroshift.soil import estado_ph as estado_ph_rangos


@dataclass(frozen=True)
class Prioridad:
    clave: str
    nombre: str
    icono: str
    columna: str
    explicacion: str


PRIORIDADES: dict[str, Prioridad] = {
    p.clave: p
    for p in [
        Prioridad(
            "agua", "Agua", "💧", "cumple_prioridad_agua",
            "La lluvia cubre al menos el 75 % del agua que necesitan los cultivos.",
        ),
        Prioridad(
            "balance", "Balance", "⚖️", "cumple_prioridad_balance",
            "La lluvia compensa la demanda de agua: no queda déficit neto (≥ 0 mm).",
        ),
        Prioridad(
            "humedad", "Humedad del suelo", "🌱", "cumple_prioridad_humedad",
            "La humedad del suelo se mantiene por encima del 25 % histórico más seco.",
        ),
        Prioridad(
            "temporal", "Ajuste temporal", "📅", "cumple_prioridad_temporal",
            "Lluvia (≥ 60 %) y humedad del suelo son suficientes al mismo tiempo.",
        ),
    ]
}

MESES = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
]


def mascara_cumple(
    escenarios: pd.DataFrame,
    prioridades: list[str],
    min_criterios: int,
) -> pd.Series:
    """True en los escenarios que cumplen todo lo que pidió el agricultor."""
    cumple = escenarios["numero_criterios_cumplidos"] >= min_criterios
    for clave in prioridades:
        cumple &= escenarios[PRIORIDADES[clave].columna]
    return cumple


def rankear_rotaciones(
    escenarios: pd.DataFrame,
    prioridades: list[str],
    min_criterios: int,
    cultivos_requeridos: list[str] | None = None,
    n_etapas: int | None = None,
    compatibilidad: dict[str, float] | None = None,
    cultivos_excluidos: set[str] | None = None,
) -> pd.DataFrame:
    """Una fila por rotación, ordenada de mejor a peor.

    `fiabilidad` = % de fechas de inicio históricas en que la rotación
    cumple las condiciones pedidas. Sólo se devuelven rotaciones con
    fiabilidad > 0.

    Los escenarios del pipeline se evalúan por balance hídrico y humedad,
    no por temperatura. `cultivos_excluidos` (ver `cultivos_no_aptos`)
    descarta rotaciones con cultivos que el clima de la región no admite,
    y `compatibilidad` (cultivo -> % ECOCROP) desempata el ranking.
    """
    df = escenarios.assign(_cumple=mascara_cumple(escenarios, prioridades, min_criterios))

    resumen = df.groupby("rotacion").agg(
        fiabilidad=("_cumple", "mean"),
        escenarios=("_cumple", "size"),
        criterios_medios=("numero_criterios_cumplidos", "mean"),
        cobertura_media=("cobertura_demanda_pct", "mean"),
        deficit_medio_mm=("deficit_balance_mm", "mean"),
        percentil_humedad=("percentil_humedad_medio", "mean"),
        duracion_dias=("duracion_total_dias", "mean"),
        n_etapas=("numero_etapas", "first"),
    )
    resumen["fiabilidad"] *= 100
    resumen = resumen[resumen["fiabilidad"] > 0].reset_index()

    if cultivos_requeridos:
        resumen = resumen[
            resumen["rotacion"].map(
                lambda r: set(cultivos_requeridos) <= set(cultivos_de_rotacion(r))
            )
        ]
    if n_etapas:
        resumen = resumen[resumen["n_etapas"] == n_etapas]

    if cultivos_excluidos:
        resumen = resumen[
            resumen["rotacion"].map(
                lambda r: not (set(cultivos_de_rotacion(r)) & cultivos_excluidos)
            )
        ]

    if compatibilidad is not None:
        resumen = resumen.assign(
            compatibilidad_media=resumen["rotacion"].map(
                lambda r: _promedio([compatibilidad.get(c, 0.0) for c in cultivos_de_rotacion(r)])
            )
        )
    else:
        resumen = resumen.assign(compatibilidad_media=float("nan"))

    return resumen.sort_values(
        ["fiabilidad", "compatibilidad_media", "criterios_medios", "deficit_medio_mm"],
        ascending=[False, False, False, True],
        na_position="last",
    ).reset_index(drop=True)


def _promedio(valores: list[float]) -> float:
    return sum(valores) / len(valores)


def cultivos_no_aptos(compatibilidad: pd.DataFrame, minimo: float) -> set[str]:
    """Cultivos que el clima de la región no admite.

    Se exige `minimo` tanto en la compatibilidad (la final, que ya no puede
    superar a la temperatura) como en el puntaje de temperatura media por
    separado: la lluvia que falta puede suplirse con riego, pero la
    temperatura no, y la fórmula de ECOCROP deja que una lluvia ideal
    compense un cultivo que no tolera el frío o el calor.
    """
    columna = (
        "compatibilidad_final"
        if "compatibilidad_final" in compatibilidad.columns
        else "compatibilidad_climatica"
    )
    no_apto = (compatibilidad[columna] < minimo) | (
        compatibilidad["puntaje_temperatura_media"] < minimo
    )
    return set(compatibilidad.loc[no_apto, "nombre"])


def sin_permutaciones(ranking: pd.DataFrame) -> pd.DataFrame:
    """Conserva sólo la mejor rotación de cada conjunto de cultivos.

    Los mismos cultivos en otro orden puntúan casi igual; mostrarlos
    todos llenaría el podio con variantes de una sola idea.
    """
    claves = ranking["rotacion"].map(lambda r: frozenset(cultivos_de_rotacion(r)))
    return ranking[~claves.duplicated()].reset_index(drop=True)


def fiabilidad_por_mes(
    escenarios: pd.DataFrame,
    rotacion: str,
    prioridades: list[str],
    min_criterios: int,
) -> pd.DataFrame:
    """% de fechas históricas que cumplen, según el mes en que se inicia."""
    df = escenarios[escenarios["rotacion"] == rotacion]
    df = df.assign(
        _cumple=mascara_cumple(df, prioridades, min_criterios),
        _mes=pd.to_datetime(df["fecha_inicio_escenario"]).dt.month,
    )
    por_mes = df.groupby("_mes")["_cumple"].mean().mul(100)
    por_mes = por_mes.reindex(range(1, 13))
    return pd.DataFrame(
        {"mes_num": range(1, 13), "mes": MESES, "fiabilidad": por_mes.to_numpy()}
    )


def estado_ph_cultivo(ph: float, cultivo: "pd.Series | dict") -> str:
    """'optimo' / 'tolerable' / 'fuera' del pH del suelo para un cultivo.

    `cultivo` es una fila de compatibilidad_cultivos_ecocrop.csv.
    """
    return estado_ph_rangos(
        ph,
        (cultivo["ph_optimo_min"], cultivo["ph_optimo_max"]),
        (cultivo["ph_absoluto_min"], cultivo["ph_absoluto_max"]),
    )
