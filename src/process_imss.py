from pathlib import Path
import unicodedata

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/raw/imss/imss_mensual_entidades_2000_2025.csv"
OUTPUT = ROOT / "data/processed/empleo_formal_imss_estatal_2010_2024.csv"

ESTADOS = {
    "AGUASCALIENTES": "01",
    "BAJA CALIFORNIA": "02",
    "BAJA CALIFORNIA SUR": "03",
    "CAMPECHE": "04",
    "COAHUILA": "05",
    "COLIMA": "06",
    "CHIAPAS": "07",
    "CHIHUAHUA": "08",
    "CIUDAD DE MEXICO": "09",
    "DURANGO": "10",
    "GUANAJUATO": "11",
    "GUERRERO": "12",
    "HIDALGO": "13",
    "JALISCO": "14",
    "ESTADO DE MEXICO": "15",
    "MICHOACAN": "16",
    "MORELOS": "17",
    "NAYARIT": "18",
    "NUEVO LEON": "19",
    "OAXACA": "20",
    "PUEBLA": "21",
    "QUERETARO": "22",
    "QUINTANA ROO": "23",
    "SAN LUIS POTOSI": "24",
    "SINALOA": "25",
    "SONORA": "26",
    "TABASCO": "27",
    "TAMAULIPAS": "28",
    "TLAXCALA": "29",
    "VERACRUZ": "30",
    "YUCATAN": "31",
    "ZACATECAS": "32",
}

MESES = {
    nombre: numero
    for numero, nombre in enumerate(
        [
            "ENERO", "FEBRERO", "MARZO", "ABRIL",
            "MAYO", "JUNIO", "JULIO", "AGOSTO",
            "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE",
        ],
        start=1,
    )
}


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.upper().split())


def main():
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            df = pd.read_csv(INPUT, header=[0, 1], encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("No se pudo identificar la codificación.")

    nombres = df.iloc[:, 0].map(normalizar)
    desconocidos = set(nombres) - set(ESTADOS) - {"TOTAL NACIONAL"}
    if desconocidos:
        raise ValueError(f"Nombres no reconocidos: {sorted(desconocidos)}")

    estados = df.loc[nombres.isin(ESTADOS)].copy()
    nombres_estados = nombres.loc[estados.index]

    if len(estados) != 32 or nombres_estados.nunique() != 32:
        raise ValueError("Se requieren exactamente 32 estados sin duplicados.")

    bloques = []
    for posicion, (anio, mes) in enumerate(df.columns[1:], start=1):
        if str(anio) not in {str(a) for a in range(2010, 2025)}:
            continue

        mes_normalizado = normalizar(mes)
        if mes_normalizado not in MESES:
            raise ValueError(f"Mes no reconocido: {mes}")

        bloques.append(pd.DataFrame({
            "cve_entidad": nombres_estados.map(ESTADOS),
            "anio": int(anio),
            "mes": MESES[mes_normalizado],
            "puestos_imss": pd.to_numeric(
                estados.iloc[:, posicion], errors="raise"
            ),
        }))

    mensual = pd.concat(bloques, ignore_index=True)

    if mensual.duplicated(["cve_entidad", "anio", "mes"]).any():
        raise ValueError("Existen registros mensuales duplicados.")

    if len(mensual) != 32 * 15 * 12:
        raise ValueError(f"Se esperaban 5760 registros; hay {len(mensual)}.")

    valores = mensual["puestos_imss"]
    if (
        valores.isna().any()
        or not valores.between(0, float("inf"), inclusive="left").all()
        or (valores % 1 != 0).any()
    ):
        raise ValueError("Hay puestos faltantes, negativos, infinitos o no enteros.")

    anual = (
        mensual.groupby(["cve_entidad", "anio"], as_index=False)
        .agg(
            puestos_imss_promedio_anual=("puestos_imss", "mean"),
            meses_disponibles=("mes", "nunique"),
        )
        .sort_values(["cve_entidad", "anio"])
    )

    if len(anual) != 480 or not anual["meses_disponibles"].eq(12).all():
        raise ValueError("El panel anual está incompleto.")

    # Recuperamos los nombres estandarizados del panel existente.
    base = pd.read_csv(
        ROOT / "data/processed/panel_estatal_base_2010_2024.csv",
        dtype={"cve_entidad": str},
    )
    catalogo = base[["cve_entidad", "entidad"]].drop_duplicates()
    anual = anual.merge(
        catalogo, on="cve_entidad", how="left", validate="many_to_one"
    )
    if anual["entidad"].isna().any():
        raise ValueError("Hay estados sin correspondencia con el panel base.")

    anual = anual[
        [
            "cve_entidad", "entidad", "anio",
            "puestos_imss_promedio_anual", "meses_disponibles",
        ]
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    anual.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    print("Entidades:", anual["cve_entidad"].nunique())
    print("Periodo:", anual["anio"].min(), "-", anual["anio"].max())
    print("Observaciones:", len(anual))
    print("Meses por entidad-año: 12")
    print("Archivo:", OUTPUT)
    print("\nSONORA:")
    print(anual.loc[anual["cve_entidad"].eq("26")].tail().to_string(index=False))


if __name__ == "__main__":
    main()
