"""Paso R07 — Recalibrar el descuento con precios de cierre reales de una agencia.

Con datos publicos solo se puede medir la BRECHA entre anuncio y escritura por
distrito, que mezcla negociacion con otras cosas (ver r06). Lo que la aisla es
tener, para un mismo piso, el ultimo precio anunciado y el precio firmado. Eso
solo lo tiene quien lo vendio.

Entrada: data/agencia/cierres.csv, con la forma de
data/agencia/plantilla_cierres.csv. Una fila por operacion cerrada:

    distrito                 nombre del distrito (como en la plantilla)
    superficie_m2            construidos
    fecha_publicacion        AAAA-MM-DD, primera vez que se anuncio
    precio_publicado_inicial EUR, primer precio anunciado
    precio_publicado_final   EUR, ultimo precio anunciado antes de la reserva
    fecha_firma              AAAA-MM-DD, escritura
    precio_cierre            EUR, precio de la escritura

Sin datos personales: ni direcciones, ni nombres, ni referencias catastrales.
Si el fichero trae una columna que lo parezca, se para con un error en vez de
procesarlo. El fichero no se versiona (.gitignore): los cierres de una agencia
no son publicos.

Salida: data/agencia/descuento_agencia.csv, por distrito, con n, mediana y
cuartiles del descuento. La demo lo usa en vez de la brecha publica solo en los
distritos con al menos MIN_CIERRES operaciones.

    python src/r07_cierres_agencia.py
"""
from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DIR_AGENCIA = RAIZ / "data" / "agencia"
F_PLANTILLA = DIR_AGENCIA / "plantilla_cierres.csv"
F_CIERRES = DIR_AGENCIA / "cierres.csv"
F_DESCUENTO = DIR_AGENCIA / "descuento_agencia.csv"

# Por debajo de esto, el cuartil de un distrito se mueve con cada operacion
# nueva: no se usa y la demo sigue con la brecha publica.
MIN_CIERRES = 10

COLUMNAS = ["distrito", "superficie_m2", "fecha_publicacion",
            "precio_publicado_inicial", "precio_publicado_final",
            "fecha_firma", "precio_cierre"]
# Fragmentos de nombre de columna que delatan un dato personal o que identifica
# el inmueble. Se comprueban sin tildes y en minusculas.
PROHIBIDAS = ["nombre", "apellido", "dni", "nif", "nie", "telefono", "movil",
              "email", "correo", "direccion", "calle", "portal", "piso_letra",
              "catastral", "comprador", "vendedor", "propietario", "cliente"]


def _canon(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", str(s))
                if unicodedata.category(c) != "Mn")
    return s.strip().lower()


def validar(d: pd.DataFrame) -> pd.DataFrame:
    personales = [c for c in d.columns if any(p in _canon(c) for p in PROHIBIDAS)]
    if personales:
        raise ValueError("El fichero trae columnas con datos personales o que "
                         f"identifican el inmueble: {personales}. Quitalas antes "
                         "de cargarlo.")
    faltan = [c for c in COLUMNAS if c not in d.columns]
    if faltan:
        raise ValueError(f"Faltan columnas: {faltan}")
    d = d[COLUMNAS].copy()
    for c in ["fecha_publicacion", "fecha_firma"]:
        d[c] = pd.to_datetime(d[c], errors="coerce")
    for c in ["superficie_m2", "precio_publicado_inicial",
              "precio_publicado_final", "precio_cierre"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["distrito_canon"] = d["distrito"].map(_canon)
    validas = (d[COLUMNAS].notna().all(axis=1)
               & (d["precio_cierre"] > 0) & (d["precio_publicado_final"] > 0)
               & (d["fecha_firma"] >= d["fecha_publicacion"]))
    return d[validas].reset_index(drop=True)


def descuentos(d: pd.DataFrame) -> pd.DataFrame:
    """Descuento por distrito. Dos medidas, porque cuentan cosas distintas:

    * sobre el ultimo precio anunciado: la negociacion final;
    * sobre el primer precio anunciado: negociacion mas las rebajas de precio
      mientras estuvo publicado. Es la que se compara con la brecha publica,
      que tambien mezcla las dos.
    """
    d = d.assign(
        descuento_final=1 - d["precio_cierre"] / d["precio_publicado_final"],
        descuento_inicial=1 - d["precio_cierre"] / d["precio_publicado_inicial"],
        dias_en_mercado=(d["fecha_firma"] - d["fecha_publicacion"]).dt.days,
    )
    g = d.groupby("distrito_canon")
    salida = pd.DataFrame({
        "distrito": g["distrito"].first(),
        "n_cierres": g.size(),
        "descuento_final_p25": g["descuento_final"].quantile(0.25),
        "descuento_final_mediana": g["descuento_final"].median(),
        "descuento_final_p75": g["descuento_final"].quantile(0.75),
        "descuento_inicial_p25": g["descuento_inicial"].quantile(0.25),
        "descuento_inicial_mediana": g["descuento_inicial"].median(),
        "descuento_inicial_p75": g["descuento_inicial"].quantile(0.75),
        "dias_en_mercado_mediana": g["dias_en_mercado"].median(),
        "fecha_firma_desde": g["fecha_firma"].min().dt.date,
        "fecha_firma_hasta": g["fecha_firma"].max().dt.date,
    }).reset_index()
    salida["suficiente"] = salida["n_cierres"] >= MIN_CIERRES
    return salida


def ejecutar(ruta: Path = F_CIERRES) -> pd.DataFrame:
    if not ruta.exists():
        raise FileNotFoundError(
            f"No hay {ruta.relative_to(RAIZ)}. Copia {F_PLANTILLA.name}, "
            "rellenala y guardala con ese nombre.")
    s = descuentos(validar(pd.read_csv(ruta)))
    s.round(4).to_csv(F_DESCUENTO, index=False)
    return s


if __name__ == "__main__":
    s = ejecutar()
    print(s[["distrito", "n_cierres", "descuento_final_mediana",
             "descuento_inicial_mediana", "suficiente"]].to_string(index=False))
    print(f"\nEscrito {F_DESCUENTO.relative_to(RAIZ)}")
