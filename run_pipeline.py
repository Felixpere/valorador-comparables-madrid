"""Ejecuta el proceso completo, de texto libre a Excel y dashboard.

    python run_pipeline.py                 # extraccion por reglas, sin red
    python run_pipeline.py --motor llm     # extraccion con la API de Anthropic
    python run_pipeline.py --sin-corpus    # reutiliza el corpus ya generado

Cada paso escribe su salida en disco antes de pasar al siguiente, asi que se
puede parar, inspeccionar cualquier fichero intermedio y retomar.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import config as cfg          # noqa: E402
import p00_generar_corpus     # noqa: E402
import p01_extraer            # noqa: E402
import p02_normalizar         # noqa: E402
import p03_valorar            # noqa: E402
import p04_evaluar            # noqa: E402
import p05_exportar_excel     # noqa: E402
import p06_dashboard          # noqa: E402


def paso(n, titulo):
    print(f"\n[{n}/6] {titulo}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--motor", choices=["auto", "llm", "reglas"], default="auto")
    ap.add_argument("--sin-corpus", action="store_true",
                    help="no regenera el corpus, usa el que ya hay en data/raw")
    ap.add_argument("--limite", type=int, default=None)
    args = ap.parse_args()

    t0 = time.time()

    paso(1, "Corpus de anuncios en texto libre")
    if args.sin_corpus and cfg.F_CORPUS.exists():
        print("    reutilizando corpus existente")
    else:
        v = p00_generar_corpus.generar()
        print(f"    {len(v)} anuncios generados")

    paso(2, "Extraccion de campos")
    ext = p01_extraer.ejecutar(args.motor, args.limite)
    print(f"    {len(ext)} registros extraidos")

    paso(3, "Limpieza y validacion")
    norm, inc = p02_normalizar.ejecutar()
    print(f"    {int(norm['apta_valoracion'].sum())}/{len(norm)} aptos para valorar, "
          f"{len(inc)} incidencias")

    paso(4, "Valoracion por comparables")
    val = p03_valorar.ejecutar()
    print(f"    {int(val['desviacion'].notna().sum())} valoraciones emitidas")

    paso(5, "Medicion")
    m = p04_evaluar.ejecutar()
    fugas = m["control_de_fugas"]
    print(f"    campos correctos: {m['extraccion']['exactitud_global_por_campo']:.1%}")
    print(f"    error mediano de valoracion: "
          f"{m['motor_valoracion']['error_mediano_valoracion']:.1%}")
    if not fugas["limpio"]:
        print(f"    ERROR: fuga de informacion detectada -> {fugas}", file=sys.stderr)
        return 1
    print("    control de fugas: limpio")

    paso(6, "Excel y dashboard")
    p05_exportar_excel.construir()
    p06_dashboard.construir()
    print(f"    {cfg.F_EXCEL}")
    print(f"    {cfg.F_DASHBOARD}")

    print(f"\nCompletado en {time.time() - t0:.1f} s.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
