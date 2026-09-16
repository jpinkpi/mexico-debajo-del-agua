from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT
    / "data"
    / "raw"
    / "conapo"
    / "poblacion"
    / "0_Pob_Mitad_1950_2070.xlsx"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "processed"
    / "poblacion_estatal_2010_2024.csv"
)


def procesar_poblacion():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {INPUT_FILE}"
        )

    datos = pd.read_excel(
        INPUT_FILE,
        sheet_name="Hoja1",
        usecols=[
            "AÑO",
            "ENTIDAD",
            "CVE_GEO",
            "EDAD",
            "SEXO",
            "POBLACION",
        ],
    )

    columnas_esperadas = {
        "AÑO",
        "ENTIDAD",
        "CVE_GEO",
        "EDAD",
        "SEXO",
        "POBLACION",
    }

    if set(datos.columns) != columnas_esperadas:
        raise ValueError(
            f"Columnas inesperadas: {list(datos.columns)}"
        )

    datos = datos[
        datos["AÑO"].between(2010, 2024)
        & datos["CVE_GEO"].between(1, 32)
    ].copy()

    sexos = set(datos["SEXO"].dropna().unique())

    if sexos != {"Hombres", "Mujeres"}:
        raise ValueError(
            f"Categorías de sexo inesperadas: {sexos}"
        )

    if datos["EDAD"].min() != 0 or datos["EDAD"].max() != 109:
        raise ValueError(
            "El rango de edades no corresponde a 0–109"
        )

    poblacion = (
        datos.groupby(
            ["CVE_GEO", "ENTIDAD", "AÑO"],
            as_index=False,
        )["POBLACION"]
        .sum()
        .rename(
            columns={
                "CVE_GEO": "cve_entidad",
                "ENTIDAD": "entidad",
                "AÑO": "anio",
                "POBLACION": "poblacion",
            }
        )
    )

    poblacion["cve_entidad"] = (
        poblacion["cve_entidad"]
        .astype(int)
        .astype(str)
        .str.zfill(2)
    )

    poblacion["anio"] = poblacion["anio"].astype(int)
    poblacion["poblacion"] = poblacion["poblacion"].astype(int)

    poblacion = poblacion.sort_values(
        ["cve_entidad", "anio"]
    )

    if poblacion["cve_entidad"].nunique() != 32:
        raise ValueError(
            "No se obtuvieron las 32 entidades"
        )

    if poblacion["anio"].nunique() != 15:
        raise ValueError(
            "No se obtuvieron los 15 años esperados"
        )

    if len(poblacion) != 480:
        raise ValueError(
            f"Se esperaban 480 observaciones y se "
            f"obtuvieron {len(poblacion)}"
        )

    if poblacion.duplicated(
        ["cve_entidad", "anio"]
    ).any():
        raise ValueError(
            "Existen duplicados en entidad-año"
        )

    if poblacion["poblacion"].isna().any():
        raise ValueError(
            "Existen valores nulos de población"
        )

    if (poblacion["poblacion"] <= 0).any():
        raise ValueError(
            "Existen valores de población no positivos"
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    poblacion.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print("=== POBLACIÓN ESTATAL ===")
    print(
        f"Entidades: "
        f"{poblacion['cve_entidad'].nunique()}"
    )
    print(
        f"Periodo: {poblacion['anio'].min()}-"
        f"{poblacion['anio'].max()}"
    )
    print(f"Observaciones: {len(poblacion)}")
    print(f"Archivo: {OUTPUT_FILE}")

    print("\n=== SONORA ===")
    print(
        poblacion[
            poblacion["cve_entidad"] == "26"
        ]
        .tail()
        .to_string(index=False)
    )


if __name__ == "__main__":
    procesar_poblacion()