"""Paso R05 — Descarga las cifras publicas con las que se actualizan los precios.

Deja en data/referencia/ dos CSV, cada uno con su fuente y fecha en la cabecera:

  * escrituras_distrito_actual.csv — precio medio DECLARADO en escritura por
    distrito, ultimo ano publicado por el Ayuntamiento de Madrid (Estadistica
    Registral Inmobiliaria del Colegio de Registradores).
  * ipv_ine_madrid.csv — Indice de Precios de Vivienda del INE, Comunidad de
    Madrid, trimestral, base 2025 (tabla 80270).

La cifra de 2018 por distrito no se descarga: esta en un PDF que no cambia
(Anuario 2019) y va transcrita en escrituras_distrito_2018.csv.

Se ejecuta a mano cuando el Ayuntamiento o el INE publican dato nuevo:

    python src/r05_referencia_precios.py

y despues `python src/r06_actualizacion_cierre.py` para recalcular factores.
No va dentro de run_pipeline.py: necesita red y los tests no deben depender de
ella. Las URL se fijan aqui; si la fuente las cambia, el script falla en vez de
escribir un CSV vacio.

Por que Registradores y no el Notariado: el Portal Estadistico del Notariado
(penotariado.com) publica el precio escriturado por municipio y codigo postal,
pero solo a traves de un mapa interactivo, sin descarga ni API documentada. La
estadistica registral es del mismo tipo (precio declarado en escritura), la
publica el Ayuntamiento en xlsx por distrito y barrio, y tiene la serie de 2018.
"""
from __future__ import annotations

import datetime as dt
import io
import json
import re
import unicodedata
import urllib.request
from pathlib import Path

import openpyxl
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DIR_REF = RAIZ / "data" / "referencia"
F_ESCRITURAS = DIR_REF / "escrituras_distrito_actual.csv"
F_IPV = DIR_REF / "ipv_ine_madrid.csv"

URL_PRECIO_DECLARADO = (
    "https://www.madrid.es/UnidadesDescentralizadas/UDCEstadistica/Nuevaweb/"
    "Edificaci%C3%B3n%20y%20Vivienda/Mercado%20de%20la%20Vivienda/"
    "Compra-Venta%20de%20vivienda/registral/E3210626.xlsx")
URL_PAGINA_AYTO = (
    "https://www.madrid.es/portales/munimadrid/es/Inicio/El-Ayuntamiento/"
    "Estadistica/Areas-de-informacion-estadistica/Edificacion-y-vivienda/"
    "Mercado-de-la-vivienda/Compra-venta-de-viviendas/")
TABLA_IPV = 80270
URL_IPV = f"https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{TABLA_IPV}?nult=40"

# Codigos de periodo del INE para los trimestres
PERIODO_INE = {19: "T1", 20: "T2", 21: "T3", 22: "T4"}


def _sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def _bajar(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=90) as r:
        return r.read()


def leer_precio_declarado(contenido: bytes) -> tuple[int, pd.DataFrame]:
    """Filas de distrito (codigo de dos cifras) del xlsx del Ayuntamiento."""
    ws = openpyxl.load_workbook(io.BytesIO(contenido), data_only=True).active
    anio, filas = None, []
    for r in ws.iter_rows(values_only=True):
        etiqueta = r[1]
        if isinstance(etiqueta, int) and 2000 < etiqueta < 2100:
            anio = etiqueta
        if isinstance(etiqueta, str):
            m = re.match(r"^(\d\d)\. (.+)$", etiqueta.strip())
            if m:
                filas.append({
                    "distrito_id": int(m.group(1)),
                    "distrito": _sin_tildes(m.group(2)).replace(" - ", "-").strip(),
                    "eur_m2_total": r[2], "eur_m2_nueva": r[3], "eur_m2_usada": r[4],
                })
    if anio is None or len(filas) != 21:
        raise ValueError(f"El xlsx no tiene la forma esperada: ano={anio}, "
                         f"{len(filas)} distritos (se esperaban 21)")
    return anio, pd.DataFrame(filas)


def leer_ipv(series: list[dict]) -> pd.DataFrame:
    filas = []
    for s in series:
        nombre = s["Nombre"]
        if not nombre.startswith("Madrid, Comunidad de") or "Índice" not in nombre:
            continue
        tipo = ("general" if "General" in nombre else
                "segunda_mano" if "segunda mano" in nombre else "nueva")
        for x in s["Data"]:
            filas.append({"trimestre": f"{x['Anyo']}{PERIODO_INE[x['FK_Periodo']]}",
                          "tipo": tipo, "indice": x["Valor"]})
    d = (pd.DataFrame(filas)
         .pivot(index="trimestre", columns="tipo", values="indice")
         .reset_index().sort_values("trimestre"))
    d = d[d["trimestre"] >= "2018T1"]
    if d.empty or "segunda_mano" not in d:
        raise ValueError("La respuesta del INE no trae la serie de Madrid esperada")
    return d[["trimestre", "general", "nueva", "segunda_mano"]]


def _escribir(ruta: Path, cabecera: list[str], d: pd.DataFrame) -> None:
    texto = "".join(f"# {linea}\n" for linea in cabecera) + d.to_csv(index=False)
    ruta.write_text(texto, encoding="utf-8")


def ejecutar(hoy: dt.date | None = None) -> dict:
    hoy = hoy or dt.date.today()
    consultado = hoy.strftime("%d/%m/%Y")

    anio, esc = leer_precio_declarado(_bajar(URL_PRECIO_DECLARADO))
    _escribir(F_ESCRITURAS, [
        "FUENTE: Ayuntamiento de Madrid, Banco de Datos, Compra-venta de viviendas, Estadistica Registral",
        "        Inmobiliaria, tabla 6 'Precio medio declarado de la vivienda (euros/m2) por Distrito y Barrio",
        "        segun Tipo'. Elaborada por el Colegio de Registradores de Espana.",
        f"URL:    {URL_PRECIO_DECLARADO}",
        f"PAGINA: {URL_PAGINA_AYTO}",
        f"EJERCICIO DE LOS DATOS: {anio}",
        f"CONSULTADO: {consultado}. Generado por src/r05_referencia_precios.py; no editar a mano.",
        "UNIDADES: euros/m2 construido, precio medio DECLARADO en escritura (no precio de oferta).",
    ], esc.assign(anio=anio))

    ipv = leer_ipv(json.loads(_bajar(URL_IPV)))
    _escribir(F_IPV, [
        "FUENTE: INE, Indice de Precios de Vivienda (IPV), base 2025, tabla 80270",
        "        'Indices por CCAA: general, vivienda nueva y de segunda mano. Trimestrales'.",
        f"URL:    {URL_IPV}",
        "AMBITO: Comunidad de Madrid (el INE no publica el IPV por municipio ni por distrito).",
        f"ULTIMO TRIMESTRE: {ipv['trimestre'].iloc[-1]}",
        f"CONSULTADO: {consultado}. Generado por src/r05_referencia_precios.py; no editar a mano.",
        "UNIDADES: indice, media de 2025 = 100. Se basa en precios de compraventa escriturada.",
    ], ipv)
    return {"anio_escrituras": anio, "ultimo_trimestre_ipv": ipv["trimestre"].iloc[-1]}


if __name__ == "__main__":
    r = ejecutar()
    print(f"Escrituras por distrito: ejercicio {r['anio_escrituras']} -> {F_ESCRITURAS.name}")
    print(f"IPV INE Madrid hasta {r['ultimo_trimestre_ipv']} -> {F_IPV.name}")
