import re
import string
from pathlib import Path

from ui.textos import MESES_CORTOS, MESES_ES_EN, TEXTOS

RAIZ = Path(__file__).resolve().parent.parent


def _campos(texto):
    return {c[1] for c in string.Formatter().parse(texto) if c[1]}


def test_cada_clave_tiene_ambos_idiomas_con_los_mismos_campos():
    for clave, (es, en) in TEXTOS.items():
        assert es.strip()
        assert en.strip()
        assert _campos(es) == _campos(en), f"{clave}: campos distintos entre ES y EN"


def test_todas_las_claves_usadas_en_la_ui_existen():
    patron = re.compile(r"""\bt\(\s*f?["']([a-zA-Z0-9_.]+)["']""")
    usadas = set()
    for archivo in [*RAIZ.joinpath("ui").rglob("*.py"), RAIZ / "app.py"]:
        usadas |= set(patron.findall(archivo.read_text(encoding="utf-8")))
    faltan = sorted(c for c in usadas if c not in TEXTOS)
    assert not faltan, f"claves sin definir: {faltan}"


def test_meses():
    assert len(MESES_CORTOS["es"]) == len(MESES_CORTOS["en"]) == 12
    assert len(MESES_ES_EN) == 12
