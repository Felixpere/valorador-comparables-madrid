"""Paso 04 — Medicion.

Que se mide y contra que
------------------------
Todo lo de aqui se mide contra la verdad de terreno del corpus SINTETICO, que
existe porque nosotros lo generamos. Es una medida de la mecanica del sistema,
no de su rendimiento en el mercado real de Madrid. Dicho de otra forma: estas
cifras dicen que las piezas encajan, no que el modelo acierte precios de verdad.

Lo que si se puede afirmar:
  * la extraccion recupera los campos que estan en el texto, y en que formatos
    falla;
  * el motor de comparables recupera desviaciones de precio que sabemos que
    existen, y con cuanto error estima el precio de mercado.

Lo que NO se puede afirmar con esto: que el motor detecte oportunidades reales.
Eso exige datos reales de cierre. Ver SUPUESTOS.md.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import config as cfg

CAMPOS_MEDIBLES = ["distrito", "superficie_m2", "habitaciones", "banos",
                   "planta", "ascensor", "estado", "anio_construccion",
                   "exterior", "precio_eur"]


def _iguales(a: pd.Series, b: pd.Series) -> pd.Series:
    """Comparacion tolerante al tipo (3 == 3.0 == '3') y a las tildes.

    Las tildes importan, y por eso se ignoran aqui. El pipeline canoniza los
    distritos en p02 quitando los diacriticos, asi que "Tetuan" y "Tetuan" con
    tilde son el MISMO dato para todo lo que viene despues. Compararlos como
    distintos no mide un error de extraccion: mide una diferencia ortografica
    que el propio sistema ya resuelve.

    No es un detalle menor. El motor de reglas escribe siempre la forma canonica
    sin tilde, porque la saca de una lista; un modelo de lenguaje escribe espanol
    correcto y pone "Tetuan" con tilde. Con la comparacion anterior, el LLM
    perdia dos campos de 250 por escribir bien, y la cifra publicada favorecia a
    las reglas por un motivo que no tiene nada que ver con extraer.
    """
    def norm(s):
        n = pd.to_numeric(s, errors="coerce")
        texto = (s.astype(str)
                 .str.normalize("NFD")
                 .str.encode("ascii", "ignore").str.decode("ascii")
                 .str.strip().str.lower())
        return np.where(n.notna(), n.astype("Float64"), texto)
    return pd.Series(norm(a) == norm(b), index=a.index)


def evaluar_extraccion(verdad: pd.DataFrame, extraido: pd.DataFrame) -> dict:
    m = verdad.merge(extraido, on="ref", suffixes=("_real", "_ext"))
    por_campo, aciertos_fila = {}, []
    for c in CAMPOS_MEDIBLES:
        ok = _iguales(m[f"{c}_real"], m[f"{c}_ext"])
        por_campo[c] = round(float(ok.mean()), 4)
        aciertos_fila.append(ok)
    aciertos = pd.concat(aciertos_fila, axis=1)

    por_formato = {}
    for fmt, g in m.groupby("formato_origen"):
        sub = aciertos.loc[g.index]
        por_formato[fmt] = round(float(sub.to_numpy().mean()), 4)

    # Desglose por motor: si parte del corpus paso por el LLM y parte por
    # reglas, mezclar las dos cifras en una sola seria enganoso.
    por_motor = {}
    for motor, g in m.groupby("motor_extraccion"):
        sub = aciertos.loc[g.index]
        por_motor[motor] = {
            "n_anuncios": int(len(g)),
            "exactitud": round(float(sub.to_numpy().mean()), 4),
            "anuncios_perfectos": round(float(sub.all(axis=1).mean()), 4),
        }

    return {
        "motor": str(extraido["motor_extraccion"].mode().iat[0]),
        "reparto_por_motor": por_motor,
        "n_anuncios": int(len(m)),
        "exactitud_global_por_campo": round(float(aciertos.to_numpy().mean()), 4),
        "anuncios_perfectos": round(float(aciertos.all(axis=1).mean()), 4),
        "exactitud_por_campo": por_campo,
        "exactitud_por_formato_de_texto": por_formato,
    }


def evaluar_motor(verdad: pd.DataFrame, valorado: pd.DataFrame) -> dict:
    m = valorado.merge(
        verdad[["ref", "desviacion_inyectada", "etiqueta_verdad", "precio_eur"]],
        on="ref", suffixes=("", "_v"))
    con_valor = m[m["desviacion"].notna()].copy()

    # Precio "justo" del generador, antes de inyectarle la desviacion
    con_valor["precio_justo"] = (con_valor["precio_eur_v"] /
                                 (1 + con_valor["desviacion_inyectada"]))
    err = (con_valor["valor_estimado_eur"] - con_valor["precio_justo"]).abs()
    mape = float((err / con_valor["precio_justo"]).median())

    marcado = con_valor["clasificacion"] == "por debajo de comparables"
    real = con_valor["etiqueta_verdad"] == "infraprecio_inyectado"
    vp = int((marcado & real).sum())
    precision = vp / max(int(marcado.sum()), 1)
    recall = vp / max(int(real.sum()), 1)

    corr = float(np.corrcoef(con_valor["desviacion"],
                             con_valor["desviacion_inyectada"])[0, 1])

    # Barrido de umbrales: cuanto mas exigente es el corte, mas limpia es la
    # lista y menos oportunidades se recuperan. No hay un umbral "correcto",
    # depende de cuantas visitas en falso se pueda permitir el equipo.
    barrido = []
    for u in [-0.05, -0.10, -0.15, -0.20, -0.25]:
        marc = con_valor["desviacion"] <= u
        v = int((marc & real).sum())
        barrido.append({
            "umbral": u,
            "marcados": int(marc.sum()),
            "precision": round(v / max(int(marc.sum()), 1), 4),
            "recall": round(v / max(int(real.sum()), 1), 4),
        })

    por_fiab = {
        f: round(float(((g["valor_estimado_eur"] - g["precio_justo"]).abs()
                        / g["precio_justo"]).median()), 4)
        for f, g in con_valor.groupby("fiabilidad")
    }

    return {
        "n_evaluados": int(len(m)),
        "n_con_valoracion": int(len(con_valor)),
        "cobertura": round(len(con_valor) / max(len(m), 1), 4),
        "error_mediano_valoracion": round(mape, 4),
        "error_mediano_por_fiabilidad": por_fiab,
        "correlacion_desviacion_estimada_vs_real": round(corr, 4),
        "infraprecio_precision": round(precision, 4),
        "infraprecio_recall": round(recall, 4),
        "barrido_umbrales": barrido,
        "nota": ("Medido sobre corpus sintetico con verdad de terreno conocida. "
                 "No es una medida de rendimiento sobre anuncios reales."),
    }


def verificar_ausencia_de_fugas(valorado: pd.DataFrame,
                                normalizado: pd.DataFrame) -> dict:
    """Comprobacion sobre la salida real, no sobre casos de test."""
    fechas = dict(zip(normalizado["ref"], pd.to_datetime(normalizado["fecha"])))
    auto, futuros = 0, 0
    for _, r in valorado.iterrows():
        if not r["refs_comparables"]:
            continue
        refs = str(r["refs_comparables"]).split(";")
        if r["ref"] in refs:
            auto += 1
        f = fechas[r["ref"]]
        if any(fechas[x] >= f for x in refs if x in fechas):
            futuros += 1
    return {
        "inmuebles_en_sus_propios_comparables": auto,
        "comparables_con_fecha_igual_o_posterior": futuros,
        "limpio": auto == 0 and futuros == 0,
    }


def comparar_motores(verdad: pd.DataFrame, extraido: pd.DataFrame) -> dict | None:
    """Los dos motores sobre EXACTAMENTE los mismos anuncios.

    `reparto_por_motor` mide cada motor sobre los anuncios que le tocaron, que no
    son los mismos: el LLM procesa los primeros y las reglas el resto. Comparar
    esas dos cifras entre si no dice cual extrae mejor, dice que a cada uno le
    tocaron documentos distintos.

    Aqui se vuelven a extraer con reglas los mismos anuncios que paso el LLM y se
    miden los dos sobre ese conjunto. Las reglas son deterministas y gratis, asi
    que la pasada extra no cuesta nada.

    Devuelve None si no hubo pasada de LLM.
    """
    import p01_extraer  # local: evita ciclo de importacion al cargar el modulo

    del_llm = extraido[extraido["motor_extraccion"].str.startswith("llm")]
    if del_llm.empty:
        return None

    refs = sorted(del_llm["ref"])
    corpus = {json.loads(l)["ref"]: json.loads(l)
              for l in cfg.F_CORPUS.read_text(encoding="utf-8").splitlines()}
    reglas = pd.DataFrame([
        {**p01_extraer.extraer_reglas(corpus[r]["texto"]), "ref": r,
         "motor_extraccion": "reglas"} for r in refs])

    v = verdad[verdad["ref"].isin(refs)]
    salida = {"n_anuncios": len(refs), "campos_comparados": len(CAMPOS_MEDIBLES),
              "motores": {}}
    for nombre, ext in [(str(del_llm["motor_extraccion"].iat[0]), del_llm),
                        ("reglas", reglas)]:
        m = v.merge(ext, on="ref", suffixes=("_real", "_ext"))
        ok = pd.concat([_iguales(m[f"{c}_real"], m[f"{c}_ext"])
                        for c in CAMPOS_MEDIBLES], axis=1)
        salida["motores"][nombre] = {
            "exactitud": round(float(ok.to_numpy().mean()), 4),
            "anuncios_perfectos": round(float(ok.all(axis=1).mean()), 4),
            "campos_fallados": int((~ok).to_numpy().sum()),
            "por_campo": {c: round(float(ok.iloc[:, i].mean()), 4)
                          for i, c in enumerate(CAMPOS_MEDIBLES)},
        }
    salida["aviso"] = (
        "Las reglas juegan en casa: sus expresiones regulares se escribieron "
        "mirando estas mismas cinco plantillas de texto. Su exactitud es "
        "sobreajuste de manual y no es extrapolable a formatos nuevos, que es "
        "justo donde un modelo de lenguaje no necesita que nadie toque el codigo. "
        f"Con {len(refs)} anuncios y {len(CAMPOS_MEDIBLES)} campos son "
        f"{len(refs) * len(CAMPOS_MEDIBLES)} observaciones por motor: una "
        "diferencia de uno o dos campos no distingue a nadie.")
    return salida


def ejecutar() -> dict:
    verdad = pd.read_csv(cfg.F_VERDAD)
    extraido = pd.read_csv(cfg.F_EXTRAIDO)
    normalizado = pd.read_csv(cfg.F_NORMALIZADO)
    valorado = pd.read_csv(cfg.F_VALORADO).fillna({"refs_comparables": ""})

    metricas = {
        "extraccion": evaluar_extraccion(verdad, extraido),
        "comparacion_de_motores": comparar_motores(verdad, extraido),
        "motor_valoracion": evaluar_motor(verdad, valorado),
        "control_de_fugas": verificar_ausencia_de_fugas(valorado, normalizado),
        "parametros": {
            "banda_superficie": cfg.BANDA_SUPERFICIE,
            "ventana_dias": cfg.VENTANA_DIAS,
            "min_comparables": cfg.MIN_COMPARABLES,
            "semilla": cfg.SEMILLA,
        },
    }
    cfg.F_METRICAS.write_text(json.dumps(metricas, indent=2, ensure_ascii=False),
                              encoding="utf-8")
    return metricas


if __name__ == "__main__":
    m = ejecutar()
    e, v, f = m["extraccion"], m["motor_valoracion"], m["control_de_fugas"]
    print(f"EXTRACCION ({e['n_anuncios']} anuncios)")
    for motor, d in e["reparto_por_motor"].items():
        print(f"  {motor:<24} n={d['n_anuncios']:<5} campos correctos "
              f"{d['exactitud']:.1%}, sin errores {d['anuncios_perfectos']:.1%}")
    print(f"  conjunto: {e['exactitud_global_por_campo']:.1%}")
    print(f"  anuncios sin ningun error: {e['anuncios_perfectos']:.1%}")
    print("  por formato de texto:")
    for k, val in sorted(e["exactitud_por_formato_de_texto"].items(),
                         key=lambda x: x[1]):
        print(f"    {k:<10} {val:.1%}")
    print("  peores campos:")
    for k, val in sorted(e["exactitud_por_campo"].items(), key=lambda x: x[1])[:4]:
        print(f"    {k:<20} {val:.1%}")
    print(f"\nMOTOR DE VALORACION")
    print(f"  cobertura: {v['cobertura']:.1%}")
    print(f"  error mediano de valoracion: {v['error_mediano_valoracion']:.1%}")
    print(f"  por fiabilidad: {v['error_mediano_por_fiabilidad']}")
    print(f"  correlacion desviacion estimada vs inyectada: "
          f"{v['correlacion_desviacion_estimada_vs_real']:.2f}")
    print(f"  infraprecio -> precision {v['infraprecio_precision']:.1%} / "
          f"recall {v['infraprecio_recall']:.1%}")
    print("  umbral   marcados  precision  recall")
    for b in v["barrido_umbrales"]:
        print(f"  {b['umbral']:>6.0%}   {b['marcados']:>8}  {b['precision']:>9.1%}"
              f"  {b['recall']:>6.1%}")
    print(f"\nCONTROL DE FUGAS: {'limpio' if f['limpio'] else 'FALLO'} {f}")
