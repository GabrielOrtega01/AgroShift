# 🌱 AgroShift

🇪🇸 [Leer en español](README.md)

A **crop-rotation decision-support tool** built with NASA and FAO Earth-observation data.

Built for the **NASA Space Apps Challenge 2026** — [*Field Shift: Adapting Farms with NASA Data*](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/).

🌐 **Live app:** https://agroshift.streamlit.app (Spanish / English toggle at the top)

A farmer picks their region and the app shows the crop rotations best suited to **their** climate, soil and water history — instead of one fixed point.

## What it does

It combines climate, soil moisture, soil properties and crop requirements to recommend **crop-rotation sequences** that:

- Make the best use of available rainfall (share of crop water demand covered).
- Keep a favourable water balance (rainfall vs. crop evapotranspiration, ETc).
- Fit the historical soil-moisture range.
- Match planting windows in time.
- Respect what the climate allows: a crop's suitability never exceeds what mean temperature and days within its range permit, and unsuitable crops are excluded.

The farmer chooses what to prioritise (water, balance, moisture, timing), how strict to be and which crops to include. The app returns a podium of rotations with their **historical reliability** (the share of 2020–2025 start dates on which they meet the request), the **best months to start**, and soil-pH warnings.

### Regions

| Region | Soil moisture |
|---|---|
| Santander, Quindío, Córdoba, Boyacá | Satellite-measured (NASA SMAP L4) |
| Cundinamarca, Valle del Cauca, Meta, Nariño | **Estimated** with a water balance from NASA POWER (labelled as such in the app) |

Adding a region is a data task, not a code task: see [`docs/como_agregar_una_region.md`](docs/como_agregar_una_region.md) (Spanish).

## Data sources

| Source | Variables | Used for |
|---|---|---|
| [NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) | Daily temperature, humidity, wind, radiation | Base climate and ETo/ETc |
| [NASA GPM IMERG](https://gpm.nasa.gov/data/imerg) | Daily rainfall (satellite + rain gauges, 0.1°) | **Rainfall source**, magnitude adjusted to CHIRPS |
| [NASA SMAP L4](https://nsidc.org/data/spl4smgp/versions/8) | Surface and root-zone soil moisture | Soil water status |
| [FAO ECOCROP](https://www.fao.org/geospatial/data-and-tools/data-portals/ecocrop/) | Per-crop temperature, rainfall, pH and cycle requirements | Crop climate suitability |
| [ISRIC SoilGrids](https://soilgrids.org/) | Soil texture, pH, organic carbon (0–30 cm, 250 m) | Regional soil and pH warnings |
| [CHIRPS](https://www.chc.ucsb.edu/data/chirps) | Monthly rainfall (satellite + rain gauges) | Reference to adjust IMERG's magnitude and to validate |

## Data quality and limits

Rainfall is **NASA GPM IMERG**, with its magnitude adjusted to CHIRPS monthly totals. The three sources were compared (`python/validar_precipitacion.py`, results in `python/data/validation/`):

- **NASA POWER was dropped for rainfall:** monthly correlation with CHIRPS r = 0.44–0.81 (mean 0.66), 2021 is ~70 % drier in Santander and Boyacá comes out 2× wetter.
- **Unadjusted IMERG** follows month-to-month and year-to-year variation better (r = 0.62–0.92, mean 0.77) but **overestimates totals** in several mountain areas (Santander +81 %, Valle +74 %, Nariño +109 %, Cundinamarca +124 %). So its daily distribution is kept and each month is scaled to CHIRPS, which matches known climatologies better.
- **Absolute millimetres remain approximate** (not validated against IDEAM stations) and 92 of 2,192 days have no IMERG file: NASA POWER fills them. The app shows the comparison in the *How it works* tab.
- Modelled soil moisture (used in 4 regions) was checked against SMAP in the 4 regions that have it (`python/validar_humedad_modelo.py`): the monthly climatology correlates at r = 0.69–0.96 and the daily rank order (Spearman) at 0.65–0.82. It is an estimate, not a measurement.
- Soil is a global estimate (SoilGrids): confirm pH and fertility with a lab test.
- Each region is a **reference point**, not an exact farm. Prices, costs and pests are not considered.
- **Temperature adjusted to elevation:** NASA POWER returns the temperature of a ~50 km cell at its mean elevation (e.g. 2,112 m for a Cauca-valley point that sits at 1,000 m); it is adjusted to the point with the standard 6.5 °C/km lapse rate (`agroshift/downscaling.py`). After the adjustment, the mean temperatures of all 8 regions match known values (±1 °C).
- ECOCROP has no useful elevation limits (coffee up to 2,800 m) nor killing temperatures for most crops, and the 50 km cell does not capture local frosts: above 2,000 m the app warns to check frost risk.

## Project layout

```
AgroShift/
├── app.py                 # Streamlit entry point
├── ui/                    # Presentation layer (theme, components, i18n, views per tab)
├── tests/                 # pytest: domain, recommender, text catalog, result CSVs
├── .github/workflows/     # CI running the tests on every push
├── docs/                  # How to add a region, submission material
└── python/
    ├── run_pipeline.py    # Orchestrator: --region, --fecha-inicio, --fecha-fin
    ├── agregar_region.py  # Register a new region (modelled soil moisture)
    ├── agroshift/         # Domain package: regions, recommender, hydrology, soil, water, sources, pipeline
    ├── 01_…05_            # Data acquisition (POWER, SMAP, ECOCROP)
    ├── 18_…               # Soil (SoilGrids), optional step
    ├── 06_…12_            # Analysis (integration, ETo FAO-56, ETc, water balance, suitability)
    └── 13_…17_            # Rotation engine
```

Design patterns used: Config/Singleton, Registry, Repository, Strategy (data sources), Pipeline / Chain of Responsibility (with *optional* steps), retry with backoff, and a Streamlit-free domain service (`recommender.py`) that is unit-tested.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
streamlit run app.py
```

Run the tests with `pip install pytest && python -m pytest`.

## Regenerate the analysis data (optional)

```bash
cd python
python run_pipeline.py --region quindio                 # full pipeline for one region
python run_pipeline.py --region quindio --analysis-only # reprocess existing raw data
python agregar_region.py --slug meta --nombre "Meta (Llanos foothills)" \
  --clima "Warm and humid: rice, oil palm, maize" --latitud 4.15 --longitud -73.63 --altitud 467 --ejecutar
```

SMAP regions require a NASA Earthdata account (`earthaccess.login(persist=True)`); regions with modelled moisture only need internet access. A full analysis of one region (steps 06→19) takes about 3 minutes; the IMERG download (~30 min, once for all regions) and SMAP are the slow parts.

## Deploy

Free on [Streamlit Community Cloud](https://streamlit.io/cloud): connect the repo, main file `app.py`, and set **Settings → General → Python version** to **3.12**.
