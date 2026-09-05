"""Paso 00 — Genera el corpus de entrada: anuncios en TEXTO LIBRE.

Por que sinteticos: los terminos de uso de los portales inmobiliarios prohiben
el scraping. No hay dataset publico de anuncios de Madrid con licencia de uso
libre, asi que se generan anuncios artificiales calibrados con estadistica
publica real (precio medio declarado y distribucion de superficies por distrito,
Colegio de Registradores via Ayuntamiento de Madrid).

El corpus imita como llega el dato en la realidad: notas de captacion, mensajes
de WhatsApp entre comerciales, fragmentos de email, fichas mal formateadas.
Cada anuncio se acompana de su verdad de terreno, que solo se usa para MEDIR la
calidad de la extraccion y del motor. Nunca entra en el pipeline de valoracion.
"""
from __future__ import annotations

import json
import random
import unicodedata
from datetime import date, timedelta

import numpy as np
import pandas as pd

import config as cfg

TRAMOS = [
    ("sup_menos40", 28, 40),
    ("sup_40_60", 40, 60),
    ("sup_60_80", 60, 80),
    ("sup_80_100", 80, 100),
    ("sup_mas100", 100, 190),
]

ESTADOS = list(cfg.COEF_ESTADO.keys())
PESOS_ESTADO = [0.08, 0.24, 0.46, 0.22]


def _eur(valor: float) -> str:
    """Formatea en convencion espanola: 227.000 (punto como separador de miles)."""
    return f"{valor:,.0f}".replace(",", ".")


def _sin_tildes(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


# --- Plantillas de redaccion --------------------------------------------------
# Cinco registros distintos a proposito: el objetivo es que la extraccion no
# pueda resolverse con un unico patron fijo.

def _texto_ficha(d: dict, rng: random.Random) -> str:
    lineas = [
        f"FICHA CAPTACION {d['ref']}",
        f"Zona: {d['distrito']} (Madrid)",
        f"Superficie construida: {d['superficie_m2']} m2",
        f"Distribucion: {d['habitaciones']} dormitorios / {d['banos']} banos",
        f"Planta {d['planta']}{'ª' if d['planta'] > 0 else ''}"
        f"{' con ascensor' if d['ascensor'] else ' SIN ASCENSOR'}",
        f"Estado: {d['estado']}",
        f"Ano construccion: {d['anio_construccion']}",
        f"Orientacion: {'exterior' if d['exterior'] else 'interior a patio'}",
        f"Precio de salida: {_eur(d['precio_eur'])} EUR",
        f"Fecha alta: {d['fecha']}",
    ]
    if rng.random() < 0.3:
        lineas.insert(4, "Comunidad: pendiente de confirmar")
    return "\n".join(lineas)


def _texto_whatsapp(d: dict, rng: random.Random) -> str:
    asc = "con ascensor" if d["ascensor"] else "sin ascensor ojo"
    ext = "exterior" if d["exterior"] else "interior"
    apertura = rng.choice(
        ["Oye te paso una que ha entrado hoy",
         "Mira esto que acaba de firmar la captadora",
         "Tengo esta en cartera desde esta manana",
         "Te reenvio lo que me pasa el companero"]
    )
    return (
        f"{apertura} ({d['ref']}, {d['fecha']}). Piso en {d['distrito']}, "
        f"{d['superficie_m2']}m2 construidos, {d['habitaciones']} habitaciones y "
        f"{d['banos']} bano{'s' if d['banos'] > 1 else ''}. "
        f"Planta {d['planta']}, {asc}. Es {ext}. "
        f"Esta {d['estado']}, edificio del {d['anio_construccion']}. "
        f"Piden {_eur(d['precio_eur'])}. Que te parece?"
    )


def _texto_portal(d: dict, rng: random.Random) -> str:
    adjetivos = rng.choice(
        ["Magnifica oportunidad", "Estupenda vivienda", "Excelente inmueble",
         "Luminosa vivienda", "Encantador piso"]
    )
    extra = rng.choice(
        ["Zona muy bien comunicada, con todos los servicios a pie de calle.",
         "A pocos minutos de metro y numerosas lineas de autobus.",
         "Entorno consolidado, con colegios y zonas verdes en el entorno.",
         "Barrio tranquilo y residencial, ideal para primera vivienda."]
    )
    asc = "El edificio dispone de ascensor." if d["ascensor"] else (
        "El inmueble se encuentra en un edificio sin ascensor."
    )
    ext = ("La vivienda es exterior y recibe muy buena luz natural."
           if d["exterior"] else "Se trata de una vivienda interior.")
    return (
        f"{adjetivos} en el distrito de {d['distrito']}. "
        f"Se distribuye en {d['habitaciones']} dormitorios y {d['banos']} banos "
        f"sobre una superficie construida de {d['superficie_m2']} metros cuadrados. "
        f"Situada en una {d['planta']}a planta. {asc} {ext} "
        f"El inmueble esta {d['estado']} y la finca es del ano {d['anio_construccion']}. "
        f"{extra} "
        f"Precio: {_eur(d['precio_eur'])} euros. "
        f"Referencia {d['ref']}, publicado el {d['fecha']}."
    )


def _texto_email(d: dict, rng: random.Random) -> str:
    return (
        f"Asunto: RV: nueva referencia {d['ref']}\n"
        f"Fecha: {d['fecha']}\n\n"
        f"Buenos dias,\n\n"
        f"Adjunto los datos de la vivienda de {d['distrito']} que comentamos ayer. "
        f"Son {d['superficie_m2']} m2 construidos, {d['habitaciones']} dormitorios, "
        f"{d['banos']} banos, planta {d['planta']}"
        f"{', edificio con ascensor' if d['ascensor'] else ', sin ascensor'}. "
        f"{'Exterior.' if d['exterior'] else 'Da a patio interior.'} "
        f"La propiedad esta {d['estado']}. Construccion de {d['anio_construccion']}. "
        f"La propiedad pide {_eur(d['precio_eur'])} euros.\n\n"
        f"Quedo atento a tus comentarios.\n"
    )


def _texto_telegrama(d: dict, rng: random.Random) -> str:
    """Formato taquigrafico, el mas dificil de parsear."""
    asc = "c/asc" if d["ascensor"] else "s/asc"
    ext = "ext" if d["exterior"] else "int"
    abrev = {"obra nueva": "ON", "reformado": "reform.",
             "buen estado": "buen edo", "a reformar": "a reformar"}[d["estado"]]
    return (
        f"{d['ref']} | {d['fecha']} | {d['distrito']} | {d['superficie_m2']}m2 | "
        f"{d['habitaciones']}d/{d['banos']}b | pl.{d['planta']} {asc} | {ext} | "
        f"{abrev} | ano {d['anio_construccion']} | "
        f"{_eur(d['precio_eur'] / 1000)}k EUR"
    )


PLANTILLAS = [_texto_ficha, _texto_whatsapp, _texto_portal, _texto_email, _texto_telegrama]


def generar(n: int = cfg.N_ANUNCIOS, semilla: int = cfg.SEMILLA) -> pd.DataFrame:
    rng = random.Random(semilla)
    np_rng = np.random.default_rng(semilla)

    distritos = pd.read_csv(cfg.F_DISTRITOS, comment="#")
    pesos_distrito = (distritos["transacciones_2022"] /
                      distritos["transacciones_2022"].sum()).to_numpy()

    d0 = date.fromisoformat(cfg.FECHA_INICIO)
    dias_rango = (date.fromisoformat(cfg.FECHA_FIN) - d0).days

    registros, textos = [], []
    for i in range(n):
        fila = distritos.iloc[np_rng.choice(len(distritos), p=pesos_distrito)]

        # Superficie: se muestrea el tramo con la distribucion real de
        # transacciones de ese distrito, y luego uniforme dentro del tramo.
        conteos = np.array([fila[c] for c, _, _ in TRAMOS], dtype=float)
        pesos_tramo = conteos / conteos.sum() if conteos.sum() > 0 else None
        idx = np_rng.choice(len(TRAMOS), p=pesos_tramo)
        _, lo, hi = TRAMOS[idx]
        superficie = int(np_rng.integers(lo, hi + 1))

        habitaciones = int(np.clip(round(superficie / 28 + np_rng.normal(0, 0.5)), 1, 6))
        banos = 1 if superficie < 75 else (2 if superficie < 130 else 3)
        if np_rng.random() < 0.12:
            banos = max(1, banos - 1)

        anio = int(np.clip(np_rng.normal(1972, 22), 1900, 2025))
        estado = rng.choices(ESTADOS, weights=PESOS_ESTADO, k=1)[0]
        if estado == "obra nueva":
            anio = int(np_rng.integers(2022, 2027))
        planta = int(np_rng.integers(0, 9))
        ascensor = bool(np_rng.random() < (0.55 if anio < 1970 else 0.94))
        exterior = bool(np_rng.random() < 0.72)

        # Precio de mercado "justo" de este inmueble
        base = fila["precio_m2_2022"] * cfg.FACTOR_ACTUALIZACION
        eur_m2 = base * cfg.COEF_ESTADO[estado] * cfg.COEF_EXTERIOR[exterior]
        if planta >= 3 and not ascensor:
            eur_m2 *= cfg.COEF_SIN_ASCENSOR_ALTA
        eur_m2 *= float(np_rng.lognormal(0, cfg.RUIDO_LOG_SIGMA))

        # Desviacion inyectada a proposito en una minoria de anuncios
        u = np_rng.random()
        desviacion_real, etiqueta = 0.0, "mercado"
        if u < cfg.PROP_INFRAPRECIO:
            desviacion_real = -float(np_rng.uniform(*cfg.MAGNITUD_DESVIACION))
            etiqueta = "infraprecio_inyectado"
        elif u < cfg.PROP_INFRAPRECIO + cfg.PROP_SOBREPRECIO:
            desviacion_real = float(np_rng.uniform(*cfg.MAGNITUD_DESVIACION))
            etiqueta = "sobreprecio_inyectado"
        eur_m2 *= (1 + desviacion_real)

        precio = int(round(eur_m2 * superficie / 1000.0) * 1000)
        fecha = (d0 + timedelta(days=int(np_rng.integers(0, dias_rango)))).isoformat()

        d = {
            "ref": f"MD-{i + 1:04d}",
            "fecha": fecha,
            "distrito": fila["distrito"],
            "superficie_m2": superficie,
            "habitaciones": habitaciones,
            "banos": banos,
            "planta": planta,
            "ascensor": ascensor,
            "estado": estado,
            "anio_construccion": anio,
            "exterior": exterior,
            "precio_eur": precio,
            "desviacion_inyectada": round(desviacion_real, 4),
            "etiqueta_verdad": etiqueta,
        }
        registros.append(d)

        plantilla = rng.choice(PLANTILLAS)
        texto = plantilla(d, rng)
        if rng.random() < 0.35:
            texto = _sin_tildes(texto)
        textos.append({"ref": d["ref"], "formato": plantilla.__name__[7:], "texto": texto})

    cfg.DIR_RAW.mkdir(parents=True, exist_ok=True)
    with open(cfg.F_CORPUS, "w", encoding="utf-8") as f:
        for t in textos:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    verdad = pd.DataFrame(registros)
    verdad.to_csv(cfg.F_VERDAD, index=False)
    return verdad


if __name__ == "__main__":
    v = generar()
    print(f"Corpus generado: {len(v)} anuncios en texto libre -> {cfg.F_CORPUS}")
    print(f"Verdad de terreno (solo para medir) -> {cfg.F_VERDAD}")
    print(v["etiqueta_verdad"].value_counts().to_string())
