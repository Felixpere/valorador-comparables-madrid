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
from graficos import FIRMA, PIDE, barra_pedido_firma, datos_barra  # noqa: E402

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


def test_la_escala_deja_ver_todo():
    spec = barra_pedido_firma(**CIFRAS).to_dict()
    dominios = [c["encoding"]["x"]["scale"]["domain"] for c in spec["layer"]
                if "scale" in c["encoding"].get("x", {})]
    assert dominios and all(d == dominios[0] for d in dominios), "una sola escala de euros"
    lo, hi = dominios[0]
    assert lo < 215_000 and hi > 273_000
