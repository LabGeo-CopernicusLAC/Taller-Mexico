"""Funciones de apoyo del taller: rutas, apertura de NetCDF, selección, mapas y cálculos ODS 14.
No contiene índices oceanográficos propios ni sustitutos de indicadores ODS.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
import shapely
from shapely import contains_xy, make_valid
from shapely.geometry import GeometryCollection
from shapely.ops import unary_union

CRS_AREA = 'EPSG:6933'  # proyección equivalente: áreas, no distancias

def encontrar_base_proyecto():
    for p in [Path.cwd().resolve(), *Path.cwd().resolve().parents]:
        if (p / 'environment.yml').exists() and (p / 'notebooks').is_dir():
            return p
    raise FileNotFoundError('Abra Jupyter desde la raíz del taller.')

def abrir_producto(carpeta, variable, tipo, confirmar_lonlat=False):
    archivos = sorted(Path(carpeta).rglob('*.nc'))
    if not archivos:
        raise FileNotFoundError(f'Sin NetCDF en {carpeta}; consulte GUIA_DATOS.md')
    datasets = []
    for archivo in archivos:
        ds = xr.open_dataset(archivo, decode_coords='all')
        ren = {k:v for k,v in [('longitude','lon'),('latitude','lat')] if k in ds.dims}
        ds = ds.rename(ren)
        if not {'lat','lon','time'}.issubset(ds.coords):
            raise ValueError(f'{archivo}: necesita coordenadas lat/lon/time CF.')
        if ds.lat.ndim != 1 or ds.lon.ndim != 1:
            raise ValueError('Esta práctica requiere grilla geográfica rectilínea.')
        for c, u in [('lat','degrees_north'),('lon','degrees_east')]:
            if ds[c].attrs.get('units') != u:
                if ds[c].attrs.get('units') or not confirmar_lonlat:
                    raise ValueError(f'{archivo}: confirme {c} en {u}; no se asigna CRS a ciegas.')
                if not (-90 <= float(ds.lat.min()) <= float(ds.lat.max()) <= 90):
                    raise ValueError('Latitud fuera de rango geográfico')
                if not (-180 <= float(ds.lon.min()) <= float(ds.lon.max()) <= 360):
                    raise ValueError('Longitud fuera de rango geográfico')
                print(f'AVISO: {archivo.name}: {c} sin units; interpretación geográfica confirmada explícitamente.')
        if variable not in ds:
            raise KeyError(f'{variable} ausente; disponibles: {list(ds.data_vars)}')
        da = ds[variable]
        extra = [d for d in da.dims if d not in ['time','lat','lon']]
        if any(da.sizes[d] != 1 for d in extra):
            raise ValueError('Seleccione explícitamente profundidad/banda antes de continuar.')
        da = da.squeeze(extra, drop=True).transpose('time','lat','lon')
        da = da.assign_coords(lon=((da.lon+180)%360)-180).sortby('lon').sortby('lat')
        if len(np.unique(da.lon)) != da.sizes['lon']:
            raise ValueError('Longitudes duplicadas tras normalizar; revise la grilla.')
        unidades = str(da.attrs.get('units','')).strip().lower().replace(' ','')
        if tipo == 'sst':
            if unidades in ['k','kelvin']: da = da - 273.15
            elif unidades not in ['degree_celsius','degrees_celsius','degc','celsius','°c']:
                raise ValueError(f'Unidad SST desconocida: {unidades}')
            da.attrs['units'] = 'degree_Celsius'
            if 'mask' in ds and ds['mask'].attrs.get('flag_meanings','') == 'water land sea_ice':
                m=ds['mask'].assign_coords(lon=((ds.lon+180)%360)-180).sortby('lon').sortby('lat')
                bits=m.fillna(0).astype('int64')
                da=da.where(m.notnull() & ((bits & 1)>0) & ((bits & 2)==0))
        else:
            if unidades in ['mgm-3','mg/m^3','mgm^-3','mg/m3','mgm**-3']: pass
            elif unidades in ['mg/l','mgl-1','mgl^-1']: da = da*1000
            else: raise ValueError(f'Unidad CHL desconocida: {unidades}; no asumir.')
            da = da.where(np.isfinite(da) & (da > 0))
            da.attrs['units'] = 'mg m-3'
        da = da.where(np.isfinite(da))
        datasets.append(da)
    da = xr.concat(datasets, dim='time', join='exact', combine_attrs='override').sortby('time')
    if da.time.to_index().has_duplicates:
        raise ValueError('Fechas duplicadas: quite versiones repetidas, no se descartan silenciosamente.')
    return da

def mensual(da):
    """Media de composiciones presentes; no ponderada por duración de ventanas."""
    return da.resample(time='MS').mean(skipna=True, keep_attrs=True)

def leer_capa(path, poligonos=True):
    g = gpd.read_file(path)
    if g.crs is None: raise ValueError(f'{path}: CRS ausente')
    if g.geometry.isna().any() or g.geometry.is_empty.any():
        raise ValueError(f'{path}: geometrías vacías')
    if not g.is_valid.all():
        raise ValueError(f'{path}: repare geometrías y registre cambios antes del análisis')
    if poligonos and not g.geom_type.isin(['Polygon','MultiPolygon']).all():
        raise ValueError(f'{path}: se necesitan polígonos; no se crean buffers de puntos')
    return g.to_crs(4326)

def mascara(da, geometria):
    x,y = np.meshgrid(da.lon.values, da.lat.values)
    # Geometría preparada: con shapely 2.0 (entorno 2026coplac) contains_xy no la prepara sola
    # y un polígono costero complejo tarda minutos en vez de segundos.
    geometria = shapely.from_wkb(shapely.to_wkb(geometria))
    shapely.prepare(geometria)
    return xr.DataArray(contains_xy(geometria,x,y),coords={'lat':da.lat,'lon':da.lon},dims=('lat','lon'))

def recortar(da, geometria):
    x0,y0,x1,y1 = geometria.bounds
    d = da.sel(lon=slice(x0,x1),lat=slice(y0,y1))
    return d.where(mascara(d,geometria))

def resumen(da, geometria, variable):
    d = recortar(da, geometria).load()
    m = mascara(d,geometria)
    n = int(m.sum())
    if not n: raise ValueError(f'{variable}: área menor que una celda o fuera del dominio')
    pesos = np.cos(np.deg2rad(d.lat)).broadcast_like(m).where(m,0)
    # Fracciones de celda no consideradas: documentar sesgo en áreas pequeñas.
    r = pd.DataFrame({'fecha':pd.to_datetime(d.time.values),
       'media':d.weighted(pesos).mean(('lat','lon')).compute().values,
       'mediana':d.median(('lat','lon'), skipna=True).compute().values,
       'validos':d.notnull().sum(('lat','lon')).compute().values})
    r['celdas_dominio'] = n
    r['cobertura_pct'] = 100*r.validos/n
    r['variable'] = variable
    from shapely.geometry import box
    huella=box(float(da.lon.min()),float(da.lat.min()),float(da.lon.max()),float(da.lat.max()))
    geo=gpd.GeoSeries([geometria,geometria.intersection(huella)],crs=4326).to_crs(CRS_AREA)
    r['area_dentro_huella_pct']=100*geo.area.iloc[1]/geo.area.iloc[0]
    # La cobertura_pct describe solo centros en la huella; esta columna revela recortes parciales.
    return r

def cargar_vectores(base):
    p = Path(base)/'data/shapes/mexico'
    capas = {}
    for key in ['zee','costa','marine_kba','pa','oecm','gestion','anp','zonificacion_anp','kba_mexico','amp_mexico_protectedplanet']:
        f = p/f'{key}.gpkg'
        if f.exists(): capas[key] = leer_capa(f, poligonos=(key!='costa'))
    return capas

def cobertura_kba(kba, pa, oecm=None):
    """Media aritmética de coberturas individuales; sin ponderar por área."""
    if kba.empty: raise ValueError('Sin Marine KBA: agregado indefinido, no cero')
    if 'kba_id' not in kba or kba.kba_id.isna().any():
        raise ValueError('Marine KBA necesita kba_id estable, no nulo.')
    k = kba.dissolve(by='kba_id',aggfunc='first').reset_index().to_crs(CRS_AREA)
    protegidas = [pa.to_crs(CRS_AREA).geometry]
    if oecm is not None: protegidas.append(oecm.to_crs(CRS_AREA).geometry)
    union = unary_union([g for serie in protegidas for g in serie])
    k['area_km2'] = k.area/1e6
    if (k.area_km2 <= 0).any(): raise ValueError('KBA con área nula')
    inter = k.copy()
    inter.geometry = k.geometry.intersection(union)
    k['cubierta_km2'] = inter.area/1e6
    k['cobertura_pct'] = 100*k.cubierta_km2/k.area_km2
    if not k.cobertura_pct.between(-1e-7,100+1e-7).all():
        raise AssertionError('Cobertura fuera de rango')
    inter = inter[~inter.is_empty].copy()
    u = gpd.GeoDataFrame({'tipo':['PA_union_OECM']},geometry=[union],crs=CRS_AREA)
    return k.to_crs(4326), inter.to_crs(4326), u.to_crs(4326), float(k.cobertura_pct.mean())

def mapa_raster(da, geometria, titulo, salida, log=False):
    from matplotlib.colors import LogNorm
    d = recortar(da, geometria)
    if not bool(d.notnull().any().compute()):
        print(titulo, ': sin celdas válidas'); return
    fig, ax = plt.subplots(figsize=(9,6))
    escala = {'CHL': (0.03, 30), 'SST': (10, 35)}
    variable = 'CHL' if log else 'SST'
    vmin, vmax = escala[variable]
    norm = LogNorm(vmin=vmin, vmax=vmax) if log else None
    d.plot(ax=ax, cmap='viridis' if log else 'turbo', norm=norm, vmin=None if log else vmin, vmax=None if log else vmax,
           cbar_kwargs={'label': 'Clorofila-a (mg m⁻³)' if log else 'SST (°C)'})
    gpd.GeoSeries([geometria], crs=4326).boundary.plot(ax=ax, color='black')
    ax.set_title(titulo); fig.tight_layout(); fig.savefig(salida, dpi=220); plt.show()

def mapa_raster(da, geometria, titulo, salida, log=False):
    from matplotlib.colors import LogNorm
    d = recortar(da,geometria)
    if not bool(d.notnull().any().compute()):
        print(titulo, ': sin celdas válidas'); return
    fig,ax=plt.subplots(figsize=(9,6))
    d.plot(ax=ax,cmap='viridis' if log else 'turbo',norm=LogNorm() if log else None)
    gpd.GeoSeries([geometria],crs=4326).boundary.plot(ax=ax,color='black')
    ax.set_title(titulo);fig.tight_layout();fig.savefig(salida,dpi=220);plt.show()


def inventario_netcdf(carpeta):
    """Usa coordenadas efectivas, no geospatial_bounds heredados del dominio LAC."""
    filas=[]
    for f in sorted(Path(carpeta).glob('*.nc')):
        with xr.open_dataset(f) as ds:
            lat=ds['lat'];lon=ds['lon'];t=pd.to_datetime(ds.time.values)
            filas.append({'archivo':f.name,'fechas':len(t),'inicio':str(t.min()),'fin':str(t.max()),
                'lat_min':float(lat.min()),'lat_max':float(lat.max()),
                'lon_min':float(lon.min()),'lon_max':float(lon.max()),
                'dlat_grados':float(np.median(np.diff(lat))),
                'dlon_grados':float(np.median(np.diff(lon))),
                'version':ds.attrs.get('product_version',''),'producto':ds.attrs.get('product_id',ds.attrs.get('id','')),
                'variables':', '.join(ds.data_vars)})
    return pd.DataFrame(filas)

def diagnostico_origen_chl(carpeta, geometria, confirmar_lonlat=False):
    """Bit 16 modelo, bits 1/2/4/8 sensores, según este producto; no es QA."""
    datos=[]
    for f in sorted(Path(carpeta).glob('*.nc')):
        with xr.open_dataset(f) as ds:
            if 'source_of_chl' not in ds: continue
            a=ds.source_of_chl.attrs
            if list(a.get('flag_masks',[])) != [1,2,4,8,16] or a.get('flag_meanings','').split() != ['MODIS_Aqua','VIIRS_NPP','VIIRS_NOAA20','OLCI','modelo']:
                raise ValueError('Codificación source_of_chl distinta: adaptar según metadatos')
        fuente=abrir_auxiliar(f,'source_of_chl')
        x=recortar(fuente,geometria).load()
        n=int(mascara(x,geometria).sum())
        valid=x.notnull();bits=x.fillna(0).astype('int64')
        sat=(bits & 15)>0;mod=(bits & 16)>0
        for j,t in enumerate(x.time.values):
            datos.append({'fecha':pd.Timestamp(t),'celdas_dominio':n,
              'solo_sensores':int((valid & sat & ~mod).isel(time=j).sum()),
              'solo_modelo':int((valid & mod & ~sat).isel(time=j).sum()),
              'mixto':int((valid & sat & mod).isel(time=j).sum()),
              'sin_fuente_identificada':int((valid & ~sat & ~mod).isel(time=j).sum()),
              'sin_flag':int((mascara(x,geometria) & ~valid).isel(time=j).sum())})
    return pd.DataFrame(datos)

def abrir_auxiliar(archivo,variable):
    ds=xr.open_dataset(archivo)
    d=ds[variable].assign_coords(lon=((ds.lon+180)%360)-180).sortby('lon').sortby('lat')
    return d


# ---------------------------------------------------------------------------
# ODS 14.5.1 con el método nacional (SIODS, INEGI / SEMARNAT)
# ---------------------------------------------------------------------------
def referencias_oficiales(base):
    """Valores oficiales consultados (SIODS-INEGI y base ONU). Ver fuentes en el CSV."""
    return pd.read_csv(Path(base)/'data/ods/referencias_oficiales_ods14.csv')

def serie_numerador_siods(anp):
    """Suma acumulada de S_MARINA (ha) por año del primer decreto.

    Reproduce el numerador del 14.5.1 nacional con el atributo declarado por CONANP.
    Supone que las ANP no cambiaron de superficie marina después del primer decreto.
    """
    a = anp.drop(columns='geometry').copy()
    a['anio'] = pd.to_datetime(a['PRIM_DEC']).dt.year
    anios = range(int(a.anio.min()), int(a.anio.max())+1)
    acumulado = a.groupby('anio')['S_MARINA'].sum().reindex(anios, fill_value=0).cumsum()
    return acumulado.rename('S_MARINA_ha').reset_index()

def cobertura_geometrica(proteccion, dominio):
    """Área de la unión de polígonos de protección dentro del dominio marino (km², EPSG:6933)."""
    dom = unary_union(dominio.to_crs(CRS_AREA).geometry)
    uni = unary_union(proteccion.to_crs(CRS_AREA).geometry)
    inter = uni.intersection(dom)
    return {'dominio_km2': dom.area/1e6, 'protegido_km2': inter.area/1e6,
            'cobertura_pct': 100*inter.area/dom.area}

def cobertura_por_categoria(anp, dominio):
    """Desagregación por categoría de manejo nacional (CAT_MANEJO); categorías no se solapan
    en la capa CONANP, pero se informa la suma para detectarlo."""
    dom = unary_union(dominio.to_crs(CRS_AREA).geometry)
    filas = []
    for cat, g in anp.to_crs(CRS_AREA).groupby('CAT_MANEJO'):
        inter = unary_union(g.geometry).intersection(dom)
        filas.append({'CAT_MANEJO': cat, 'n_anp': len(g),
                      'S_MARINA_km2_declarada': g['S_MARINA'].sum()/100,
                      'protegido_km2_geometrico': inter.area/1e6,
                      'cobertura_pct_geometrica': 100*inter.area/dom.area})
    return pd.DataFrame(filas).sort_values('protegido_km2_geometrico', ascending=False)


# ---------------------------------------------------------------------------
# ODS 14.1.1: llevar la CHL de CopernicusLAC a la grilla de 4 km de OC-CCI
# ---------------------------------------------------------------------------
def agregar_grilla_occi(da, geometria, min_fraccion=0.5):
    """Agrega CHL fina (0,01°) a la grilla global de OC-CCI 4 km (1/24°).

    - Media en log10 (media geométrica), coherente con la distribución lognormal de la CHL
      y con el operador temporal declarado por el propio producto (exp(mean(ln chl))).
    - Una celda de 4 km se conserva solo si al menos `min_fraccion` de sus celdas finas
      son agua válida dentro de la geometría: imita un píxel grueso «mayoritariamente agua».
      Las celdas mixtas de costa se pierden, como en un producto de 4 km.
    - Solo homogeneiza la resolución espacial. NO convierte el producto en OC-CCI:
      algoritmo, sensores y referencia 2000–2004 siguen siendo distintos.
    Devuelve (chl_4km, fraccion_valida) como DataArray (time, lat, lon).
    """
    d = recortar(da, geometria).load()
    dentro = mascara(d, geometria).values
    lon, lat = d.lon.values, d.lat.values
    ix = np.floor((lon + 180) * 24).astype(int)
    iy = np.floor((lat + 90) * 24).astype(int)
    ux, jx = np.unique(ix, return_inverse=True)
    uy, jy = np.unique(iy, return_inverse=True)
    idx = jy[:, None] * len(ux) + jx[None, :]
    ncel = len(ux) * len(uy)
    n_total = np.bincount(idx.ravel(), minlength=ncel)
    salida, fracciones = [], []
    for t in range(d.sizes['time']):
        v = d.isel(time=t).values
        ok = np.isfinite(v) & dentro & (v > 0)
        suma = np.bincount(idx[ok], weights=np.log10(v[ok]), minlength=ncel)
        n = np.bincount(idx[ok], minlength=ncel)
        f = n / np.maximum(n_total, 1)
        media = np.where(f >= min_fraccion, 10 ** (suma / np.maximum(n, 1)), np.nan)
        salida.append(media.reshape(len(uy), len(ux)))
        fracciones.append(f.reshape(len(uy), len(ux)))
    coords = {'time': d.time.values, 'lat': -90 + (uy + 0.5) / 24, 'lon': -180 + (ux + 0.5) / 24}
    chl4 = xr.DataArray(np.stack(salida), coords=coords, dims=('time', 'lat', 'lon'), name='chl_4km')
    chl4.attrs['units'] = 'mg m-3'
    frac = xr.DataArray(np.stack(fracciones), coords=coords, dims=('time', 'lat', 'lon'), name='fraccion_valida')
    return chl4, frac

def comparar_1km_4km(chl_fina, chl4, frac, geometria, min_fraccion=0.5):
    """Tabla mensual: media de CHL a ~1 km y a 4 km, y porcentaje de celdas finas válidas
    que quedan en celdas de 4 km descartadas (franja costera que desaparece)."""
    d = recortar(chl_fina, geometria).load()
    dentro = mascara(d, geometria)
    filas = []
    for t in range(d.sizes['time']):
        fina = d.isel(time=t).where(dentro)
        w1 = np.cos(np.deg2rad(fina.lat)).broadcast_like(fina).where(fina.notnull())
        media_1 = float((fina * w1).sum() / w1.sum())
        g = chl4.isel(time=t)
        w4 = np.cos(np.deg2rad(g.lat)).broadcast_like(g).where(g.notnull())
        media_4 = float((g * w4).sum() / w4.sum())
        # celdas finas válidas cuyo píxel de 4 km fue descartado
        f_fina = frac.isel(time=t).reindex(lat=np.floor((d.lat.values + 90) * 24) / 24 - 90 + 1 / 48,
                                           lon=np.floor((d.lon.values + 180) * 24) / 24 - 180 + 1 / 48,
                                           method='nearest')
        mask_perd = (f_fina.values < min_fraccion) & fina.notnull().values
        perdidas = int(mask_perd.sum())
        validas = int(fina.notnull().sum())
        chl_perdida = float(np.nanmedian(fina.values[mask_perd])) if perdidas else np.nan
        filas.append({'fecha': pd.Timestamp(d.time.values[t]), 'chl_1km_media': media_1, 'chl_4km_media': media_4,
                      'celdas_1km_validas': validas, 'celdas_4km_validas': int(g.notnull().sum()),
                      'pct_1km_en_pixeles_4km_descartados': 100 * perdidas / max(validas, 1),
                      'chl_1km_mediana_general': float(np.nanmedian(fina.values)),
                      'chl_1km_mediana_descartada': chl_perdida})
    return pd.DataFrame(filas)
