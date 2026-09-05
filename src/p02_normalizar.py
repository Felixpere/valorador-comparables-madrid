"""Paso 02 — Limpieza, tipado y validacion.

Lo que sale de una extraccion sobre texto libre nunca es utilizable tal cual:
hay campos vacios, distritos escritos de cinco maneras y valores imposibles.
Aqui se decide, con reglas explicitas, que fila entra al motor de valoracion y
cual se aparta.

Nada se borra en silencio. Toda fila descartada sale en el informe de calidad
con el motivo, y ese informe acaba en el Excel y en el dashboard.
"""
from __future__ import annotations

import unicodedata

import numpy as np
import pandas as pd

import config as cfg
from p01_extraer import DISTRITOS_CANON

# Campos sin los cuales no se puede valorar un inmueble
CRITICOS = ["distrito", "superficie_m2", "precio_eur", "fecha"]

RANGOS = {
    "superficie_m2": (15, 500),
    "precio_eur": (30_000, 6_000_000),
    "habitaciones": (1, 10),
    "banos": (1, 6),
    "planta": (0, 30),
    "anio_construccion": (1850, 2027),
}

ESTADOS_VALIDOS = set(cfg.COEF_ESTADO)


def _clave(t: str) -> str:
    t = "".join(c for c in unicodedata.normalize("NFD", str(t))
                if unicodedata.category(c) != "Mn")
    return t.lower().replace("-", " ").replace(".", "").strip()


MAPA_DISTRITOS = {_clave(d): d for d in DISTRITOS_CANON}
# Variantes habituales que se ven en texto redactado por personas
MAPA_DISTRITOS.update({
    "puente vallecas": "Puente de Vallecas",
    "vallecas puente": "Puente de Vallecas",
    "villa vallecas": "Villa de Vallecas",
    "san blas": "San Blas-Canillejas",
    "canillejas": "San Blas-Canillejas",
    "fuencarral": "Fuencarral-El Pardo",
    "el pardo": "Fuencarral-El Pardo",
    "moncloa": "Moncloa-Aravaca",
    "aravaca": "Moncloa-Aravaca",
    "ciudad lineal": "Ciudad Lineal",
})


def _canon_distrito(v):
    if pd.isna(v):
        return None
    return MAPA_DISTRITOS.get(_clave(v))


def _a_bool(v):
    if isinstance(v, bool):
        return v
    if pd.isna(v):
        return None
    s = str(v).strip().lower()
    if s in {"true", "si", "sí", "1", "1.0", "yes"}:
        return True
    if s in {"false", "no", "0", "0.0"}:
        return False
    return None


def normalizar(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    incidencias = []

    def anota(mask, campo, motivo):
        for ref in df.loc[mask, "ref"]:
            incidencias.append({"ref": ref, "campo": campo, "motivo": motivo})

    # 1. Duplicados por referencia: se queda la primera aparicion
    dup = df.duplicated("ref", keep="first")
    anota(dup, "ref", "referencia duplicada")
    df = df[~dup].copy()

    # 2. Distrito a nomenclatura oficial del Ayuntamiento
    df["distrito_bruto"] = df["distrito"]
    df["distrito"] = df["distrito"].map(_canon_distrito)
    anota(df["distrito"].isna() & df["distrito_bruto"].notna(),
          "distrito", "distrito no reconocido")

    # 3. Numericos: lo que no convierte se vuelve nulo, no se adivina
    for campo, (lo, hi) in RANGOS.items():
        df[campo] = pd.to_numeric(df[campo], errors="coerce")
        fuera = df[campo].notna() & ~df[campo].between(lo, hi)
        anota(fuera, campo, f"fuera de rango plausible [{lo}, {hi}]")
        df.loc[fuera, campo] = np.nan

    for campo in ["habitaciones", "banos", "planta", "anio_construccion"]:
        df[campo] = df[campo].astype("Int64")

    # 4. Booleanos y categorias
    for campo in ["ascensor", "exterior"]:
        df[campo] = df[campo].map(_a_bool).astype("boolean")

    df["estado"] = df["estado"].astype(str).str.strip().str.lower()
    invalido = ~df["estado"].isin(ESTADOS_VALIDOS)
    anota(invalido & df["estado"].ne("nan"), "estado", "estado no catalogado")
    df.loc[invalido, "estado"] = pd.NA

    # 5. Fecha
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce", format="mixed")
    anota(df["fecha"].isna(), "fecha", "fecha ausente o ilegible")

    # 6. Criticos: sin ellos no hay valoracion posible
    falta_critico = df[CRITICOS].isna().any(axis=1)
    for campo in CRITICOS:
        anota(df[campo].isna(), campo, "campo critico ausente -> fila apartada")

    df["apta_valoracion"] = ~falta_critico
    df["eur_m2"] = (df["precio_eur"] / df["superficie_m2"]).round(2)

    # 7. Imputaciones minimas, siempre marcadas
    df["estado_imputado"] = df["estado"].isna()
    df["estado"] = df["estado"].fillna("buen estado")   # supuesto conservador
    df["exterior_imputado"] = df["exterior"].isna()
    df["exterior"] = df["exterior"].fillna(True)

    informe = pd.DataFrame(incidencias, columns=["ref", "campo", "motivo"])
    return df, informe


def ejecutar() -> tuple[pd.DataFrame, pd.DataFrame]:
    bruto = pd.read_csv(cfg.F_EXTRAIDO)
    df, informe = normalizar(bruto)
    cfg.DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(cfg.F_NORMALIZADO, index=False)
    informe.to_csv(cfg.DIR_PROCESSED / "informe_calidad.csv", index=False)
    return df, informe


if __name__ == "__main__":
    df, informe = ejecutar()
    n_ok = int(df["apta_valoracion"].sum())
    print(f"Normalizados {len(df)} registros. Aptos para valorar: {n_ok} "
          f"({n_ok / len(df):.1%}).")
    if len(informe):
        print("\nIncidencias por motivo:")
        print(informe["motivo"].value_counts().to_string())
    else:
        print("Sin incidencias.")
