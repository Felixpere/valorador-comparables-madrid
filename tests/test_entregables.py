"""Las copias de entregables/ tienen que coincidir con lo que genera el codigo.

entregables/ es una foto fija de outputs/ y no se actualiza sola. Si alguien
regenera y no copia, o edita a mano una copia, este test falla y dice que
fichero difiere y que hay que copiar.

- dashboard_real.html es determinista: comparacion directa.
- dashboard.html lleva impresa la fecha y hora de ejecucion ("Ejecutado el
  dd/mm/aaaa hh:mm"). Se ignora esa marca y nada mas: el resto de la linea
  (cuantos anuncios) si se compara.
- Los finales de linea se normalizan: git los convierte al hacer checkout en
  Windows, y eso no es una diferencia de contenido.

Sin outputs/ (por ejemplo en la integracion continua, que pasa los tests antes
de ejecutar el pipeline) no hay con que comparar y el test se salta.
"""
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
OUTPUTS = RAIZ / "outputs"
ENTREGABLES = RAIZ / "entregables"

MARCA_EJECUCION = re.compile(r"Ejecutado el \d{2}/\d{2}/\d{4} \d{2}:\d{2}")


def _normalizar(texto: str, ignorar_marca: bool) -> list[str]:
    texto = texto.replace("\r\n", "\n")
    if ignorar_marca:
        texto = MARCA_EJECUCION.sub("Ejecutado el <fecha>", texto)
    return texto.split("\n")


def comparar(nombre: str, ignorar_marca: bool = False,
             dir_outputs: Path = OUTPUTS, dir_entregables: Path = ENTREGABLES) -> str | None:
    """None si coinciden; si no, el mensaje que explica que hacer."""
    generado = _normalizar((dir_outputs / nombre).read_text(encoding="utf-8"), ignorar_marca)
    copia = _normalizar((dir_entregables / nombre).read_text(encoding="utf-8"), ignorar_marca)
    if generado == copia:
        return None
    linea = next((i for i, (a, b) in enumerate(zip(generado, copia), start=1) if a != b),
                 min(len(generado), len(copia)) + 1)
    return (f"entregables/{nombre} no coincide con outputs/{nombre} "
            f"(primera diferencia en la línea {linea}). "
            f"Si outputs/ está al día, copia el regenerado: "
            f"cp outputs/{nombre} entregables/{nombre}")


@pytest.mark.parametrize("nombre, ignorar_marca", [
    ("dashboard_real.html", False),
    ("dashboard.html", True),
])
def test_entregables_coinciden_con_outputs(nombre, ignorar_marca):
    if not (OUTPUTS / nombre).exists():
        pytest.skip(f"falta outputs/{nombre}: hay que generarlo antes")
    diferencia = comparar(nombre, ignorar_marca)
    assert diferencia is None, diferencia


# ------------------------------------------------ el propio test, comprobado
def _pareja(tmp_path, generado: str, copia: str, nombre="dashboard.html"):
    (tmp_path / "outputs").mkdir()
    (tmp_path / "entregables").mkdir()
    (tmp_path / "outputs" / nombre).write_text(generado, encoding="utf-8", newline="")
    (tmp_path / "entregables" / nombre).write_text(copia, encoding="utf-8", newline="")
    return tmp_path / "outputs", tmp_path / "entregables"


def test_la_marca_de_ejecucion_no_cuenta(tmp_path):
    o, e = _pareja(tmp_path, "<p>Ejecutado el 19/09/2026 10:05 sobre 2000 anuncios.</p>\n",
                   "<p>Ejecutado el 07/09/2026 22:41 sobre 2000 anuncios.</p>\n")
    assert comparar("dashboard.html", True, o, e) is None


def test_el_resto_de_la_linea_de_la_marca_si_cuenta(tmp_path):
    o, e = _pareja(tmp_path, "<p>Ejecutado el 19/09/2026 10:05 sobre 2000 anuncios.</p>\n",
                   "<p>Ejecutado el 07/09/2026 22:41 sobre 1999 anuncios.</p>\n")
    assert comparar("dashboard.html", True, o, e) is not None


def test_los_finales_de_linea_no_cuentan(tmp_path):
    o, e = _pareja(tmp_path, "a\nb\n", "a\r\nb\r\n", "dashboard_real.html")
    assert comparar("dashboard_real.html", False, o, e) is None


def test_el_fallo_dice_que_fichero_y_que_hay_que_copiar(tmp_path):
    o, e = _pareja(tmp_path, "igual\n12,0 %\n", "igual\n11,9 %\n", "dashboard_real.html")
    mensaje = comparar("dashboard_real.html", False, o, e)
    assert "entregables/dashboard_real.html no coincide con outputs/dashboard_real.html" in mensaje
    assert "línea 2" in mensaje
    assert "cp outputs/dashboard_real.html entregables/dashboard_real.html" in mensaje


def test_en_dashboard_real_la_fecha_si_cuenta(tmp_path):
    # Es determinista: si cambiara algo con aspecto de marca, seria un cambio real.
    o, e = _pareja(tmp_path, "Ejecutado el 19/09/2026 10:05\n", "Ejecutado el 07/09/2026 22:41\n",
                   "dashboard_real.html")
    assert comparar("dashboard_real.html", False, o, e) is not None
