from pathlib import Path

import earthaccess


# ============================================================
# CONFIGURACIÓN
# ============================================================

LATITUD = 7.119
LONGITUD = -73.122

FECHA_INICIO = "2020-01-01"
FECHA_FIN = "2020-12-31"

OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "smap"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# AUTENTICACIÓN
# ============================================================

print("=" * 60)
print("INSPECCIÓN SMAP - AGROSHIFT")
print("=" * 60)

print("\nIniciando sesión en NASA Earthdata...")

earthaccess.login()

print("Autenticación completada.")


# ============================================================
# BÚSQUEDA
# ============================================================

print("\nBuscando archivos SMAP...")

resultados = earthaccess.search_data(
    short_name="SPL4SMGP",
    temporal=(FECHA_INICIO, FECHA_FIN),
    bounding_box=(
        LONGITUD,
        LATITUD,
        LONGITUD,
        LATITUD
    )
)


# ============================================================
# RESULTADOS
# ============================================================

print("\n" + "=" * 60)
print("RESULTADO DE LA BÚSQUEDA")
print("=" * 60)

print(f"\nPeriodo:")
print(f"{FECHA_INICIO} -> {FECHA_FIN}")

print(f"\nArchivos encontrados: {len(resultados)}")

if len(resultados) > 0:
    tamanio_aproximado_gb = (
        len(resultados) * 140
    ) / 1024

    print(
        f"Tamaño aproximado de descarga: "
        f"{tamanio_aproximado_gb:.2f} GB"
    )

    print("\nPrimeros archivos encontrados:")

    for granulo in resultados[:5]:
        print(granulo)

    print("\nÚltimos archivos encontrados:")

    for granulo in resultados[-5:]:
        print(granulo)

else:
    print("\nNo se encontraron archivos SMAP para el periodo indicado.")

print("\nInspección terminada.")