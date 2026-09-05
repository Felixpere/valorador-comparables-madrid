"""Tests del tramo texto -> dato limpio."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from p01_extraer import extraer_reglas          # noqa: E402
from p02_normalizar import normalizar           # noqa: E402


# --------------------------------------------------------------- extraccion
def test_precio_con_separador_de_miles_espanol():
    d = extraer_reglas("La propiedad pide 227.000 euros.")
    assert d["precio_eur"] == 227_000


def test_precio_abreviado_en_miles():
    d = extraer_reglas("MD-0010 | Centro | 59m2 | 360k EUR")
    assert d["precio_eur"] == 360_000


def test_sin_ascensor_no_se_confunde_con_con_ascensor():
    assert extraer_reglas("planta 4, sin ascensor").get("ascensor") is False
    assert extraer_reglas("El edificio dispone de ascensor.").get("ascensor") is True
    assert extraer_reglas("pl.7 s/asc").get("ascensor") is False


def test_a_reformar_no_se_clasifica_como_reformado():
    assert extraer_reglas("El inmueble esta a reformar").get("estado") == "a reformar"
    assert extraer_reglas("Piso reformado en 2021").get("estado") == "reformado"


def test_campo_ausente_se_deja_vacio_y_no_se_inventa():
    d = extraer_reglas("Piso en Retiro, 80 m2. Precio a consultar.")
    assert d["precio_eur"] is None
    assert d["habitaciones"] is None


def test_texto_sin_tildes_se_resuelve_igual():
    con = extraer_reglas("Vivienda en Chamberí, 90 metros cuadrados")
    sin = extraer_reglas("Vivienda en Chamberi, 90 metros cuadrados")
    assert con["distrito"] == sin["distrito"] == "Chamberi"


# ------------------------------------------------------------- normalizacion
def _fila(**kw):
    base = dict(ref="X-1", distrito="Centro", superficie_m2=80, habitaciones=3,
                banos=1, planta=2, ascensor=True, estado="buen estado",
                anio_construccion=1980, exterior=True, precio_eur=400_000,
                fecha="2026-01-15", formato_origen="ficha",
                motor_extraccion="reglas")
    base.update(kw)
    return base


def test_variantes_de_distrito_se_unifican():
    df = pd.DataFrame([_fila(ref="A", distrito="puente vallecas"),
                       _fila(ref="B", distrito="SAN BLAS"),
                       _fila(ref="C", distrito="Chamberí")])
    out, _ = normalizar(df)
    assert list(out["distrito"]) == ["Puente de Vallecas", "San Blas-Canillejas",
                                     "Chamberi"]


def test_distrito_desconocido_no_se_adivina():
    out, inc = normalizar(pd.DataFrame([_fila(distrito="Alcobendas")]))
    assert pd.isna(out.iloc[0]["distrito"])
    assert not out.iloc[0]["apta_valoracion"]
    assert "distrito no reconocido" in set(inc["motivo"])


def test_valor_fuera_de_rango_se_anula_y_se_registra():
    out, inc = normalizar(pd.DataFrame([_fila(superficie_m2=4000)]))
    assert pd.isna(out.iloc[0]["superficie_m2"])
    assert any("fuera de rango" in m for m in inc["motivo"])


def test_duplicados_por_referencia_se_eliminan():
    out, inc = normalizar(pd.DataFrame([_fila(), _fila()]))
    assert len(out) == 1
    assert "referencia duplicada" in set(inc["motivo"])


def test_fila_sin_precio_no_es_apta_pero_se_conserva():
    out, _ = normalizar(pd.DataFrame([_fila(precio_eur=None)]))
    assert len(out) == 1
    assert not out.iloc[0]["apta_valoracion"]


def test_imputaciones_quedan_marcadas():
    out, _ = normalizar(pd.DataFrame([_fila(estado=None, exterior=None)]))
    assert bool(out.iloc[0]["estado_imputado"])
    assert bool(out.iloc[0]["exterior_imputado"])
    assert out.iloc[0]["estado"] == "buen estado"


def test_eur_m2_se_calcula_bien():
    out, _ = normalizar(pd.DataFrame([_fila(precio_eur=400_000, superficie_m2=80)]))
    assert out.iloc[0]["eur_m2"] == pytest.approx(5000.0)
