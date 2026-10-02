from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"


def main():
    base = pd.read_csv(
        PROCESSED / "panel_estatal_base_2010_2024.csv",
        dtype={"cve_entidad": str},
    )
    imss = pd.read_csv(
        PROCESSED / "empleo_formal_imss_estatal_2010_2024.csv",
        dtype={"cve_entidad": str},
    )

    llaves = ["cve_entidad", "anio"]
    esperadas = pd.MultiIndex.from_product(
        [[f"{c:02d}" for c in range(1, 33)], range(2010, 2025)],
        names=llaves,
    )

    for nombre, df in [("base", base), ("IMSS", imss)]:
        df["cve_entidad"] = df["cve_entidad"].str.zfill(2)

        if df.duplicated(llaves).any():
            raise ValueError(f"Hay llaves duplicadas en {nombre}.")

        actuales = pd.MultiIndex.from_frame(df[llaves])
        if (
            len(df) != 480
            or len(esperadas.difference(actuales))
            or len(actuales.difference(esperadas))
        ):
            raise ValueError(f"Cobertura estatal/anual incorrecta en {nombre}.")

    if not imss["meses_disponibles"].eq(12).all():
        raise ValueError("Hay promedios IMSS con menos de 12 meses.")

    puestos = pd.to_numeric(
        imss["puestos_imss_promedio_anual"], errors="raise"
    )
    if not puestos.between(0, float("inf"), inclusive="neither").all():
        raise ValueError("Hay promedios IMSS faltantes, no positivos o infinitos.")
    imss["puestos_imss_promedio_anual"] = puestos

    panel = base.merge(
        imss[llaves + ["puestos_imss_promedio_anual", "meses_disponibles"]],
        on=llaves,
        how="outer",
        validate="one_to_one",
        indicator=True,
    )

    if not panel["_merge"].eq("both").all():
        raise ValueError("Existen observaciones sin correspondencia.")

    panel = (
        panel.drop(columns="_merge")
        .sort_values(llaves)
        .reset_index(drop=True)
    )

    panel["crecimiento_puestos_imss_pct"] = (
        panel.groupby("cve_entidad")["puestos_imss_promedio_anual"]
        .pct_change(fill_method=None)
        .mul(100)
        .round(3)
    )

    salida = PROCESSED / "panel_estatal_v2_2010_2024.csv"
    panel.to_csv(salida, index=False, encoding="utf-8-sig")

    print("Entidades:", panel["cve_entidad"].nunique())
    print("Observaciones:", len(panel))
    print("Archivo:", salida)
    print("\nSONORA:")
    columnas = [
        "anio", "pib_real_per_capita",
        "puestos_imss_promedio_anual", "crecimiento_puestos_imss_pct",
    ]
    print(
        panel.loc[panel["cve_entidad"].eq("26"), columnas]
        .tail()
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
