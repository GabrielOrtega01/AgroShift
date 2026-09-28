import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agroshift.regions import get_region

REGION = get_region(os.environ.get("AGROSHIFT_REGION", "santander"))
REGION_SLUG = REGION.slug


# ============================================================
# AGROSHIFT
# CÁLCULO DE EVAPOTRANSPIRACIÓN DE REFERENCIA (ETo)
# FAO-56 Penman-Monteith - cálculo diario
# ============================================================

print("=" * 70)
print("AGROSHIFT - ETo FAO-56 PENMAN-MONTEITH")
print(f"Región: {REGION.nombre}")
print("=" * 70)


# ------------------------------------------------------------
# RUTAS
# ------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ARCHIVO_ENTRADA = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    REGION_SLUG,
    "agroshift_environmental_2020.csv"
)

ARCHIVO_SALIDA = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    REGION_SLUG,
    "eto_2020.csv"
)

ARCHIVO_GRAFICA = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    REGION_SLUG,
    "eto_diaria_2020.png"
)

ARCHIVO_MENSUAL = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    REGION_SLUG,
    "eto_mensual_2020.csv"
)


# ------------------------------------------------------------
# CONSTANTES FAO-56
# ------------------------------------------------------------

LATITUD = REGION.latitud
ALTITUD = REGION.altitud_m   # m s.n.m., valor aproximado para el punto
ALBEDO = 0.23
SIGMA = 4.903e-9      # MJ K^-4 m^-2 día^-1


# ------------------------------------------------------------
# FUNCIONES
# ------------------------------------------------------------

def radiacion_extraterrestre(latitud, dia_ano):
    """
    Calcula Ra (MJ/m²/día) según FAO-56.
    """

    phi = np.deg2rad(latitud)

    dr = 1 + 0.033 * np.cos(
        2 * np.pi / 365 * dia_ano
    )

    delta = 0.409 * np.sin(
        2 * np.pi / 365 * dia_ano - 1.39
    )

    omega_s = np.arccos(
        -np.tan(phi) * np.tan(delta)
    )

    Gsc = 0.0820

    Ra = (
        (24 * 60 / np.pi)
        * Gsc
        * dr
        * (
            omega_s * np.sin(phi) * np.sin(delta)
            +
            np.cos(phi)
            * np.cos(delta)
            * np.sin(omega_s)
        )
    )

    return Ra


def presion_atmosferica(altitud):
    """
    Presión atmosférica aproximada (kPa)
    según FAO-56.
    """

    return 101.3 * (
        ((293 - 0.0065 * altitud) / 293)
        ** 5.26
    )


# ------------------------------------------------------------
# CARGAR DATOS
# ------------------------------------------------------------

print("\nCargando datos ambientales NASA 2020...")

df = pd.read_csv(ARCHIVO_ENTRADA)

print(f"✓ Registros cargados: {len(df)}")


# ------------------------------------------------------------
# VALIDAR COLUMNAS
# ------------------------------------------------------------

columnas_requeridas = [
    "fecha",
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "WS10M",
    "ALLSKY_SFC_SW_DWN"
]

faltantes = [
    columna
    for columna in columnas_requeridas
    if columna not in df.columns
]

if faltantes:
    raise ValueError(
        f"Faltan columnas requeridas: {faltantes}"
    )


# ------------------------------------------------------------
# CONVERSIÓN DE DATOS
# ------------------------------------------------------------

df["fecha"] = pd.to_datetime(
    df["fecha"],
    errors="coerce"
)

for columna in columnas_requeridas[1:]:
    df[columna] = pd.to_numeric(
        df[columna],
        errors="coerce"
    )


df = df.dropna(
    subset=columnas_requeridas
).copy()


# ------------------------------------------------------------
# DÍA DEL AÑO
# ------------------------------------------------------------

df["dia_ano"] = df["fecha"].dt.dayofyear


# ------------------------------------------------------------
# 1. TEMPERATURA
# ------------------------------------------------------------

T = df["T2M"]

Tmax = df["T2M_MAX"]

Tmin = df["T2M_MIN"]


# ------------------------------------------------------------
# 2. VIENTO
# ------------------------------------------------------------

# NASA POWER entrega viento a 10 m.
#
# FAO-56 utiliza viento a 2 m.

z = 10.0

df["u2"] = (
    df["WS10M"]
    * 4.87
    / np.log(67.8 * z - 5.42)
)


# ------------------------------------------------------------
# 3. PRESIÓN ATMOSFÉRICA
# ------------------------------------------------------------

P = presion_atmosferica(ALTITUD)

print("\nParámetros del sitio")
print("-" * 70)

print(f"Latitud:                    {LATITUD:.3f}°")
print(f"Altitud utilizada:          {ALTITUD:.1f} m")
print(f"Presión atmosférica:        {P:.2f} kPa")


# ------------------------------------------------------------
# 4. CONSTANTE PSICROMÉTRICA
# ------------------------------------------------------------

gamma = 0.000665 * P

df["gamma"] = gamma


# ------------------------------------------------------------
# 5. PRESIÓN DE VAPOR DE SATURACIÓN
# ------------------------------------------------------------

def presion_vapor_saturacion(temperatura):
    return (
        0.6108
        * np.exp(
            (17.27 * temperatura)
            / (temperatura + 237.3)
        )
    )


df["es_tmax"] = presion_vapor_saturacion(Tmax)

df["es_tmin"] = presion_vapor_saturacion(Tmin)

df["es"] = (
    df["es_tmax"]
    + df["es_tmin"]
) / 2


# ------------------------------------------------------------
# 6. PRESIÓN DE VAPOR REAL
# ------------------------------------------------------------

df["ea"] = (
    df["es"]
    * df["RH2M"]
    / 100
)


# ------------------------------------------------------------
# 7. DÉFICIT DE PRESIÓN DE VAPOR
# ------------------------------------------------------------

df["deficit_presion_vapor"] = (
    df["es"]
    - df["ea"]
)


# ------------------------------------------------------------
# 8. PENDIENTE DE LA CURVA DE PRESIÓN DE VAPOR
# ------------------------------------------------------------

df["delta"] = (
    4098
    * df["es"]
    / (T + 237.3) ** 2
)


# ------------------------------------------------------------
# 9. RADIACIÓN SOLAR Rs
# ------------------------------------------------------------

# NASA POWER - comunidad AG
#
# ALLSKY_SFC_SW_DWN:
# Radiación solar incidente en superficie.
#
# Para los datos diarios utilizados en este proyecto
# se trabaja en MJ/m²/día.
#
# No se realiza conversión adicional.

df["Rs"] = df["ALLSKY_SFC_SW_DWN"]


# ------------------------------------------------------------
# 10. RADIACIÓN EXTRATERRESTRE Ra
# ------------------------------------------------------------

df["Ra"] = df["dia_ano"].apply(
    lambda x: radiacion_extraterrestre(
        LATITUD,
        x
    )
)


# ------------------------------------------------------------
# 11. RADIACIÓN DE CIELO DESPEJADO Rso
# ------------------------------------------------------------

df["Rso"] = (
    0.75
    + 2e-5 * ALTITUD
) * df["Ra"]


# ------------------------------------------------------------
# 12. RADIACIÓN NETA DE ONDA CORTA Rns
# ------------------------------------------------------------

df["Rns"] = (
    (1 - ALBEDO)
    * df["Rs"]
)


# ------------------------------------------------------------
# 13. RELACIÓN Rs / Rso
# ------------------------------------------------------------

df["Rs_Rso"] = (
    df["Rs"]
    / df["Rso"]
)

# FAO limita la relación a 1
df["Rs_Rso"] = df["Rs_Rso"].clip(
    upper=1.0
)


# ------------------------------------------------------------
# 14. RADIACIÓN NETA DE ONDA LARGA Rnl
# ------------------------------------------------------------

Tmax_K = Tmax + 273.16

Tmin_K = Tmin + 273.16

df["Rnl"] = (
    SIGMA
    * (
        (
            Tmax_K ** 4
            +
            Tmin_K ** 4
        ) / 2
    )
    * (
        0.34
        - 0.14
        * np.sqrt(
            df["ea"].clip(lower=0)
        )
    )
    * (
        1.35
        * df["Rs_Rso"]
        - 0.35
    )
)


# ------------------------------------------------------------
# 15. RADIACIÓN NETA TOTAL
# ------------------------------------------------------------

df["Rn"] = (
    df["Rns"]
    - df["Rnl"]
)


# Evitar radiación neta negativa extrema
df["Rn"] = df["Rn"].clip(
    lower=0
)


# ------------------------------------------------------------
# 16. FLUJO DE CALOR DEL SUELO
# ------------------------------------------------------------

# Para cálculo diario FAO-56:
# G ≈ 0

G = 0.0


# ------------------------------------------------------------
# 17. ETo FAO PENMAN-MONTEITH
# ------------------------------------------------------------

numerador = (
    0.408
    * df["delta"]
    * (df["Rn"] - G)
    +
    gamma
    * (
        900
        / (T + 273)
    )
    * df["u2"]
    * df["deficit_presion_vapor"]
)

denominador = (
    df["delta"]
    +
    gamma
    * (
        1
        + 0.34 * df["u2"]
    )
)


df["ETo"] = (
    numerador
    / denominador
)


# ------------------------------------------------------------
# 18. CONTROL DE VALORES
# ------------------------------------------------------------

df["ETo"] = df["ETo"].clip(
    lower=0
)


# ------------------------------------------------------------
# 19. GUARDAR RESULTADO DIARIO
# ------------------------------------------------------------

columnas_salida = [
    "fecha",
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "WS10M",
    "u2",
    "ALLSKY_SFC_SW_DWN",
    "Rs",
    "Ra",
    "Rso",
    "Rns",
    "Rnl",
    "Rn",
    "es",
    "ea",
    "deficit_presion_vapor",
    "delta",
    "ETo"
]

resultado = df[columnas_salida].copy()


resultado.to_csv(
    ARCHIVO_SALIDA,
    index=False
)


# ------------------------------------------------------------
# 20. ESTADÍSTICAS
# ------------------------------------------------------------

print("\n" + "-" * 70)
print("RESULTADOS ETo FAO-56")
print("-" * 70)

print(
    f"ETo media:             "
    f"{resultado['ETo'].mean():.2f} mm/día"
)

print(
    f"ETo mínima:            "
    f"{resultado['ETo'].min():.2f} mm/día"
)

print(
    f"ETo máxima:            "
    f"{resultado['ETo'].max():.2f} mm/día"
)

print(
    f"ETo acumulada 2020:    "
    f"{resultado['ETo'].sum():.2f} mm"
)

print(
    f"\nRadiación neta media:   "
    f"{resultado['Rn'].mean():.2f} MJ/m²/día"
)

print(
    f"Radiación solar media:  "
    f"{resultado['Rs'].mean():.2f} MJ/m²/día"
)

print(
    f"Viento a 2 m medio:     "
    f"{resultado['u2'].mean():.2f} m/s"
)


# ------------------------------------------------------------
# 21. RESUMEN MENSUAL
# ------------------------------------------------------------

resultado["mes"] = (
    resultado["fecha"].dt.month
)
resultado["anio"] = (
    resultado["fecha"].dt.year
)

eto_mensual = (
    resultado
    .groupby("mes")
    .agg(
        ETo_media=("ETo", "mean"),
    )
    .reset_index()
)

# ETo_acumulada es una suma dentro de un mes: con varios años hay que
# sumar por (año, mes) y luego promediar entre años, o el acumulado de
# varios eneros quedaría sumado como si fuera un solo mes.
eto_acumulada_por_anio = (
    resultado.groupby(["anio", "mes"])["ETo"]
    .sum()
    .reset_index(name="ETo_acumulada")
)

eto_acumulada_promedio = (
    eto_acumulada_por_anio.groupby("mes")["ETo_acumulada"]
    .mean()
    .reset_index()
)

eto_mensual = eto_mensual.merge(eto_acumulada_promedio, on="mes")


eto_mensual.to_csv(
    ARCHIVO_MENSUAL,
    index=False
)


print("\nETo acumulada por mes:")
print(
    eto_mensual.to_string(
        index=False
    )
)


# ------------------------------------------------------------
# 22. GRÁFICA
# ------------------------------------------------------------

plt.figure(
    figsize=(12, 6)
)

plt.plot(
    resultado["fecha"],
    resultado["ETo"]
)

plt.title(
    "Evapotranspiración de referencia ETo - AgroShift 2020"
)

plt.xlabel(
    "Fecha"
)

plt.ylabel(
    "ETo (mm/día)"
)

plt.grid(
    True,
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    ARCHIVO_GRAFICA,
    dpi=150
)

plt.close()


# ------------------------------------------------------------
# 23. VALIDACIÓN
# ------------------------------------------------------------

print("\n" + "-" * 70)
print("VALIDACIÓN")
print("-" * 70)

print(
    f"✓ Registros procesados: "
    f"{len(resultado)}"
)

print(
    f"✓ Valores ETo calculados: "
    f"{resultado['ETo'].notna().sum()}"
)

print(
    f"✓ Valores negativos: "
    f"{(resultado['ETo'] < 0).sum()}"
)

print(
    f"✓ Valores faltantes: "
    f"{resultado['ETo'].isna().sum()}"
)

print(
    f"✓ Archivo diario generado:"
)

print(
    ARCHIVO_SALIDA
)

print(
    f"\n✓ Archivo mensual generado:"
)

print(
    ARCHIVO_MENSUAL
)

print(
    f"\n✓ Gráfica generada:"
)

print(
    ARCHIVO_GRAFICA
)

print("\n" + "=" * 70)
print("✓ CÁLCULO FAO-56 DE ETo COMPLETADO")
print("=" * 70)