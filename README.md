<p align="center">
<img src="https://www.copernicuslac-chile.eu/wp-content/uploads/2024/05/logo_copernicuslac_chile.svg" alt="Copernicus LAC Chile" width="1200"/>
</p>

# Territorio, ciudad y mar - Módulo de Monitoreo de Costas 
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

Se requierede Git y Jupyter Notebook para poder realizar este taller. Se recomienda que se instale la última distribución de Anaconda o de Miniconda (más ligero) en su sistema operativo. Las distribuciones de Anaconda y Miniconda incluyen Jupyter Notebook.

## Instalación desde GitHub
La manera más simple para instalar los paquetes es via `Git`. Los usuarios pueden clonar este repositorio ejecutando los siguientes comandos desde su `terminal` (Linux/OSx) o desde el `Anaconda prompt`.

Si no tienes tienes `Git` instalado o no sabes si esta instalado, recomendamos asegurarte que `conda` está actualizado mediante el siguiente código:

```bash
conda update -n base conda
conda update --all
```
Ahora podemos asegurarnos de tener `Git` ejecutando la siguiente línea:

```bash
conda install git
```

En general el terminal se encuentra en el menú de inicio de la mayoría de las distribuciones de Linux y en la carpeta de Aplicaciones/Utilidades en OS X. Como alternativa, se debería poder abrir el terminal de Anaconda desde el menú de inicio (o desde el dock, o ejecutando el Anaconda Navigator). 

Una vez abierto el terminal, se debe navegar hacia la carpeta donde deseas colocar el taller  

```bash
cd /ruta/a/carpeta/taller_copernicus_lac
```

Una vez en la carpeta correcta, ejecutar el siguiente comando:

<!-- Una vez abierto el terminal, ejecutar el siguiente comando: -->
```bash
git clone --recurse-submodules --remote-submodules https://github.com/LabGeo-CopernicusLAC/Taller-IDE-Uruguay.git
```

Esto creará una copia local de todos los archivos relevantes, incluyendo los Jupyter Notebooks a ejecutar, códigos auxiliares y datos.

O usa el botón **Code → Download ZIP**. También puedes recibir el ZIP de la organización. El material es solo para participantes del taller.

El material ocupa unos 200 MB, casi todo en los dos archivos de datos NetCDF de `data/sst` y `data/chl`.

## Jupyter-Lab

Este taller es compatible con Python 3.11. Frente a las multiples opciones posibles, se recomienda que los usuarios instalen el paquete de Anaconda adecuado para su sistema operativo.
Para asegurarse que se cuente con todas las dependencias requeridas para la ejecución del taller, se recomienda que se configure el entorno de Python adecuado, como se explica a continuación.

## Entorno de Python

Python permite a los usuarios crear entornos específicos que se adapten a sus proyectos.
Los tutoriales incluidos en este taller requieren de varios paquetes que no vienen incluidos por defecto en Anaconda. En este directorio, los usuarios encontrarán un archivo *environment.yaml* que se puede utilizar para configurar un entorno con todos los paquetes necesarios ya instalados.

El taller usa el entorno **`2026coplac`**, el mismo de los módulos terrestres de la jornada (Atlas Urbano y Cobertura y Uso de Suelo). **Si ya lo instalaste para esos módulos, no tienes que reinstalarlo.**

Abre **Anaconda Prompt** (Windows) o la **terminal** (Linux/macOS), navega hasta la carpeta del repositorio que descargaste en la sección «Instalación» anterior. y crea el entorno:

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

Ahora sí, estamos listos para iniciar JupyterLab y realizar el taller!!

*Nota: Recordar que es necesario activar el entorno en cada sesión nueva*

## Iniciar JupyterLab

Este Taller se basa en una serie de cuadernos de Jupyter ([Jupyter Notebooks](https://jupyter.org)), diseñados para ejecutarse en Jupyter Lab.
Los cuadernos de Jupyter facilitan el aprendizaje interactivo al permitirnos combinar código, descripciones de texto y visualizaciones de datos. 

Con el entorno activado:

```bash
jupyter lab
```

En cada notebook selecciona el kernel **Python (2026coplac)** (arriba a la derecha).

*Nota: Es importante ejecutar Jupyter Lab desde el directorio correcto. Jupyter Lab no puede encontrar nada que esté “por encima” de él en un árbol de directorios.

## Fuentes de datos

Ver [DATOS_Y_LICENCIAS.md](DATOS_Y_LICENCIAS.md).

## Contacto
Cualquier duda puedes escribirnos al soporte técnico — tallerXXXXXXXXX2026@copernicuslac-chile.eu

Servicios de geomática CopernicusLAC Chile
labgeo@cmm.uchile.cl
