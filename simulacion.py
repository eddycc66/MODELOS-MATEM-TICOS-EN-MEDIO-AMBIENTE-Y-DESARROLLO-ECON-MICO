"""
================================================================================
SIMULACIÓN REALISTA DE INUNDACIÓN DEL RÍO PIRAÍ - VERSIÓN MEJORADA
ANIMACIÓN PROFESIONAL CON FONDO SATELITAL ESTILO GOOGLE EARTH
================================================================================

Mejoras en esta versión:
- Imagen satelital de alta calidad como fondo (Google Satellite style)
- Agua de inundación con color marrón/beige (agua turbia realista)
- Mejor contraste y visibilidad
- Texto profesional estilo TikTok/redes sociales
- Transiciones suaves entre frames

Basado en: DESBORDAMIENTO_PIRAI_COLAB.py
Versión: 6.0 - Animación Mejorada
================================================================================
"""

print("=" * 80)
print("🌊 SIMULACIÓN MEJORADA DE INUNDACIÓN - RÍO PIRAÍ")
print("=" * 80)
print("📡 Datos: CHIRPS + Sentinel-2 RGB de alta calidad")
print("🎯 Estilo: Animación profesional con fondo satelital")
print("=" * 80)

# ============================================================================
# PASO 1: INSTALACIÓN DE DEPENDENCIAS
# ============================================================================
print("\n📦 PASO 1/8: Instalando dependencias...")
!pip install earthengine-api geemap rasterio geopandas imageio matplotlib pillow scipy -q

import ee
import geemap
import numpy as np
import rasterio
from rasterio import features
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Rectangle
import imageio
import os
from datetime import datetime
from PIL import Image as PILImage
from scipy.ndimage import zoom

print("✅ Dependencias instaladas")

# ============================================================================
# PASO 2: INICIALIZACIÓN DE EARTH ENGINE
# ============================================================================
print("\n🔐 PASO 2/8: Inicializando Earth Engine...")
try:
    ee.Initialize(project='eddycc66')
    print("✅ Earth Engine inicializado")
except:
    print("⚠️  Autenticando...")
    ee.Authenticate()
    ee.Initialize(project='eddycc66')
    print("✅ Autenticación completada")

# ============================================================================
# PASO 3: CARGAR DATOS DESDE GEE
# ============================================================================
print("\n🗺️  PASO 3/8: Cargando datos desde Google Earth Engine...")

# Cargar cuenca
cuenca_fc = ee.FeatureCollection('projects/eddycc66/assets/cuenca_pirai')
cuenca_geometry = cuenca_fc.geometry()
area_cuenca_km2 = cuenca_geometry.area().getInfo() / 1e6

# Cargar río
rio_fc = ee.FeatureCollection('projects/eddycc66/assets/rio_pirai')
rio_geometry = rio_fc.geometry()

# Cargar DEM
dem_collection = ee.ImageCollection('COPERNICUS/DEM/GLO30')
dem_ee = dem_collection.select('DEM').mosaic().clip(cuenca_geometry)

# Fill sinks
dem_filled = dem_ee
for i in range(5):
    dem_filled = dem_filled.focal_max(radius=1, kernelType='square') \
                           .min(dem_filled.focal_min(radius=1, kernelType='square'))

print(f"✅ Datos geoespaciales cargados")
print(f"   📊 Área de cuenca: {area_cuenca_km2:.2f} km²")

# ============================================================================
# PASO 4: DESCARGAR IMAGEN SATELITAL DE ALTA CALIDAD
# ============================================================================
print("\n🛰️  PASO 4/8: Descargando imagen satelital de ALTA CALIDAD...")
print("   💡 Esta será la base visual de la animación")

os.makedirs('/content/datos_temp', exist_ok=True)

try:
    # Buscar la MEJOR imagen Sentinel-2 disponible
    print("   ⏳ Buscando imagen Sentinel-2 con mínima nubosidad...")

    sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR') \
        .filterBounds(cuenca_geometry) \
        .filterDate('2023-01-01', '2024-12-31') \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)) \
        .sort('CLOUDY_PIXEL_PERCENTAGE')

    n_s2_images = sentinel2.size().getInfo()

    if n_s2_images > 0:
        # Tomar la mejor imagen
        s2_image = sentinel2.first()
        cloud_pct = s2_image.get('CLOUDY_PIXEL_PERCENTAGE').getInfo()
        fecha_imagen = ee.Date(s2_image.get('system:time_start')).format('YYYY-MM-dd').getInfo()

        print(f"   ✅ Imagen encontrada: {fecha_imagen} (nubes: {cloud_pct:.1f}%)")

        # Crear composición RGB de ALTA CALIDAD
        # Usar bandas B4 (Red), B3 (Green), B2 (Blue)
        rgb = s2_image.select(['B4', 'B3', 'B2']).clip(cuenca_geometry)

        # Descargar con alta resolución
        print("   📥 Descargando imagen RGB de alta resolución...")
        print("   ⚠️  Esto puede tomar 2-3 minutos...")

        # Usar dimensiones grandes para mejor calidad
        thumb_url = rgb.getThumbURL({
            'region': cuenca_geometry,
            'dimensions': 2048,  # Alta resolución
            'min': 0,
            'max': 3000,
            'format': 'png'
        })

        import urllib.request
        urllib.request.urlretrieve(thumb_url, '/content/datos_temp/satellite_hq.png')

        # Leer imagen
        pil_img = PILImage.open('/content/datos_temp/satellite_hq.png')
        satellite_bg = np.array(pil_img)

        # Quitar canal alpha si existe
        if satellite_bg.ndim == 3 and satellite_bg.shape[2] == 4:
            satellite_bg = satellite_bg[:, :, :3]

        print(f"   ✅ Imagen satelital descargada: {satellite_bg.shape}")

        # Mejorar contraste y brillo para mejor visualización
        from PIL import ImageEnhance
        pil_img_enhanced = PILImage.fromarray(satellite_bg)

        # Aumentar contraste
        enhancer = ImageEnhance.Contrast(pil_img_enhanced)
        pil_img_enhanced = enhancer.enhance(1.2)

        # Aumentar brillo ligeramente
        enhancer = ImageEnhance.Brightness(pil_img_enhanced)
        pil_img_enhanced = enhancer.enhance(1.1)

        satellite_bg = np.array(pil_img_enhanced)
        print("   ✅ Imagen mejorada (contraste + brillo)")

    else:
        print("   ⚠️  No se encontraron imágenes Sentinel-2")
        print("   💡 Usando fondo alternativo...")
        satellite_bg = None

except Exception as e:
    print(f"   ⚠️  Error descargando imagen: {str(e)}")
    satellite_bg = None

# ============================================================================
# PASO 5: DESCARGAR DEM Y CREAR MÁSCARAS
# ============================================================================
print("\n💾 PASO 5/8: Descargando DEM y creando máscaras...")

# Descargar DEM
print("   ⏳ Descargando DEM...")
region = cuenca_geometry

try:
    dem_url = dem_filled.getDownloadURL({
        'scale': 90,
        'region': region,
        'format': 'GEO_TIFF'
    })

    import urllib.request
    urllib.request.urlretrieve(dem_url, '/content/datos_temp/dem.tif')

    # Leer DEM
    with rasterio.open('/content/datos_temp/dem.tif') as src:
        dem = src.read(1)
        transform = src.transform
        crs = src.crs
        meta = src.meta.copy()

    print(f"✅ DEM descargado: {dem.shape}")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    raise

# Crear máscaras
print("   ⏳ Creando máscaras de cuenca y río...")

from shapely.geometry import shape

# Máscara de cuenca
cuenca_geojson = cuenca_geometry.getInfo()
cuenca_geom = shape(cuenca_geojson)
cuenca_gdf = gpd.GeoDataFrame([1], geometry=[cuenca_geom], crs=crs)

cuenca_mask = features.rasterize(
    [(geom, 1) for geom in cuenca_gdf.geometry],
    out_shape=dem.shape,
    transform=transform,
    fill=0,
    dtype=np.uint8
)

# Máscara de río
rio_geojson = rio_geometry.getInfo()
rio_geom = shape(rio_geojson)
rio_gdf = gpd.GeoDataFrame([1], geometry=[rio_geom], crs=crs)

rio_mask = features.rasterize(
    [(geom, 1) for geom in rio_gdf.geometry],
    out_shape=dem.shape,
    transform=transform,
    fill=0,
    dtype=np.uint8
)

print(f"✅ Máscaras creadas")
print(f"   🌊 Píxeles de río: {np.sum(rio_mask)}")
print(f"   🗺️  Píxeles de cuenca: {np.sum(cuenca_mask)}")

# Redimensionar imagen satelital para coincidir con DEM
if satellite_bg is not None:
    if satellite_bg.shape[0] != dem.shape[0] or satellite_bg.shape[1] != dem.shape[1]:
        print(f"   ⏳ Redimensionando imagen satelital para coincidir con DEM...")
        zoom_y = dem.shape[0] / satellite_bg.shape[0]
        zoom_x = dem.shape[1] / satellite_bg.shape[1]
        satellite_bg = zoom(satellite_bg, (zoom_y, zoom_x, 1), order=1).astype(np.uint8)
        print(f"   ✅ Imagen redimensionada: {satellite_bg.shape}")

# ============================================================================
# FUNCIÓN DE PROPAGACIÓN DE INUNDACIÓN
# ============================================================================

def propagar_inundacion(dem, semillas, nivel_agua, pasos=100):
    """
    Propaga la inundación desde las semillas (río) según topografía
    """
    inundacion = np.zeros_like(dem, dtype=bool)

    # Obtener coordenadas de semillas
    y_seed, x_seed = np.where(semillas)
    puntos_activos = list(zip(y_seed, x_seed))

    # Marcar semillas como inundadas
    for y, x in puntos_activos:
        inundacion[y, x] = True

    # Propagar inundación
    for iteracion in range(pasos):
        nuevos_puntos = []

        for y, x in puntos_activos:
            # Nivel de agua en este punto
            elev_actual = dem[y, x] + nivel_agua

            # Revisar vecinos (8 direcciones)
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue

                    ny, nx = y + dy, x + dx

                    # Verificar límites
                    if 0 <= ny < dem.shape[0] and 0 <= nx < dem.shape[1]:
                        # Condiciones de inundación
                        condicion = (
                            not inundacion[ny, nx] and
                            dem[ny, nx] <= elev_actual and
                            dem[ny, nx] >= dem[y, x] - 1.0
                        )

                        if condicion:
                            inundacion[ny, nx] = True
                            nuevos_puntos.append((ny, nx))

        puntos_activos = nuevos_puntos

        if not puntos_activos:
            break

    return inundacion.astype(np.uint8)

# ============================================================================
# PASO 6: SIMULACIÓN DE INUNDACIÓN
# ============================================================================
print("\n🌊 PASO 6/8: Simulando inundación con niveles progresivos...")

OUTPUT_DIR = '/content/resultados_inundacion_mejorado'
os.makedirs(OUTPUT_DIR, exist_ok=True)
for subdir in ['rasters', 'animacion_pro']:
    os.makedirs(os.path.join(OUTPUT_DIR, subdir), exist_ok=True)

# Niveles de agua a simular (progresivos)
niveles_agua = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 7.0]

print(f"   📊 Simulando {len(niveles_agua)} niveles de agua")
print(f"   🎯 Rango: {min(niveles_agua):.1f}m a {max(niveles_agua):.1f}m")

log_data = []

for i, nivel in enumerate(niveles_agua):
    print(f"   ⏳ Nivel {nivel:.1f}m ({i+1}/{len(niveles_agua)})...")

    # Definir semillas (río)
    semillas = (rio_mask == 1)

    # Propagar inundación
    inundacion = propagar_inundacion(dem, semillas, nivel, pasos=100)

    # Aplicar máscara de cuenca
    inundacion = inundacion * cuenca_mask

    # Guardar raster
    meta_inundacion = meta.copy()
    meta_inundacion.update({'dtype': 'uint8', 'nodata': 0})

    raster_path = os.path.join(OUTPUT_DIR, 'rasters', f'inundacion_{nivel:.1f}m.tif')
    with rasterio.open(raster_path, 'w', **meta_inundacion) as dst:
        dst.write(inundacion, 1)

    # Calcular área
    area_m2 = np.sum(inundacion) * abs(transform[0] * transform[4])
    area_km2 = area_m2 / 1e6

    log_data.append({
        'Nivel_m': nivel,
        'Area_km2': area_km2,
        'Pixeles': np.sum(inundacion)
    })

print("✅ Simulación completada")

# ============================================================================
# PASO 7: CREAR ANIMACIÓN PROFESIONAL CON FONDO HD (ESTILO GOOGLE EARTH)
# ============================================================================
print("\n🎬 PASO 7/8: Creando animación PROFESIONAL HD...")
print("   🛰️  Usando fondo satelital de sub-metro (Estilo Google Earth)")
print("   🎨 Estilo: Agua turbia realista sobre fondo HD")

# Intentar importar contextily (instalado en el paso 1 si no estaba)
try:
    import contextily as ctx
    HAS_CONTEXTILY = True
except ImportError:
    print("   ⚠️  Contextily no encontrado. Instalando...")
    !pip install contextily -q
    import contextily as ctx
    HAS_CONTEXTILY = True

# Crear paleta de colores para agua turbia (marrón/beige)
# Captura el color de los sedimentos del Piraí en crecida
agua_colors = [
    (0.0, '#7B3F00'),  # Marrón chocolate (profundo)
    (0.4, '#A0522D'),  # Marrón siena
    (0.8, '#D2B48C'),  # Tan/Beige (sucio)
    (1.0, '#F5DEB3')   # Trigo (espuma/limo)
]

# Crear colormap personalizado
agua_cmap = mcolors.LinearSegmentedColormap.from_list('agua_turbia_hd',
                                                       [c[1] for c in agua_colors])

# Obtener rectángulo de la cuenca para el recorte del basemap
from shapely.geometry import mapping
cuenca_bounds = cuenca_gdf.total_bounds # [minx, miny, maxx, maxy]

for i, nivel in enumerate(niveles_agua):
    print(f"   ⏳ Generando Frame {i+1}/{len(niveles_agua)} (Nivel {nivel:.1f}m)...")

    # Cargar inundación
    raster_path = os.path.join(OUTPUT_DIR, 'rasters', f'inundacion_{nivel:.1f}m.tif')
    with rasterio.open(raster_path) as src:
        inund_data = src.read(1)
        inund_extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
        current_crs = src.crs.to_string()

    area_km2 = log_data[i]['Area_km2']

    # Crear figura de alta resolución
    fig, ax = plt.subplots(figsize=(16, 16), facecolor='black')

    # Plot de la inundación (con color turbio realista)
    inund_masked = np.ma.masked_where(inund_data == 0, inund_data)

    # Añadir un poco de ruido de textura al agua para realismo
    ny, nx = inund_data.shape
    textura = np.random.normal(0.9, 0.1, (ny, nx))
    inund_texturizada = inund_masked * textura

    # Visualizar inundación
    im = ax.imshow(inund_texturizada, cmap=agua_cmap, alpha=0.72,
                   extent=inund_extent, zorder=5)

    # Contorno del río principal (Guía visual)
    rio_gdf.plot(ax=ax, color='#1E40AF', linewidth=4, alpha=0.6, zorder=4)

    # AGREGAR FONDO SATELITAL HD (Estilo Google Earth)
    # Usamos Esri.WorldImagery porque es de sub-metro y gratuito para estos usos
    try:
        ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery,
                        crs=current_crs, attribution=False, zorder=1)
        # Añadir etiquetas de carreteras suavemente (opcional)
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.PositronOnlyLabels,
                        crs=current_crs, attribution=False, zorder=6, alpha=0.4)
    except Exception as e:
        print(f"   ⚠️ Error al cargar basemap HD: {e}")
        # Fallback a Sentinel-2 si fallase contextily
        if satellite_bg is not None:
            ax.imshow(satellite_bg, extent=inund_extent, zorder=1)

    # Ajustar límites a la cuenca
    ax.set_xlim(cuenca_bounds[0], cuenca_bounds[2])
    ax.set_ylim(cuenca_bounds[1], cuenca_bounds[3])

    # --- INTERFAZ PROFESIONAL (Estilo TikTok/News) ---

    # Franja Superior (Título)
    ax.add_patch(Rectangle((0, 0.88), 1, 0.12, transform=ax.transAxes,
                           facecolor='black', alpha=0.75, zorder=10))

    ax.text(0.5, 0.95, "SIMULACIÓN DEL RÍO PIRAÍ", transform=ax.transAxes,
           fontsize=32, fontweight='bold', color='white', ha='center', zorder=11)
    ax.text(0.5, 0.91, "ESCENARIO DE INUNDACIÓN EN SANTA CRUZ", transform=ax.transAxes,
           fontsize=20, color='#FBBF24', ha='center', zorder=11, fontweight='semibold')

    # Franja Inferior (Datos)
    ax.add_patch(Rectangle((0, 0), 1, 0.08, transform=ax.transAxes,
                           facecolor='black', alpha=0.75, zorder=10))

    status_color = 'white'
    if nivel >= 5.0: status_color = '#EF4444' # Rojo alerta
    elif nivel >= 3.0: status_color = '#F59E0B' # Naranja advertencia

    info_str = f"NIVEL: {nivel:.1f} m  |  ÁREA ESTIMADA: {area_km2:.2f} km²"
    ax.text(0.5, 0.04, info_str, transform=ax.transAxes,
           fontsize=18, color=status_color, ha='center', va='center',
           zorder=11, family='monospace', fontweight='bold')

    # Branding / Créditos
    ax.text(0.98, 0.02, "@en.estado.critico24", transform=ax.transAxes,
           fontsize=14, color='white', ha='right', va='bottom',
           alpha=0.8, zorder=11, style='italic')

    ax.text(0.02, 0.02, "Fuente: SAT PIRAÍ | Copernicus", transform=ax.transAxes,
           fontsize=10, color='gray', ha='left', va='bottom', zorder=11)

    ax.axis('off')
    plt.tight_layout(pad=0)

    # Guardar frame en alta calidad
    frame_path = os.path.join(OUTPUT_DIR, 'animacion_pro', f'frame_{i:03d}.png')
    plt.savefig(frame_path, dpi=120, bbox_inches='tight',
               facecolor='black', edgecolor='none', pad_inches=0)
    plt.close()

print("✅ Frames HD generados exitosamente")

# ============================================================================
# PASO 8: COMPILAR ANIMACIÓN FINAL
# ============================================================================
print("\n🎬 PASO 8/8: Compilando animación final...")

archivos_frames = [
    os.path.join(OUTPUT_DIR, 'animacion_pro', f'frame_{i:03d}.png')
    for i in range(len(niveles_agua))
]

gif_path = os.path.join(OUTPUT_DIR, 'SIMULACION_PIRAI_EARTH_HD.gif')

# Crear GIF con loop infinito
with imageio.get_writer(gif_path, mode='I', duration=700, loop=0) as writer:
    for archivo in archivos_frames:
        image = imageio.v2.imread(archivo)
        writer.append_data(image)

print(f"\n🚀 ¡PROCESO FINALIZADO!")
print(f"  Animación HD guardada en: {gif_path}")
print(f"🗺️  El fondo ahora es imagen satelital de alta resolución (tipo Google Earth).")

# Mostrar resultado en Colab
from IPython.display import Image, display
display(Image(filename=gif_path))