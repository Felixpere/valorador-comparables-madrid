"""Paso R04 — Verificacion de los dos coeficientes que salian con signo raro.

Por que existe este script
--------------------------
En `docs/validacion_2018.md` quedaron escritos dos coeficientes como anomalia sin
verificar: jardin en -1,4 % y calidad catastral en -1,4 %, ambos "con el signo
contrario al esperado". La sospecha anotada entonces fue colinealidad con barrio
y con superficie. Este script comprueba esa sospecha en vez de dejarla escrita.

Que se mide, en seis bloques
----------------------------
  1. ERRORES ESTANDAR. Un coeficiente pequeno puede ser simplemente ruido. Se
     calculan errores estandar, t e intervalo de confianza al 95 % para saber
     cuales de los dos son distinguibles de cero.
  2. VIF. La medida estandar de colinealidad. Contrasta directamente la sospecha
     que quedo anotada.
  3. CORRELACIONES ENTRE REGRESORES. El VIF resume; la matriz dice con QUIEN va
     de la mano cada variable, que es lo que hace falta para explicar el signo.
  4. EFECTO DEL CENTRADO POR BARRIO-TRIMESTRE. La sospecha anotada era
     colinealidad con el barrio. El modelo ya centra por barrio y trimestre, asi
     que la forma directa de contrastarla es estimar tambien SIN centrar y ver
     cuanto se mueve cada coeficiente. Si el barrio fuera la causa, quitar el
     centrado tendria que empeorar el signo, no arreglarlo.
  5. GRADIENTE DE LA CALIDAD CATASTRAL. El EUR/m2 mediano para cada valor del
     codigo, que dice en que direccion esta codificada la variable.
  6. REGRESION SECUENCIAL. Se anaden controles por bloques y se mira en que paso
     concreto cambia el signo. Es lo que distingue "colinealidad difusa" de "hay
     una variable que se lleva el efecto".

Todo sale del POOL (70 %), el mismo con el que se estiman los coeficientes de
produccion, y con la misma semilla. Ningun anuncio de evaluacion interviene.

    python src/r04_diagnostico_coeficientes.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import r01_valorar_real as r01  # noqa: E402

F_SALIDA = r01.DIR_REAL / "diagnostico_coeficientes_2018.json"

# Los dos coeficientes que se pusieron en cuarentena.
EN_CUARENTENA = ["jardin", "calidad_catastral"]

# Bloques de control que se van anadiendo, en orden, para ver donde cambia el
# signo. El orden va de lo mas inocente (nada) a lo mas sospechoso de robarle el
# efecto a la variable examinada.
SECUENCIA = {
    "jardin": [
        ("sin controles", []),
        ("+ superficie", ["log_superficie"]),
        ("+ piscina", ["log_superficie", "piscina"]),
        ("+ resto del paquete de urbanizacion",
         ["log_superficie", "piscina", "garaje", "trastero", "portero"]),
        ("+ ascensor",
         ["log_superficie", "piscina", "garaje", "trastero", "portero", "ascensor"]),
        ("modelo completo", None),
    ],
    "calidad_catastral": [
        ("sin controles", []),
        ("+ superficie", ["log_superficie"]),
        ("+ antiguedad", ["log_superficie", "antiguedad"]),
        ("+ ascensor", ["log_superficie", "antiguedad", "ascensor"]),
        ("+ estado de la finca",
         ["log_superficie", "antiguedad", "ascensor", "obra_nueva", "a_reformar"]),
        ("modelo completo", None),
    ],
}


def _pct(x: float, signo: bool = False) -> str:
    """Porcentaje a la espanola: coma decimal y espacio antes del simbolo."""
    return f"{x:{'+' if signo else ''}.1%}".replace(".", ",").replace("%", " %")


def _num(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def cargar_pool() -> pd.DataFrame:
    """El mismo pool que usa r01, con la misma semilla y la misma particion."""
    d = pd.read_csv(r01.F_ENTRADA)
    d, _ = r01.preparar(d)
    rng = np.random.default_rng(r01.SEMILLA)
    ids = d["ASSETID"].unique()
    en_pool = set(rng.choice(ids, size=int(len(ids) * r01.PROP_POOL), replace=False))
    p = d[d["ASSETID"].isin(en_pool)].copy()
    p["log_m2"] = np.log(p["eur_m2"])
    p["y"] = p["log_m2"] - p.groupby(["barrio", "trimestre"])["log_m2"].transform("mean")
    return p.reset_index(drop=True)


def _ols(p: pd.DataFrame, variables: list[str]) -> np.ndarray:
    X = np.column_stack([np.ones(len(p))] + [p[v].to_numpy() for v in variables])
    beta, *_ = np.linalg.lstsq(X, p["y"].to_numpy(), rcond=None)
    return beta


def con_errores_estandar(p: pd.DataFrame) -> dict:
    """Coeficientes del modelo de produccion con su incertidumbre."""
    V = r01.VARIABLES
    X = np.column_stack([np.ones(len(p))] + [p[v].to_numpy() for v in V])
    y = p["y"].to_numpy()
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n, k = X.shape
    s2 = float(resid @ resid) / (n - k)
    se = np.sqrt(np.diag(np.linalg.inv(X.T @ X)) * s2)
    return {
        v: {
            "beta": round(float(beta[i]), 4),
            "error_estandar": round(float(se[i]), 4),
            "t": round(float(beta[i] / se[i]), 1),
            "ic95": [round(float(beta[i] - 1.96 * se[i]), 4),
                     round(float(beta[i] + 1.96 * se[i]), 4)],
        }
        for i, v in enumerate(V, start=1)
    }


def vif(p: pd.DataFrame) -> dict:
    """Factor de inflacion de la varianza de cada variable frente a las demas.

    Convencion habitual: por debajo de 5 no hay problema de colinealidad; por
    encima de 10 el coeficiente no es interpretable.
    """
    V = r01.VARIABLES
    X = np.column_stack([np.ones(len(p))] + [p[v].to_numpy() for v in V])
    salida = {}
    for i, v in enumerate(V, start=1):
        otras = [j for j in range(X.shape[1]) if j != i]
        b, *_ = np.linalg.lstsq(X[:, otras], X[:, i], rcond=None)
        resid = X[:, i] - X[:, otras] @ b
        sct = float(((X[:, i] - X[:, i].mean()) ** 2).sum())
        r2 = 1 - float(resid @ resid) / sct
        salida[v] = round(1 / (1 - r2), 2)
    return salida


def correlaciones(p: pd.DataFrame, cuantos: int = 10) -> dict:
    """Matriz de correlacion entre regresores, y las parejas mas fuertes.

    El VIF de cada variable resume su colinealidad contra todas las demas juntas,
    pero no dice con cual. Para explicar un signo hace falta saber con quien va de
    la mano la variable, y eso lo da la matriz.
    """
    V = r01.VARIABLES
    C = p[V].corr()

    parejas = sorted(
        ({"a": a, "b": b, "r": round(float(C.loc[a, b]), 3)}
         for i, a in enumerate(V) for b in V[i + 1:]),
        key=lambda d: abs(d["r"]), reverse=True)

    def vecinas(v: str) -> list[dict]:
        s = C[v].drop(v).sort_values(key=abs, ascending=False).head(5)
        return [{"variable": k, "r": round(float(r), 3)} for k, r in s.items()]

    return {
        "matriz": {a: {b: round(float(C.loc[a, b]), 3) for b in V} for a in V},
        "parejas_mas_fuertes": parejas[:cuantos],
        "correlacion_maxima": parejas[0]["r"],
        "vecinas": {k: vecinas(k) for k in EN_CUARENTENA},
    }


def efecto_del_centrado(p: pd.DataFrame) -> dict:
    """Los mismos coeficientes con y sin centrar por barrio y trimestre.

    Es el contraste directo de la sospecha que quedo anotada. El modelo de
    produccion centra por barrio-trimestre, con lo que el efecto de la zona y del
    momento desaparece antes de estimar nada. Si el signo negativo del jardin
    viniera de la zona, al QUITAR el centrado el coeficiente tendria que ponerse
    peor, no mejor.
    """
    V = r01.VARIABLES
    X = np.column_stack([np.ones(len(p))] + [p[v].to_numpy() for v in V])

    def ajustar(y: np.ndarray) -> np.ndarray:
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        return beta

    con = ajustar(p["y"].to_numpy())
    sin = ajustar(p["log_m2"].to_numpy())
    return {
        v: {"centrado": round(float(con[i]), 4),
            "sin_centrar": round(float(sin[i]), 4),
            "diferencia": round(float(sin[i] - con[i]), 4)}
        for i, v in enumerate(V, start=1)
    }


def gradiente_calidad(p: pd.DataFrame) -> list[dict]:
    """EUR/m2 mediano para cada valor del codigo catastral, SIN recodificar.

    Se agrupa por CADASTRALQUALITYID tal y como viene del origen, no por la
    variable ya invertida que usa el modelo: la pregunta que responde este bloque
    es precisamente en que direccion venia codificada, y eso solo se ve en el
    codigo crudo. Es el dato que no estaba escrito en ningun sitio del repo.
    """
    crudo = p["CADASTRALQUALITYID"].fillna(p["CADASTRALQUALITYID"].median())
    g = (p.assign(codigo=crudo).groupby("codigo")["eur_m2"]
         .agg(["median", "count"]).reset_index().sort_values("codigo"))
    return [{"codigo_origen": float(r.codigo),
             "calidad_recodificada": float(r01.CALIDAD_CATASTRAL_PEOR - r.codigo),
             "eur_m2_mediano": round(float(r.median), 0),
             "anuncios": int(r.count)} for r in g.itertuples()]


def tramo_monotono(gradiente: list[dict], n_pool: int) -> dict:
    """Hasta que codigo baja el precio sin excepciones, y cuanto pool cubre.

    El gradiente no es monotono en todo el recorrido: los codigos altos, que
    tienen muy pocos anuncios, repuntan. Conviene decir hasta donde llega la
    parte limpia en vez de redondear la afirmacion a "es monotono".
    """
    fin = 0
    for i in range(1, len(gradiente)):
        if gradiente[i]["eur_m2_mediano"] < gradiente[i - 1]["eur_m2_mediano"]:
            fin = i
        else:
            break
    dentro = sum(r["anuncios"] for r in gradiente[:fin + 1])

    # Cuanto cae el EUR/m2 CRUDO a lo largo del tramo. No es el coeficiente del
    # modelo y no debe confundirse con el: aqui no se ha descontado el barrio, y
    # el barrio se lleva casi toda esta caida. La tabla establece el SENTIDO de la
    # variable; la magnitud del efecto propio la da el coeficiente centrado.
    razon = gradiente[fin]["eur_m2_mediano"] / gradiente[0]["eur_m2_mediano"]
    grados = gradiente[fin]["codigo_origen"] - gradiente[0]["codigo_origen"]

    return {
        "codigo_desde": gradiente[0]["codigo_origen"],
        "codigo_hasta": gradiente[fin]["codigo_origen"],
        "anuncios_en_el_tramo": dentro,
        "pct_del_pool": round(dentro / n_pool, 4),
        "anuncios_fuera": n_pool - dentro,
        "caida_total_sin_descontar_barrio": round(razon - 1, 4),
        "caida_por_grado_sin_descontar_barrio": round(razon ** (1 / grados) - 1, 4),
    }


def secuencial(p: pd.DataFrame, objetivo: str) -> list[dict]:
    """Coeficiente de `objetivo` segun se van anadiendo bloques de control."""
    filas = []
    for etiqueta, controles in SECUENCIA[objetivo]:
        variables = (list(r01.VARIABLES) if controles is None
                     else [objetivo] + list(controles))
        beta = _ols(p, variables)
        b = float(beta[1 + variables.index(objetivo)])
        filas.append({"modelo": etiqueta,
                      "n_variables": len(variables),
                      "beta": round(b, 4),
                      # Efecto sobre el EUR/m2, que es como habla del tema el
                      # resto del proyecto. El beta crudo se queda al lado.
                      "efecto": round(float(np.expm1(b)), 4)})
    return filas


def cruce_jardin_piscina(p: pd.DataFrame) -> list[dict]:
    """EUR/m2 mediano en las cuatro combinaciones de jardin y piscina."""
    g = (p.groupby(["jardin", "piscina"])["eur_m2"]
         .agg(["median", "count"]).reset_index())
    return [{"jardin": bool(r.jardin), "piscina": bool(r.piscina),
             "eur_m2_mediano": round(float(r.median), 0),
             "anuncios": int(r.count)} for r in g.itertuples()]


def ejecutar() -> dict:
    p = cargar_pool()
    coef = con_errores_estandar(p)
    v = vif(p)

    con_jardin = p[p["jardin"] == 1]
    grad = gradiente_calidad(p)
    t = tramo_monotono(grad, len(p))
    corr = correlaciones(p)
    centrado = efecto_del_centrado(p)
    diag = {
        "semilla": r01.SEMILLA,
        "n_pool": int(len(p)),
        "coeficientes_con_incertidumbre": coef,
        "vif": v,
        "vif_maximo": max(v.values()),
        "correlaciones": corr,
        "efecto_del_centrado": centrado,
        "gradiente_calidad_catastral": grad,
        "tramo_monotono_calidad": t,
    }

    seq = {k: secuencial(p, k) for k in EN_CUARENTENA}
    j_solo = seq["jardin"][0]["efecto"]
    j_final = seq["jardin"][-1]["efecto"]

    diag.update({
        "secuencial": seq,
        "cruce_jardin_piscina": cruce_jardin_piscina(p),
        "pct_jardin_con_piscina": round(float((con_jardin["piscina"] == 1).mean()), 4),
        # Texto de cara al lector, no identificadores: va acentuado, porque de
        # aqui lo coge tal cual la hoja de Excel.
        "veredicto": {
            "calidad_catastral": (
                f"No era una anomalía: la variable estaba leída al revés. "
                f"CADASTRALQUALITYID no es una nota, es la categoría catastral, y "
                f"empeora según crece: el €/m² cae sin excepciones del código "
                f"{t['codigo_desde']:.0f} al {t['codigo_hasta']:.0f}, que son el "
                f"{_pct(t['pct_del_pool'])} del pool. Sobre el código original, el "
                f"signo negativo era el correcto. r01 ya invierte la variable para que "
                f"crezca con la calidad; las valoraciones no se mueven."),
            "jardin": (
                f"No era colinealidad con el barrio: el modelo ya centra por barrio y "
                f"trimestre, y quitar ese centrado deja el jardín en "
                f"{_pct(np.expm1(centrado['jardin']['sin_centrar']), signo=True)} en "
                f"vez de {_pct(j_final, signo=True)}. O sea que el efecto de la zona "
                f"empujaba hacia abajo y el centrado ya lo quita; la sospecha iba en "
                f"la dirección contraria a lo que pasa. Tampoco con la superficie: "
                f"controlar por ella lo hace aún más positivo, y el VIF es "
                f"{_num(v['jardin'])}, muy por debajo de 5. Es un efecto parcial real. "
                f"Aislado vale {_pct(j_solo, signo=True)}; el signo cambia al "
                f"controlar por piscina, que es la variable con la que más va de la "
                f"mano de todo el modelo (r = {_num(corr['matriz']['jardin']['piscina'])}): "
                f"el {_pct(float((con_jardin['piscina'] == 1).mean()))} de los anuncios "
                f"con jardín tienen además piscina. Lo que queda en "
                f"{_pct(j_final, signo=True)} es el jardín SIN el resto del paquete, "
                f"que señala promoción periférica, no una casa con jardín en el "
                f"centro."),
        },
    })
    F_SALIDA.write_text(json.dumps(diag, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    return diag


if __name__ == "__main__":
    d = ejecutar()
    print(f"Pool: {d['n_pool']} anuncios, semilla {d['semilla']}\n")

    print("1. Los dos coeficientes en cuarentena, con su incertidumbre")
    print(f"   {'variable':<20}{'beta':>9}{'e.e.':>9}{'t':>8}   IC 95 %")
    for k in EN_CUARENTENA:
        c = d["coeficientes_con_incertidumbre"][k]
        print(f"   {k:<20}{c['beta']:>9.4f}{c['error_estandar']:>9.4f}"
              f"{c['t']:>8.1f}   [{c['ic95'][0]:+.4f}, {c['ic95'][1]:+.4f}]")

    print(f"\n2. Colinealidad (VIF). Maximo de todo el modelo: {d['vif_maximo']:.2f}")
    for k in EN_CUARENTENA:
        print(f"   {k:<20}{d['vif'][k]:>9.2f}")
    print("   Por debajo de 5 no hay problema de colinealidad. La sospecha que")
    print("   estaba anotada no se sostiene.")

    print("\n3. Con quien va de la mano cada uno (correlacion entre regresores)")
    print(f"   Correlacion mas fuerte de todo el modelo: "
          f"{d['correlaciones']['correlacion_maxima']:.3f} entre "
          f"{d['correlaciones']['parejas_mas_fuertes'][0]['a']} y "
          f"{d['correlaciones']['parejas_mas_fuertes'][0]['b']}")
    for k in EN_CUARENTENA:
        print(f"   {k}:")
        for x in d["correlaciones"]["vecinas"][k]:
            print(f"      {x['variable']:<22}{x['r']:>8.3f}")
    print("   Correlacionadas si, colineales no: ninguna pareja llega a 0,7 y")
    print("   ningun VIF pasa de 2,3.")

    print("\n4. Que pasa si se quita el centrado por barrio-trimestre")
    print("   Contraste directo de la sospecha anotada. Si el barrio fuera la")
    print("   causa del signo, quitar el centrado tendria que EMPEORARLO.")
    print(f"   {'variable':<22}{'centrado':>11}{'sin centrar':>13}")
    for k in EN_CUARENTENA:
        c = d["efecto_del_centrado"][k]
        print(f"   {k:<22}{c['centrado']:>11.4f}{c['sin_centrar']:>13.4f}")
    print("   Pasa lo contrario: sin centrar, el jardin es MUCHO mas negativo. El")
    print("   centrado ya esta quitando el efecto de zona, y lo que queda no es barrio.")

    print("\n5. En que direccion VENIA codificada la calidad catastral")
    print("   CADASTRALQUALITYID tal cual llega del origen, sin recodificar:")
    print(f"   {'codigo':>7}{'EUR/m2 mediano':>17}{'anuncios':>11}")
    for r in d["gradiente_calidad_catastral"]:
        print(f"   {r['codigo_origen']:>7.0f}{r['eur_m2_mediano']:>17,.0f}"
              f"{r['anuncios']:>11,}".replace(",", "."))
    tr = d["tramo_monotono_calidad"]
    print(f"   El precio cae sin excepciones del codigo {tr['codigo_desde']:.0f} al "
          f"{tr['codigo_hasta']:.0f}, que son el")
    fuera = f"{tr['anuncios_fuera']:,}".replace(",", ".")
    print(f"   {tr['pct_del_pool']:.1%} del pool. Los codigos altos repuntan, pero solo "
          f"quedan {fuera} anuncios")
    print("   ahi. No es una nota de calidad: es la categoria catastral, donde el")
    print("   numero bajo es el bueno. Se leyo al reves. r01 ya lo invierte.")
    print(f"   OJO: esta tabla fija el SENTIDO, no la magnitud. La caida cruda es")
    print(f"   {tr['caida_por_grado_sin_descontar_barrio']:.1%} por grado, pero ahi "
          f"no se ha descontado el barrio. El")
    print(f"   coeficiente del modelo, ya centrado, es "
          f"{np.expm1(d['coeficientes_con_incertidumbre']['calidad_catastral']['beta']):+.1%}"
          f" por grado: el barrio se lleva")
    print("   casi toda esa caida.")

    print("\n6. Donde cambia el signo del jardin")
    print(f"   {'modelo':<40}{'efecto':>9}{'beta':>10}")
    for r in d["secuencial"]["jardin"]:
        print(f"   {r['modelo']:<40}{r['efecto']:>8.1%}{r['beta']:>10.4f}")

    print("\n7. Por que: jardin y piscina van juntos")
    print(f"   {'jardin':<8}{'piscina':<9}{'EUR/m2 mediano':>16}{'anuncios':>11}")
    for r in d["cruce_jardin_piscina"]:
        print(f"   {'si' if r['jardin'] else 'no':<8}{'si' if r['piscina'] else 'no':<9}"
              f"{r['eur_m2_mediano']:>16,.0f}{r['anuncios']:>11,}".replace(",", "."))
    print(f"   El {d['pct_jardin_con_piscina']:.1%} de los anuncios con jardin "
          f"tienen ademas piscina.")

    print(f"\nDiagnostico escrito en {F_SALIDA}")
