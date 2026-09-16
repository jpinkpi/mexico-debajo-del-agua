from pathlib import Path
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "data" / "raw" / "inegi" / "pibe" / "pibe_2.xlsx"
OUTPUT_FILE = (
    ROOT
    / "data"
    / "processed"
    / "pibe_real_estatal_2010_2024.csv"
)

ENTIDADES = {
    "Aguascalientes": "01",
    "Baja California": "02",
    "Baja California Sur": "03",
    "Campeche": "04",
    "Coahuila de Zaragoza": "05",
    "Colima": "06",
    "Chiapas": "07",
    "Chihuahua": "08",
    "Ciudad de México": "09",
    "Durango": "10",
    "Guanajuato": "11",
    "Guerrero": "12",
    "Hidalgo": "13",
    "Jalisco": "14",
    "México": "15",
    "Michoacán de Ocampo": "16",
    "Morelos": "17",
    "Nayarit": "18",
    "Nuevo León": "19",
    "Oaxaca": "20",
    "Puebla": "21",
    "Querétaro": "22",
    "Quintana Roo": "23",
    "San Luis Potosí": "24",
    "Sinaloa": "25",
    "Sonora": "26",
    "Tabasco": "27",
    "Tamaulipas": "28",
    "Tlaxcala": "29",
    "Veracruz de Ignacio de la Llave": "30",
    "Yucatán": "31",
    "Zacatecas": "32",
}


def extraer_anio(valor):
    coincidencia = re.match(r"^(\d{4})", str(valor))
    if coincidencia:
        return int(coincidencia.group(1))
    return None


def procesar_pibe():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {INPUT_FILE}"
        )

    raw = pd.read_excel(
        INPUT_FILE,
        sheet_name="Tabulado",
        header=None,
    )

    primera_columna = raw.iloc[:, 0].astype(str).str.strip()

    marcadores = raw.index[
        primera_columna.eq("Millones de pesos a precios de 2018")
    ].tolist()

    if not marcadores:
        raise ValueError(
            "No se encontró la sección de valores constantes de 2018"
        )

    fila_unidad = marcadores[0]
    fila_anios = fila_unidad - 1

    columnas_anios = {}

    for columna, valor in raw.iloc[fila_anios].items():
        anio = extraer_anio(valor)

        if anio is not None and 2010 <= anio <= 2024:
            columnas_anios[columna] = anio

    if len(columnas_anios) != 15:
        raise ValueError(
            f"Se esperaban 15 años y se encontraron "
            f"{len(columnas_anios)}"
        )

    # La primera sección contiene unidad, concepto,
    # total nacional y las 32 entidades.
    seccion = raw.iloc[fila_unidad:fila_unidad + 40].copy()

    seccion.iloc[:, 0] = (
        seccion.iloc[:, 0]
        .astype(str)
        .str.strip()
    )

    estados = seccion[
        seccion.iloc[:, 0].isin(ENTIDADES)
    ].copy()
    estados = estados.drop_duplicates(
     subset=[estados.columns[0]],
     keep="first",
)
    if len(estados) != 32:
        encontrados = sorted(estados.iloc[:, 0].unique())
        faltantes = sorted(set(ENTIDADES) - set(encontrados))

        raise ValueError(
            f"Se esperaban 32 entidades y se encontraron "
            f"{len(estados)}. Faltantes: {faltantes}"
        )

    columnas_seleccionadas = [0] + list(columnas_anios)
    estados = estados[columnas_seleccionadas]

    estados.columns = (
        ["entidad"]
        + [columnas_anios[c] for c in columnas_anios]
    )

    panel = estados.melt(
        id_vars="entidad",
        var_name="anio",
        value_name="pib_real_millones",
    )

    panel["cve_entidad"] = panel["entidad"].map(ENTIDADES)
    panel["anio"] = panel["anio"].astype(int)
    panel["pib_real_millones"] = pd.to_numeric(
        panel["pib_real_millones"],
        errors="coerce",
    )

    panel = panel[
        [
            "cve_entidad",
            "entidad",
            "anio",
            "pib_real_millones",
        ]
    ].sort_values(
        ["cve_entidad", "anio"]
    )

    if len(panel) != 480:
        raise ValueError(
            f"Se esperaban 480 observaciones y se obtuvieron "
            f"{len(panel)}"
        )

    if panel["pib_real_millones"].isna().any():
        raise ValueError("Existen valores nulos en el PIB")

    if panel.duplicated(["cve_entidad", "anio"]).any():
        raise ValueError(
            "Existen duplicados en la llave entidad-año"
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    panel.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print("=== PIBE REAL ESTATAL ===")
    print(f"Entidades: {panel['cve_entidad'].nunique()}")
    print(f"Periodo: {panel['anio'].min()}-{panel['anio'].max()}")
    print(f"Observaciones: {len(panel)}")
    print(f"Archivo: {OUTPUT_FILE}")

    print("\n=== SONORA ===")
    print(
        panel[panel["cve_entidad"] == "26"]
        .tail()
        .to_string(index=False)
    )


if __name__ == "__main__":
    procesar_pibe()