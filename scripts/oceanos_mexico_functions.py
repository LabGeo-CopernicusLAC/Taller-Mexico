"""Funciones del notebook 01_OCEANOS_ODS14_mexico.

Las celdas del notebook son cortas y la selección se hace con widgets (con respaldo manual si
ipywidgets no está disponible). El estado compartido se guarda en el diccionario ESTADO.
"""
from pathlib import Path
import json

from herramientas import *  # noqa: F401,F403  (numpy, pandas, geopandas, xarray, plt, funciones base)
from IPython.display import display, clear_output, HTML

try:
    import ipywidgets as widgets
    IPYWIDGETS_AVAILABLE = True
except ImportError:  # pragma: no cover
    widgets = None
    IPYWIDGETS_AVAILABLE = False

ESTADO = {}

MESES = [f'2024-{m:02d}' for m in range(1, 13)]
MES_SUGERIDO = {1: '2024-05', 2: '2024-08', 3: '2024-01', 4: '2024-08', 5: '2024-08'}
NOMBRES_AREA = {1: 'Baja California – Pacífico', 2: 'Golfo de California', 3: 'Pacífico sur',
                4: 'Golfo de México', 5: 'Caribe mexicano'}


# ---------------------------------------------------------------------------
# Parte 0 — preparación
# ---------------------------------------------------------------------------
def encontrar_base():
    for p in [Path.cwd().resolve(), *Path.cwd().resolve().parents]:
        if (p / 'environment.yml').exists() and (p / 'scripts').is_dir():
            return p
    raise FileNotFoundError('Abra Jupyter desde la carpeta del taller.')


def preparar_entorno(confirmar_lonlat=True):
    """Carga NetCDF, capas y valores oficiales. Tarda uno o dos minutos."""
    base = encontrar_base()
    ESTADO['BASE'] = base
    ESTADO['sst'] = mensual(abrir_producto(base / 'data/sst', 'analysed_sst', 'sst', confirmar_lonlat=confirmar_lonlat))
    ESTADO['chl'] = mensual(abrir_producto(base / 'data/chl', 'chlor_a', 'chl', confirmar_lonlat=confirmar_lonlat))
    capas = cargar_vectores(base)
    ESTADO['capas'] = capas
    ESTADO['zee'] = capas['zee']
    ESTADO['anp'] = capas['anp']
    ESTADO['anp_marinas'] = capas['anp'].loc[capas['anp']['S_MARINA'] > 0].copy()
    ESTADO['areas'] = leer_capa(base / 'data/shapes/mexico/areas_estudio.gpkg')
    ESTADO['ref'] = referencias_oficiales(base)
    ESTADO['mar'] = unary_union(capas['zee'].geometry)
    print('✅ Datos cargados')
    print(f"   SST: {ESTADO['sst'].sizes['time']} meses, grilla {ESTADO['sst'].sizes['lat']}×{ESTADO['sst'].sizes['lon']}")
    print(f"   CHL: {ESTADO['chl'].sizes['time']} meses, grilla {ESTADO['chl'].sizes['lat']}×{ESTADO['chl'].sizes['lon']}")
    print(f"   ANP federales: {len(ESTADO['anp'])} (con superficie marina: {len(ESTADO['anp_marinas'])})")
    return ESTADO


# ---------------------------------------------------------------------------
# Parte 1 — exploración del producto
# ---------------------------------------------------------------------------
def explorar_productos():
    """Inventario de los NetCDF y mapa de las cinco áreas."""
    base = ESTADO['BASE']
    inv = pd.concat([inventario_netcdf(base / 'data' / t).assign(tipo=t.upper()) for t in ['sst', 'chl']], ignore_index=True)
    display(inv[['tipo', 'archivo', 'fechas', 'inicio', 'fin', 'lat_min', 'lat_max', 'lon_min', 'lon_max', 'dlat_grados']])
    areas = ESTADO['areas'].copy()
    areas['geometry'] = areas.geometry.intersection(ESTADO['mar'])
    fig, ax = plt.subplots(figsize=(11, 6))
    ESTADO['zee'].boundary.plot(ax=ax, color='#2E8B57', linewidth=.8)
    areas.boundary.plot(ax=ax, color='#0B4F6C', linewidth=1.4)
    for _, r in ESTADO['areas'].iterrows():
        c = r.geometry.centroid
        ax.text(c.x, c.y, str(r.id_area), fontsize=14, weight='bold', color='#0B4F6C', ha='center')
    ax.set(xlim=(-121, -85), ylim=(13, 33.5), xlabel='Longitud (°)', ylabel='Latitud (°)',
           title='Cinco áreas de trabajo (recortadas a la ZEE) y huella de los datos 2024')
    ax.add_patch(plt.Rectangle((-120.14, 13.82), 34.26, 18.7, fill=False, ls='--', color='grey'))
    fig.tight_layout(); plt.show()
    tabla = ESTADO['areas'].drop(columns='geometry').copy()
    tabla['nombre'] = tabla.id_area.map(NOMBRES_AREA)
    display(tabla[['id_area', 'nombre', 'poem_referencia']])


# ---------------------------------------------------------------------------
# Parte 2 — selección de área (widget)
# ---------------------------------------------------------------------------
def aplicar_seleccion(id_area, grupo, mostrar=True):
    """Fija el área y el grupo. La usan el widget y el modo manual."""
    grupo = str(grupo).strip().replace(' ', '_') or 'grupo_01'
    if not grupo.replace('_', '').isalnum():
        raise ValueError('Nombre de grupo: solo letras, números y guion bajo')
    a = ESTADO['areas'].loc[ESTADO['areas'].id_area == int(id_area)]
    if len(a) != 1:
        raise ValueError('Área inexistente')
    region = a.geometry.iloc[0].intersection(ESTADO['mar'])
    base = ESTADO['BASE']
    ESTADO.update(id_area=int(id_area), grupo=grupo, region=region, ventana=a.geometry.iloc[0],
                  nombre_area=NOMBRES_AREA[int(id_area)], poem=a.poem_referencia.iloc[0],
                  mes=ESTADO.get('mes') or MES_SUGERIDO[int(id_area)],
                  FIG=base / 'outputs/figures' / grupo, TAB=base / 'outputs/tables' / grupo)
    ESTADO['FIG'].mkdir(parents=True, exist_ok=True); ESTADO['TAB'].mkdir(parents=True, exist_ok=True)
    if mostrar:
        print(f"✅ Área {id_area}: {ESTADO['nombre_area']} · grupo «{grupo}»")
        print(f"   POEM de referencia (aproximada): {ESTADO['poem']}")
        mapa_area()
    return ESTADO


def launch_seleccion_area(id_area_inicial=4, grupo_inicial='grupo_01'):
    """Desplegables de área y grupo con botón de confirmación.
    La selección inicial queda aplicada aunque no se pulse el botón."""
    aplicar_seleccion(id_area_inicial, grupo_inicial, mostrar=False)
    if not IPYWIDGETS_AVAILABLE:
        print('ℹ️ ipywidgets no disponible: use aplicar_seleccion(id_area, grupo) en una celda.')
        return aplicar_seleccion(id_area_inicial, grupo_inicial)
    area_w = widgets.Dropdown(options=[(f'{k} · {v}', k) for k, v in NOMBRES_AREA.items()], value=id_area_inicial,
                              description='Área:', layout=widgets.Layout(width='95%'), style={'description_width': '120px'})
    grupo_w = widgets.Text(value=grupo_inicial, description='Grupo:', layout=widgets.Layout(width='95%'),
                           style={'description_width': '120px'})
    boton = widgets.Button(description='Confirmar área', button_style='success', icon='check', layout=widgets.Layout(width='190px'))
    salida = widgets.Output()

    def confirmar(_=None):
        with salida:
            clear_output(wait=True)
            ESTADO['mes'] = MES_SUGERIDO[area_w.value]
            aplicar_seleccion(area_w.value, grupo_w.value)

    boton.on_click(confirmar)
    ESTADO['_widgets_area'] = (area_w, grupo_w, boton, salida)
    display(widgets.VBox([widgets.HTML('<b>Selección del área de trabajo</b><br>Elija el área y escriba el nombre del grupo; luego confirme.'),
                          area_w, grupo_w, widgets.HBox([boton]), salida]))
    with salida:
        aplicar_seleccion(id_area_inicial, grupo_inicial)
    return None


# ---------------------------------------------------------------------------
# Modo sin internet
# ---------------------------------------------------------------------------
HOSTS_PRUEBA = [('tile.openstreetmap.org', 443), ('cdn.jsdelivr.net', 443)]


def hay_internet(timeout=3):
    """Comprueba si se alcanzan el servidor de mapas y la CDN que usa Folium."""
    import socket
    for host, puerto in HOSTS_PRUEBA:
        try:
            socket.create_connection((host, puerto), timeout=timeout).close()
        except OSError:
            return False
    return True


def configurar_conexion(sin_internet=None):
    """Define el modo de trabajo. None = detectar; True = forzar sin internet; False = forzar con internet."""
    if sin_internet is None:
        sin_internet = not hay_internet()
        origen = 'detectado automáticamente'
    else:
        origen = 'fijado a mano'
    ESTADO['sin_internet'] = bool(sin_internet)
    if ESTADO['sin_internet']:
        print(f'📴 Modo SIN internet ({origen}).')
        print('   · El mapa interactivo (Folium + OpenStreetMap) se sustituye por un mapa estático con las ANP rotuladas.')
        print('   · Todo lo demás funciona igual: los datos, los menús, el visor y la calculadora son locales.')
        print('   · El logo del encabezado no se verá: es una imagen web.')
    else:
        print(f'🌐 Modo CON internet ({origen}): se usará el mapa interactivo con fondo de OpenStreetMap.')
    return ESTADO['sin_internet']


def mapa_area():
    """Mapa interactivo si hay internet; si no, mapa estático equivalente."""
    if 'sin_internet' not in ESTADO:
        configurar_conexion()
    if ESTADO['sin_internet']:
        return mapa_estatico_area()
    return mapa_interactivo_area()


def mapa_estatico_area():
    """Mapa sin internet: área ∩ ZEE, costa (borde de la ZEE) y ANP marinas rotuladas."""
    region = ESTADO['region']
    anp = ESTADO['anp_marinas'][ESTADO['anp_marinas'].intersects(region)].copy()
    x0, y0, x1, y1 = region.bounds
    fig, ax = plt.subplots(figsize=(10, 7))
    gpd.GeoSeries([region], crs=4326).plot(ax=ax, color='#EEF5FC', edgecolor='#0B4F6C', linewidth=1.2)
    ESTADO['zee'].boundary.plot(ax=ax, color='#5B6B7A', linewidth=0.5)
    if len(anp):
        anp.plot(ax=ax, column='CAT_MANEJO', categorical=True, alpha=0.55, edgecolor='#1B2A3A', linewidth=0.6,
                 legend=True, legend_kwds={'title': 'Categoría de manejo', 'loc': 'lower left', 'fontsize': 8})
        tabla = anp[['NOMBRE', 'CAT_MANEJO', 'superficie_marina_reportada_km2']].copy()
        tabla = tabla.sort_values('superficie_marina_reportada_km2', ascending=False).reset_index(drop=True)
        tabla.index = tabla.index + 1
        for i, (_, r) in enumerate(anp.loc[anp.superficie_marina_reportada_km2.sort_values(ascending=False).index].iterrows(), start=1):
            p = r.geometry.representative_point()
            if x0 <= p.x <= x1 and y0 <= p.y <= y1:
                ax.annotate(str(i), (p.x, p.y), fontsize=9, weight='bold', ha='center', color='#1B2A3A',
                            bbox=dict(boxstyle='circle,pad=0.2', fc='white', ec='#1B2A3A', lw=0.5))
    ax.set(xlim=(x0 - 0.3, x1 + 0.3), ylim=(y0 - 0.3, y1 + 0.3), xlabel='Longitud (°)', ylabel='Latitud (°)',
           title=f"Área {ESTADO['id_area']}: {ESTADO['nombre_area']} · ANP con superficie marina (mapa sin internet)")
    fig.tight_layout(); fig.savefig(ESTADO['FIG'] / '02_mapa_area_sin_internet.png', dpi=200); plt.show()
    if len(anp):
        print('Números del mapa:')
        display(tabla.rename(columns={'NOMBRE': 'ANP', 'CAT_MANEJO': 'Categoría', 'superficie_marina_reportada_km2': 'Superficie marina (km²)'}).round(0))
    return None


def mapa_interactivo_area():
    """Mapa Folium de la ventana ∩ ZEE con las ANP marinas (requiere internet para el fondo)."""
    try:
        import folium
    except ImportError:
        print('Folium no disponible: se muestra el mapa estático.')
        return mapa_estatico_area()
    region = gpd.GeoDataFrame({'nombre': [ESTADO['nombre_area']]}, geometry=[ESTADO['region']], crs=4326)
    anp = ESTADO['anp_marinas'][ESTADO['anp_marinas'].intersects(ESTADO['region'])].copy()
    anp['geometry'] = anp.geometry.simplify(0.005)
    region['geometry'] = region.geometry.simplify(0.01)
    x0, y0, x1, y1 = ESTADO['region'].bounds
    m = folium.Map(location=[(y0 + y1) / 2, (x0 + x1) / 2], zoom_start=6, tiles='OpenStreetMap', control_scale=True)
    folium.GeoJson(region.to_json(), name='Área (ventana ∩ ZEE)',
                   style_function=lambda f: {'color': '#0B4F6C', 'weight': 2, 'fillOpacity': 0.05}).add_to(m)
    if len(anp):
        cols = ['NOMBRE', 'CAT_MANEJO', 'superficie_marina_reportada_km2']
        folium.GeoJson(anp[cols + ['geometry']].to_json(), name='ANP con superficie marina',
                       style_function=lambda f: {'color': '#2E8B57', 'weight': 1.5, 'fillOpacity': 0.35},
                       tooltip=folium.GeoJsonTooltip(fields=cols, aliases=['ANP:', 'Categoría:', 'Superficie marina (km²):'])).add_to(m)
    folium.LayerControl().add_to(m)
    m.fit_bounds([[y0, x0], [y1, x1]])
    display(m)
    return m


# ---------------------------------------------------------------------------
# Parte 3 — ODS 14.1.1
# ---------------------------------------------------------------------------
def dibujar_mes(variable, mes):
    d = ESTADO['sst'] if variable == 'SST' else ESTADO['chl']
    fecha = pd.Timestamp(mes)
    if fecha not in pd.to_datetime(d.time.values):
        print(variable, ': mes no disponible'); return
    mapa_raster(d.sel(time=fecha), ESTADO['region'], f"{variable} {mes} · área {ESTADO['id_area']}",
                ESTADO['FIG'] / f'03_{variable}_{mes}.png', log=(variable == 'CHL'))


def launch_visor_mensual():
    """Visor de mapas mensuales: variable y mes con desplegables."""
    if not IPYWIDGETS_AVAILABLE:
        for v in ['SST', 'CHL']:
            dibujar_mes(v, ESTADO['mes'])
        return None
    var_w = widgets.ToggleButtons(options=['SST', 'CHL'], value='SST', description='Variable:')
    mes_w = widgets.SelectionSlider(options=MESES, value=ESTADO['mes'], description='Mes:', continuous_update=False,
                                    layout=widgets.Layout(width='70%'))
    salida = widgets.Output()

    def redibujar(_=None):
        ESTADO['mes'] = mes_w.value
        with salida:
            clear_output(wait=True)
            dibujar_mes(var_w.value, mes_w.value)

    var_w.observe(redibujar, names='value'); mes_w.observe(redibujar, names='value')
    ESTADO['_widgets_visor'] = (var_w, mes_w, salida)
    display(widgets.VBox([widgets.HTML(f"<b>Visor mensual</b> · mes sugerido para esta área: {MES_SUGERIDO[ESTADO['id_area']]}"),
                          var_w, mes_w, salida]))
    redibujar()
    return None


def run_series_14_1_1():
    rs = resumen(ESTADO['sst'], ESTADO['region'], 'SST'); rc = resumen(ESTADO['chl'], ESTADO['region'], 'CHL')
    ESTADO['series'] = pd.concat([rs, rc], ignore_index=True)
    ESTADO['series'].to_csv(ESTADO['TAB'] / '03_series_SST_CHL.csv', index=False)
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    for ax, r, et in zip(axes, [rs, rc], ['SST (°C)', 'CHL (mg m⁻³)']):
        ax.plot(r.fecha, r['media'], marker='o', label='media espacial')
        ax.plot(r.fecha, r['mediana'], ls='--', label='mediana espacial')
        ax.set_ylabel(et); ax.legend()
    axes[1].set_yscale('log')
    fig.suptitle(f"Ciclo anual 2024 · área {ESTADO['id_area']}"); fig.tight_layout(); fig.savefig(ESTADO['FIG'] / '03_series.png', dpi=200); plt.show()
    chlconc = rc[['fecha', 'media', 'mediana', 'cobertura_pct']].rename(columns={'media': 'media_mg_m3', 'mediana': 'mediana_mg_m3'})
    chlconc['media_mg_L'] = chlconc.media_mg_m3 / 1000
    chlconc.to_csv(ESTADO['TAB'] / '03_EN_MAR_CHLCONC_componente.csv', index=False)
    ESTADO['CHL_ANUAL'] = float(rc['media'].mean())
    print(f"CHL media 2024 (media de 12 meses): {ESTADO['CHL_ANUAL']:.3f} mg m⁻³ = {ESTADO['CHL_ANUAL'] / 1000:.6f} mg L⁻¹")
    print(f'Cobertura mínima del campo: {rc.cobertura_pct.min():.1f} % · producto L4: puede incluir relleno')
    return ESTADO['series']


def run_4km():
    chl4, frac4 = agregar_grilla_occi(ESTADO['chl'], ESTADO['region'])
    comp = comparar_1km_4km(ESTADO['chl'], chl4, frac4, ESTADO['region'])
    comp.to_csv(ESTADO['TAB'] / '03_CHL_1km_vs_4km.csv', index=False)
    ESTADO['comp_4km'] = comp
    print(f"Media anual: {comp.chl_1km_media.mean():.3f} mg m⁻³ a ~1 km · {comp.chl_4km_media.mean():.3f} mg m⁻³ a 4 km")
    print(f"Celdas de ~1 km que caen en píxeles de 4 km descartados: {comp.pct_1km_en_pixeles_4km_descartados.mean():.2f} %")
    print(f"Mediana de CHL en esas celdas: {comp.chl_1km_mediana_descartada.mean():.2f} mg m⁻³ "
          f"frente a {comp.chl_1km_mediana_general.mean():.2f} mg m⁻³ en toda el área")
    from matplotlib.colors import LogNorm
    t = pd.Timestamp(ESTADO['mes'])
    fina = recortar(ESTADO['chl'], ESTADO['region']).sel(time=t)
    gruesa = chl4.sel(time=t)
    vmin, vmax = float(fina.quantile(0.02)), float(fina.quantile(0.98))
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharex=True, sharey=True)
    for ax, d, titulo in [(axes[0], fina, '~1 km (CopernicusLAC)'), (axes[1], gruesa, '4 km (grilla OC-CCI)')]:
        d.plot(ax=ax, cmap='viridis', norm=LogNorm(vmin=vmin, vmax=vmax), add_colorbar=(ax is axes[1]))
        ax.set_title(f"CHL {ESTADO['mes']} · {titulo}")
    fig.tight_layout(); fig.savefig(ESTADO['FIG'] / f"03_CHL_1km_vs_4km_{ESTADO['mes']}.png", dpi=200); plt.show()
    return comp


def show_referencia_onu_14_1_1():
    ref = ESTADO['ref']
    dev = ref[ref.serie == 'EN_MAR_CHLDEV']
    anm = ref[ref.serie == 'EN_MAR_CHLANM'].pivot(index='anio', columns='desglose', values='valor')
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(dev.anio, dev.valor, marker='o'); axes[0].set(title='EN_MAR_CHLDEV · México', ylabel='%', xlabel='año')
    anm.plot(kind='bar', ax=axes[1]); axes[1].set(title='EN_MAR_CHLANM · México por frecuencia', ylabel='%', xlabel='año')
    fig.tight_layout(); fig.savefig(ESTADO['FIG'] / '03_referencia_ONU_14_1_1.png', dpi=200); plt.show()
    print('Último valor CHLDEV:', int(dev.anio.max()), '→', round(float(dev.loc[dev.anio.idxmax(), 'valor']), 2), '%')


# ---------------------------------------------------------------------------
# Parte 4 — ODS 14.5.1
# ---------------------------------------------------------------------------
def run_reproduccion_siods():
    ref = ESTADO['ref']
    num = serie_numerador_siods(ESTADO['anp'])
    siods_ha = ref[ref.serie == 'SIODS_14.5.1_numerador'][['anio', 'valor']].rename(columns={'valor': 'SIODS_ha'})
    siods_pct = ref[ref.serie == 'SIODS_14.5.1_pct'][['anio', 'valor']].rename(columns={'valor': 'SIODS_pct'})
    comp = siods_ha.merge(num, on='anio', how='left').merge(siods_pct, on='anio')
    comp['S_MARINA_ha'] = comp.S_MARINA_ha.ffill()
    comp['diferencia_ha'] = comp.S_MARINA_ha - comp.SIODS_ha
    comp['ZEE_implicita_km2'] = comp.SIODS_ha / 100 / (comp.SIODS_pct / 100)
    comp.to_csv(ESTADO['TAB'] / '04_reproduccion_SIODS_14_5_1.csv', index=False)
    ESTADO['ZEE_SIODS_KM2'] = float(comp.ZEE_implicita_km2.median())
    ESTADO['geo_nacional'] = cobertura_geometrica(ESTADO['anp'], ESTADO['zee'])
    display(comp[['anio', 'SIODS_ha', 'S_MARINA_ha', 'diferencia_ha', 'SIODS_pct']].tail(10).rename(columns={'anio': 'año'}))
    print('Diferencia máxima del numerador:', round(comp.diferencia_ha.abs().max(), 1), 'ha')
    print(f"ZEE implícita en el SIODS: {ESTADO['ZEE_SIODS_KM2']:,.0f} km² (constante en toda la serie)")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(comp.anio, comp.S_MARINA_ha / 100 / ESTADO['ZEE_SIODS_KM2'] * 100, lw=3, alpha=.5, label='reproducido (CONANP / ZEE implícita)')
    ax.plot(siods_pct.anio, siods_pct.SIODS_pct, marker='o', ms=3, label='publicado SIODS (INEGI)')
    mpa = ref[ref.serie == 'ER_MRN_MPA']; ax.plot(mpa.anio, mpa.valor, ls='--', label='ONU ER_MRN_MPA (método KBA)')
    ax.axhline(10, color='grey', lw=.8); ax.text(1994, 11, 'meta 14.5: 10 %', color='grey')
    ax.set(ylabel='%', title='ODS 14.5.1 · México'); ax.legend(); fig.tight_layout()
    fig.savefig(ESTADO['FIG'] / '04_serie_14_5_1.png', dpi=200); plt.show()
    return comp


def calcular_14_5_1(numerador_km2, denominador_km2):
    pct = 100 * numerador_km2 / denominador_km2
    ref = ESTADO['ref']
    oficial = float(ref[(ref.serie == 'SIODS_14.5.1_pct') & (ref.anio == 2024)].valor.iloc[0])
    global_ = float(ref[(ref.serie == 'ER_MRN_MPA') & (ref.anio == 2024)].valor.iloc[0])
    print(f'Resultado: {numerador_km2:,.0f} / {denominador_km2:,.0f} km² = {pct:.2f} %')
    print(f'SIODS 2024 (oficial nacional): {oficial:.2f} % · diferencia {pct - oficial:+.2f} puntos')
    print(f'ONU ER_MRN_MPA 2024 (método KBA, otra pregunta): {global_:.2f} %')
    ESTADO['calculo_14_5_1'] = {'numerador_km2': numerador_km2, 'denominador_km2': denominador_km2, 'pct': pct}
    return pct


def launch_calculadora_14_5_1():
    """Calculadora interactiva: el grupo elige numerador y denominador y compara con el SIODS."""
    s_marina = ESTADO['anp']['S_MARINA'].sum() / 100
    geo = ESTADO['geo_nacional']
    numeradores = [(f'Atributo S_MARINA de CONANP ({s_marina:,.0f} km²)', s_marina),
                   (f"Geometría ANP ∩ ZEE ({geo['protegido_km2']:,.0f} km²)", geo['protegido_km2'])]
    denominadores = [(f"ZEE implícita en el SIODS, CONABIO ({ESTADO['ZEE_SIODS_KM2']:,.0f} km²)", ESTADO['ZEE_SIODS_KM2']),
                     (f"ZEE Marine Regions v12 ({geo['dominio_km2']:,.0f} km²)", geo['dominio_km2'])]
    if not IPYWIDGETS_AVAILABLE:
        for (tn, n) in numeradores:
            for (td, d) in denominadores:
                print('·', tn, '/', td); calcular_14_5_1(n, d)
        return None
    num_w = widgets.Dropdown(options=numeradores, value=s_marina, description='Numerador:',
                             layout=widgets.Layout(width='95%'), style={'description_width': '120px'})
    den_w = widgets.Dropdown(options=denominadores, value=ESTADO['ZEE_SIODS_KM2'], description='Denominador:',
                             layout=widgets.Layout(width='95%'), style={'description_width': '120px'})
    manual_w = widgets.FloatText(value=0.0, description='Otro denominador (km², 0 = no usar):',
                                 layout=widgets.Layout(width='60%'), style={'description_width': '260px'})
    boton = widgets.Button(description='Calcular 14.5.1', button_style='primary', icon='calculator', layout=widgets.Layout(width='190px'))
    salida = widgets.Output()

    def calcular(_=None):
        with salida:
            clear_output(wait=True)
            den = manual_w.value if manual_w.value > 0 else den_w.value
            calcular_14_5_1(num_w.value, den)

    boton.on_click(calcular)
    ESTADO['_widgets_calc'] = (num_w, den_w, manual_w, boton, salida)
    display(widgets.VBox([widgets.HTML('<b>Calculadora del 14.5.1 nacional</b><br>Combine numerador y denominador y compare con el valor oficial.'),
                          num_w, den_w, manual_w, widgets.HBox([boton]), salida]))
    calcular()
    return None


def run_categorias_y_area():
    cat = cobertura_por_categoria(ESTADO['anp'], ESTADO['zee'])
    cat.to_csv(ESTADO['TAB'] / '04_14_5_1_por_categoria.csv', index=False)
    ESTADO['cat'] = cat
    display(cat.round(2))
    ven = cobertura_geometrica(ESTADO['anp'], gpd.GeoDataFrame(geometry=[ESTADO['region']], crs=4326))
    ESTADO['ven'] = ven
    print(f"Área {ESTADO['id_area']}: {ven['protegido_km2']:,.0f} km² protegidos de {ven['dominio_km2']:,.0f} km² de ZEE = {ven['cobertura_pct']:.1f} %")
    protegida = ESTADO['region'].intersection(unary_union(ESTADO['anp_marinas'].geometry))
    filas = []
    for clase, geom in [('dentro de ANP marinas', protegida), ('resto del área', ESTADO['region'].difference(protegida))]:
        if geom.is_empty:
            continue
        for nombre, d in [('SST', ESTADO['sst']), ('CHL', ESTADO['chl'])]:
            try:
                r = resumen(d, geom, nombre); r['clase'] = clase; filas.append(r)
            except ValueError as e:
                print(e)
    if filas:
        ctx = pd.concat(filas, ignore_index=True)
        ctx.to_csv(ESTADO['TAB'] / '04_contexto_SST_CHL_ANP.csv', index=False)
        display(ctx.groupby(['variable', 'clase'])['media'].agg(['mean', 'min', 'max']).round(3))
    print('Una diferencia dentro/fuera describe ubicación (costa, profundidad), no efecto de la protección.')
    return cat


# ---------------------------------------------------------------------------
# Parte 5 — ODS 14.2.1 y ficha
# ---------------------------------------------------------------------------
def run_14_2_1():
    ref = ESTADO['ref']
    display(ref[ref.ods == '14.2.1'][['anio', 'valor', 'desglose']].rename(columns={'anio': 'año'}))
    s = ESTADO['series']
    filas = []
    for var, r in s.groupby('variable'):
        filas.append({'variable': var, 'mes_min': r.loc[r['media'].idxmin(), 'fecha'].strftime('%Y-%m'), 'min': r['media'].min(),
                      'mes_max': r.loc[r['media'].idxmax(), 'fecha'].strftime('%Y-%m'), 'max': r['media'].max(),
                      'amplitud': r['media'].max() - r['media'].min()})
    estac = pd.DataFrame(filas).set_index('variable')
    estac.to_csv(ESTADO['TAB'] / '05_estacionalidad_region_POEM.csv')
    print(f"Área {ESTADO['id_area']} ≈ {ESTADO['poem']} (aproximación: la ventana no es el polígono oficial del POEM)")
    display(estac.round(3))
    return estac


def exportar_ficha(interpretacion=''):
    ref = ESTADO['ref']
    v = lambda s, y: float(ref[(ref.serie == s) & (ref.anio == y)].valor.iloc[0])
    geo, ven = ESTADO['geo_nacional'], ESTADO['ven']
    ficha = pd.DataFrame([
        {'ODS': '14.1.1', 'serie': 'EN_MAR_CHLDEV', 'valor_oficial': f"{v('EN_MAR_CHLDEV', 2022):.2f} % (2022)", 'fuente_oficial': 'ONU, nivel 1 global',
         'resultado_grupo': 'no calculable: otro producto y sin referencia 2000–2004', 'tipo': 'indicador oficial'},
        {'ODS': '14.1.1', 'serie': 'EN_MAR_CHLCONC', 'valor_oficial': 'sin dato nacional', 'fuente_oficial': 'SIODS no publica 14.1.1',
         'resultado_grupo': f"{ESTADO['CHL_ANUAL']:.3f} mg m⁻³ ({ESTADO['CHL_ANUAL'] / 1000:.6f} mg L⁻¹), área {ESTADO['id_area']}, 2024",
         'tipo': 'componente; estimación CopernicusLAC no validada'},
        {'ODS': '14.2.1', 'serie': 'EN_SCP_ECSYBA', 'valor_oficial': '1 (sí), cuatro POEM', 'fuente_oficial': 'ONU; SIODS no lo publica',
         'resultado_grupo': f"contexto ambiental de {ESTADO['poem']}", 'tipo': 'contexto; no entra en el cálculo'},
        {'ODS': '14.5.1', 'serie': 'SIODS nacional', 'valor_oficial': f"{v('SIODS_14.5.1_pct', 2024):.2f} % (2024)", 'fuente_oficial': 'SIODS-INEGI (SEMARNAT)',
         'resultado_grupo': f"numerador CONANP reproducido (±0,4 ha); geometría ∩ ZEE Marine Regions = {geo['cobertura_pct']:.2f} %",
         'tipo': 'reproducción del método nacional'},
        {'ODS': '14.5.1', 'serie': 'ER_MRN_MPA', 'valor_oficial': f"{v('ER_MRN_MPA', 2024):.2f} % (2024)", 'fuente_oficial': 'ONU (BirdLife, IUCN, UNEP-WCMC)',
         'resultado_grupo': 'no reproducido: falta clasificación Marine KBA y OECM', 'tipo': 'indicador oficial global'},
        {'ODS': '14.5.1', 'serie': 'cobertura en el área', 'valor_oficial': '—', 'fuente_oficial': '—',
         'resultado_grupo': f"{ven['cobertura_pct']:.1f} % de la ZEE del área {ESTADO['id_area']}", 'tipo': 'desagregación docente'}])
    tab = ESTADO['TAB']
    ficha.to_csv(tab / '05_ficha_ODS14.csv', index=False)
    with pd.ExcelWriter(tab / '05_ficha_ODS14.xlsx') as w:
        ficha.to_excel(w, sheet_name='Ficha', index=False)
        ESTADO['series'].to_excel(w, sheet_name='SST_CHL_2024', index=False)
        ESTADO['cat'].to_excel(w, sheet_name='14.5.1_categorias', index=False)
        if 'comp_4km' in ESTADO:
            ESTADO['comp_4km'].to_excel(w, sheet_name='CHL_1km_vs_4km', index=False)
    (tab / '05_interpretacion.md').write_text(interpretacion, encoding='utf-8')
    (tab / 'trazabilidad.json').write_text(json.dumps({'grupo': ESTADO['grupo'], 'id_area': ESTADO['id_area'], 'area': ESTADO['nombre_area'],
        'mes_mapa': ESTADO['mes'], 'netcdf': [p.name for p in sorted((ESTADO['BASE'] / 'data').rglob('*.nc'))],
        'referencias': 'data/ods/referencias_oficiales_ods14.csv'}, ensure_ascii=False, indent=2))
    display(ficha)
    print('Salidas en', tab.relative_to(ESTADO['BASE']), 'y', ESTADO['FIG'].relative_to(ESTADO['BASE']))
    return ficha


# ---------------------------------------------------------------------------
# Anexo (opcional)
# ---------------------------------------------------------------------------
def anexo_procedencia_chl():
    origen = diagnostico_origen_chl(ESTADO['BASE'] / 'data/chl', ESTADO['region'], True)
    display(origen if not origen.empty else 'El archivo no trae source_of_chl')


def _kba_desde_descarga(base):
    """Busca en data/descargas la base KBA descargada por la persona usuaria
    (ZIP o shapefile), extrae México y guarda data/shapes/mexico/kba_mexico.gpkg."""
    import tempfile, zipfile
    carpeta = Path(base) / 'data/descargas'
    if not carpeta.exists():
        return None
    candidatos = sorted(carpeta.rglob('*.shp')) + sorted(carpeta.rglob('*.zip'))
    with tempfile.TemporaryDirectory() as tmp:
        shp = None
        for c in candidatos:
            if c.suffix == '.shp' and 'pnt' not in c.stem.lower():
                shp = c; break
            if c.suffix == '.zip':
                with zipfile.ZipFile(c) as z:
                    nombres = [n for n in z.namelist() if n.lower().endswith('.shp') and 'pnt' not in n.lower()]
                    if not nombres:
                        continue
                    stem = nombres[0][:-4]
                    for n in z.namelist():
                        if n.startswith(stem) and '..' not in n:
                            z.extract(n, tmp)
                    shp = Path(tmp) / nombres[0]; break
        if shp is None:
            return None
        print(f'Leyendo {shp.name} (puede tardar un poco si es la base mundial)...')
        try:
            k = gpd.read_file(shp, where="ISO3 = 'MEX'")
        except Exception:
            k = gpd.read_file(shp)
            k = k[k['ISO3'] == 'MEX']
    if k.empty or 'SitRecID' not in k:
        print('⚠️ El archivo no tiene KBA de México o le falta el campo SitRecID.')
        return None
    k = k.to_crs(4326)
    k['geometry'] = k.geometry.make_valid()
    k['kba_id'] = k['SitRecID'].astype(str)
    salida = Path(base) / 'data/shapes/mexico/kba_mexico.gpkg'
    k.to_file(salida, layer='kba_mexico', driver='GPKG')
    print(f'✅ {len(k)} KBA de México guardadas en data/shapes/mexico/kba_mexico.gpkg')
    return k


def anexo_diagnostico_kba():
    capas = ESTADO['capas']
    if 'kba_mexico' not in capas:
        k = _kba_desde_descarga(ESTADO['BASE'])
        if k is None:
            print('ℹ️ Este anexo necesita las KBA, que no se incluyen en el paquete por sus términos de uso.')
            print('   Descárgalas como indica DATOS_Y_LICENCIAS.md («Datos que debes descargar tú»),')
            print('   pon el ZIP en la carpeta data/descargas y vuelve a ejecutar esta celda.')
            return None
        capas['kba_mexico'] = leer_capa(ESTADO['BASE'] / 'data/shapes/mexico/kba_mexico.gpkg')
    pa = capas.get('pa', capas.get('anp'))  # pa = ANP federales CONANP
    k, inter, u, media_kba = cobertura_kba(capas['kba_mexico'], pa, capas.get('oecm'))
    sel = k[k.intersects(ESTADO['region'])]
    sel.drop(columns='geometry').to_csv(ESTADO['TAB'] / '06_diagnostico_KBA_ANP.csv', index=False)
    print(f'Media de cobertura, {len(k)} KBA (terrestres y marinas): {media_kba:.1f} % · KBA en el área: {len(sel)}')
    print('Diagnóstico geométrico; no es el indicador 14.5.1.')
