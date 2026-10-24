"""La barra de la demo dibuja las cifras del motor tal cual, sin calcular nada.

No necesitan datos reales: se construye el grafico con cifras de prueba y se mira
que lo que se dibuja y lo que se rotula sean exactamente esas cifras.
"""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "demo"))

pytest.importorskip("altair")
import pandas as pd  # noqa: E402

from graficos import (FIRMA, PIDE, TOOLTIP_MAPA, barra_pedido_firma,  # noqa: E402
                      datos_barra, mapa_comparables)

CIFRAS = dict(oferta=244_000, margen_min=215_000, margen_max=273_000,
              firma_min=217_000, firma_max=239_000)


def test_las_piezas_son_las_cifras_del_motor():
    piezas, _ = datos_barra(**CIFRAS)
    p = piezas.set_index("pieza")
    assert (p.loc["margen", "desde"], p.loc["margen", "hasta"]) == (215_000, 273_000)
    assert (p.loc["anuncio", "desde"], p.loc["anuncio", "hasta"]) == (244_000, 244_000)
    assert (p.loc["firma", "desde"], p.loc["firma", "hasta"]) == (217_000, 239_000)
    assert p.loc["firma", "fila"] == FIRMA and p.loc["anuncio", "fila"] == PIDE


def test_las_etiquetas_dicen_las_mismas_cifras():
    _, etiquetas = datos_barra(**CIFRAS)
    textos = " | ".join(etiquetas["texto"])
    for cifra in ["244.000 €", "215.000 €", "273.000 €", "217.000 € – 239.000 €"]:
        assert cifra in textos


def test_firma_por_encima_del_anuncio_tambien_se_dibuja():
    # Distritos donde de media se escrituro por encima de lo anunciado
    piezas, _ = datos_barra(oferta=300_000, margen_min=264_000, margen_max=336_000,
                            firma_min=295_000, firma_max=315_000)
    firma = piezas.set_index("pieza").loc["firma"]
    assert firma["hasta"] > 300_000


def _puntos(n=12, destacados=8):
    return pd.DataFrame({
        "lat": [40.43 + i * 0.001 for i in range(n)],
        "lon": [-3.70 + i * 0.001 for i in range(n)],
        "m2": [60 + i for i in range(n)],
        "eur_m2_2018": [5000 + 10 * i for i in range(n)],
        "eur_m2_hoy": [9000 + 10 * i for i in range(n)],
        "destacado": [i < destacados for i in range(n)],
    })


def test_el_mapa_separa_los_de_la_tabla_del_resto():
    pytest.importorskip("pydeck")
    deck = mapa_comparables(_puntos())
    # pydeck guarda los datos de cada capa como lista de registros
    resto, destacados = (pd.DataFrame(c.data) for c in deck.layers)
    assert len(resto) == 4 and len(destacados) == 8
    assert destacados["destacado"].all() and not resto["destacado"].any()


def test_el_mapa_se_centra_en_los_comparables_y_rotula_en_euros():
    pytest.importorskip("pydeck")
    p = _puntos()
    deck = mapa_comparables(p)
    assert deck.initial_view_state.latitude == pytest.approx(p["lat"].mean())
    assert deck.initial_view_state.longitude == pytest.approx(p["lon"].mean())
    destacados = pd.DataFrame(deck.layers[1].data)
    assert destacados["eur_m2_hoy_txt"].iloc[0] == "9.000"
    assert "€/m²" in TOOLTIP_MAPA["html"]


def test_la_escala_deja_ver_todo():
    spec = barra_pedido_firma(**CIFRAS).to_dict()
    dominios = [c["encoding"]["x"]["scale"]["domain"] for c in spec["layer"]
                if "scale" in c["encoding"].get("x", {})]
    assert dominios and all(d == dominios[0] for d in dominios), "una sola escala de euros"
    lo, hi = dominios[0]
    assert lo < 215_000 and hi > 273_000
