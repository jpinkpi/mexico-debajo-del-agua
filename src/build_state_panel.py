from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

PIBE_FILE = (
    ROOT
    / "data"
    / "processed"
    / "pibe_real_estatal_2010_2024.csv"
)

POPULATION_FILE = (
    ROOT
    / "data"
    / "processed"
    / "poblacion_estatal_2010_2024.csv"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "processed"
    / "panel_estatal_base_2010_2024.csv"
)


def construir_panel():
    archivos = [PIBE_FILE, POPULATION_FILE]

    for archivo in archivos:
        if not archivo.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo: {archivo}"
            )

    pib = pd.read_csv(
        PIBE_FILE,
        dtype={"cve_entidad": str},
    )

    poblacion = pd.read_csv(
        POPULATION_FILE,
        dtype={"cve_entidad": str},
    )

    pib["cve_entidad"] = pib["cve_entidad"].str.zfill(2)
    poblacion["cve_entidad"] = (
        poblacion["cve_entidad"].str.zfill(2)
    )

    pib = pib.rename(
        columns={"entidad": "entidad_pibe"}
    )

    poblacion = poblacion.rename(
        columns={"entidad": "entidad_conapo"}
    )

    panel = pib.merge(
        poblacion,
        on=["cve_entidad", "anio"],
        how="outer",
        validate="one_to_one",
        indicator=True,
    )

    problemas = panel[panel["_merge"] != "both"]

    if not problemas.empty:
        raise ValueError(
            "Existen observaciones sin correspondencia:\n"
            f"{problemas.to_string(index=False)}"
        )

    panel = panel.drop(columns="_merge")

    diferencias_nombres = (
        panel.loc[
            panel["entidad_pibe"]
            != panel["entidad_conapo"],
            [
                "cve_entidad",
                "entidad_pibe",
                "entidad_conapo",
            ],
        ]
        .drop_duplicates()
        .sort_values("cve_entidad")
    )

    # Conservamos como nombre estandarizado el empleado
    # por el PIBE; la integración se realiza por código.
    panel["entidad"] = panel["entidad_pibe"]

    panel["pib_real_per_capita"] = (
        panel["pib_real_millones"] * 1_000_000
        / panel["poblacion"]
    )

    panel = panel.sort_values(
        ["cve_entidad", "anio"]
    ).reset_index(drop=True)

    panel["crecimiento_pib_real_pct"] = (
        panel.groupby("cve_entidad")[
            "pib_real_millones"
        ]
        .pct_change(fill_method=None)
        .mul(100)
    )

    panel["crecimiento_poblacion_pct"] = (
        panel.groupby("cve_entidad")[
            "poblacion"
        ]
        .pct_change(fill_method=None)
        .mul(100)
    )

    panel["crecimiento_pib_pc_pct"] = (
        panel.groupby("cve_entidad")[
            "pib_real_per_capita"
        ]
        .pct_change(fill_method=None)
        .mul(100)
    )

    panel["pib_real_per_capita"] = (
        panel["pib_real_per_capita"].round(2)
    )

    columnas_porcentaje = [
        "crecimiento_pib_real_pct",
        "crecimiento_poblacion_pct",
        "crecimiento_pib_pc_pct",
    ]

    panel[columnas_porcentaje] = (
        panel[columnas_porcentaje].round(3)
    )

    panel = panel[
        [
            "cve_entidad",
            "entidad",
            "anio",
            "pib_real_millones",
            "poblacion",
            "pib_real_per_capita",
            "crecimiento_pib_real_pct",
            "crecimiento_poblacion_pct",
            "crecimiento_pib_pc_pct",
        ]
    ]

    if len(panel) != 480:
        raise ValueError(
            f"Se esperaban 480 observaciones y se "
            f"obtuvieron {len(panel)}"
        )

    if panel.duplicated(
        ["cve_entidad", "anio"]
    ).any():
        raise ValueError(
            "Existen duplicados en la llave entidad-año"
        )

    columnas_sin_nulos = [
        "pib_real_millones",
        "poblacion",
        "pib_real_per_capita",
    ]

    if panel[columnas_sin_nulos].isna().any().any():
        raise ValueError(
            "Existen valores nulos en variables principales"
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    panel.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print("=== PANEL ESTATAL BASE ===")
    print(f"Entidades: {panel['cve_entidad'].nunique()}")
    print(f"Periodo: {panel['anio'].min()}-{panel['anio'].max()}")
    print(f"Observaciones: {len(panel)}")
    print(f"Archivo: {OUTPUT_FILE}")

    if diferencias_nombres.empty:
        print("\nSin discrepancias de nombres entre fuentes.")
    else:
        print("\n=== DIFERENCIAS DE NOMBRES ===")
        print(diferencias_nombres.to_string(index=False))

    print("\n=== SONORA ===")
    print(
        panel[
            panel["cve_entidad"] == "26"
        ]
        .tail()
        .to_string(index=False)
    )


if __name__ == "__main__":
    construir_panel()