"""Paso R00 — Carga de datos REALES: {idealista18}.

Que es
------
94.815 anuncios reales de venta de vivienda en Madrid, los cuatro trimestres de
2018, con 41 variables por anuncio y coordenadas aproximadas. Publicado por la
propia idealista junto a dos universidades:

    Rey-Blanco, D., Arbues, P. (idealista), Lopez, F. (UPCT) y Paez, A.
    (McMaster University), "A geo-referenced micro-data set of real estate
    listings for Spain's three largest cities", Environment and Planning B:
    Urban Analytics and City Science, 2024.
    https://doi.org/10.1177/23998083241242844
    https://github.com/paezha/idealista18

Licencia: ODbL-1.0 (Open Database License). Atribucion obligatoria.

No es scraping. Es un producto de datos abiertos publicado por el propio portal.

Lo que hay que decir siempre
----------------------------
Son datos de 2018. Sirven para analizar la ESTRUCTURA del mercado (que barrios
son mas caros que otros, cuanto se dispersa el precio dentro de un barrio, que
atributos pesan) y para validar el motor. NO sirven para hablar del nivel de
precios de hoy. Los autores ademas anadieron ruido aleatorio a coordenadas y
precios por proteccion de datos.

Este script deja un CSV plano con el barrio ya asignado por punto en poligono.
"""
from __future__ import annotations

import sys
import urllib.request
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

RAIZ = Path(__file__).resolve().parent.parent
DIR_REAL = RAIZ / "data" / "real"
DIR_RDA = DIR_REAL / "rda"
F_SALIDA = DIR_REAL / "madrid_2018.csv"
F_BARRIOS = DIR_REAL / "barrios_madrid.csv"

BASE_URL = "https://github.com/paezha/idealista18/raw/master/data/"
FICHEROS = ["Madrid_Sale.rda", "Madrid_Polygons.rda"]

CITA = ("Rey-Blanco, Arbues, Lopez y Paez (2024), {idealista18}, "
        "Environment and Planning B, doi:10.1177/23998083241242844. Licencia ODbL-1.0.")


def descargar() -> None:
    DIR_RDA.mkdir(parents=True, exist_ok=True)
    for f in FICHEROS:
        destino = DIR_RDA / f
        if destino.exists():
            continue
        print(f"    descargando {f}...")
        urllib.request.urlretrieve(BASE_URL + f, destino)


def _poligonos(mp: pd.DataFrame):
    """Convierte la geometria sf anidada (multipoligono > poligono > anillo) a shapely."""
    from shapely.geometry import Polygon, MultiPolygon

    salida = []
    for _, fila in mp.iterrows():
        partes = []
        for poligono in fila["geometry"]:
            anillos = [np.asarray(a) for a in poligono]
            if not anillos or len(anillos[0]) < 4:
                continue
            partes.append(Polygon(anillos[0], anillos[1:] if len(anillos) > 1 else None))
        if partes:
            salida.append((fila["LOCATIONID"], fila["LOCATIONNAME"],
                           MultiPolygon(partes) if len(partes) > 1 else partes[0]))
    return salida


def asignar_barrio(ventas: pd.DataFrame, mp: pd.DataFrame) -> pd.DataFrame:
    """Punto en poligono. Sin geopandas: indice espacial de shapely, suficiente
    para 95.000 puntos y 135 barrios."""
    from shapely.geometry import Point
    from shapely.strtree import STRtree

    poligonos = _poligonos(mp)
    formas = [p[2] for p in poligonos]
    arbol = STRtree(formas)

    puntos = [Point(x, y) for x, y in zip(ventas["LONGITUDE"], ventas["LATITUDE"])]
    ids, nombres = [], []
    for punto in puntos:
        encontrado = None
        for idx in arbol.query(punto):
            if formas[idx].contains(punto):
                encontrado = idx
                break
        ids.append(poligonos[encontrado][0] if encontrado is not None else None)
        nombres.append(poligonos[encontrado][1] if encontrado is not None else None)

    ventas = ventas.copy()
    ventas["barrio_id"] = ids
    ventas["barrio"] = nombres
    return ventas


def ejecutar() -> pd.DataFrame:
    import rdata

    descargar()
    ventas = rdata.read_rda(str(DIR_RDA / "Madrid_Sale.rda"))["Madrid_Sale"]
    mp = rdata.read_rda(str(DIR_RDA / "Madrid_Polygons.rda"),
                        default_encoding="utf8")["Madrid_Polygons"]
    ventas.columns = [str(c) for c in ventas.columns]
    mp.columns = [str(c) for c in mp.columns]
    ventas = ventas.drop(columns=["geometry"])

    print(f"    {len(ventas)} anuncios, {len(mp)} barrios")
    ventas = asignar_barrio(ventas, mp)

    sin_barrio = ventas["barrio"].isna().sum()
    print(f"    sin barrio asignado: {sin_barrio} ({sin_barrio / len(ventas):.2%})")

    # Trimestre legible y fecha nominal de corte
    ventas["trimestre"] = ventas["PERIOD"].map(
        {201803: "2018T1", 201806: "2018T2", 201809: "2018T3", 201812: "2018T4"})
    ventas["fecha_corte"] = ventas["PERIOD"].map(
        {201803: "2018-03-31", 201806: "2018-06-30",
         201809: "2018-09-30", 201812: "2018-12-31"})

    DIR_REAL.mkdir(parents=True, exist_ok=True)
    ventas.to_csv(F_SALIDA, index=False)

    resumen = (ventas.dropna(subset=["barrio"])
               .groupby(["barrio_id", "barrio"])
               .agg(anuncios=("PRICE", "size"),
                    eur_m2_mediano=("UNITPRICE", "median"),
                    superficie_mediana=("CONSTRUCTEDAREA", "median"))
               .reset_index()
               .sort_values("eur_m2_mediano", ascending=False))
    resumen.to_csv(F_BARRIOS, index=False)
    return ventas


if __name__ == "__main__":
    v = ejecutar()
    print(f"\nGuardado -> {F_SALIDA}")
    print(f"Fuente: {CITA}\n")
    print(v.groupby("trimestre").agg(
        anuncios=("PRICE", "size"),
        eur_m2_mediano=("UNITPRICE", "median"),
        precio_mediano=("PRICE", "median")).to_string())
    print(f"\nIdentificadores unicos: {v['ASSETID'].nunique()} sobre {len(v)} filas")
