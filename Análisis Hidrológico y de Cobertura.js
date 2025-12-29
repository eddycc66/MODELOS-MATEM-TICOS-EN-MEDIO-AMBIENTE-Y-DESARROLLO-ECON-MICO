// ============================================
// PROYECTO DIDÁCTICO COMPLETO - VERIFICADO
// Google Earth Engine - Análisis Hidrológico y de Cobertura
// ============================================

// 1. CARGA DEL ÁREA DE ESTUDIO
// Opción A: Si tienes el asset
var areaEstudio = ee.FeatureCollection('projects/eddycc66/assets/area_pirai3');

// Opción B: Si no tienes el asset, usa esta área de ejemplo
// var areaEstudio = ee.FeatureCollection(
//   ee.Geometry.Rectangle([-63.5, -17.6, -63.2, -17.3])
// );

Map.centerObject(areaEstudio, 10);
Map.addLayer(areaEstudio, {color: 'FF0000'}, 'Área de estudio');

// 2. ANÁLISIS DEL TERRENO (FORMA CORRECTA)
// 2.1. Cargar Modelo Digital de Elevación
var dem = ee.Image('NASA/NASADEM_HGT/001').select('elevation').clip(areaEstudio);
// Alternativas si NASA no funciona:
// var dem = ee.Image('CGIAR/SRTM90_V4').clip(areaEstudio);
// var dem = ee.Image('USGS/SRTMGL1_003').clip(areaEstudio);

Map.addLayer(dem, {min: 200, max: 800, palette: ['green', 'yellow', 'brown']}, 'Elevación (m)');

// 2.2. CALCULAR PENDIENTE (FORMA CORRECTA)
var slope = ee.Terrain.slope(dem);
Map.addLayer(slope, {min: 0, max: 45, palette: ['white', 'brown']}, 'Pendiente (grados)');

// 2.3. CALCULAR ORIENTACIÓN (ASPECT)
var aspect = ee.Terrain.aspect(dem);
Map.addLayer(aspect, {min: 0, max: 360}, 'Orientación');

// 2.4. Calcular área total
var areaKm2 = areaEstudio.geometry().area().divide(1e6);
print('Área total del estudio:', areaKm2, 'km²');

// 3. SIMULACIÓN DE RED HÍDRICA (para fines didácticos)
// Basado en valores de elevación
var elevacionMedia = dem.reduceRegion({
  reducer: ee.Reducer.mean(),
  geometry: areaEstudio,
  scale: 90,
  maxPixels: 1e9
}).get('elevation');

print('Elevación media:', elevacionMedia, 'm');

// Crear capa simulada de cursos de agua (áreas con menor pendiente)
var cursosAguaSimulados = slope.lt(5).selfMask();
Map.addLayer(cursosAguaSimulados, {palette: ['blue']}, 'Cursos de agua simulados');

// 4. ESTIMACIÓN DE CAUDAL (Modelo simplificado)
var precipitacionAnual = 1200; // mm/año
var coeficienteEscorrentia = 0.3;

// Fórmula: Q = (A * P * C) / 31.536 (conversión a m³/s)
var caudal = areaKm2.multiply(precipitacionAnual)
                    .multiply(coeficienteEscorrentia)
                    .multiply(0.0317);

print('Caudal estimado:', caudal, 'm³/s');

// 5. ANÁLISIS DE COBERTURA VEGETAL CON SENTINEL-2
// 5.1. Cargar y procesar imágenes Sentinel-2
var sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(areaEstudio)
  .filterDate('2024-01-01', '2024-07-01') // Período más corto para evitar timeouts
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .median()
  .clip(areaEstudio);

// 5.2. Calcular NDVI
var ndvi = sentinel2.normalizedDifference(['B8', 'B4']).rename('NDVI');
Map.addLayer(ndvi, {
  min: -0.2,
  max: 0.8,
  palette: ['brown', 'yellow', 'green', 'darkgreen']
}, 'NDVI 2024');

// 5.3. Clasificar cobertura forestal
var bosque = ndvi.gt(0.4).selfMask(); // NDVI > 0.4 = bosque
var matorral = ndvi.gt(0.2).and(ndvi.lte(0.4)).selfMask(); // 0.2-0.4 = matorral
var sueloDesnudo = ndvi.lte(0.2).selfMask(); // NDVI ≤ 0.2 = suelo desnudo

Map.addLayer(bosque, {palette: ['darkgreen']}, 'Bosque');
Map.addLayer(matorral, {palette: ['yellowgreen']}, 'Matorral');
Map.addLayer(sueloDesnudo, {palette: ['brown']}, 'Suelo desnudo');

// 5.4. Calcular áreas
var areaBosqueHa = bosque.multiply(ee.Image.pixelArea())
                         .divide(1e4)
                         .reduceRegion({
                           reducer: ee.Reducer.sum(),
                           geometry: areaEstudio,
                           scale: 30,
                           maxPixels: 1e9
                         }).get('NDVI');

var areaMatorralHa = matorral.multiply(ee.Image.pixelArea())
                             .divide(1e4)
                             .reduceRegion({
                               reducer: ee.Reducer.sum(),
                               geometry: areaEstudio,
                               scale: 30,
                               maxPixels: 1e9
                             }).get('NDVI');

var ndviPromedio = ndvi.reduceRegion({
  reducer: ee.Reducer.mean(),
  geometry: areaEstudio,
  scale: 30,
  maxPixels: 1e9
}).get('NDVI');

print('Área de bosque:', areaBosqueHa, 'ha');
print('Área de matorral:', areaMatorralHa, 'ha');
print('NDVI promedio:', ndviPromedio);

// 6. PREPARAR DATOS PARA EXPORTACIÓN
var resultados = ee.FeatureCollection([
  ee.Feature(null, {
    'area_total_km2': areaKm2,
    'elevacion_media_m': elevacionMedia,
    'caudal_m3_s': caudal,
    'area_bosque_ha': areaBosqueHa,
    'area_matorral_ha': areaMatorralHa,
    'ndvi_promedio': ndviPromedio,
    'precipitacion_mm_anual': precipitacionAnual,
    'coef_escorrentia': coeficienteEscorrentia,
    'fecha_procesamiento': ee.Date(new Date()).format('YYYY-MM-dd HH:mm:ss')
  })
]);

// 7. EXPORTAR A CSV
Export.table.toDrive({
  collection: resultados,
  description: 'Exportacion_Datos_Estudio',
  folder: 'GEE_Projects', // CAMBIA ESTO A TU CARPETA
  fileNamePrefix: 'datos_hidrologicos',
  fileFormat: 'CSV'
});

// 8. MENSAJES FINALES
print('==============================================');
print('✅ PROYECTO COMPLETADO EXITOSAMENTE');
print('==============================================');
print('📊 RESUMEN DE RESULTADOS:');
print('   • Área total: ' + areaKm2 + ' km²');
print('   • Elevación media: ' + elevacionMedia + ' m');
print('   • Caudal estimado: ' + caudal + ' m³/s');
print('   • NDVI promedio: ' + ndviPromedio);
print('   • Área bosque: ' + areaBosqueHa + ' ha');
print('');
print('📤 INSTRUCCIONES PARA EXPORTAR:');
print('   1. Ve a la pestaña "Tasks" (panel superior derecho)');
print('   2. Haz clic en "Run" junto a "Exportacion_Datos_Estudio"');
print('   3. Configura la carpeta de destino en Google Drive');
print('   4. Espera 1-2 minutos');
print('   5. El archivo "datos_hidrologicos.csv" estará en tu Drive');
print('==============================================');