"""Actualizacion a precios de hoy, precio de firma estimado y demo.

Los tests de arriba no necesitan los datos reales y corren en la integracion
continua. Los de abajo (motor y app de la demo) necesitan
data/real/madrid_2018.csv y se saltan si no esta.
"""
import io
import json
import sys
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "demo"))

import r05_referencia_precios as r05  # noqa: E402
import r06_actualizacion_cierre as r06  # noqa: E402
import r07_cierres_agencia as r07  # noqa: E402

HAY_DATOS = Path(r06.F_ENTRADA).exists()


# --- Ficheros de referencia ---------------------------------------------------

def test_escrituras_2018_cuadran_con_su_propia_tabla():
    """La transcripcion del PDF se comprueba sola: los tramos suman el total.

    Salvo donde la propia fuente descuadra, que va declarado en la cabecera del
    CSV. Si aparece un descuadre nuevo, es un error al transcribir."""
    e = r06.leer_ref(r06.F_ESC_2018)
    assert len(e) == 21 and e["distrito_id"].tolist() == list(range(1, 22))
    tramos = e[[c for *_, c in r06.TRAMOS]].sum(axis=1)
    descuadre = dict(zip(e["distrito"], e["transacciones_2018"] - tramos))
    declarados = {"Chamberi": 313, "Latina": 2, "Usera": 1,
                  "Villa de Vallecas": 1, "Vicalvaro": 3}
    assert {d: v for d, v in descuadre.items() if v} == declarados
    assert "DESCUADRE DE LA FUENTE" in r06.F_ESC_2018.read_text(encoding="utf-8")
    assert e[["eur_m2_total_2018", "eur_m2_usada_2018"]].gt(1000).all().all()


@pytest.mark.parametrize("ruta", [r06.F_ESC_2018, r06.F_ESC_ACTUAL, r06.F_IPV])
def test_referencias_declaran_fuente_y_fecha(ruta):
    assert r06.cabecera(ruta, "FUENTE")
    assert r06.cabecera(ruta, "CONSULTADO")[:10].count("/") == 2


def test_la_registral_no_es_la_tabla_de_idealista():
    """La tabla de segunda mano del Anuario es de idealista (oferta). Su ciudad
    en 2018 es 3.466 EUR/m2. La registral de 2018 no puede coincidir con ella."""
    texto = r06.F_ESC_2018.read_text(encoding="utf-8")
    assert "3.2" in texto and "OFERTA" in texto
    e = r06.leer_ref(r06.F_ESC_2018)
    assert e.loc[e["distrito"] == "Centro", "eur_m2_total_2018"].item() == pytest.approx(4809.31)


def test_ipv_trae_2018_y_el_ultimo_ano_completo():
    ipv = r06.leer_ref(r06.F_IPV)
    anio = int(r06.leer_ref(r06.F_ESC_ACTUAL)["anio"].iloc[0])
    for a in (2018, anio):
        assert ipv["trimestre"].str.startswith(str(a)).sum() == 4


# --- Lectores de r05 con ficheros de juguete ----------------------------------

def test_leer_precio_declarado_de_un_xlsx_como_el_del_ayuntamiento():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append([None, "6. Precio medio declarado"])
    ws.append([None, 2031])
    ws.append([None, "Ciudad de Madrid", 5000, 5100, 4900])
    for i in range(1, 22):
        ws.append([None, f"{i:02d}. Distrito {i}", 1000 + i, 1100 + i, 900 + i])
        ws.append([None, f"{i:02d}1. Un barrio", 1, 1, 1])
    buf = io.BytesIO()
    wb.save(buf)
    anio, d = r05.leer_precio_declarado(buf.getvalue())
    assert anio == 2031 and len(d) == 21
    assert d.loc[0, "eur_m2_usada"] == 901


def test_leer_precio_declarado_falla_si_cambia_la_forma():
    wb = openpyxl.Workbook()
    wb.active.append([None, "01. Centro", 1, 2, 3])
    buf = io.BytesIO()
    wb.save(buf)
    with pytest.raises(ValueError):
        r05.leer_precio_declarado(buf.getvalue())


def test_leer_ipv_de_una_respuesta_como_la_del_ine():
    serie = lambda nombre, v: {"Nombre": nombre, "Data": [  # noqa: E731
        {"Anyo": 2018, "FK_Periodo": 19, "Valor": v},
        {"Anyo": 2017, "FK_Periodo": 22, "Valor": 1.0}]}
    d = r05.leer_ipv([
        serie("Madrid, Comunidad de. General. Índice. ", 60.0),
        serie("Madrid, Comunidad de. Vivienda nueva. Índice. ", 55.0),
        serie("Madrid, Comunidad de. Vivienda segunda mano. Índice. ", 66.0),
        serie("Madrid, Comunidad de. General. Variación anual. ", 9.9),
        serie("Galicia. General. Índice. ", 1.0),
    ])
    assert d.to_dict("records") == [
        {"trimestre": "2018T1", "general": 60.0, "nueva": 55.0, "segunda_mano": 66.0}]


# --- Factores y brecha de r06 --------------------------------------------------

def _ipv_juguete():
    t = [f"{a}T{q}" for a in (2018, 2025) for q in range(1, 5)] + ["2026T1"]
    v = [90, 90, 90, 90, 100, 100, 100, 100, 110]
    return pd.DataFrame({"trimestre": t, "segunda_mano": v})


def test_factor_de_actualizacion_compone_registro_e_ipv():
    e18 = pd.DataFrame({"distrito_id": [1], "distrito": ["X"], "eur_m2_usada_2018": [2000.0]})
    eac = pd.DataFrame({"distrito_id": [1], "eur_m2_usada": [3000.0], "anio": [2025]})
    f, meta = r06.factores_actualizacion(e18, eac, _ipv_juguete())
    # 3000/2000 x 110/100 x 90/90
    assert f["factor_actualizacion"].item() == pytest.approx(1.5 * 1.1)
    assert f["factor_solo_ine"].item() == pytest.approx(110 / 90)
    assert meta["trimestre_actual"] == "2026T1"


def test_factor_falla_si_falta_un_trimestre():
    ipv = _ipv_juguete().drop(index=5)
    e18 = pd.DataFrame({"distrito_id": [1], "distrito": ["X"], "eur_m2_usada_2018": [1.0]})
    eac = pd.DataFrame({"distrito_id": [1], "eur_m2_usada": [1.0], "anio": [2025]})
    with pytest.raises(ValueError):
        r06.factores_actualizacion(e18, eac, ipv)


def _registro(usada, mezcla=(0, 0, 1, 0, 0)):
    return pd.Series({"eur_m2_usada_2018": usada,
                      **{c: m for (*_, c), m in zip(r06.TRAMOS, mezcla)}})


def test_brecha_nula_si_anuncio_y_escritura_coinciden():
    a = pd.DataFrame({"eur_m2": [3000.0] * 6, "CONSTRUCTEDAREA": [70] * 6})
    b = r06.brecha_distrito(a, _registro(3000.0))
    assert b["brecha_min"] == pytest.approx(0) and b["brecha_max"] == pytest.approx(0)


def test_brecha_reponderada_usa_la_mezcla_que_se_escrituro():
    # Pisos pequenos caros y grandes baratos. Si solo se escrituran grandes, la
    # media reponderada tiene que ser la de los grandes.
    a = pd.DataFrame({"eur_m2": [5000.0, 5000.0, 2000.0],
                      "CONSTRUCTEDAREA": [35, 35, 120]})
    b = r06.brecha_distrito(a, _registro(1800.0, mezcla=(0, 0, 0, 0, 10)))
    assert b["eur_m2_anuncio_media_reponderada"] == pytest.approx(2000.0)
    assert b["brecha_media_reponderada"] == pytest.approx(0.1)
    assert b["brecha_min"] <= b["brecha_central"] <= b["brecha_max"]


def test_pesos_por_tramo_suman_uno():
    s = pd.Series([30, 50, 50, 70, 90, 150])
    mezcla = {c: 0.2 for *_, c in r06.TRAMOS}
    assert r06.pesos_por_tramo(s, mezcla).sum() == pytest.approx(1)


def test_factores_publicados_son_coherentes_con_las_referencias():
    """Lo versionado en data/real/factores_distrito.csv se recalcula desde los
    CSV de referencia, sin datos de anuncios."""
    f = pd.read_csv(r06.F_FACTORES)
    rec, _ = r06.factores_actualizacion(r06.leer_ref(r06.F_ESC_2018),
                                        r06.leer_ref(r06.F_ESC_ACTUAL),
                                        r06.leer_ref(r06.F_IPV))
    assert np.allclose(f["factor_actualizacion"], rec["factor_actualizacion"], atol=1e-4)
    assert (f["brecha_min"] <= f["brecha_central"] + 1e-9).all()
    assert (f["brecha_central"] <= f["brecha_max"] + 1e-9).all()
    assert f["factor_actualizacion"].between(1, 3).all()
    resumen = json.loads(r06.F_RESUMEN.read_text(encoding="utf-8"))
    assert resumen["brecha_max_distritos"] == pytest.approx(f["brecha_max"].max(), abs=1e-4)


# --- Cierres de agencia (r07) ---------------------------------------------------

def _cierres(n, distrito="Chamberi", descuento=0.05):
    return pd.DataFrame({
        "distrito": [distrito] * n, "superficie_m2": [80] * n,
        "fecha_publicacion": ["2026-01-01"] * n,
        "precio_publicado_inicial": [520_000] * n,
        "precio_publicado_final": [500_000] * n,
        "fecha_firma": ["2026-03-01"] * n,
        "precio_cierre": [500_000 * (1 - descuento)] * n,
    })


def test_plantilla_de_agencia_es_valida():
    d = r07.validar(pd.read_csv(r07.F_PLANTILLA))
    assert len(d) == 1


@pytest.mark.parametrize("columna", ["direccion", "Nombre vendedor", "teléfono", "ref_catastral"])
def test_agencia_rechaza_datos_personales(columna):
    d = _cierres(3).assign(**{columna: "x"})
    with pytest.raises(ValueError, match="personales"):
        r07.validar(d)


def test_descuento_de_agencia_y_umbral_de_muestra():
    d = pd.concat([_cierres(r07.MIN_CIERRES, "Chamberí", 0.05),
                   _cierres(r07.MIN_CIERRES - 1, "Usera", 0.08)])
    s = r07.descuentos(r07.validar(d)).set_index("distrito_canon")
    assert s.loc["chamberi", "descuento_final_mediana"] == pytest.approx(0.05)
    assert s.loc["chamberi", "dias_en_mercado_mediana"] == 59
    assert bool(s.loc["chamberi", "suficiente"]) is True
    assert bool(s.loc["usera", "suficiente"]) is False


def test_agencia_descarta_filas_imposibles():
    d = _cierres(2)
    d.loc[0, "fecha_firma"] = "2025-01-01"   # firma antes de publicar
    assert len(r07.validar(d)) == 1


# --- Motor y app de la demo (necesitan datos reales) --------------------------

necesita_datos = pytest.mark.skipif(not HAY_DATOS, reason="sin data/real/madrid_2018.csv")


@pytest.fixture(scope="module")
def motor():
    from motor import Motor
    return Motor()


@necesita_datos
def test_ejemplos_de_la_demo_se_valoran(motor):
    from motor import COMPARABLES_A_MOSTRAR, EJEMPLOS
    from r01_valorar_real import MIN_COMPARABLES
    distritos = set()
    for ficha in EJEMPLOS.values():
        r = motor.valorar(ficha)
        assert r.valorable and r.n_comparables >= MIN_COMPARABLES
        assert 0 < len(r.comparables) <= COMPARABLES_A_MOSTRAR
        assert r.cierre_min <= r.cierre_max
        assert r.oferta_hoy == pytest.approx(r.valor_2018 * r.factor_actualizacion, abs=500)
        distritos.add(r.distrito)
    assert len(distritos) == len(EJEMPLOS), "los ejemplos tienen que ser de zonas distintas"


@necesita_datos
def test_demo_usa_la_misma_valoracion_que_se_valido(motor):
    """El valor de 2018 tiene que ser exactamente el de r01.valorar."""
    import r01_valorar_real as r01
    from motor import EJEMPLOS
    ficha = next(iter(EJEMPLOS.values()))
    directo = r01.valorar(motor.pool, motor.fila(ficha), motor.beta).iloc[0]
    assert motor.valorar(ficha).valor_2018 == directo["valor_estimado"]


@necesita_datos
def test_coeficientes_de_la_demo_son_los_publicados(motor):
    import r01_valorar_real as r01
    publicados = json.loads(r01.F_METRICAS.read_text(encoding="utf-8"))["coeficientes"]
    for v, b in zip(r01.VARIABLES, motor.beta[1:]):
        assert round(float(b), 4) == publicados[v]


@necesita_datos
def test_sin_muestra_no_se_inventa_cifra(motor):
    from motor import EJEMPLOS
    ficha = {**next(iter(EJEMPLOS.values())), "superficie_m2": 400}
    r = motor.valorar(ficha)
    assert not r.valorable and np.isnan(r.oferta_hoy)


@necesita_datos
def test_descuento_de_agencia_sustituye_al_publico(motor, monkeypatch):
    from motor import EJEMPLOS
    ficha = next(iter(EJEMPLOS.values()))
    s = r07.descuentos(r07.validar(_cierres(r07.MIN_CIERRES, "Chamberí", 0.05)))
    monkeypatch.setattr(motor, "agencia", s.set_index("distrito_canon"))
    r = motor.valorar(ficha)
    assert "agencia" in r.origen_descuento
    assert r.descuento_min == pytest.approx(0.05) and r.descuento_max == pytest.approx(0.05)


@necesita_datos
def test_la_app_arranca_y_carga_los_ejemplos():
    st = pytest.importorskip("streamlit.testing.v1")
    at = st.AppTest.from_file(str(RAIZ / "demo" / "app.py"), default_timeout=90).run()
    assert not at.exception
    for i in range(len(at.button)):
        at.button[i].click().run()
        assert not at.exception
        assert any(m.value.startswith("## ") and "€" in m.value for m in at.markdown)
