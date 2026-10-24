"""Los ejemplos propios de la demo vienen de un fichero local que git ignora.

Quien clone el repositorio no lo tiene, y la demo tiene que arrancar igual. Y si
el fichero existe pero esta roto, o tiene entradas a medias, tampoco puede
romper nada: se descarta lo que no vale y se carga el resto.
"""
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "demo"))
sys.path.insert(0, str(RAIZ / "src"))

from motor import cargar_ejemplos_locales  # noqa: E402

VALIDO = dict(barrio="Trafalgar", superficie_m2=95, habitaciones=3, banos=2, planta=4,
              ascensor=True, terraza=False, estado="Buen estado", nota="una nota")


def _fichero(tmp_path, contenido) -> Path:
    f = tmp_path / "ejemplos_locales.json"
    f.write_text(contenido if isinstance(contenido, str) else json.dumps(contenido),
                 encoding="utf-8")
    return f


def test_sin_fichero_no_hay_ejemplos_y_no_se_rompe(tmp_path):
    assert cargar_ejemplos_locales(tmp_path / "no_existe.json") == {}


def test_fichero_roto_no_se_rompe(tmp_path):
    assert cargar_ejemplos_locales(_fichero(tmp_path, "{ esto no es json")) == {}
    assert cargar_ejemplos_locales(_fichero(tmp_path, "[1, 2, 3]")) == {}


def test_entrada_valida_se_carga_con_su_nota(tmp_path):
    e = cargar_ejemplos_locales(_fichero(tmp_path, {"Piso A": VALIDO}))
    assert list(e) == ["Piso A"]
    assert e["Piso A"]["barrio"] == "Trafalgar" and e["Piso A"]["nota"] == "una nota"


def test_entradas_a_medias_se_descartan_y_las_demas_se_cargan(tmp_path):
    sin_campo = {k: v for k, v in VALIDO.items() if k != "planta"}
    tipo_mal = {**VALIDO, "superficie_m2": "95"}
    estado_mal = {**VALIDO, "estado": "Regular"}
    bool_como_int = {**VALIDO, "planta": True}
    sin_nota = {k: v for k, v in VALIDO.items() if k != "nota"}
    e = cargar_ejemplos_locales(_fichero(tmp_path, {
        "_formato": "documentacion, se ignora", "mal 1": sin_campo, "mal 2": tipo_mal,
        "mal 3": estado_mal, "mal 4": bool_como_int, "mal 5": "no es un dict",
        "bien": sin_nota}))
    assert list(e) == ["bien"] and e["bien"]["nota"] is None


def test_la_plantilla_del_repo_es_valida():
    e = cargar_ejemplos_locales(RAIZ / "demo" / "ejemplos_locales.ejemplo.json")
    assert len(e) == 1 and next(iter(e.values()))["barrio"] == "Trafalgar"


def test_el_fichero_local_esta_ignorado_por_git():
    r = subprocess.run(["git", "check-ignore", "-q", "demo/ejemplos_locales.json"],
                       cwd=RAIZ, capture_output=True)
    assert r.returncode == 0, "demo/ejemplos_locales.json tiene que estar en .gitignore"
    r = subprocess.run(["git", "check-ignore", "-q", "demo/ejemplos_locales.ejemplo.json"],
                       cwd=RAIZ, capture_output=True)
    assert r.returncode == 1, "la plantilla .ejemplo.json si va al repositorio"
