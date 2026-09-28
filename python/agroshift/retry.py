"""Reintentos ante errores de red transitorios.

Las descargas SMAP corren horas seguidas; un único corte de red (DNS,
timeout) sin reintento tira toda la corrida. `con_reintentos` reintenta
la llamada con espera creciente antes de rendirse.
"""

import time


def con_reintentos(func, intentos: int = 4, espera_base: int = 5):
    for intento in range(1, intentos + 1):
        try:
            return func()
        except Exception as error:
            if intento == intentos:
                raise
            espera = espera_base * intento
            print(
                f"  Fallo de red ({error}); reintentando en {espera}s "
                f"({intento}/{intentos})..."
            )
            time.sleep(espera)
