"""Descarga series estatales desde la API del Banco de Indicadores del INEGI."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import requests


API_BASE = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml"


def descargar_indicador(
    indicador: str,
    area: str,
    fuente: str,
    token: str,
) -> tuple[pd.DataFrame, dict]:
    url = f"{API_BASE}/INDICATOR/{indicador}/es/{area}/false/{fuente}/2.0/{token}"
    respuesta = requests.get(url, params={"type": "json"}, timeout=60)
    respuesta.raise_for_status()
    payload = respuesta.json()

    series = payload.get("Series", [])
    if not series:
        raise ValueError(f"INEGI no devolvió series para el indicador {indicador}")

    serie = series[0]
    observaciones = pd.DataFrame(serie.get("OBSERVATIONS", []))
    if observaciones.empty:
        raise ValueError(f"La serie {indicador} no contiene observaciones")

    columnas = {
        "TIME_PERIOD": "periodo",
        "OBS_VALUE": "valor",
        "COBER_GEO": "cve_geo",
        "OBS_STATUS": "estatus",
        "OBS_EXCEPTION": "excepcion",
        "OBS_SOURCE": "fuente_observacion",
        "OBS_NOTE": "nota_observacion",
    }
    observaciones = observaciones.rename(columns=columnas)
    observaciones["valor"] = pd.to_numeric(
        observaciones["valor"].astype(str).str.replace(",", "", regex=False),
        errors="coerce",
    )
    observaciones["id_indicador"] = indicador

    metadatos = {
        "id_indicador": indicador,
        "frecuencia": serie.get("FREQ"),
        "unidad": serie.get("UNIT"),
        "multiplicador": serie.get("UNIT_MULT"),
        "fuente": serie.get("SOURCE"),
        "ultima_actualizacion": serie.get("LASTUPDATE"),
        "nota": serie.get("NOTE"),
    }
    return observaciones, metadatos


def ejecutar(config_path: Path, output_dir: Path) -> None:
    token = os.getenv("INEGI_TOKEN")
    if not token:
        raise RuntimeError("Falta la variable de entorno INEGI_TOKEN")

    config = pd.read_csv(config_path, dtype=str).fillna("")
    faltantes = config.loc[config["id_indicador"].str.strip().eq(""), "variable"].tolist()
    if faltantes:
        lista = ", ".join(faltantes)
        raise ValueError(f"Faltan identificadores INEGI en la configuración: {lista}")

    output_dir.mkdir(parents=True, exist_ok=True)
    metadatos = []

    for fila in config.itertuples(index=False):
        datos, meta = descargar_indicador(
            indicador=fila.id_indicador.strip(),
            area=fila.area_geografica.strip(),
            fuente=fila.fuente_api.strip(),
            token=token,
        )
        datos.insert(0, "variable", fila.variable)
        datos.to_csv(output_dir / f"{fila.variable}.csv", index=False, encoding="utf-8-sig")
        meta["variable"] = fila.variable
        metadatos.append(meta)

    pd.DataFrame(metadatos).to_csv(
        output_dir / "metadata_descargas.csv",
        index=False,
        encoding="utf-8-sig",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/inegi"),
    )
    args = parser.parse_args()
    ejecutar(args.config, args.output)
