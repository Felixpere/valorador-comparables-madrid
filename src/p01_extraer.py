"""Paso 01 — De texto libre a campos estructurados.

Dos motores intercambiables que devuelven EXACTAMENTE el mismo esquema:

  * "llm"    : llama a la API de Anthropic y pide JSON estricto. Es el motor que
               aguanta formatos nuevos sin tocar codigo.
  * "reglas" : expresiones regulares. Determinista, gratis, sin red. Se usa como
               respaldo y como linea base contra la que comparar al LLM.

El motor se elige con --motor. Por defecto "auto": usa LLM si hay
ANTHROPIC_API_KEY en el entorno, y reglas si no la hay. Asi la demo se ejecuta
siempre, con o sin conexion.

La columna motor_extraccion viaja con el dato hasta el Excel: en cualquier fila
se puede saber quien la extrajo.
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
import os
import re
import sys
import unicodedata

import pandas as pd

import config as cfg

DISTRITOS_CANON = [
    "Centro", "Arganzuela", "Retiro", "Salamanca", "Chamartin", "Tetuan",
    "Chamberi", "Fuencarral-El Pardo", "Moncloa-Aravaca", "Latina",
    "Carabanchel", "Usera", "Puente de Vallecas", "Moratalaz", "Ciudad Lineal",
    "Hortaleza", "Villaverde", "Villa de Vallecas", "Vicalvaro",
    "San Blas-Canillejas", "Barajas",
]

ESQUEMA = """{
  "distrito": string | null,            // uno de los 21 distritos de Madrid
  "superficie_m2": number | null,       // superficie construida
  "habitaciones": number | null,
  "banos": number | null,
  "planta": number | null,              // 0 = bajo
  "ascensor": boolean | null,
  "estado": "obra nueva" | "reformado" | "buen estado" | "a reformar" | null,
  "anio_construccion": number | null,
  "exterior": boolean | null,           // true exterior, false interior
  "precio_eur": number | null,          // precio pedido en euros, entero
  "fecha": string | null                // ISO YYYY-MM-DD
}"""

PROMPT_SISTEMA = (
    "Eres un extractor de datos inmobiliarios. Recibes el texto libre de una nota "
    "de captacion, un mensaje interno o un anuncio, y devuelves sus campos "
    "estructurados.\n\n"
    "Reglas:\n"
    "1. Devuelve UNICAMENTE un objeto JSON valido. Sin texto antes ni despues, "
    "sin bloques de codigo.\n"
    "2. Si un campo no aparece en el texto, ponlo a null. No lo estimes, no lo "
    "deduzcas y no lo inventes.\n"
    "3. 'k' o 'K' tras una cifra significa miles. El punto es separador de miles "
    "en espanol: 227.000 son doscientos veintisiete mil.\n"
    "4. El texto puede venir sin tildes.\n\n"
    f"Esquema de salida:\n{ESQUEMA}"
)


def _norm(t: str) -> str:
    t = "".join(c for c in unicodedata.normalize("NFD", t)
                if unicodedata.category(c) != "Mn")
    return t.lower()


# ---------------------------------------------------------------- motor reglas
def extraer_reglas(texto: str) -> dict:
    t = _norm(texto)
    out = {c: None for c in cfg.CAMPOS}
    out["fecha"] = None

    for d in DISTRITOS_CANON:
        if _norm(d) in t:
            out["distrito"] = d
            break

    m = re.search(r"(\d{2,3})\s*(?:m2|metros cuadrados|metros)", t)
    if m:
        out["superficie_m2"] = float(m.group(1))

    m = re.search(r"(\d)\s*(?:dormitorios?|habitaciones?)|(\d)\s*d\s*/", t)
    if m:
        out["habitaciones"] = float(m.group(1) or m.group(2))

    m = re.search(r"(\d)\s*banos?|/\s*(\d)\s*b\b", t)
    if m:
        out["banos"] = float(m.group(1) or m.group(2))

    m = re.search(r"(?:planta\s*(\d)|pl\.\s*(\d)|(\d)\s*a?\s*planta)", t)
    if m:
        out["planta"] = float(next(g for g in m.groups() if g))

    if re.search(r"sin ascensor|s/asc", t):
        out["ascensor"] = False
    elif re.search(r"con ascensor|dispone de ascensor|c/asc", t):
        out["ascensor"] = True

    if re.search(r"obra nueva|\bon\b", t):
        out["estado"] = "obra nueva"
    elif "a reformar" in t:
        out["estado"] = "a reformar"
    elif re.search(r"reformad|reform\.", t):
        out["estado"] = "reformado"
    elif re.search(r"buen estado|buen edo", t):
        out["estado"] = "buen estado"

    m = re.search(r"(?:ano|construccion de|del)\s*(19\d{2}|20[0-2]\d)", t)
    if m:
        out["anio_construccion"] = float(m.group(1))

    if re.search(r"\binterior\b|patio interior|\bint\b", t):
        out["exterior"] = False
    elif re.search(r"\bexterior\b|\bext\b", t):
        out["exterior"] = True

    m = re.search(r"(\d{2,3})\s*k\s*eur", t)
    if m:
        out["precio_eur"] = float(m.group(1)) * 1000
    else:
        m = re.search(r"(\d{1,3}(?:\.\d{3})+)", t)
        if m:
            out["precio_eur"] = float(m.group(1).replace(".", ""))

    m = re.search(r"(20\d{2}-\d{2}-\d{2})", t)
    if m:
        out["fecha"] = m.group(1)

    return out


# ------------------------------------------------------------------- motor LLM
def extraer_llm(texto: str, cliente) -> dict:
    r = cliente.messages.create(
        model=cfg.MODELO_LLM,
        max_tokens=600,
        system=PROMPT_SISTEMA,
        messages=[{"role": "user", "content": texto}],
    )
    bruto = "".join(b.text for b in r.content if b.type == "text").strip()
    bruto = re.sub(r"^```(?:json)?|```$", "", bruto, flags=re.MULTILINE).strip()
    datos = json.loads(bruto)
    return {c: datos.get(c) for c in cfg.CAMPOS + ["fecha"]}


def _cliente_anthropic():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        print("[aviso] falta el paquete 'anthropic' (pip install anthropic)",
              file=sys.stderr)
        return None
    return anthropic.Anthropic()


def ejecutar(motor: str = "auto", limite: int | None = None,
             hilos: int = 8, muestra_llm: int | None = None) -> pd.DataFrame:
    cliente = _cliente_anthropic() if motor in ("auto", "llm") else None
    if motor == "llm" and cliente is None:
        raise SystemExit("Motor 'llm' pedido pero no hay ANTHROPIC_API_KEY o falta el SDK.")
    usar_llm = cliente is not None and motor in ("auto", "llm")
    etiqueta = "llm:" + cfg.MODELO_LLM if usar_llm else "reglas"
    # Modo hibrido: solo los N primeros anuncios pasan por el modelo, el resto
    # por reglas. Abarata la demo sin ocultar nada: cada fila lleva escrito
    # quien la extrajo, y las metricas se reportan por separado.
    n_llm = (cfg.MUESTRA_LLM if muestra_llm is None else muestra_llm) if usar_llm else 0
    if usar_llm:
        print(f"[extraccion] {n_llm} anuncios por {etiqueta}, el resto por reglas")
    else:
        print("[extraccion] motor = reglas (sin ANTHROPIC_API_KEY o motor forzado)")

    with open(cfg.F_CORPUS, encoding="utf-8") as f:
        anuncios = [json.loads(l) for l in f]
    if limite:
        anuncios = anuncios[:limite]

    llm_refs = {a["ref"] for a in anuncios[:n_llm]} if usar_llm else set()

    def procesar(a: dict) -> dict:
        if a["ref"] in llm_refs:
            try:
                campos, motor_fila = extraer_llm(a["texto"], cliente), etiqueta
            except Exception as e:                     # red caida, JSON roto, cuota
                print(f"  [{a['ref']}] fallo LLM ({type(e).__name__}), uso reglas",
                      file=sys.stderr)
                campos, motor_fila = extraer_reglas(a["texto"]), "reglas (respaldo)"
        else:
            campos, motor_fila = extraer_reglas(a["texto"]), "reglas"
        campos["ref"] = a["ref"]
        campos["formato_origen"] = a["formato"]
        campos["motor_extraccion"] = motor_fila
        return campos

    if llm_refs:
        # Un anuncio por llamada, en paralelo.
        with ThreadPoolExecutor(max_workers=hilos) as pool:
            filas = list(pool.map(procesar, anuncios))
    else:
        filas = [procesar(a) for a in anuncios]

    df = pd.DataFrame(filas)
    cfg.DIR_INTERIM.mkdir(parents=True, exist_ok=True)
    df.to_csv(cfg.F_EXTRAIDO, index=False)
    return df


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--motor", choices=["auto", "llm", "reglas"], default="auto")
    p.add_argument("--limite", type=int, default=None)
    p.add_argument("--hilos", type=int, default=8)
    p.add_argument("--muestra-llm", type=int, default=None,
                   dest="muestra_llm",
                   help="cuantos anuncios pasan por el LLM (resto: reglas)")
    args = p.parse_args()
    df = ejecutar(args.motor, args.limite, args.hilos, args.muestra_llm)
    print(f"Extraidos {len(df)} anuncios -> {cfg.F_EXTRAIDO}")
    print("Reparto por motor:")
    print(df["motor_extraccion"].value_counts().to_string())
    print("Campos vacios por columna:")
    print(df[cfg.CAMPOS].isna().sum().to_string())
