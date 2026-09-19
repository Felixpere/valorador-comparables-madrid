"""Tests de la constancia del motor: un entregable degradado no puede pasar por completo.

Sin pasada de LLM el pipeline sigue siendo valido, pero el entregable pierde la
comparacion entre motores. Tiene que avisarlo la consola al arrancar y al
terminar, y tiene que constar en metricas.json y en la hoja Resumen del Excel.
"""
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ))

import p01_extraer                              # noqa: E402
from p04_evaluar import estado_del_entregable   # noqa: E402
from p05_exportar_excel import linea_entregable  # noqa: E402
import run_pipeline                             # noqa: E402

LLM = "llm:claude-haiku-4-5"


def _mezcla(llm=0, reglas=0, respaldo=0):
    return pd.DataFrame(
        [{"motor_extraccion": LLM}] * llm
        + [{"motor_extraccion": "reglas"}] * reglas
        + [{"motor_extraccion": "reglas (respaldo)"}] * respaldo)


# ----------------------------------------------------------- estado en el JSON
def test_solo_reglas_queda_marcado_como_incompleto():
    e = estado_del_entregable(_mezcla(reglas=2000))
    assert e["estado"] == "solo_reglas"
    assert e["motores"] == {"reglas": 2000}
    assert "NO lleva la comparación" in e["aviso"]


def test_con_la_muestra_del_llm_esta_completo():
    e = estado_del_entregable(_mezcla(llm=25, reglas=1975))
    assert e == {"estado": "completo", "motores": {LLM: 25, "reglas": 1975}, "aviso": None}


def test_si_parte_de_la_muestra_cae_a_reglas_es_parcial_y_lo_cuenta():
    e = estado_del_entregable(_mezcla(llm=22, reglas=1975, respaldo=3))
    assert e["estado"] == "parcial"
    assert "3 de los 25 anuncios" in e["aviso"]
    assert "se hace sobre 22" in e["aviso"]


# ----------------------------------------------------------- estado en el Excel
def test_el_excel_dice_si_esta_incompleto():
    texto, incompleto = linea_entregable({"entregable": estado_del_entregable(_mezcla(reglas=2000))})
    assert incompleto is True
    assert texto.startswith("ENTREGABLE INCOMPLETO")
    assert "reglas (2.000 anuncios)" in texto


def test_el_excel_dice_con_que_motores_se_hizo_cuando_esta_completo():
    texto, incompleto = linea_entregable(
        {"entregable": estado_del_entregable(_mezcla(llm=25, reglas=1975))})
    assert incompleto is False
    assert texto == f"Extracción: {LLM} (25 anuncios) + reglas (1.975 anuncios). Entregable completo."


def test_metricas_sin_estado_no_pasan_por_completas():
    texto, incompleto = linea_entregable({})
    assert incompleto is True and "SIN ESTADO" in texto


# ----------------------------------------------------------- consola
def test_se_sabe_antes_de_arrancar_por_que_no_habra_llm(monkeypatch):
    assert p01_extraer.motivo_sin_llm("reglas") == "motor forzado a reglas (--motor reglas)"
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert p01_extraer.motivo_sin_llm("auto") == "no hay ANTHROPIC_API_KEY en el entorno"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setattr(p01_extraer.importlib.util, "find_spec", lambda nombre: None)
    assert "anthropic" in p01_extraer.motivo_sin_llm("auto")
    monkeypatch.setattr(p01_extraer.importlib.util, "find_spec", lambda nombre: object())
    assert p01_extraer.motivo_sin_llm("auto") is None


def test_el_aviso_sale_por_stderr_y_como_warning_en_github_actions(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    run_pipeline.avisar("texto de prueba")
    out, err = capsys.readouterr()
    assert "AVISO: texto de prueba" in err and "::warning" not in out
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    run_pipeline.avisar("texto de prueba")
    out, _ = capsys.readouterr()
    assert "::warning title=Entregable incompleto::texto de prueba" in out
