import earthaccess

# ============================================================
# AGROSHIFT - NASA SMAP
# Búsqueda de datos de humedad del suelo
# ============================================================

LATITUDE = 7.119
LONGITUDE = -73.122

START_DATE = "2020-01-01"
END_DATE = "2020-01-03"

print("==========================================")
print("        AGROSHIFT - NASA SMAP")
print("==========================================")

print("\nUbicación:")
print(f"Latitud: {LATITUDE}")
print(f"Longitud: {LONGITUDE}")

print(f"\nPeriodo:")
print(f"{START_DATE} - {END_DATE}")

print("\nBuscando datos SMAP...")

try:
    results = earthaccess.search_data(
        short_name="SPL4SMGP",
        temporal=(START_DATE, END_DATE),
        bounding_box=(
            LONGITUDE,
            LATITUDE,
            LONGITUDE,
            LATITUDE
        )
    )

    print("\n==========================================")
    print("RESULTADO DE LA BÚSQUEDA")
    print("==========================================")

    print(f"\nArchivos encontrados: {len(results)}")

    if results:
        print("\nPrimeros resultados:")

        for i, result in enumerate(results[:5], start=1):
            print(f"\n--- Resultado {i} ---")
            print(result)

    else:
        print("\nNo se encontraron archivos SMAP.")

except Exception as error:
    print("\nERROR:")
    print(error)