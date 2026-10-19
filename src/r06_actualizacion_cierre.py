"""Paso R06 — Precios de 2018 a hoy, y del anuncio a la escritura.

Dos numeros por distrito, los dos con fuente publica:

1. FACTOR DE ACTUALIZACION (2018T4 -> ultimo trimestre del INE)
   Los comparables de la demo son anuncios de 2018T4. Para llevarlos a hoy:

       factor = (usada_actual / usada_2018)            por distrito, Registradores
              x (IPV[ultimo] / IPV[media del ano actual]) de la media anual al ultimo trimestre
              x (IPV[media 2018] / IPV[2018T4])          de la media de 2018 al cuarto trimestre

   Se usa el precio de vivienda USADA, no el total: el total se mueve con las
   promociones nuevas que se escrituran cada ano (en Vicalvaro se dobla por eso)
   y los anuncios de la demo son de segunda mano. El IPV es de la Comunidad de
   Madrid: el INE no lo publica por distrito. Como contraste se da tambien el
   factor que sale solo con el IPV, igual para toda la ciudad.

   Supuesto declarado: se actualiza el precio de anuncio con la evolucion del
   precio de escritura. Equivale a suponer que la distancia entre lo que se pide
   y lo que se firma no ha cambiado desde 2018.

2. BRECHA ANUNCIO-ESCRITURA (2018)
   brecha = 1 - EUR/m2 escriturado (usada, 2018) / EUR/m2 anunciado (2018)

   No es el descuento de negociacion. Lo contiene, pero mezcla ademas:
     * anuncios que nunca se vendieron (los caros duran mas y pesan mas);
     * el desfase entre acordar el precio y que la escritura se inscriba;
     * pisos distintos: los anunciados no son los vendidos;
     * cualquier diferencia entre lo pagado y lo declarado en escritura.
   Por eso se da un RANGO: cuatro formas razonables de medir el anuncio medio
   (media o mediana, y con o sin reponderar por la mezcla de superficies que se
   escrituraron) y el rango va de la menor a la mayor. La cifra "central" que se
   guarda es la media reponderada, porque el Registro publica un "precio medio";
   la fuente no detalla como lo calcula, asi que es una eleccion, no un dato. La
   media sale casi siempre en el extremo alto del rango (los precios por m2 tienen
   cola hacia arriba), y por eso la demo no la ensena: solo el rango.

   La mezcla de superficies es la del total escriturado (nueva y usada juntas):
   el Registro no la publica solo para usada.

Salida: data/real/factores_distrito.csv (se versiona: es pequeno y lo citan la
demo y los tests). Necesita data/real/madrid_2018.csv (ver r00).

    python src/r06_actualizacion_cierre.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from r01_valorar_real import F_ENTRADA, preparar

RAIZ = Path(__file__).resolve().parent.parent
DIR_REF = RAIZ / "data" / "referencia"
F_ESC_2018 = DIR_REF / "escrituras_distrito_2018.csv"
F_ESC_ACTUAL = DIR_REF / "escrituras_distrito_actual.csv"
F_IPV = DIR_REF / "ipv_ine_madrid.csv"
F_FACTORES = RAIZ / "data" / "real" / "factores_distrito.csv"
F_RESUMEN = RAIZ / "data" / "real" / "factores_distrito.json"

TRIMESTRE_COMPARABLES = "2018T4"
# Limites de los tramos de superficie del Registro, en m2 construidos
TRAMOS = [(0, 40, "sup_menos40"), (40, 60, "sup_40_60"), (60, 80, "sup_60_80"),
          (80, 100, "sup_80_100"), (100, 10 ** 6, "sup_mas100")]


def leer_ref(ruta: Path) -> pd.DataFrame:
    return pd.read_csv(ruta, comment="#")


def cabecera(ruta: Path, campo: str) -> str:
    """Valor de una linea '# CAMPO: valor' de la cabecera de un CSV de referencia."""
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.startswith(f"# {campo}:"):
            return linea.split(":", 1)[1].strip()
    raise KeyError(f"{ruta.name} no declara {campo}")


def distrito_de(barrio_id: pd.Series) -> pd.Series:
    """'0-EU-ES-28-07-001-079-04-001' -> 4. El codigo 079 es el municipio de Madrid."""
    return barrio_id.str.split("-").str[7].astype(int)


def _mediana_ponderada(x: np.ndarray, w: np.ndarray) -> float:
    orden = np.argsort(x)
    x, w = x[orden], w[orden]
    acumulado = np.cumsum(w)
    return float(x[np.searchsorted(acumulado, acumulado[-1] / 2)])


def pesos_por_tramo(superficie: pd.Series, mezcla_registro: dict[str, float]) -> np.ndarray:
    """Pesos que dan a los anuncios la misma mezcla de superficies que se escrituro."""
    w = np.zeros(len(superficie))
    s = superficie.to_numpy()
    for lo, hi, col in TRAMOS:
        dentro = (s >= lo) & (s < hi)
        if dentro.any():
            w[dentro] = mezcla_registro[col] / dentro.sum()
    return w


def brecha_distrito(anuncios: pd.DataFrame, fila_registro: pd.Series) -> dict:
    """Las cuatro medidas de la brecha anuncio-escritura de un distrito."""
    m2 = anuncios["eur_m2"].to_numpy()
    total = sum(fila_registro[c] for *_, c in TRAMOS)
    mezcla = {c: fila_registro[c] / total for *_, c in TRAMOS}
    w = pesos_por_tramo(anuncios["CONSTRUCTEDAREA"], mezcla)
    anuncio = {
        "media": float(m2.mean()),
        "mediana": float(np.median(m2)),
        "media_reponderada": float(np.average(m2, weights=w)),
        "mediana_reponderada": _mediana_ponderada(m2, w),
    }
    escritura = float(fila_registro["eur_m2_usada_2018"])
    brechas = {k: 1 - escritura / v for k, v in anuncio.items()}
    return {
        "eur_m2_anuncio_media_reponderada": anuncio["media_reponderada"],
        "brecha_central": brechas["media_reponderada"],
        "brecha_min": min(brechas.values()),
        "brecha_max": max(brechas.values()),
        **{f"brecha_{k}": v for k, v in brechas.items()},
    }


def factores_actualizacion(esc_2018: pd.DataFrame, esc_actual: pd.DataFrame,
                           ipv: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    ipv = ipv.set_index("trimestre")["segunda_mano"]
    anio = int(esc_actual["anio"].iloc[0])
    ultimo = ipv.index[-1]
    del_anio = ipv[[t for t in ipv.index if t.startswith(str(anio))]]
    de_2018 = ipv[[t for t in ipv.index if t.startswith("2018")]]
    if len(del_anio) != 4 or len(de_2018) != 4:
        raise ValueError(f"El IPV no trae los cuatro trimestres de 2018 y de {anio}")

    a_ultimo = float(ipv[ultimo] / del_anio.mean())
    a_t4 = float(de_2018.mean() / ipv[TRIMESTRE_COMPARABLES])
    f = esc_2018[["distrito_id", "distrito", "eur_m2_usada_2018"]].merge(
        esc_actual[["distrito_id", "eur_m2_usada"]], on="distrito_id", validate="1:1")
    f["factor_registro"] = f["eur_m2_usada"] / f["eur_m2_usada_2018"]
    f["factor_actualizacion"] = f["factor_registro"] * a_ultimo * a_t4
    f["factor_solo_ine"] = float(ipv[ultimo] / ipv[TRIMESTRE_COMPARABLES])
    meta = {"anio_escrituras": anio, "trimestre_actual": ultimo,
            "ipv_ajuste_a_ultimo_trimestre": round(a_ultimo, 4),
            "ipv_ajuste_media2018_a_T4": round(a_t4, 4)}
    return f.rename(columns={"eur_m2_usada": f"eur_m2_usada_{anio}"}), meta


def ejecutar() -> pd.DataFrame:
    esc_2018 = leer_ref(F_ESC_2018)
    esc_actual = leer_ref(F_ESC_ACTUAL)
    ipv = leer_ref(F_IPV)
    f, meta = factores_actualizacion(esc_2018, esc_actual, ipv)

    d, _ = preparar(pd.read_csv(F_ENTRADA))
    d["distrito_id"] = distrito_de(d["barrio_id"])
    # Solo segunda mano, para compararlo con la escritura de vivienda usada
    usados = d[d["obra_nueva"] == 0]
    filas = []
    for r in esc_2018.itertuples():
        anuncios = usados[usados["distrito_id"] == r.distrito_id]
        filas.append({"distrito_id": r.distrito_id, "anuncios_2018": len(anuncios),
                      **brecha_distrito(anuncios, esc_2018.loc[r.Index])})
    salida = f.merge(pd.DataFrame(filas), on="distrito_id", validate="1:1")
    salida.round(4).to_csv(F_FACTORES, index=False)

    resumen = {
        **meta,
        "fuentes": {
            "escrituras_2018": cabecera(F_ESC_2018, "FUENTE"),
            "escrituras_actual": cabecera(F_ESC_ACTUAL, "FUENTE"),
            "escrituras_actual_consultado": cabecera(F_ESC_ACTUAL, "CONSULTADO")[:10],
            "ipv": cabecera(F_IPV, "FUENTE"),
            "ipv_consultado": cabecera(F_IPV, "CONSULTADO")[:10],
        },
        "brecha_central_mediana_distritos": round(float(salida["brecha_central"].median()), 4),
        "brecha_min_distritos": round(float(salida["brecha_min"].min()), 4),
        "brecha_max_distritos": round(float(salida["brecha_max"].max()), 4),
        "factor_actualizacion_min": round(float(salida["factor_actualizacion"].min()), 4),
        "factor_actualizacion_max": round(float(salida["factor_actualizacion"].max()), 4),
        "factor_solo_ine": round(float(salida["factor_solo_ine"].iloc[0]), 4),
    }
    F_RESUMEN.write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    return salida


if __name__ == "__main__":
    s = ejecutar()
    cols = ["distrito", "factor_actualizacion", "factor_solo_ine",
            "brecha_min", "brecha_central", "brecha_max"]
    with pd.option_context("display.width", 140):
        print(s[cols].round(3).to_string(index=False))
