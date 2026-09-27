# 🌱 AgroShift

Herramienta de apoyo a la decisión para **rotación de cultivos**, construida con datos de observación de la Tierra de la NASA y de la FAO.

Proyecto para el **NASA Space Apps Challenge 2026** — reto [*"Cambio de rumbo: adaptando las granjas con datos de la NASA"*](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/).

Región de análisis: **Santander, Colombia** (año de referencia 2020).

## ¿Qué hace?

Cruza clima, humedad del suelo y requerimientos agronómicos para recomendar **secuencias de rotación de cultivos** que:

- Aprovechen mejor la precipitación disponible (cobertura de la demanda hídrica).
- Mantengan un balance hídrico favorable (precipitación vs. evapotranspiración del cultivo, ETc).
- Se ajusten a los rangos de humedad del suelo históricos.
- Encajen temporalmente con las ventanas de siembra.

## Fuentes de datos

| Fuente | Variable | Uso |
|---|---|---|
| [NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) | Temperatura, precipitación, humedad, viento, radiación (diario) | Clima base y cálculo de ETo/ETc |
| [NASA SMAP L4](https://nsidc.org/data/spl4smgp/versions/8) | Humedad del suelo superficial y de zona radicular | Estado hídrico del suelo |
| [FAO ECOCROP](https://www.fao.org/geospatial/data-and-tools/data-portals/ecocrop/) | Requerimientos de temperatura, lluvia, pH, ciclo por cultivo | Compatibilidad climática de cultivos |

## Estructura del proyecto

```
AgroShift/
├── app.py                  # App web (Streamlit) — MVP de presentación
├── requirements.txt        # Dependencias de la app (Streamlit Cloud las usa)
├── python/
│   ├── requirements.txt    # Dependencias del pipeline de análisis
│   ├── nasa_power.py       # Descarga de datos NASA POWER
│   ├── nasa_smap.py        # Descarga de datos NASA SMAP
│   ├── obtener_cultivos_ecocrop.py  # Descarga de datos FAO ECOCROP
│   ├── calcular_eto*.py / calcular_etc.py  # Evapotranspiración (FAO-56)
│   ├── analisis_*.py       # Análisis ambiental, hídrico y de rotaciones
│   ├── analisis_rotacion_v10.py    # Última versión del análisis por etapas
│   ├── analisis_escenarios_rotacion_v7.py  # Última versión de escenarios priorizados
│   └── data/
│       ├── analysis/       # CSVs y gráficas generadas (resultados)
│       └── crops/          # Catálogo de cultivos y compatibilidad ECOCROP
└── docs/
```

> Los scripts en `python/` tienen sufijos de versión (`_v5`, `_v8`, `_v10`...) porque son iteraciones del análisis. La app (`app.py`) consume los resultados **ya calculados** en `python/data/analysis/`, no vuelve a correr el pipeline.

## Cómo correr la app localmente

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
streamlit run app.py
```

Abre `http://localhost:8501`.

## Cómo regenerar los datos de análisis (opcional)

Los scripts en `python/` necesitan sus propias dependencias (incluye `earthaccess` para autenticarse contra NASA Earthdata):

```bash
cd python
pip install -r requirements.txt
python nasa_power.py
python nasa_smap.py
# ...
python analisis_rotacion_v10.py
```

## Despliegue

La app está pensada para desplegarse gratis en [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Conecta este repositorio de GitHub.
2. Archivo principal: `app.py`.
3. Streamlit Cloud instala automáticamente `requirements.txt` de la raíz.
