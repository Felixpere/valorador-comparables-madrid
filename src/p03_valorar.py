"""Paso 03 — Valoracion por comparables.

Para cada inmueble se construye su propio conjunto de comparables:

  * mismo distrito,
  * superficie dentro de +/-20%,
  * publicados ESTRICTAMENTE ANTES que el inmueble evaluado, dentro de una
    ventana de 270 dias,
  * y nunca el propio inmueble.

Sobre esos comparables se calcula un EUR/m2 mediano, ajustado por estado de
conservacion, orientacion y ascensor. La desviacion entre el precio pedido y ese
valor estimado es la senal.

Sobre las fugas de informacion
------------------------------
Es el error que arruina en silencio este tipo de modelos: el resultado sale
excelente porque el modelo esta mirando datos que no podria tener. Aqui se
bloquea en tres sitios y hay tests que lo comprueban:

  1. El inmueble evaluado se excluye por referencia de su propio conjunto.
  2. El filtro temporal es estricto (<, no <=): nada del mismo dia ni posterior.
  3. Los coeficientes de ajuste se reestiman cada mes usando solo datos de meses
     anteriores. El primer mes no se valora: no hay historico.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import config as cfg

# Variables del ajuste hedonico. El distrito no entra: los comparables ya son
# del mismo distrito, asi que su efecto se cancela.
ESTADOS_ORD = ["a reformar", "buen estado", "reformado", "obra nueva"]
MIN_OBS_AJUSTE = 80          # por debajo de esto no se estima ajuste, se deja a 1


def _matriz(df: pd.DataFrame) -> np.ndarray:
    """Variables explicativas: estado (dummies), exterior, planta alta sin ascensor."""
    cols = [np.ones(len(df))]
    for e in ESTADOS_ORD[1:]:                     # "a reformar" es la categoria base
        cols.append((df["estado"] == e).astype(float).to_numpy())
    cols.append(df["exterior"].fillna(True).astype(float).to_numpy())
    alta_sin_asc = ((df["planta"].fillna(0) >= 3) &
                    (~df["ascensor"].fillna(True).astype(bool))).astype(float)
    cols.append(alta_sin_asc.to_numpy())
    return np.column_stack(cols)


def estimar_coeficientes(historico: pd.DataFrame) -> np.ndarray | None:
    """OLS sobre log(EUR/m2), centrado por distrito para aislar el efecto de los atributos."""
    if len(historico) < MIN_OBS_AJUSTE:
        return None
    h = historico.copy()
    h["log_m2"] = np.log(h["eur_m2"])
    h["y"] = h["log_m2"] - h.groupby("distrito")["log_m2"].transform("mean")
    X = _matriz(h)
    beta, *_ = np.linalg.lstsq(X, h["y"].to_numpy(), rcond=None)
    return beta


def _ajuste(df: pd.DataFrame, beta: np.ndarray | None) -> np.ndarray:
    """Factor multiplicativo que lleva cada inmueble a 'estado base'."""
    if beta is None:
        return np.ones(len(df))
    X = _matriz(df)
    X[:, 0] = 0.0                                  # el intercepto no se transporta
    return np.exp(X @ beta)


def valorar(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["apta_valoracion"]].copy()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.sort_values("fecha").reset_index(drop=True)
    df["mes"] = df["fecha"].dt.to_period("M")

    # Coeficientes por mes, estimados solo con meses anteriores
    coef_mes: dict[pd.Period, np.ndarray | None] = {}
    for mes in sorted(df["mes"].unique()):
        coef_mes[mes] = estimar_coeficientes(df[df["mes"] < mes])

    resultados = []
    for _, s in df.iterrows():
        beta = coef_mes[s["mes"]]

        ventana_ini = s["fecha"] - pd.Timedelta(days=cfg.VENTANA_DIAS)
        comps = df[
            (df["ref"] != s["ref"])                       # 1. nunca el propio inmueble
            & (df["fecha"] < s["fecha"])                  # 2. estrictamente anteriores
            & (df["fecha"] >= ventana_ini)
            & (df["distrito"] == s["distrito"])
            & (df["superficie_m2"].between(
                s["superficie_m2"] * (1 - cfg.BANDA_SUPERFICIE),
                s["superficie_m2"] * (1 + cfg.BANDA_SUPERFICIE)))
        ]

        base = {
            "ref": s["ref"],
            "fecha": s["fecha"],
            "distrito": s["distrito"],
            "superficie_m2": s["superficie_m2"],
            "estado": s["estado"],
            "precio_eur": s["precio_eur"],
            "eur_m2_pedido": s["eur_m2"],
            "n_comparables": len(comps),
            "ajuste_estimado": beta is not None,
        }

        if len(comps) < cfg.MIN_COMPARABLES:
            # Distinguir "aun no hay historico" de "segmento poco liquido" importa:
            # lo primero se resuelve solo con el tiempo, lo segundo no.
            sin_historico = (s["fecha"] - df["fecha"].min()).days < 60
            motivo = ("ventana inicial sin histórico" if sin_historico
                      else "segmento con pocas operaciones comparables")
            resultados.append({**base, "valor_estimado_eur": np.nan,
                               "eur_m2_comparables": np.nan, "desviacion": np.nan,
                               "score_oportunidad": np.nan, "fiabilidad": "sin muestra",
                               "clasificacion": "no valorable",
                               "motivo_no_valorable": motivo,
                               "refs_comparables": ""})
            continue

        # Cada comparable se lleva a las condiciones del inmueble evaluado
        f_comp = _ajuste(comps, beta)
        f_suj = float(_ajuste(pd.DataFrame([s]), beta)[0])
        m2_ajustado = comps["eur_m2"].to_numpy() / f_comp * f_suj

        mediana = float(np.median(m2_ajustado))
        valor = mediana * s["superficie_m2"]
        desviacion = s["precio_eur"] / valor - 1.0

        q1, q3 = np.percentile(m2_ajustado, [25, 75])
        dispersion = (q3 - q1) / mediana
        if len(comps) >= 15 and dispersion < 0.22:
            fiabilidad = "alta"
        elif len(comps) >= 8 and dispersion < 0.35:
            fiabilidad = "media"
        else:
            fiabilidad = "baja"

        score = float(np.clip(50 - desviacion * 250, 0, 100))
        if desviacion <= cfg.UMBRAL_OPORTUNIDAD:
            clas = "por debajo de comparables"
        elif desviacion >= -cfg.UMBRAL_OPORTUNIDAD:
            clas = "por encima de comparables"
        else:
            clas = "en linea con comparables"

        resultados.append({
            **base,
            "valor_estimado_eur": round(valor, 0),
            "eur_m2_comparables": round(mediana, 2),
            "desviacion": round(desviacion, 4),
            "score_oportunidad": round(score, 1),
            "dispersion_comparables": round(float(dispersion), 4),
            "fiabilidad": fiabilidad,
            "clasificacion": clas,
            "motivo_no_valorable": "",
            "refs_comparables": ";".join(comps["ref"].head(30)),
        })

    return pd.DataFrame(resultados)


def ejecutar() -> pd.DataFrame:
    df = pd.read_csv(cfg.F_NORMALIZADO)
    res = valorar(df)
    res.to_csv(cfg.F_VALORADO, index=False)
    return res


if __name__ == "__main__":
    r = ejecutar()
    val = r["desviacion"].notna()
    print(f"Evaluados {len(r)} inmuebles. Con valoracion: {val.sum()} "
          f"({val.mean():.1%}). Sin muestra suficiente: {(~val).sum()}.")
    print("\nClasificacion:")
    print(r["clasificacion"].value_counts().to_string())
    print("\nFiabilidad:")
    print(r["fiabilidad"].value_counts().to_string())
    nv = r[r["clasificacion"] == "no valorable"]
    if len(nv):
        print("\nMotivo de las no valorables:")
        print(nv["motivo_no_valorable"].value_counts().to_string())
