"""Tests del dashboard de datos reales (r03).

Por que existe este fichero
---------------------------
El dashboard publicaba cifras escritas a mano en la prosa: el error del motor, la
distancia entre niveles de fiabilidad, el tamano del conjunto de datos. Todas
eran correctas el dia que se escribieron. El problema no es que estuvieran mal,
es que no se recalculan: en cuanto cambian los datos, el HTML se desincroniza en
silencio y no salta nada.

El test central es `test_toda_cifra_publicada_sale_del_json`. Compara lo que se
lee en el HTML con lo que dice el JSON, hasta el decimal que se publica, y por eso
atrapa la familia entera de fallos y no solo los de un dia.

Los dos tests de formato y de recorte no necesitan `data/real/`, asi que corren
tambien en la integracion continua.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

import r03_dashboard_real as r03  # noqa: E402

DIR_REAL = RAIZ / "data" / "real"
NECESARIOS = ["metricas_2018.json", "valoraciones_2018.csv", "barrios_madrid.csv",
              "caso_trazado.json", "diagnostico_coeficientes_2018.json"]


def _num(texto: str) -> float:
    """Numero a la espanola -> float. '5.161,88' -> 5161.88"""
    return float(texto.replace(".", "").replace(",", "."))


@pytest.fixture(scope="module")
def dashboard(tmp_path_factory) -> str:
    faltan = [f for f in NECESARIOS if not (DIR_REAL / f).exists()]
    if faltan:
        pytest.skip(f"faltan en data/real/: {', '.join(faltan)}")
    salida = tmp_path_factory.mktemp("dash") / "dashboard_real.html"
    original, r03.F_SALIDA = r03.F_SALIDA, salida
    try:
        r03.construir()
    finally:
        r03.F_SALIDA = original
    return salida.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def metricas() -> dict:
    if not (DIR_REAL / "metricas_2018.json").exists():
        pytest.skip("no hay metricas_2018.json")
    return json.loads((DIR_REAL / "metricas_2018.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------- el test central
def _afirmaciones(m: dict, diag: dict) -> list[tuple]:
    """(nombre, patron, valor esperado) para cada cifra que el HTML publica.

    El patron ancla la cifra a SU sitio en el texto. Comprobar solo que el valor
    aparece en alguna parte del documento no vale: "12,0 %" sale tambien en la
    tabla de metodos, asi que un "12 %" tecleado en la prosa pasaria inadvertido.
    Eso es exactamente el fallo que este test tiene que atrapar.
    """
    mo, bb, bc = (m["motor_comparables"], m["base_mediana_barrio"],
                  m["base_mediana_ciudad"])
    fiab, por_n = m["error_por_fiabilidad"], m["error_por_n_comparables"]
    cen, tramo = diag["efecto_del_centrado"], diag["tramo_monotono_calidad"]
    N, P = r03._n, r03._p

    return [
        # --- banda de cifras de cabecera
        ("error mediano (cifra)",
         r"<b>([^<]+)</b><span>error mediano fuera de muestra", P(mo["error_absoluto_mediano"])),
        ("dentro de ±10 % (cifra)",
         r"<b>([^<]+)</b><span>estimaciones dentro de ±10 %", P(mo["dentro_de_10pct"])),
        ("cobertura (cifra)", r"<b>([^<]+)</b><span>cobertura", P(m["cobertura"])),
        ("sesgo (cifra)", r"<b>([^<]+)</b><span>sesgo", P(mo["sesgo_mediano"])),

        # --- prosa de la cabecera y del sello
        ("anuncios de evaluación", r"Una agregada, sobre ([\d.]+)\s*anuncios reales",
         N(m["n_evaluacion"])),
        ("anuncios de origen", r"idealista18</b>, ([\d.]+)\s*anuncios\s*de venta",
         N(m["n_anuncios_origen"])),

        # --- la frase que lleva la cifra suelta, la que estaba a mano
        ("error del motor en prosa", r"Un error del ([\d.,]+ %)", P(mo["error_absoluto_mediano"])),

        # --- la lectura honesta contra la línea base
        ("mejora sobre la base del barrio", r"línea base del barrio en\s*([\d.,]*\d) puntos",
         N((bb["error_absoluto_mediano"] - mo["error_absoluto_mediano"]) * 100, 1)),
        ("base del barrio en prosa", r"ya te lleva al\s*([\d.,]+ %)",
         P(bb["error_absoluto_mediano"])),
        ("base de la ciudad en prosa", r"no distinguir zona\s*\(([\d.,]+ %)\)",
         P(bc["error_absoluto_mediano"])),

        # --- fiabilidad: los dos extremos, sin resta
        ("fiabilidad alta en prosa", r"va de ([\d.,]+ %) en el nivel alto", P(fiab["alta"])),
        ("fiabilidad baja en prosa", r"a ([\d.,]+ %) en el bajo", P(fiab["baja"])),

        # --- dispersión frente a número de comparables
        ("error con pocos comparables", r"baja el error del\s*([\d.,]+ %)",
         P(por_n["5-9"]["error_absoluto_mediano"])),
        ("error con muchos comparables", r"baja el error del\s*[\d.,]+ %\s*al\s*([\d.,]+ %)",
         P(por_n["50 o mas"]["error_absoluto_mediano"])),

        # --- el caso trazado
        ("anuncios del pool en el embudo", r"Paso 1 — De ([\d.]+) anuncios", N(m["n_pool"])),

        # --- el bloque de límites
        ("VIF máximo", r"VIF más alto de todo el modelo es ([\d.,]*\d)",
         N(max(diag["vif"].values()), 2)),
        ("correlación máxima", r"correlación más fuerte entre regresores es ([\d.,]*\d)",
         N(abs(diag["correlaciones"]["correlacion_maxima"]), 3)),
        ("jardín sin centrar", r"el jardín se va a\s*(-?[\d.,]+ %)",
         P(np.expm1(cen["jardin"]["sin_centrar"]))),
        ("jardín en el modelo", r"en vez de\s*(-?[\d.,]+ %)", P(np.expm1(m["coeficientes"]["jardin"]))),
        ("calidad catastral corregida", r"Ya está invertida, sale en\s*(-?[\d.,]+ %)",
         P(np.expm1(m["coeficientes"]["calidad_catastral"]))),
        ("jardines con piscina", r"Encaja con que el\s*([\d.,]+ %)",
         P(diag["pct_jardin_con_piscina"])),
        ("identificadores únicos", r"los ([\d.]+)\s*identificadores",
         N(m["n_identificadores_unicos"])),
        ("anuncios en los códigos sin resolver", r"Son ([\d.]+)\s*anuncios",
         N(tramo["anuncios_fuera"])),
    ]


def test_toda_cifra_publicada_sale_del_json(dashboard, metricas):
    """Cada cifra del HTML, en su sitio, comparada con la del JSON.

    Si alguien vuelve a teclear un numero en la prosa, o si los datos cambian y
    el texto se queda viejo, esto falla y dice cual.
    """
    diag = json.loads(
        (DIR_REAL / "diagnostico_coeficientes_2018.json").read_text(encoding="utf-8"))

    fallos = []
    for nombre, patron, esperado in _afirmaciones(metricas, diag):
        encontrado = re.search(patron, dashboard, re.S)
        if not encontrado:
            fallos.append(f"{nombre}: no se encuentra en el HTML (patrón {patron!r})")
        elif " ".join(encontrado[1].split()) != esperado:
            fallos.append(f"{nombre}: el HTML dice {encontrado[1]!r} "
                          f"y el JSON dice {esperado!r}")

    assert not fallos, "cifras publicadas que no cuadran con el JSON:\n  " + \
                       "\n  ".join(fallos)


def test_la_ecuacion_del_caso_cuadra(dashboard):
    """La multiplicacion escrita tiene que dar el resultado escrito.

    Antes no daba: la mediana salia redondeada a entero (5.162) y 5.162 x 73 son
    376.826, no los 376.817 que se publicaban. El resultado era correcto y la
    ecuacion, falsa.
    """
    eq = re.search(r"Valor estimado: <b>([\d.,]+) × (\d+) m²\s*=\s*([\d.,]+) €</b>",
                   dashboard)
    assert eq, "no se encuentra la ecuación del valor estimado en el HTML"

    mediana, superficie, valor = _num(eq[1]), int(eq[2]), _num(eq[3])
    # El resultado se publica redondeado al euro, asi que se admite medio euro.
    assert abs(mediana * superficie - valor) <= 0.5 + superficie * 0.005


def test_ninguna_cifra_de_fiabilidad_se_presenta_como_una_resta(dashboard):
    """La distancia entre niveles ya no se publica como diferencia.

    Se publicaba "5,6 puntos entre extremos", correcto sobre los valores exactos
    (0,1037 y 0,1593), pero irreproducible por quien lee la pantalla: alli pone
    10,4 y 15,9, que restados dan 5,5. Se dan los dos extremos y no la resta.
    """
    assert "puntos entre extremos" not in dashboard


# --------------------------------------------- formato y recorte, sin datos
@pytest.mark.parametrize("valor, dec, esperado", [
    (6522.5, 0, "6.523"),      # el caso que lo destapo: Castellana
    (2.5, 0, "3"),             # al par daria 2
    (0.5, 0, "1"),             # al par daria 0
    (-6522.5, 0, "-6.523"),    # el medio se va hacia arriba en magnitud
    (1234567.0, 0, "1.234.567"),
    (5161.88, 2, "5.161,88"),
])
def test_el_redondeo_es_comercial_y_no_al_par(valor, dec, esperado):
    """Python redondea al par, asi que 6.522,5 daba 6.522 en el dashboard y
    6.523 en la documentacion. Misma cifra, dos valores, ninguno mal."""
    assert r03._n(valor, dec) == esperado


def test_el_porcentaje_no_arrastra_el_error_del_binario():
    # 0.1035 * 100 en float da 10.349999999999998, que truncado bajaria a 10,3.
    assert r03._p(0.1035) == "10,4 %"
    assert r03._p(0.1037) == "10,4 %"
    assert r03._p(0.1593) == "15,9 %"


def test_el_pie_del_histograma_cabe_dentro_del_viewbox():
    """El texto estaba en y=186 dentro de un viewBox de alto 184 y se recortaba."""
    v = pd.DataFrame({"valor_estimado": np.linspace(90, 110, 60),
                      "precio_pedido": np.full(60, 100.0)})
    svg = r03.histograma_error(v)

    alto = float(re.search(r'viewBox="0 0 [\d.]+ ([\d.]+)"', svg)[1])
    ys = [float(y) for y in re.findall(r'<text[^>]*\sy="([\d.]+)"', svg)]
    assert ys, "el histograma no tiene ningún texto"
    assert max(ys) <= alto, f"texto en y={max(ys)} fuera del viewBox de alto {alto}"
