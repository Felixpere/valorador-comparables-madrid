"""Motor de la demo: valora un piso descrito a mano con el metodo validado.

No reimplementa nada. La valoracion la hace `r01.valorar`, la misma funcion que
se midio fuera de muestra (error mediano del 12 %), con el mismo pool, la misma
semilla y los mismos coeficientes. Encima se aplican dos pasos con fuente
publica, calculados en r06:

  valor 2018 (comparables 2018T4)  x factor de actualizacion  = anuncio estimado hoy
  anuncio estimado hoy x (1 - brecha anuncio-escritura)     = firma estimada (rango)

Lo que el formulario pide y el modelo validado no usa (habitaciones y banos) solo
sirve para elegir que comparables se ensenan primero. Los atributos que el
formulario no pide toman el valor tipico del barrio.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

import r01_valorar_real as r01  # noqa: E402
from r06_actualizacion_cierre import (F_FACTORES, F_RESUMEN,  # noqa: E402
                                      TRIMESTRE_COMPARABLES, distrito_de)
from r07_cierres_agencia import F_DESCUENTO, MIN_CIERRES, _canon  # noqa: E402

ESTADOS = ["Buen estado", "A reformar", "Obra nueva"]
COMPARABLES_A_MOSTRAR = 8

# Tres pisos inventados, en zonas de precio muy distinto, para no improvisar
# en directo. No copian ningun anuncio real.
EJEMPLOS = {
    "Chamberí · Trafalgar": dict(
        barrio="Trafalgar", superficie_m2=90, habitaciones=3, banos=2,
        planta=3, ascensor=True, terraza=False, estado="Buen estado"),
    "Carabanchel · Vista Alegre": dict(
        barrio="Vista Alegre", superficie_m2=70, habitaciones=3, banos=1,
        planta=2, ascensor=False, terraza=False, estado="A reformar"),
    "Tetuán · Bellas Vistas": dict(
        barrio="Bellas Vistas", superficie_m2=75, habitaciones=2, banos=1,
        planta=4, ascensor=True, terraza=True, estado="Buen estado"),
}


@dataclass
class Resultado:
    valorable: bool
    motivo: str = ""
    barrio: str = ""
    distrito: str = ""
    n_comparables: int = 0
    fiabilidad: str = ""
    eur_m2_2018: float = float("nan")
    valor_2018: float = float("nan")
    factor_actualizacion: float = float("nan")
    factor_solo_ine: float = float("nan")
    oferta_hoy: float = float("nan")
    descuento_min: float = float("nan")
    descuento_max: float = float("nan")
    origen_descuento: str = ""
    cierre_min: float = float("nan")
    cierre_max: float = float("nan")
    error_mediano: float = float("nan")
    error_fiabilidad: float = float("nan")
    comparables: pd.DataFrame = field(default_factory=pd.DataFrame)
    mapa: pd.DataFrame = field(default_factory=pd.DataFrame)


def _redondear(x: float, a: int = 1000) -> float:
    return float(np.round(x / a) * a)


class Motor:
    def __init__(self, ruta_anuncios: Path = r01.F_ENTRADA):
        d, _ = r01.preparar(pd.read_csv(ruta_anuncios))
        # La misma particion que r01: el pool del que salen comparables y
        # coeficientes es exactamente el que se valido.
        rng = np.random.default_rng(r01.SEMILLA)
        ids = d["ASSETID"].unique()
        en_pool = set(rng.choice(ids, size=int(len(ids) * r01.PROP_POOL), replace=False))
        self.pool = d[d["ASSETID"].isin(en_pool)].copy()
        self.pool["distrito_id"] = distrito_de(self.pool["barrio_id"])
        self.beta = r01.estimar_coeficientes(self.pool)
        self.pool["factor"] = r01.factor(self.pool, self.beta)
        self.pool["m2_neutro"] = self.pool["eur_m2"] / self.pool["factor"]
        self.tipico = self.pool.groupby("barrio")[r01.VARIABLES].mean()

        self.factores = pd.read_csv(F_FACTORES).set_index("distrito_id")
        self.resumen = json.loads(F_RESUMEN.read_text(encoding="utf-8"))
        self.metricas = json.loads(r01.F_METRICAS.read_text(encoding="utf-8"))
        self.agencia = (pd.read_csv(F_DESCUENTO).set_index("distrito_canon")
                        if F_DESCUENTO.exists() else None)

        t4 = self.pool[self.pool["trimestre"] == TRIMESTRE_COMPARABLES]
        por_barrio = t4.groupby("barrio").agg(distrito_id=("distrito_id", "first"),
                                              n=("ASSETID", "size"))
        self.barrios = por_barrio.join(
            self.factores["distrito"], on="distrito_id").reset_index()

    # ------------------------------------------------------------------
    def fila(self, ficha: dict) -> pd.DataFrame:
        """El piso del formulario con las columnas que espera r01.valorar."""
        v = self.tipico.loc[ficha["barrio"]].to_dict()
        v.update({
            "obra_nueva": float(ficha["estado"] == "Obra nueva"),
            "a_reformar": float(ficha["estado"] == "A reformar"),
            "ascensor": float(ficha["ascensor"]),
            "terraza": float(ficha["terraza"]),
            "planta": float(np.clip(ficha["planta"], 0, 15)),
            "log_superficie": float(np.log(ficha["superficie_m2"])),
        })
        if ficha["estado"] == "Obra nueva":
            v["antiguedad"] = 0.0
        return pd.DataFrame([{
            **v, "ASSETID": "piso-del-formulario", "barrio": ficha["barrio"],
            "trimestre": TRIMESTRE_COMPARABLES,
            "CONSTRUCTEDAREA": float(ficha["superficie_m2"]),
            "PRICE": np.nan, "eur_m2": np.nan,
        }])

    def _descuento(self, distrito_id: int) -> tuple[float, float, str]:
        f = self.factores.loc[distrito_id]
        if self.agencia is not None:
            clave = _canon(f["distrito"])
            if clave in self.agencia.index and self.agencia.loc[clave, "suficiente"]:
                a = self.agencia.loc[clave]
                return (float(a["descuento_final_p25"]), float(a["descuento_final_p75"]),
                        f"cierres de la agencia ({int(a['n_cierres'])} operaciones; "
                        "el rango es la mitad central de ellas)")
        return (float(f["brecha_min"]), float(f["brecha_max"]),
                "datos públicos de 2018 (Registradores frente a anuncios; el rango "
                "va de la menor a la mayor de cuatro formas de medirlo)")

    def _banda(self, ficha: dict) -> pd.DataFrame:
        """Los anuncios del barrio y el trimestre con superficie parecida (±20 %),
        ordenados de mas a menos parecido en superficie, habitaciones y banos."""
        m2 = ficha["superficie_m2"]
        g = self.pool[(self.pool["barrio"] == ficha["barrio"])
                      & (self.pool["trimestre"] == TRIMESTRE_COMPARABLES)
                      & self.pool["CONSTRUCTEDAREA"].between(
                          m2 * (1 - r01.BANDA_SUPERFICIE), m2 * (1 + r01.BANDA_SUPERFICIE))]
        parecido = (np.abs(np.log(g["CONSTRUCTEDAREA"] / m2)) / r01.BANDA_SUPERFICIE
                    + 0.5 * (g["ROOMNUMBER"] - ficha["habitaciones"]).abs()
                    + 0.5 * (g["BATHNUMBER"] - ficha["banos"]).abs())
        return g.assign(parecido=parecido).sort_values(["parecido", "ASSETID"])

    def _mapa(self, ficha: dict, factor_piso: float, factor_hoy: float) -> pd.DataFrame:
        """Todos los comparables de la banda con su posicion, para el mapa.

        `destacado` marca los que salen en la tabla (los mas parecidos). El
        €/m² equivalente es el mismo calculo que la ultima columna de la tabla.
        """
        g = self._banda(ficha)
        return pd.DataFrame({
            "lat": g["LATITUDE"].astype(float),
            "lon": g["LONGITUDE"].astype(float),
            "m2": g["CONSTRUCTEDAREA"].astype(int),
            "eur_m2_2018": g["eur_m2"].round(0).astype(int),
            "eur_m2_hoy": (g["m2_neutro"] * factor_piso * factor_hoy).round(0).astype(int),
            "destacado": np.arange(len(g)) < COMPARABLES_A_MOSTRAR,
        }).reset_index(drop=True)

    def _comparables(self, ficha: dict, factor_piso: float, factor_hoy: float) -> pd.DataFrame:
        g = self._banda(ficha).head(COMPARABLES_A_MOSTRAR)
        return pd.DataFrame({
            "m²": g["CONSTRUCTEDAREA"].astype(int),
            "Habitaciones": g["ROOMNUMBER"].astype(int),
            "Baños": g["BATHNUMBER"].astype(int),
            "Planta": g["planta"].astype(int),
            "Ascensor": np.where(g["ascensor"] == 1, "Sí", "No"),
            "Estado": np.select([g["obra_nueva"] == 1, g["a_reformar"] == 1],
                                ["Obra nueva", "A reformar"], "Buen estado"),
            "€/m² pedido (2018)": g["eur_m2"].round(0).astype(int),
            "€/m² equivalente a su piso, hoy": (g["m2_neutro"] * factor_piso
                                                 * factor_hoy).round(0).astype(int),
        }).reset_index(drop=True)

    def valorar(self, ficha: dict) -> Resultado:
        fila = self.fila(ficha)
        r = r01.valorar(self.pool, fila, self.beta).iloc[0]
        b = self.barrios.set_index("barrio").loc[ficha["barrio"]]
        distrito_id = int(b["distrito_id"])
        f = self.factores.loc[distrito_id]
        base = dict(barrio=ficha["barrio"], distrito=str(f["distrito"]),
                    n_comparables=int(r["n_comparables"]))
        if pd.isna(r["valor_estimado"]):
            return Resultado(valorable=False, motivo=r["motivo_no_valorable"], **base)

        factor_piso = float(r01.factor(fila, self.beta)[0])
        oferta = float(r["valor_estimado"]) * float(f["factor_actualizacion"])
        d_min, d_max, origen = self._descuento(distrito_id)
        m = self.metricas
        return Resultado(
            valorable=True, **base,
            fiabilidad=r["fiabilidad"],
            eur_m2_2018=float(r["eur_m2_comparables"]),
            valor_2018=float(r["valor_estimado"]),
            factor_actualizacion=float(f["factor_actualizacion"]),
            factor_solo_ine=float(f["factor_solo_ine"]),
            oferta_hoy=_redondear(oferta),
            descuento_min=d_min, descuento_max=d_max, origen_descuento=origen,
            # Descuento mayor -> firma menor
            cierre_min=_redondear(oferta * (1 - d_max)),
            cierre_max=_redondear(oferta * (1 - d_min)),
            error_mediano=float(m["motor_comparables"]["error_absoluto_mediano"]),
            error_fiabilidad=float(m["error_por_fiabilidad"][r["fiabilidad"]]),
            comparables=self._comparables(ficha, factor_piso,
                                          float(f["factor_actualizacion"])),
            mapa=self._mapa(ficha, factor_piso, float(f["factor_actualizacion"])),
        )
