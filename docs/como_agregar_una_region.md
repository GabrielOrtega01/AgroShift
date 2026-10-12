# Cómo agregar una región nueva

AgroShift puede crecer sin tocar código: una región es un punto de referencia
(coordenadas + altitud) y su pipeline de datos.

Hay dos tipos de región, según de dónde sale la humedad del suelo:

| Tipo | `fuente_humedad` | Humedad del suelo | Costo de agregarla |
|---|---|---|---|
| **SMAP** | `smap` | Medida por el satélite NASA SMAP L4 | Cuenta NASA Earthdata y varias horas de descarga |
| **Modelo** | `modelo` | Estimada con un balance hídrico a partir de NASA POWER (`agroshift/hydrology.py`) | Solo internet; ~3 min de análisis (+~30 min la primera vez por la lluvia IMERG) |

Las 4 regiones originales (Santander, Quindío, Córdoba y Boyacá) usan SMAP. Las
que se agregan con la herramienta de abajo usan modelo, y la app lo rotula
(«estimada con modelo»).

## Región con humedad modelada (recomendado)

```bash
cd python

python agregar_region.py \
  --slug meta \
  --nombre "Meta (piedemonte llanero)" \
  --clima "Cálido y húmedo, arroz, palma y maíz" \
  --latitud 4.15 --longitud -73.63 --altitud 467 \
  --ejecutar
```

- `--slug`: identificador en minúsculas, sin tildes ni espacios.
- `--altitud`: metros sobre el nivel del mar (se usa para la presión atmosférica
  y la radiación en el cálculo de ETo).
- `--ejecutar`: además de registrar la región corre `run_pipeline.py` para ella.
  Sin esta opción solo la registra (en `python/data/regiones_adicionales.json`).

El pipeline de una región modelada ejecuta: NASA POWER → suelo (SoilGrids,
opcional) → lluvia IMERG y totales CHIRPS (opcionales; requieren Earthdata y
~30 min la primera vez, porque cada archivo diario de IMERG es global) →
análisis 06–19. No descarga SMAP ni vuelve a bajar ECOCROP si ya
existe.

Al terminar, la región aparece sola en el selector de la app (se listan las
regiones que tienen resultados). Para publicarla en Streamlit Cloud hay que
subir a GitHub su carpeta `python/data/analysis/<slug>/` (los archivos
intermedios pesados ya están excluidos por `.gitignore`), su
`python/data/power/nasa_power_<slug>.csv`, `python/data/soil/suelo_<slug>.csv`
y `python/data/regiones_adicionales.json`.

Para que el nombre y el clima de la región salgan traducidos al inglés, agrega
tres claves en `ui/textos.py` (`region.<slug>.nombre`, `.corto` y `.clima`); si
faltan, la app usa el texto en español.

## Región con SMAP

1. Resuelve la celda de la grilla SMAP EASE-Grid 2.0 del punto: descarga un
   gránulo de muestra y busca la celda más cercana en sus arreglos
   `cell_lat`/`cell_lon` (el algoritmo está en `python/02_descargar_nasa_smap.py`).
2. Agrega un `Region(...)` con `fila_smap` y `columna_smap` a `_REGIONES_SMAP`
   en `python/agroshift/regions.py`.
3. Configura tus credenciales una vez:
   `python -c "import earthaccess; earthaccess.login(persist=True)"`.
4. `python run_pipeline.py --region <slug>`. La descarga de SMAP tarda varias
   horas (1 lectura por día, ~3.5 s por archivo).

## Cómo validar el resultado

```bash
python -m pytest            # estructura y rangos de los CSV de cada región
python validar_precipitacion.py   # contrasta la lluvia de POWER con CHIRPS
```
