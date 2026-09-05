"""Paso R02 — Seguir una valoracion concreta de principio a fin.

Coge un anuncio del conjunto de evaluacion y reconstruye todo lo que el motor
hizo con el: que comparables eligio, por que descarto los demas, que ajuste
aplico a cada uno y de donde sale el numero final.

Es la respuesta a "vale, pero de donde sale esa cifra". Cualquier valoracion del
sistema se puede abrir asi.

    python src/r02_caso.py                       # caso de ejemplo por defecto
    python src/r02_caso.py A7455690789996765481  # cualquier otro
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import r01_valorar_real as r01

CASO_POR_DEFECTO = "A7455690789996765481"
F_SALIDA = r01.DIR_REAL / "caso_trazado.json"

ETIQUETAS = {
    "obra_nueva": "obra nueva", "a_reformar": "a reformar",
    "ascensor": "ascensor", "terraza": "terraza",
    "aire_acondicionado": "aire acondicionado", "interior": "interior",
    "ultima_planta": "última planta", "garaje": "garaje", "trastero": "trastero",
    "piscina": "piscina", "portero": "portero", "jardin": "jardín",
    "duplex": "dúplex", "estudio": "estudio",
}


def _rasgos(fila) -> list[str]:
    r = []
    for var, txt in ETIQUETAS.items():
        if float(getattr(fila, var, 0)) == 1:
            r.append(txt)
    if not any(float(getattr(fila, v, 0)) == 1 for v in ("obra_nueva", "a_reformar")):
        r.insert(0, "segunda mano en buen estado")
    if float(getattr(fila, "interior", 0)) == 0:
        r.append("exterior")
    return r


def trazar(assetid: str = CASO_POR_DEFECTO) -> dict:
    d = pd.read_csv(r01.F_ENTRADA)
    d, _ = r01.preparar(d)

    rng = np.random.default_rng(r01.SEMILLA)
    ids = d["ASSETID"].unique()
    en_pool = set(rng.choice(ids, size=int(len(ids) * r01.PROP_POOL), replace=False))
    marca = d["ASSETID"].isin(en_pool)
    pool, evaluacion = d[marca], d[~marca]

    fila = evaluacion[evaluacion["ASSETID"] == assetid]
    if fila.empty:
        raise SystemExit(f"{assetid} no esta en el conjunto de evaluacion.")
    s = fila.iloc[0]

    beta = r01.estimar_coeficientes(pool)
    f_suj = float(r01.factor(fila, beta)[0])

    # Los tres filtros, aplicados en orden, contando cuanto descarta cada uno
    mismo_barrio = pool[pool["barrio"] == s["barrio"]]
    mismo_trim = mismo_barrio[mismo_barrio["trimestre"] == s["trimestre"]]
    lo = s["CONSTRUCTEDAREA"] * (1 - r01.BANDA_SUPERFICIE)
    hi = s["CONSTRUCTEDAREA"] * (1 + r01.BANDA_SUPERFICIE)
    comps = mismo_trim[mismo_trim["CONSTRUCTEDAREA"].between(lo, hi)].copy()

    comps["factor"] = r01.factor(comps, beta)
    comps["eur_m2_ajustado"] = comps["eur_m2"] / comps["factor"] * f_suj
    comps = comps.sort_values("eur_m2_ajustado")

    mediana = float(comps["eur_m2_ajustado"].median())
    valor = mediana * s["CONSTRUCTEDAREA"]
    q1, q3 = np.percentile(comps["eur_m2_ajustado"], [25, 75])

    return {
        "sujeto": {
            "id": assetid, "barrio": s["barrio"], "trimestre": s["trimestre"],
            "superficie_m2": int(s["CONSTRUCTEDAREA"]),
            "habitaciones": int(s["ROOMNUMBER"]), "banos": int(s["BATHNUMBER"]),
            "planta": int(s["planta"]), "anio": int(s["CADCONSTRUCTIONYEAR"]),
            "rasgos": _rasgos(s),
            "precio_pedido": float(s["PRICE"]),
            "eur_m2_pedido": round(float(s["eur_m2"]), 0),
        },
        "embudo": [
            {"paso": "Anuncios en el conjunto de comparables",
             "quedan": int(len(pool))},
            {"paso": f"Mismo barrio ({s['barrio']})", "quedan": int(len(mismo_barrio))},
            {"paso": f"Mismo trimestre ({s['trimestre']})", "quedan": int(len(mismo_trim))},
            {"paso": f"Superficie entre {lo:.0f} y {hi:.0f} m²", "quedan": int(len(comps))},
        ],
        "comparables": [
            {"superficie_m2": int(c.CONSTRUCTEDAREA),
             "precio": float(c.PRICE),
             "eur_m2": round(float(c.eur_m2), 0),
             "eur_m2_ajustado": round(float(c.eur_m2_ajustado), 0),
             "rasgos": ", ".join(_rasgos(c))}
            for c in comps.itertuples()],
        "resultado": {
            # Con dos decimales, no redondeada a entero. El dashboard escribe la
            # ecuacion "mediana x superficie = valor", y con la mediana ya
            # redondeada la multiplicacion no cuadraba: 5.162 x 73 da 376.826 y
            # el valor real es 376.817. El numero estaba bien; la ecuacion, no.
            "eur_m2_mediano_ajustado": round(mediana, 2),
            "rango_intercuartilico": [round(float(q1), 0), round(float(q3), 0)],
            "dispersion": round(float((q3 - q1) / mediana), 3),
            "valor_estimado": round(valor, 0),
            "precio_pedido": float(s["PRICE"]),
            "desviacion": round(float(s["PRICE"] / valor - 1), 4),
            "n_comparables": int(len(comps)),
        },
    }


if __name__ == "__main__":
    caso = trazar(sys.argv[1] if len(sys.argv) > 1 else CASO_POR_DEFECTO)
    F_SALIDA.write_text(json.dumps(caso, indent=2, ensure_ascii=False), encoding="utf-8")
    s, r = caso["sujeto"], caso["resultado"]
    print(f"{s['barrio']}, {s['trimestre']} — {s['superficie_m2']} m², "
          f"{s['habitaciones']} hab, {s['banos']} baño(s), planta {s['planta']}, "
          f"finca de {s['anio']}")
    print(f"  {', '.join(s['rasgos'])}")
    print(f"  Pide {s['precio_pedido']:,.0f} € "
          f"({s['eur_m2_pedido']:,.0f} €/m²)\n".replace(",", "."))
    for p in caso["embudo"]:
        print(f"  {p['paso']:<45}{p['quedan']:>8}")
    def eur(x):
        return f"{x:,.0f}".replace(",", ".")
    print(f"\n  €/m² mediano de los comparables, ajustado: "
          f"{eur(r['eur_m2_mediano_ajustado'])} €")
    print(f"  Valor estimado: {eur(r['valor_estimado'])} €")
    print(f"  Desviación: {r['desviacion']:+.1%}")
