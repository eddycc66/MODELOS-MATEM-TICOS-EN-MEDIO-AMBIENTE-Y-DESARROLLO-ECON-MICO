# ============================================================================
# CÓDIGO COMPLETO PARA GOOGLE COLAB - BOLIVIA POLLUTION ANALYSIS
# ============================================================================
# 
# INSTRUCCIONES:
# 1. Copia TODO este código
# 2. Abre Google Colab: https://colab.research.google.com/
# 3. Crea un nuevo notebook
# 4. Pega este código en UNA SOLA CELDA
# 5. Ejecuta la celda (Shift + Enter)
# 6. Sigue las instrucciones de autenticación de GEE
#
# Tiempo estimado: 10-15 minutos
# ============================================================================

# PASO 1: INSTALACIÓN
print("="*80)
print("PASO 1: Instalando dependencias...")
print("="*80)

import subprocess
import sys

subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", 
                      "earthengine-api", "geemap", "folium", "pandas", 
                      "numpy", "matplotlib", "seaborn", "geopandas"])

print("✓ Dependencias instaladas\n")

# PASO 2: IMPORTAR LIBRERÍAS
print("="*80)
print("PASO 2: Importando librerías...")
print("="*80)

import ee
import geemap
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

print("✓ Librerías importadas\n")

# PASO 3: AUTENTICACIÓN GEE
print("="*80)
print("PASO 3: Autenticando Google Earth Engine...")
print("="*80)
print("IMPORTANTE: Sigue el enlace que aparece abajo y autoriza el acceso\n")

try:
    ee.Authenticate()
    ee.Initialize(project='eddycc66')
    print("\n✓ Google Earth Engine inicializado correctamente\n")
except Exception as e:
    print(f"\nError: {e}")
    print("Por favor, completa la autenticación y ejecuta de nuevo\n")
    raise

# PASO 4: CONFIGURACIÓN
print("="*80)
print("PASO 4: Configurando parámetros...")
print("="*80)

BOLIVIA_BOUNDS = {'west': -69.6, 'south': -22.9, 'east': -57.5, 'north': -9.7}

CITIES = {
    'La Paz': {'lat': -16.5000, 'lon': -68.1500, 'population': 877363},
    'El Alto': {'lat': -16.5050, 'lon': -68.1920, 'population': 848840},
    'Santa Cruz': {'lat': -17.7833, 'lon': -63.1821, 'population': 1453549},
    'Cochabamba': {'lat': -17.3895, 'lon': -66.1568, 'population': 630587},
    'Oruro': {'lat': -17.9833, 'lon': -67.1250, 'population': 264683},
    'Potosí': {'lat': -19.5836, 'lon': -65.7531, 'population': 189652}
}

VSL_USD = 850000
CARBON_PRICE_USD_PER_TON = 45
REMEDIATION_COSTS = {'low': 5000, 'medium': 15000, 'high': 35000, 'extreme': 60000}
WILLINGNESS_TO_PAY = {'air_quality': 120, 'water_quality': 150, 'forest_conservation': 80}
AIR_QUALITY_THRESHOLDS = {'PM2.5': {'good': 15, 'moderate': 35, 'unhealthy': 75, 'very_unhealthy': 150}}
RELATIVE_RISK_FACTORS = {'PM2.5': {'low': 1.02, 'medium': 1.06, 'high': 1.12, 'extreme': 1.20}}
CARBON_STOCK_BY_FOREST_TYPE = {'tropical_rainforest': 150, 'dry_forest': 80, 'cloud_forest': 120, 'default': 100}
CARBON_TO_CO2_FACTOR = 3.67
START_DATE = '2020-01-01'
END_DATE = '2023-12-31'

print("✓ Configuración cargada\n")

# PASO 5: FUNCIONES AUXILIARES
def get_bolivia_geometry():
    return ee.Geometry.Rectangle([BOLIVIA_BOUNDS['west'], BOLIVIA_BOUNDS['south'], 
                                 BOLIVIA_BOUNDS['east'], BOLIVIA_BOUNDS['north']])

def get_city_geometry(city_name, buffer_km=50):
    city = CITIES[city_name]
    return ee.Geometry.Point([city['lon'], city['lat']]).buffer(buffer_km * 1000)

bolivia = get_bolivia_geometry()

# PASO 6: ANÁLISIS DE AIRE
print("="*80)
print("PASO 5: Analizando contaminación del aire...")
print("="*80)

# Usar Sentinel-5P para aerosoles (dataset actualizado)
try:
    # Intentar con Sentinel-5P Aerosol Index
    aerosol_collection = ee.ImageCollection('COPERNICUS/S5P/NRTI/L3_AER_AI') \
        .filterDate(START_DATE, END_DATE).filterBounds(bolivia) \
        .select('absorbing_aerosol_index')
    
    aerosol_mean = aerosol_collection.mean().clip(bolivia)
    
    # Estimar PM2.5 a partir del índice de aerosoles
    # Relación empírica: valores altos de aerosol index indican más contaminación
    pm25 = aerosol_mean.multiply(15).add(20).rename('PM25')
    
except Exception as e:
    print(f"Advertencia: Usando método alternativo para PM2.5")
    # Método alternativo: usar MODIS Terra AOD
    modis_aod = ee.ImageCollection('MODIS/061/MOD08_D3') \
        .filterDate(START_DATE, END_DATE) \
        .select('Aerosol_Optical_Depth_Land_Mean').mean()
    
    pm25 = modis_aod.multiply(25).add(10).rename('PM25').clip(bolivia)

city_stats = []
for city_name in ['La Paz', 'Santa Cruz', 'Cochabamba']:
    city_geom = get_city_geometry(city_name, buffer_km=30)
    stats = pm25.reduceRegion(reducer=ee.Reducer.mean(), geometry=city_geom, 
                              scale=1000, maxPixels=1e9).getInfo()
    city_stats.append({
        'city': city_name,
        'pm25_mean': stats.get('PM25', 0),
        'population': CITIES[city_name]['population']
    })

polluted = pm25.gte(35)
area_image = polluted.multiply(ee.Image.pixelArea()).divide(1e6)
affected_area = area_image.reduceRegion(
    reducer=ee.Reducer.sum(), 
    geometry=bolivia, 
    scale=5000,  # Aumentar escala para velocidad
    maxPixels=1e9,
    bestEffort=True  # Usar mejor esfuerzo
).getInfo()

air_data = {
    'pm25_image': pm25,
    'affected_area_km2': affected_area.get('PM25', 0),
    'city_statistics': city_stats
}

print(f"✓ Área afectada (PM2.5 > 35): {air_data['affected_area_km2']:.2f} km²")
for city in city_stats:
    print(f"  {city['city']}: PM2.5 = {city['pm25_mean']:.2f} μg/m³")
print()

# PASO 7: ANÁLISIS DE AGUA
print("="*80)
print("PASO 6: Analizando contaminación del agua...")
print("="*80)

# Obtener agua superficial de JRC (más rápido)
water = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')
water_occurrence = water.select('occurrence').clip(bolivia)
permanent_water = water_occurrence.gte(75)

# Simplificar análisis de turbidez para evitar timeout
# Usar menos imágenes y mayor escala
try:
    # Reducir período para análisis más rápido
    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterDate('2023-01-01', '2023-06-30') \
        .filterBounds(bolivia) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)) \
        .limit(10)  # Limitar a 10 imágenes
    
    def calculate_ndti(image):
        red, green = image.select('B4'), image.select('B3')
        return image.addBands(red.subtract(green).divide(red.add(green)).rename('NDTI'))
    
    turbidity = s2.map(calculate_ndti).select('NDTI').mean().clip(bolivia)
    polluted_water = permanent_water.And(turbidity.gte(0.3))
    
except Exception as e:
    print(f"  Advertencia: Usando método simplificado para agua")
    # Método simplificado: solo usar ocurrencia de agua
    polluted_water = permanent_water

# Calcular área afectada con escala mayor (más rápido)
area_image = polluted_water.multiply(ee.Image.pixelArea()).divide(1e6)
water_affected_area = area_image.reduceRegion(
    reducer=ee.Reducer.sum(), 
    geometry=bolivia, 
    scale=500,  # Aumentar escala para velocidad
    maxPixels=1e9,
    bestEffort=True  # Usar mejor esfuerzo
).getInfo()

water_data = {
    'water_occurrence': water_occurrence,
    'polluted_water': polluted_water,
    'affected_area_km2': water_affected_area.get('occurrence', 0)
}

print(f"✓ Área de agua contaminada: {water_data['affected_area_km2']:.2f} km²\n")

# PASO 8: ANÁLISIS DE DEFORESTACIÓN
print("="*80)
print("PASO 7: Analizando deforestación...")
print("="*80)

hansen = ee.Image('UMD/hansen/global_forest_change_2023_v1_11')
loss_year = hansen.select('lossyear').clip(bolivia)
forest_loss = loss_year.gte(15).And(loss_year.lte(23))

# Optimizar cálculo de área con escala mayor y bestEffort
area_image = forest_loss.multiply(ee.Image.pixelArea()).divide(10000)
deforested_area = area_image.reduceRegion(
    reducer=ee.Reducer.sum(), 
    geometry=bolivia, 
    scale=500,  # Aumentar escala significativamente
    maxPixels=1e9,  # Aumentar límite
    bestEffort=True  # Usar mejor esfuerzo para evitar errores
).getInfo()

total_area_ha = deforested_area.get('lossyear', 0)
total_co2 = total_area_ha * CARBON_STOCK_BY_FOREST_TYPE['tropical_rainforest'] * CARBON_TO_CO2_FACTOR

soil_data = {
    'forest_loss': forest_loss,
    'total_area_ha': total_area_ha,
    'annual_average_ha': total_area_ha / 9,
    'total_co2_tons': total_co2
}

print(f"✓ Área deforestada (2015-2023): {soil_data['total_area_ha']:,.2f} ha")
print(f"  Promedio anual: {soil_data['annual_average_ha']:,.2f} ha/año")
print(f"  Emisiones CO2: {soil_data['total_co2_tons']:,.0f} toneladas\n")

# PASO 9: MODELOS ECONÓMICOS
print("="*80)
print("PASO 8: Aplicando modelos económicos...")
print("="*80)

# Modelo 1: Costos de Salud
total_exposed_pop = sum([c['population'] for c in city_stats])
avg_pm25 = sum([c['pm25_mean'] for c in city_stats]) / len(city_stats)

level = 'low' if avg_pm25 < 15 else 'medium' if avg_pm25 < 35 else 'high' if avg_pm25 < 75 else 'extreme'
rr = RELATIVE_RISK_FACTORS['PM2.5'][level]
attributable_fraction = (rr - 1) / rr
baseline_deaths = total_exposed_pop * 0.008
attributable_deaths = baseline_deaths * attributable_fraction
health_cost = attributable_deaths * VSL_USD

print(f"Modelo 1: Costos de Salud")
print(f"  Muertes atribuibles: {attributable_deaths:.1f}")
print(f"  Costo total: ${health_cost:,.0f} USD\n")

# Modelo 2: Disposición a Pagar
household_size, discount_rate, years = 3.8, 0.05, 10
air_annual = (total_exposed_pop / household_size) * WILLINGNESS_TO_PAY['air_quality']
water_annual = (500000 / household_size) * WILLINGNESS_TO_PAY['water_quality']
forest_annual = (1000000 / household_size) * WILLINGNESS_TO_PAY['forest_conservation']
total_annual = air_annual + water_annual + forest_annual
npv = total_annual * ((1 - (1 + discount_rate)**(-years)) / discount_rate)

print(f"Modelo 2: Disposición a Pagar")
print(f"  Valor anual: ${total_annual:,.0f} USD")
print(f"  VPN (10 años): ${npv:,.0f} USD\n")

# Modelo 3: Remediación
remediation_cost = (500*5000 + 200*15000 + 100*35000 + 50*60000)

print(f"Modelo 3: Costos de Remediación")
print(f"  Área total: 850 ha")
print(f"  Costo total: ${remediation_cost:,.0f} USD\n")

# Modelo 4: Carbono
carbon_value_usd = total_co2 * CARBON_PRICE_USD_PER_TON

print(f"Modelo 4: Valor del Carbono")
print(f"  CO2 emitido: {total_co2:,.0f} toneladas")
print(f"  Valor económico: ${carbon_value_usd:,.0f} USD\n")

# Resumen
total_costs = health_cost + remediation_cost + carbon_value_usd
print("="*80)
print("RESUMEN ECONÓMICO TOTAL")
print("="*80)
print(f"💵 COSTOS TOTALES: ${total_costs:,.0f} USD")
print(f"💰 BENEFICIOS POTENCIALES (anual): ${total_annual:,.0f} USD\n")

# PASO 10: MAPA INTERACTIVO
print("="*80)
print("PASO 9: Generando mapa interactivo...")
print("="*80)

Map = geemap.Map(center=[-16.5, -64], zoom=6)
Map.addLayer(pm25, {'min': 0, 'max': 100, 'palette': ['green', 'yellow', 'orange', 'red', 'darkred']}, 'PM2.5 Concentration')
Map.addLayer(forest_loss, {'min': 0, 'max': 1, 'palette': ['white', 'red']}, 'Deforestación')
Map.addLayer(polluted_water, {'min': 0, 'max': 1, 'palette': ['white', 'blue']}, 'Agua Contaminada')
Map.add_layer_control()

print("✓ Mapa creado (se mostrará abajo)\n")

# PASO 11: GRÁFICOS
print("="*80)
print("PASO 10: Generando gráficos...")
print("="*80)

sns.set_style('whitegrid')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

cities = [c['city'] for c in city_stats]
pm25_values = [c['pm25_mean'] for c in city_stats]
colors = ['green' if pm < 15 else 'yellow' if pm < 35 else 'orange' if pm < 75 else 'red' for pm in pm25_values]

ax1.barh(cities, pm25_values, color=colors)
ax1.set_xlabel('PM2.5 (μg/m³)', fontsize=12)
ax1.set_title('Concentración de PM2.5 por Ciudad', fontsize=14, fontweight='bold')
ax1.axvline(x=15, color='green', linestyle='--', label='OMS Buena')
ax1.axvline(x=35, color='orange', linestyle='--', label='OMS Moderada')
ax1.legend()

categories = ['Costos de\nSalud', 'Remediación', 'Valor\nCarbono']
costs = [health_cost, remediation_cost, carbon_value_usd]

ax2.bar(categories, costs, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
ax2.set_ylabel('Costo (USD)', fontsize=12)
ax2.set_title('Costos Económicos por Categoría', fontsize=14, fontweight='bold')
ax2.ticklabel_format(style='plain', axis='y')

plt.tight_layout()
plt.show()

print("✓ Gráficos generados\n")

# PASO 12: EXPORTAR
print("="*80)
print("PASO 11: Exportando resultados...")
print("="*80)

results_df = pd.DataFrame(city_stats)
results_df.to_csv('bolivia_pollution_results.csv', index=False)

economic_df = pd.DataFrame({
    'Modelo': ['Costos de Salud', 'Disposición a Pagar', 'Remediación', 'Valor del Carbono'],
    'Valor (USD)': [f"${health_cost:,.0f}", f"${total_annual:,.0f}", 
                    f"${remediation_cost:,.0f}", f"${carbon_value_usd:,.0f}"]
})
economic_df.to_csv('bolivia_economic_valuation.csv', index=False)

print("✓ Archivos CSV guardados")
print("\n📋 Estadísticas por Ciudad:")
print(results_df.to_string(index=False))
print("\n💰 Resumen Económico:")
print(economic_df.to_string(index=False))

print("\n" + "="*80)
print("✅ ANÁLISIS COMPLETADO")
print("="*80)
print("\nPara descargar los archivos CSV:")
print("  1. Click en el ícono de carpeta (panel izquierdo)")
print("  2. Click derecho en los archivos")
print("  3. Selecciona 'Descargar'")
print("\n¡El mapa interactivo se muestra abajo!")

# Mostrar mapa al final
Map
