"""Selección de 1 gránulo SMAP por día (de los 8 disponibles cada 3h).

SMAP L4 publica una imagen cada 3 horas. Descargar las 8/día para 6 años
de historial en varias regiones es inviable en la práctica: cada archivo
tarda ~7s en descargarse desde los servidores de NASA (medido), así que
8/día × 365 × 6 años ya son ~34h por región solo en SMAP.

Nos quedamos con la lectura más cercana a una hora fija por día — es
suficiente para el resto del pipeline, que solo necesita una señal
diaria de humedad del suelo, no la variación intradiaria.
"""

import re

HORA_OBJETIVO = "133000"  # 13:30 UTC ≈ media mañana en Colombia (UTC-5)

_PATRON_FECHA_HORA = re.compile(r"_(\d{8})T(\d{6})_")


def un_granulo_por_dia(resultados, hora_objetivo: str = HORA_OBJETIVO):
    """Filtra una lista de gránulos SMAP, dejando solo el más cercano
    a `hora_objetivo` (HHMMSS) por cada día calendario presente."""

    mejores = {}

    for granulo in resultados:
        enlaces = granulo.data_links()
        if not enlaces:
            continue

        nombre = enlaces[0].split("/")[-1]
        match = _PATRON_FECHA_HORA.search(nombre)
        if not match:
            continue

        fecha, hora = match.groups()
        diferencia = abs(int(hora) - int(hora_objetivo))

        actual = mejores.get(fecha)
        if actual is None or diferencia < actual[0]:
            mejores[fecha] = (diferencia, granulo)

    return [granulo for _, granulo in mejores.values()]
