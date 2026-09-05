"""Paso R01 — Motor de comparables sobre datos REALES y su validacion.

Diseno de la validacion
-----------------------
Los anuncios se parten en dos por sorteo con semilla fija:

  * POOL (70 %)       — el unico conjunto del que pueden salir comparables, y el
                        unico con el que se estiman los coeficientes de ajuste.
  * EVALUACION (30 %) — anuncios que el motor no ha visto nunca. Se estima su
                        valor y se compara con lo que realmente pedian.

Ningun anuncio de evaluacion participa en su propia valoracion, ni directamente
ni a traves de los coeficientes. La particion es por anuncio, no por fila.

Que mide y que no
-----------------
Mide con cuanto error el motor reproduce el PRECIO PEDIDO de un anuncio real de
Madrid que no habia visto. No mide si ese precio era correcto, ni si el piso se
vendio, ni a cuanto. Para eso harian falta precios de escritura, que no estan en
ningun conjunto abierto a nivel de inmueble.

Lineas base
-----------
Un error del X % no significa nada por si solo. Se compara siempre contra dos
alternativas mas tontas y mas baratas:

  1. Mediana de EUR/m2 de toda la ciudad multiplicada por la superficie.
  2. Mediana de EUR/m2 del barrio y trimestre multiplicada por la superficie.

Si el motor de comparables no mejora claramente la segunda, no aporta, y eso
tambien es un resultado.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DIR_REAL = RAIZ / "data" / "real"
F_ENTRADA = DIR_REAL / "madrid_2018.csv"
F_VALORADO = DIR_REAL / "valoraciones_2018.csv"
F_METRICAS = DIR_REAL / "metricas_2018.json"
F_CALIDAD = DIR_REAL / "calidad_2018.csv"

SEMILLA = 20260904
PROP_POOL = 0.70
BANDA_SUPERFICIE = 0.20
MIN_COMPARABLES = 5

# Peor categoria catastral presente en el conjunto. Solo sirve para invertir el
# codigo y que "calidad_catastral" crezca con la calidad. Ver preparar().
CALIDAD_CATASTRAL_PEOR = 9

# Filtros de plausibilidad. Todo lo que caiga fuera se aparta con su motivo.
RANGOS = {
    "PRICE": (30_000, 6_000_000),
    "UNITPRICE": (500, 15_000),
    "CONSTRUCTEDAREA": (20, 500),
    "ROOMNUMBER": (0, 10),
    "BATHNUMBER": (0, 6),
}

# Variables del ajuste hedonico. La categoria base de estado es
# "segunda mano en buen estado" (BUILTTYPEID_3).
VARIABLES = [
    "obra_nueva", "a_reformar", "ascensor", "terraza", "aire_acondicionado",
    "interior", "planta", "ultima_planta", "garaje", "trastero", "piscina",
    "portero", "jardin", "duplex", "estudio", "calidad_catastral",
    "log_superficie", "antiguedad",
]


def preparar(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    incidencias = []
    n0 = len(d)

    sin_barrio = d["barrio"].isna()
    incidencias.append({"motivo": "sin barrio asignado", "filas": int(sin_barrio.sum())})
    d = d[~sin_barrio].copy()

    for col, (lo, hi) in RANGOS.items():
        fuera = ~d[col].between(lo, hi)
        incidencias.append({"motivo": f"{col} fuera de [{lo}, {hi}]",
                            "filas": int(fuera.sum())})
        d = d[~fuera].copy()

    # Un mismo ASSETID aparece varias veces dentro de un trimestre, con precios
    # ligeramente distintos. Se queda una fila por anuncio y trimestre para no
    # contar el mismo inmueble como varios comparables.
    dup = d.duplicated(["ASSETID", "trimestre"], keep="first")
    incidencias.append({"motivo": "anuncio repetido en el mismo trimestre",
                        "filas": int(dup.sum())})
    d = d[~dup].copy()

    d["obra_nueva"] = d["BUILTTYPEID_1"].astype(float)
    d["a_reformar"] = d["BUILTTYPEID_2"].astype(float)
    d["ascensor"] = d["HASLIFT"].astype(float)
    d["terraza"] = d["HASTERRACE"].astype(float)
    d["aire_acondicionado"] = d["HASAIRCONDITIONING"].astype(float)
    d["interior"] = (d["FLATLOCATIONID"] == 2).astype(float)
    d["planta"] = d["FLOORCLEAN"].fillna(d["FLOORCLEAN"].median()).clip(0, 15)
    d["ultima_planta"] = d["ISINTOPFLOOR"].astype(float)
    d["garaje"] = d["HASPARKINGSPACE"].astype(float)
    d["trastero"] = d["HASBOXROOM"].astype(float)
    d["piscina"] = d["HASSWIMMINGPOOL"].astype(float)
    d["portero"] = d["HASDOORMAN"].astype(float)
    d["jardin"] = d["HASGARDEN"].astype(float)
    d["duplex"] = d["ISDUPLEX"].astype(float)
    d["estudio"] = d["ISSTUDIO"].astype(float)
    # CADASTRALQUALITYID no es una nota de calidad: es la categoria catastral,
    # que va de mejor a peor segun crece el numero. En el pool el EUR/m2 mediano
    # cae de forma monotona de 5.995 (codigo 0) a 2.114 (codigo 7), y esa es la
    # comprobacion que lo fija; la direccion no esta documentada en el paquete.
    # Se invierte para que la variable crezca con la calidad y su coeficiente se
    # lea sin trampa. La inversion no mueve ninguna valoracion: entra en el
    # factor como un desplazamiento constante que se cancela al dividir el
    # EUR/m2 de cada comparable por su propio factor. Ver r04 y test_valoracion_real.
    d["calidad_catastral"] = CALIDAD_CATASTRAL_PEOR - d["CADASTRALQUALITYID"].fillna(
        d["CADASTRALQUALITYID"].median()).astype(float)
    d["log_superficie"] = np.log(d["CONSTRUCTEDAREA"])
    d["antiguedad"] = (2018 - d["CADCONSTRUCTIONYEAR"].clip(1850, 2018)).astype(float)
    d["eur_m2"] = d["PRICE"] / d["CONSTRUCTEDAREA"]

    inc = pd.DataFrame(incidencias)
    inc["pct"] = (inc["filas"] / n0).round(5)
    return d.reset_index(drop=True), inc


def estimar_coeficientes(pool: pd.DataFrame) -> np.ndarray:
    """OLS sobre log(EUR/m2) centrado por barrio y trimestre.

    Al centrar por barrio-trimestre desaparece el efecto de la zona y del
    momento, y lo que queda es el peso de los atributos del inmueble.
    """
    p = pool.copy()
    p["log_m2"] = np.log(p["eur_m2"])
    p["y"] = p["log_m2"] - p.groupby(["barrio", "trimestre"])["log_m2"].transform("mean")
    X = np.column_stack([np.ones(len(p))] + [p[v].to_numpy() for v in VARIABLES])
    beta, *_ = np.linalg.lstsq(X, p["y"].to_numpy(), rcond=None)
    return beta


def factor(d: pd.DataFrame, beta: np.ndarray) -> np.ndarray:
    """Factor que lleva cada inmueble a atributos neutros."""
    X = np.column_stack([np.zeros(len(d))] + [d[v].to_numpy() for v in VARIABLES])
    return np.exp(X @ beta)


def valorar(pool: pd.DataFrame, evaluacion: pd.DataFrame,
            beta: np.ndarray) -> pd.DataFrame:
    pool = pool.copy()
    pool["factor"] = factor(pool, beta)
    pool["m2_neutro"] = pool["eur_m2"] / pool["factor"]

    # Lineas base calculadas solo con el pool
    base_ciudad = float(pool["eur_m2"].median())
    base_barrio = (pool.groupby(["barrio", "trimestre"])["eur_m2"]
                   .median().to_dict())

    grupos = {k: g for k, g in pool.groupby(["barrio", "trimestre"])}
    ev = evaluacion.copy()
    ev["factor"] = factor(ev, beta)

    filas = []
    for r in ev.itertuples():
        clave = (r.barrio, r.trimestre)
        g = grupos.get(clave)
        base = {
            "ASSETID": r.ASSETID, "trimestre": r.trimestre, "barrio": r.barrio,
            "superficie_m2": r.CONSTRUCTEDAREA, "precio_pedido": r.PRICE,
            "eur_m2_pedido": r.eur_m2,
            "valor_base_ciudad": base_ciudad * r.CONSTRUCTEDAREA,
            "valor_base_barrio": base_barrio.get(clave, base_ciudad) * r.CONSTRUCTEDAREA,
        }
        if g is None:
            filas.append({**base, "n_comparables": 0, "valor_estimado": np.nan,
                          "desviacion": np.nan, "fiabilidad": "sin muestra",
                          "motivo_no_valorable": "barrio sin anuncios en el trimestre"})
            continue

        lo = r.CONSTRUCTEDAREA * (1 - BANDA_SUPERFICIE)
        hi = r.CONSTRUCTEDAREA * (1 + BANDA_SUPERFICIE)
        comps = g[g["CONSTRUCTEDAREA"].between(lo, hi)]

        if len(comps) < MIN_COMPARABLES:
            filas.append({**base, "n_comparables": len(comps),
                          "valor_estimado": np.nan, "desviacion": np.nan,
                          "fiabilidad": "sin muestra",
                          "motivo_no_valorable": "menos de "
                                                 f"{MIN_COMPARABLES} comparables"})
            continue

        m2 = comps["m2_neutro"].to_numpy() * r.factor
        mediana = float(np.median(m2))
        valor = mediana * r.CONSTRUCTEDAREA
        q1, q3 = np.percentile(m2, [25, 75])
        dispersion = (q3 - q1) / mediana

        if len(comps) >= 15 and dispersion < 0.22:
            fiab = "alta"
        elif len(comps) >= 8 and dispersion < 0.35:
            fiab = "media"
        else:
            fiab = "baja"

        filas.append({**base, "n_comparables": len(comps),
                      "valor_estimado": round(valor, 0),
                      "eur_m2_comparables": round(mediana, 2),
                      "dispersion_comparables": round(float(dispersion), 4),
                      "desviacion": round(r.PRICE / valor - 1, 4),
                      "fiabilidad": fiab, "motivo_no_valorable": ""})
    return pd.DataFrame(filas)


# Tramos de numero de comparables. Sirven para separar dos cosas que se
# confunden: tener MUCHOS comparables y tenerlos POCO dispersos. El dashboard
# afirma que lo segundo pesa y lo primero casi no, y esta es la medida que lo
# sostiene. Sin ella la afirmacion iba escrita a mano.
TRAMOS_COMPARABLES = [("5-9", 5, 9), ("10-19", 10, 19),
                      ("20-49", 20, 49), ("50 o mas", 50, 10 ** 9)]


def _error_por_n_comparables(con: pd.DataFrame) -> dict:
    e = (con["valor_estimado"] - con["precio_pedido"]).abs() / con["precio_pedido"]
    salida = {}
    for etiqueta, lo, hi in TRAMOS_COMPARABLES:
        dentro = con["n_comparables"].between(lo, hi)
        if dentro.any():
            salida[etiqueta] = {
                "error_absoluto_mediano": round(float(e[dentro].median()), 4),
                "anuncios": int(dentro.sum()),
            }
    return salida


def _error(estimado: pd.Series, real: pd.Series) -> dict:
    e = (estimado - real).abs() / real
    rel = estimado / real - 1
    return {
        "error_absoluto_mediano": round(float(e.median()), 4),
        "dentro_de_10pct": round(float((e <= 0.10).mean()), 4),
        "dentro_de_20pct": round(float((e <= 0.20).mean()), 4),
        "sesgo_mediano": round(float(rel.median()), 4),
    }


def ejecutar() -> dict:
    d = pd.read_csv(F_ENTRADA)
    # Recuento del origen ANTES de limpiar. Se publica porque el dashboard lo
    # cita, y toda cifra que se ensena tiene que salir de aqui y no de la prosa.
    n_origen = int(len(d))
    n_identificadores = int(d["ASSETID"].nunique())
    d, incidencias = preparar(d)
    incidencias.to_csv(F_CALIDAD, index=False)

    rng = np.random.default_rng(SEMILLA)
    ids = d["ASSETID"].unique()
    en_pool = set(rng.choice(ids, size=int(len(ids) * PROP_POOL), replace=False))
    marca = d["ASSETID"].isin(en_pool)
    pool, evaluacion = d[marca], d[~marca]

    beta = estimar_coeficientes(pool)
    res = valorar(pool, evaluacion, beta)
    res.to_csv(F_VALORADO, index=False)

    con = res[res["desviacion"].notna()]
    metricas = {
        "fuente": ("idealista18 (Rey-Blanco, Arbues, Lopez y Paez, 2024), "
                   "doi:10.1177/23998083241242844, licencia ODbL-1.0. "
                   "Anuncios de venta en Madrid, cuatro trimestres de 2018."),
        "n_anuncios_origen": n_origen,
        "n_identificadores_unicos": n_identificadores,
        "n_anuncios_utilizables": int(len(d)),
        "n_pool": int(len(pool)),
        "n_evaluacion": int(len(evaluacion)),
        "n_barrios": int(d["barrio"].nunique()),
        "cobertura": round(len(con) / max(len(res), 1), 4),
        "motor_comparables": _error(con["valor_estimado"], con["precio_pedido"]),
        "base_mediana_barrio": _error(con["valor_base_barrio"], con["precio_pedido"]),
        "base_mediana_ciudad": _error(con["valor_base_ciudad"], con["precio_pedido"]),
        "error_por_fiabilidad": {
            f: _error(g["valor_estimado"], g["precio_pedido"])["error_absoluto_mediano"]
            for f, g in con.groupby("fiabilidad")},
        "error_por_n_comparables": _error_por_n_comparables(con),
        "coeficientes": {v: round(float(b), 4)
                         for v, b in zip(VARIABLES, beta[1:])},
        # Texto de cara al lector, no identificadores: va acentuado, porque de
        # aqui lo cogen tal cual el Excel y el dashboard.
        "limitaciones": [
            "El objetivo es el precio PEDIDO, no el de cierre.",
            "Datos de 2018. No representan el nivel de precios actual.",
            "Coordenadas y precios llevan ruido aleatorio añadido por los autores "
            "del conjunto de datos por protección de datos.",
            "El identificador de anuncio no enlaza entre trimestres en la versión "
            "publicada, así que no se puede seguir un mismo inmueble en el tiempo.",
        ],
    }
    F_METRICAS.write_text(json.dumps(metricas, indent=2, ensure_ascii=False),
                          encoding="utf-8")
    return metricas


if __name__ == "__main__":
    m = ejecutar()
    print(f"Anuncios utilizables: {m['n_anuncios_utilizables']}  "
          f"(pool {m['n_pool']} / evaluacion {m['n_evaluacion']})")
    print(f"Cobertura: {m['cobertura']:.1%}\n")
    print(f"{'metodo':<26}{'error mediano':>14}{'±10%':>9}{'±20%':>9}{'sesgo':>9}")
    for nombre, clave in [("comparables por barrio", "motor_comparables"),
                          ("mediana del barrio", "base_mediana_barrio"),
                          ("mediana de la ciudad", "base_mediana_ciudad")]:
        e = m[clave]
        print(f"{nombre:<26}{e['error_absoluto_mediano']:>13.1%}"
              f"{e['dentro_de_10pct']:>9.1%}{e['dentro_de_20pct']:>9.1%}"
              f"{e['sesgo_mediano']:>9.1%}")
    print("\nError por fiabilidad:")
    for f, e in sorted(m["error_por_fiabilidad"].items()):
        print(f"  {f:<8}{e:.1%}")
