from pathlib import Path
import h5py


BASE_DIR = Path(__file__).resolve().parent

archivo = (
    BASE_DIR
    / "data"
    / "smap"
    / "SMAP_L4_SM_gph_20200101T133000_Vv8010_001.h5"
)


def mostrar_atributos(objeto, titulo):
    print(f"\n--- {titulo} ---")

    if not objeto.attrs:
        print("No tiene atributos.")

    for clave, valor in objeto.attrs.items():
        if isinstance(valor, bytes):
            valor = valor.decode("utf-8", errors="replace")

        print(f"{clave}: {valor}")


print("=" * 70)
print("INSPECCIÓN DEL TIEMPO SMAP")
print("=" * 70)

print(f"\nArchivo:")
print(archivo)

if not archivo.exists():
    print("\nERROR: No se encontró el archivo.")
    print("Verifica que el archivo exista dentro de data\\smap")
    exit()


with h5py.File(archivo, "r") as hdf:

    # ---------------------------------------------------------
    # Dataset time
    # ---------------------------------------------------------
    time_ds = hdf["time"]

    print("\n--- Dataset time ---")
    print("Shape:", time_ds.shape)
    print("Tipo de dato:", time_ds.dtype)
    print("Valor:", time_ds[()])

    mostrar_atributos(time_ds, "Atributos del dataset time")

    # ---------------------------------------------------------
    # Atributos generales del archivo
    # ---------------------------------------------------------
    mostrar_atributos(hdf, "Atributos generales del archivo")

    # ---------------------------------------------------------
    # Buscar atributos relacionados con tiempo o fecha
    # ---------------------------------------------------------
    print("\n--- Atributos relacionados con tiempo/fecha ---")

    encontrados = False

    def buscar_atributos(nombre, objeto):
        global encontrados

        for clave, valor in objeto.attrs.items():

            clave_lower = clave.lower()

            if (
                "time" in clave_lower
                or "date" in clave_lower
                or "begin" in clave_lower
                or "end" in clave_lower
            ):

                if isinstance(valor, bytes):
                    valor = valor.decode("utf-8", errors="replace")

                print(f"{nombre} -> {clave}: {valor}")
                encontrados = True

    hdf.visititems(buscar_atributos)

    if not encontrados:
        print("No se encontraron atributos relacionados con fecha/hora.")


print("\n" + "=" * 70)
print("INSPECCIÓN TERMINADA")
print("=" * 70)