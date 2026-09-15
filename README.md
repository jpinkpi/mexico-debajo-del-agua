# México debajo del agua

Proyecto reproducible para estudiar si el crecimiento económico, el empleo y la inversión en las 32 entidades federativas de México se traducen en mejores condiciones laborales y sociales.

## Alcance inicial

- Unidad de análisis: entidad federativa-año.
- Cobertura objetivo: 2010-2024.
- Llave primaria: `cve_entidad`, `anio`.
- Primera fase: población, PIB estatal real y población ocupada.
- Segunda fase: ingreso laboral, informalidad, subocupación y pobreza laboral.
- Tercera fase: empleo IMSS, IED, exportaciones e inversión pública.

## Principio metodológico

No se mezclan automáticamente datos anuales y trimestrales. Para cada variable se conserva su frecuencia original, unidad, fuente, fecha de actualización y método de agregación. La ENOE requiere además respetar ponderadores y cambios metodológicos.

## Primeras hipótesis

1. Mayor productividad estatal no implica necesariamente mayor ingreso laboral real.
2. Mayor intensidad exportadora no implica necesariamente menor informalidad.
3. La IED produce resultados distintos según las capacidades productivas previas de cada estado.
4. Más puestos registrados en el IMSS no garantizan una reducción proporcional de la precariedad.

## Uso del descargador INEGI

1. Solicita un token gratuito para la API del Banco de Indicadores del INEGI.
2. Copia `config/indicadores.example.csv` como `config/indicadores.csv`.
3. Obtén las claves exactas mediante el Constructor de Consultas del INEGI.
4. Guarda el token en una variable de entorno llamada `INEGI_TOKEN`.
5. Ejecuta:

```bash
pip install -r requirements.txt
python src/download_inegi.py --config config/indicadores.csv
```

En PowerShell:

```powershell
$env:INEGI_TOKEN="TU_TOKEN"
python src/download_inegi.py --config config/indicadores.csv
```

El script genera un CSV largo por indicador en `data/raw/inegi/`. Los identificadores de ejemplo están deliberadamente vacíos: no deben inventarse ni inferirse de títulos generales del banco.

## Fuentes principales

- INEGI, API del Banco de Indicadores y PIBE, año base 2018.
- INEGI, ENOE para ocupación, informalidad y subocupación.
- INEGI, medición de pobreza laboral y multidimensional.
- IMSS, puestos registrados y salario base de cotización.
- Secretaría de Economía, inversión extranjera directa.
- INEGI, exportaciones trimestrales por entidad federativa.
- Finanzas públicas estatales y municipales.

## Siguiente entrega analítica

Una gráfica de productividad aproximada contra ingreso laboral real por entidad, acompañada de una tabla de casos atípicos. La productividad se calculará como PIB real dividido entre población ocupada promedio anual, dejando explícito que no equivale a productividad por hora.
