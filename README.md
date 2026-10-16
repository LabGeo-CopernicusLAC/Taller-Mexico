<p align="center">
<img src="https://www.copernicuslac-chile.eu/wp-content/uploads/2024/05/logo_copernicuslac_chile.svg" alt="Copernicus LAC Chile" width="1200"/>
</p>

# Territorio, ciudad y mar — Módulo de Monitoreo de Costas
## ODS 14 con productos CopernicusLAC Chile y datos oficiales de México

Material práctico del bloque **Monitoreo de Costas** del taller de servicios CopernicusLAC Chile para el monitoreo estratégico en México, coordinado con el Subsistema Nacional de Información Geográfica, Medio Ambiente, Ordenamiento Territorial y Urbano (SNIGMAOTU).

## ¿Cuándo se dicta?

| Sesión | Fecha | Horario |
|---|---|---|
| Presencial | miércoles 11 de noviembre de 2026 | 13:00 – 15:30 |

## ¿Qué haremos?

Trabajaremos con la **temperatura superficial del mar (SST)** y la **clorofila-a (CHL)** mensuales de 2024 producidas por CopernicusLAC Chile, y las compararemos con los indicadores del **ODS 14** que publican México (Sistema de Información de los ODS, SIODS, del INEGI) y Naciones Unidas:

- **14.1.1** Eutrofización costera: la clorofila como componente y la serie oficial de la ONU.
- **14.5.1** Cobertura de zonas protegidas: reproduciremos el valor que publica el SIODS.
- **14.2.1** Enfoques ecosistémicos: contexto ambiental de los programas de ordenamiento ecológico marino.

Cada grupo elegirá una de cinco áreas del mar mexicano: Baja California – Pacífico, Golfo de California, Pacífico sur, Golfo de México o Caribe mexicano.

## Prerrequisitos

Se requiere **Jupyter**. Recomendamos instalar [Anaconda](https://www.anaconda.com/download) o [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (más ligero), que incluyen Jupyter y el gestor de entornos `conda`.

Traer **computador portátil** propio con el entorno instalado y probado **antes del taller** (ver abajo). La sala puede no tener una conexión estable: descarga este material con anticipación.

## Descarga

El repositorio es **privado**: acepta la invitación que te llegará a tu cuenta de GitHub. Luego, desde la terminal (Linux/macOS) o Anaconda Prompt (Windows):

```bash
git clone <URL-del-repositorio>
```

O usa el botón **Code → Download ZIP**. También puedes recibir el ZIP de la organización. El material es solo para participantes del taller.

El material ocupa unos 200 MB, casi todo en los dos archivos de datos NetCDF de `data/sst` y `data/chl`.

## Entorno de Python

El taller usa el entorno **`2026coplac`**, el mismo de los módulos terrestres de la jornada (Atlas Urbano y Cobertura y Uso de Suelo). **Si ya lo instalaste para esos módulos, no tienes que reinstalarlo.**

Abre **Anaconda Prompt** (Windows) o la **terminal** (Linux/macOS), entra en la carpeta del taller y crea el entorno:

```bash
cd ruta/a/la/carpeta/del/taller
conda env create -f environment.yml
```

Actívalo:

```bash
conda activate 2026coplac
```

Registra el entorno como *kernel* de Jupyter:

```bash
# Windows
setup_kernel.bat
# macOS / Linux
bash setup_kernel.sh
```

## Iniciar JupyterLab

Con el entorno activado:

```bash
jupyter lab
```

En cada notebook selecciona el kernel **Python (2026coplac)** (arriba a la derecha).

## Notebooks

| Notebook | Cuándo | Qué hace |
|---|---|---|
| `notebooks/00_test_entorno.ipynb` | **antes del taller** | Comprueba bibliotecas, carpetas y datos. Si termina sin errores, tu equipo está listo |
| `notebooks/01_OCEANOS_ODS14_mexico.ipynb` | en el taller | Actividad guiada: selección del área con menús, visor mensual de SST y CHL, ODS 14.1.1, calculadora del 14.5.1, 14.2.1 y ficha del grupo |

Ejecuta las celdas de arriba hacia abajo. El notebook 01 funciona **sin internet**: si no hay conexión, el mapa interactivo se reemplaza por un mapa estático (Paso 0.2).

Los resultados de cada grupo se guardan en `outputs/figures/<grupo>` y `outputs/tables/<grupo>`.

## Estructura

```text
├── notebooks/        00_test_entorno, 01_OCEANOS_ODS14_mexico
├── scripts/          funciones del taller (no es necesario modificarlas)
├── data/
│   ├── sst/          temperatura superficial del mar, mensual 2024 (NetCDF)
│   ├── chl/          clorofila-a, mensual 2024 (NetCDF)
│   ├── shapes/mexico ANP federales (CONANP), ZEE (Marine Regions), áreas de trabajo
│   ├── ods/          valores oficiales del SIODS y de la ONU
│   └── descargas/    aquí van los datos que descargas tú (ver DATOS_Y_LICENCIAS.md)
├── outputs/          resultados de cada grupo
├── environment.yml   entorno 2026coplac
└── DATOS_Y_LICENCIAS.md
```

## Fuentes de datos

Ver [DATOS_Y_LICENCIAS.md](DATOS_Y_LICENCIAS.md).

## Contacto

Servicio de Monitoreo de Costas — CopernicusLAC Chile
labgeo@cmm.uchile.cl
