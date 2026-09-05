"""Tests del motor de comparables.

El bloque importante es el de fugas. Un motor de valoracion con fuga de
informacion da resultados excelentes y no sirve para nada, y el fallo no se ve
mirando los numeros: hay que comprobarlo explicitamente.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import config as cfg                              # noqa: E402
from p03_valorar import valorar                   # noqa: E402


def cartera(n=60, distrito="Centro", superficie=80, eur_m2=5000,
            inicio="2025-01-01", paso_dias=3):
    """Cartera sintetica homogenea: todos comparables entre si."""
    fechas = pd.to_datetime(inicio) + pd.to_timedelta(
        np.arange(n) * paso_dias, unit="D")
    return pd.DataFrame({
        "ref": [f"T-{i:03d}" for i in range(n)],
        "fecha": fechas,
        "distrito": distrito,
        "superficie_m2": float(superficie),
        "habitaciones": 3, "banos": 1, "planta": 1,
        "ascensor": True, "exterior": True, "estado": "buen estado",
        "anio_construccion": 1980,
        "precio_eur": float(eur_m2 * superficie),
        "eur_m2": float(eur_m2),
        "apta_valoracion": True,
    })


# ------------------------------------------------------------------- fugas
def test_ningun_inmueble_esta_en_sus_propios_comparables():
    r = valorar(cartera())
    for _, fila in r.iterrows():
        assert fila["ref"] not in str(fila["refs_comparables"]).split(";")


def test_ningun_comparable_es_del_mismo_dia_o_posterior():
    df = cartera()
    fechas = dict(zip(df["ref"], df["fecha"]))
    r = valorar(df)
    for _, fila in r.iterrows():
        for ref in filter(None, str(fila["refs_comparables"]).split(";")):
            assert fechas[ref] < fechas[fila["ref"]]


def test_mismo_dia_no_cuenta_como_comparable():
    """Cinco anuncios el mismo dia no se valoran entre si."""
    df = cartera(n=5, paso_dias=0)
    r = valorar(df)
    assert r["n_comparables"].max() == 0


def test_el_futuro_no_cambia_el_pasado():
    """Anadir anuncios posteriores no puede alterar valoraciones ya emitidas."""
    df = cartera(n=40)
    base = valorar(df)
    extra = cartera(n=20, eur_m2=12_000, inicio="2026-06-01")
    extra["ref"] = [f"F-{i:03d}" for i in range(20)]
    ampliado = valorar(pd.concat([df, extra], ignore_index=True))

    comun = base.merge(ampliado, on="ref", suffixes=("_a", "_b"))
    pd.testing.assert_series_equal(
        comun["valor_estimado_eur_a"], comun["valor_estimado_eur_b"],
        check_names=False)


# ------------------------------------------------------------ reglas de corte
def test_sin_muestra_suficiente_no_se_inventa_una_valoracion():
    df = cartera(n=cfg.MIN_COMPARABLES)     # el primero no tiene historico
    r = valorar(df)
    primeras = r.head(cfg.MIN_COMPARABLES)
    assert primeras["valor_estimado_eur"].isna().all()
    assert (primeras["clasificacion"] == "no valorable").all()


def test_comparables_solo_del_mismo_distrito():
    a = cartera(n=30, distrito="Centro", eur_m2=6000)
    b = cartera(n=30, distrito="Usera", eur_m2=2000)
    b["ref"] = [f"U-{i:03d}" for i in range(30)]
    r = valorar(pd.concat([a, b], ignore_index=True))
    ultima_centro = r[r["ref"] == "T-029"].iloc[0]
    assert all(x.startswith("T-") for x in ultima_centro["refs_comparables"].split(";"))


def test_superficie_fuera_de_banda_se_excluye():
    a = cartera(n=30, superficie=80)
    b = cartera(n=30, superficie=200)          # +150%, fuera de la banda de +/-20%
    b["ref"] = [f"G-{i:03d}" for i in range(30)]
    b["precio_eur"] = b["eur_m2"] * 200
    r = valorar(pd.concat([a, b], ignore_index=True))
    ultima = r[r["ref"] == "T-029"].iloc[0]
    assert all(x.startswith("T-") for x in ultima["refs_comparables"].split(";"))


def test_ventana_temporal_descarta_lo_demasiado_antiguo():
    df = cartera(n=40, paso_dias=30)           # 40 meses de historico
    r = valorar(df)
    ultima = r.iloc[-1]
    esperado_max = cfg.VENTANA_DIAS // 30
    assert ultima["n_comparables"] <= esperado_max


# ------------------------------------------------------------------- calculo
def test_precio_en_linea_da_desviacion_cero():
    r = valorar(cartera(n=40))
    v = r[r["desviacion"].notna()]
    assert v["desviacion"].abs().max() < 1e-9


def test_precio_un_20_por_ciento_por_debajo_se_detecta():
    df = cartera(n=40)
    df.loc[df.index[-1], "precio_eur"] = 5000 * 80 * 0.80
    df.loc[df.index[-1], "eur_m2"] = 5000 * 0.80
    r = valorar(df)
    ultima = r[r["ref"] == df.iloc[-1]["ref"]].iloc[0]
    assert ultima["desviacion"] == pytest.approx(-0.20, abs=1e-6)
    assert ultima["clasificacion"] == "por debajo de comparables"


def test_score_acotado_entre_0_y_100():
    df = cartera(n=40)
    df.loc[df.index[-1], "precio_eur"] = 5000 * 80 * 0.1
    df.loc[df.index[-1], "eur_m2"] = 500
    r = valorar(df)
    s = r["score_oportunidad"].dropna()
    assert s.between(0, 100).all()


def test_resultado_reproducible():
    df = cartera(n=40)
    a, b = valorar(df.copy()), valorar(df.copy())
    pd.testing.assert_frame_equal(a, b)
