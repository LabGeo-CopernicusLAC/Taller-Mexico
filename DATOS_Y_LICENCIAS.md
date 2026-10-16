# Datos y licencias

| Archivo | Contenido | Fuente | Uso |
|---|---|---|---|
| `data/sst/CMC_SST_2024MM_*.nc` | Temperatura superficial del mar, compuestos mensuales 2024, grilla 0,02° (L4) | CopernicusLAC Chile, Servicio de Monitoreo de Costas | Material del taller, https://copernicuslac-chile.eu/ |
| `data/chl/CMC_CHL_2024MM_*.nc` | Clorofila-a, compuestos mensuales 2024, grilla 0,01° (L4, multisensor) | CopernicusLAC Chile, Servicio de Monitoreo de Costas | Material del taller, https://copernicuslac-chile.eu/ |
| `data/shapes/mexico/anp.gpkg` | 232 Áreas Naturales Protegidas federales, con superficie marina declarada (`S_MARINA`) | CONANP, Información Geoespacial de las ANP (archivo `shp_anp_20260924`), normalizado a EPSG:4326 | Datos públicos de CONANP; citar la fuente |
| `data/shapes/mexico/zee.gpkg` | Zona Económica Exclusiva de México | Marine Regions / VLIZ, World EEZ v12 (2023-10-25), MRGID 8429 | CC BY 4.0; ver `LICENSE_EEZ_v12.txt`. Cita: Flanders Marine Institute (2023), Maritime Boundaries Geodatabase v12, https://doi.org/10.14284/632. Compilación internacional sin valor legal |
| `data/shapes/mexico/areas_estudio.gpkg` | Cinco áreas de trabajo (rectángulos docentes) con su POEM de referencia aproximada | Elaboración propia del taller | No son límites oficiales |
| `data/ods/referencias_oficiales_ods14.csv` | Valores oficiales de los indicadores 14.1.1, 14.2.1 y 14.5.1 para México | INEGI, SIODS (agenda2030.mx); ONU, Global SDG Indicators Database; consulta 13-10-2026 | Valores publicados, no recalculados; cada fila cita su fuente |

## Datos que debes descargar tú

Casi todo viene incluido. Solo falta una capa, que no se puede repartir en el taller porque su licencia lo prohíbe:

**Áreas Clave para la Biodiversidad (KBA)** — solo se usa en el anexo opcional A.2 del notebook 01. No hace falta para el taller.

1. Entra en [keybiodiversityareas.org/kba-data/request](https://keybiodiversityareas.org/kba-data/request) y completa el formulario de uso no comercial. En la extensión elige **país: México**.
2. Espera el correo con el enlace de descarga. **Tardan de 5 a 10 días hábiles**: pídelo con al menos dos semanas de antelación.
3. Descarga el ZIP y ponlo, **sin descomprimir**, en la carpeta `data/descargas/` del taller.
4. Ejecuta la celda del anexo A.2. El notebook extrae México y prepara la capa automáticamente.

Recuerda que las KBA son para uso personal: no las subas al repositorio ni las compartas.

## Limitaciones principales

- Los NetCDF cubren de 120,1° O a 85,9° O y de 13,8° N a 32,5° N: no toda la ZEE mexicana.
- Un producto L4 rellena huecos (nubes) con interpolación o modelo: alta cobertura no significa observación en cada píxel.
- La clorofila satelital en aguas costeras turbias puede estar sobrestimada por sedimento y materia orgánica disuelta.
- Un solo año (2024) no permite calcular anomalías climatológicas.
