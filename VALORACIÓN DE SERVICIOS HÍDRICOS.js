// ============================================
// VALORACIÓN DE SERVICIOS HÍDRICOS - BOLIVIA (CORREGIDO)
// Cuenca del Río Piraí, Santa Cruz
// ============================================

// 1. DELIMITACIÓN DEL ÁREA DE ESTUDIO
// Cuenca del Río Piraí (coordenadas aproximadas)
var cuencaPirai = ee.Geometry.Polygon([
  [-63.5, -17.4], [-63.2, -17.4],
  [-63.2, -17.8], [-63.5, -17.8],
  [-63.5, -17.4]
]);

// Punto de toma de agua para Santa Cruz (aproximado)
var puntoTomaAgua = ee.Geometry.Point([-63.2, -17.5]);

// Áreas urbanas (Santa Cruz ciudad)
var areaUrbana = ee.Geometry.Polygon([
  [-63.25, -17.75], [-63.15, -17.75],
  [-63.15, -17.8], [-63.25, -17.8],
  [-63.25, -17.75]
]);

Map.centerObject(cuencaPirai, 10);
Map.addLayer(cuencaPirai, {color: 'blue'}, 'Cuenca Río Piraí');
Map.addLayer(puntoTomaAgua, {color: 'red'}, 'Punto toma agua');
Map.addLayer(areaUrbana, {color: 'orange'}, 'Área urbana Santa Cruz');

// 2. ANÁLISIS HIDROLÓGICO DETALLADO
// 2.1. Modelo Digital de Elevación (NASA DEM)
var dem = ee.Image('NASA/NASADEM_HGT/001').select('elevation').clip(cuencaPirai);

// 2.2. Calcular pendiente para identificar zonas de recarga
var slope = ee.Terrain.slope(dem);
Map.addLayer(slope, {min: 0, max: 45, palette: ['white', 'brown']}, 'Pendiente');

// 2.3. Clasificar zonas por función hidrológica
var zonasRecarga = slope.lt(15).selfMask();  // Zonas planas = recarga
var zonasEscorrentia = slope.gt(15).selfMask(); // Zonas inclinadas = escorrentía

Map.addLayer(zonasRecarga, {palette: ['lightblue']}, 'Zonas de recarga');
Map.addLayer(zonasEscorrentia, {palette: ['darkblue']}, 'Zonas de escorrentía');

// 3. ANÁLISIS DE COBERTURA VEGETAL (SENTINEL-2)
// 3.1. Filtrar imágenes para época seca y húmeda
var epocaSeca = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(cuencaPirai)
  .filterDate('2024-05-01', '2024-10-31')  // Mayo-Oct (seca)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .median()
  .clip(cuencaPirai);

var epocaHumeda = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(cuencaPirai)
  .filterDate('2024-11-01', '2025-04-30')  // Nov-Abr (húmeda)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .median()
  .clip(cuencaPirai);

// 3.2. Calcular NDVI para ambas épocas
var ndviSeca = epocaSeca.normalizedDifference(['B8', 'B4']).rename('NDVI_seca');
var ndviHumeda = epocaHumeda.normalizedDifference(['B8', 'B4']).rename('NDVI_humeda');

Map.addLayer(ndviSeca, {min: 0, max: 0.8, palette: ['brown', 'yellow', 'green']}, 'NDVI Época Seca');
Map.addLayer(ndviHumeda, {min: 0, max: 0.8, palette: ['brown', 'yellow', 'green']}, 'NDVI Época Húmeda');

// 3.3. Clasificar tipos de vegetación por importancia hídrica
var bosquePrimario = ndviHumeda.gt(0.6).selfMask();
var bosqueSecundario = ndviHumeda.gt(0.4).and(ndviHumeda.lte(0.6)).selfMask();
var vegetacionRiparia = ndviHumeda.gt(0.5).and(slope.lt(10)).selfMask();
var agricultura = ndviHumeda.gt(0.3).and(ndviHumeda.lte(0.4)).selfMask();
var pastizales = ndviHumeda.gt(0.2).and(ndviHumeda.lte(0.3)).selfMask();
var sueloDesnudo = ndviHumeda.lte(0.2).selfMask();

// Añadir cada tipo al mapa
Map.addLayer(bosquePrimario, {palette: ['darkgreen']}, 'Bosque Primario');
Map.addLayer(vegetacionRiparia, {palette: ['#00FF00']}, 'Vegetación Riparia');

// 4. CÁLCULO DE PARÁMETROS HIDROLÓGICOS
// 4.1. Área total de la cuenca
var areaTotalKm2 = cuencaPirai.area().divide(1e6);

// 4.2. Precipitación media anual (CHIRPS - versión mejorada)
var precipitacionAnual = ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD')
  .filterBounds(cuencaPirai)
  .filterDate('2020-01-01', '2024-12-31')
  .select('precipitation')
  .mean()
  .multiply(73)  // Convertir a mm/año (365/5 = 73)
  .clip(cuencaPirai);

var precipitacionMedia = precipitacionAnual.reduceRegion({
  reducer: ee.Reducer.mean(),
  geometry: cuencaPirai,
  scale: 5000,
  maxPixels: 1e9
}).get('precipitation');

Map.addLayer(precipitacionAnual, {min: 800, max: 1500, palette: ['white', 'blue', 'darkblue']}, 'Precipitación Anual');

// 4.3. Coeficiente de escorrentía por tipo de cobertura
// Crear imagen con coeficientes
var coeficienteBosque = ee.Image(0.15).where(bosquePrimario, 1).selfMask();
var coeficienteMatorral = ee.Image(0.25).where(bosqueSecundario, 1).selfMask();
var coeficienteRipario = ee.Image(0.10).where(vegetacionRiparia, 1).selfMask();
var coeficienteAgric = ee.Image(0.35).where(agricultura, 1).selfMask();
var coeficientePastizal = ee.Image(0.30).where(pastizales, 1).selfMask();
var coeficienteSuelo = ee.Image(0.60).where(sueloDesnudo, 1).selfMask();

// Combinar todos los coeficientes
var coeficientes = ee.Image(0.3)  // Valor por defecto
  .where(bosquePrimario, 0.15)
  .where(bosqueSecundario, 0.25)
  .where(vegetacionRiparia, 0.10)
  .where(agricultura, 0.35)
  .where(pastizales, 0.30)
  .where(sueloDesnudo, 0.60);

// 4.4. Caudal estimado
var escorrentiaTotal = precipitacionAnual.multiply(coeficientes).multiply(areaTotalKm2);
var caudalEstimado = escorrentiaTotal.multiply(0.0317); // Convertir a m³/s

// 5. CÁLCULO DE POBLACIÓN BENEFICIADA
// 5.1. Usar datos de población (WorldPop - versión corregida)
try {
  var poblacion = ee.Image('WorldPop/GP/100m/pop_age_sex/2020')
    .select('population')
    .clip(areaUrbana);
} catch (e) {
  // Alternativa si falla WorldPop
  var poblacion = ee.Image.constant(5000).rename('population').clip(areaUrbana);
}

var poblacionTotal = poblacion.reduceRegion({
  reducer: ee.Reducer.sum(),
  geometry: areaUrbana,
  scale: 100,
  maxPixels: 1e9
}).get('population');

// 5.2. Consumo de agua per cápita (Bolivia: 80-120 L/persona/día)
var consumoPerCapita = 100; // Litros/persona/día
var consumoTotal = ee.Number(poblacionTotal)
  .multiply(consumoPerCapita)
  .divide(1000)  // Litros a m³
  .divide(86400); // Días a segundos

// 6. VALORACIÓN ECONÓMICA PRELIMINAR
// 6.1. Parámetros económicos para Bolivia
var costoTratamiento = 0.45;           // USD/m³ tratamiento convencional
var valorDomestico = 0.60;             // USD/m³ tarifa residencial

// 6.2. Cálculo de valores
var caudalAnualM3 = caudalEstimado.multiply(60 * 60 * 24 * 365);

// A. Valor por tratamiento evitado
var valorTratamientoEvitado = caudalAnualM3.multiply(costoTratamiento);

// B. Valor por uso doméstico
var valorUsoDomestico = caudalAnualM3.multiply(valorDomestico);

// C. Valor por suministro municipal
var valorMunicipal = ee.Number(poblacionTotal)
  .multiply(consumoPerCapita * 365 / 1000)  // m³/año
  .multiply(valorDomestico);

// 7. ANÁLISIS DE VULNERABILIDAD HÍDRICA
// 7.1. Relación oferta-demanda
var relacionOfertaDemanda = caudalEstimado.divide(consumoTotal);

// 7.2. Zonas críticas para conservación
var zonasCriticas = slope.gt(20).and(bosquePrimario);
Map.addLayer(zonasCriticas, {palette: ['red']}, 'Zonas Críticas Conservación');

// 8. CÁLCULO DE ÁREAS DE COBERTURA
var calcularAreaHa = function(imagen) {
  return imagen.multiply(ee.Image.pixelArea())
               .divide(1e4)
               .reduceRegion({
                 reducer: ee.Reducer.sum(),
                 geometry: cuencaPirai,
                 scale: 30,
                 maxPixels: 1e9
               }).getNumber('constant');
};

var areaBosquePrimarioHa = calcularAreaHa(bosquePrimario.rename('constant'));
var areaVegetacionRipariaHa = calcularAreaHa(vegetacionRiparia.rename('constant'));
var areaZonasCriticasHa = calcularAreaHa(zonasCriticas.rename('constant'));

// 9. EXPORTACIÓN DE RESULTADOS DETALLADOS
var resultados = ee.FeatureCollection([
  ee.Feature(null, {
    // Datos básicos
    'proyecto': 'Valoracion_Hidrica_Bolivia',
    'cuenca': 'Rio_Pirai',
    'departamento': 'Santa_Cruz',
    'fecha_analisis': '2024',
    
    // Parámetros hidrológicos
    'area_total_km2': areaTotalKm2,
    'precipitacion_media_mm': precipitacionMedia,
    'caudal_estimado_m3_s': caudalEstimado,
    'caudal_anual_m3': caudalAnualM3,
    
    // Cobertura vegetal
    'area_bosque_primario_ha': areaBosquePrimarioHa,
    'area_vegetacion_riparia_ha': areaVegetacionRipariaHa,
    'ndvi_promedio_humeda': ndviHumeda.reduceRegion({
      reducer: ee.Reducer.mean(), 
      geometry: cuencaPirai, 
      scale: 30
    }).get('NDVI_humeda'),
    
    // Demografía
    'poblacion_beneficiada': poblacionTotal,
    'consumo_total_m3_s': consumoTotal,
    'relacion_oferta_demanda': relacionOfertaDemanda,
    
    // Valoración económica
    'valor_tratamiento_evitado_usd': valorTratamientoEvitado,
    'valor_uso_domestico_usd': valorUsoDomestico,
    'valor_municipal_usd': valorMunicipal,
    
    // Vulnerabilidad
    'area_zonas_criticas_ha': areaZonasCriticasHa,
    
    'fecha_exportacion': ee.Date(new Date()).format('YYYY-MM-dd HH:mm')
  })
]);

// 10. MOSTRAR RESULTADOS EN CONSOLA
print('============================================================');
print('💧 VALORACIÓN DE SERVICIOS HÍDRICOS - BOLIVIA');
print('============================================================');
print('📍 CUENCA: Río Piraí, Santa Cruz');
print('📊 ÁREA TOTAL: ' + areaTotalKm2 + ' km²');
print('🌧️ PRECIPITACIÓN MEDIA: ' + precipitacionMedia + ' mm/año');
print('💦 CAUDAL ESTIMADO: ' + caudalEstimado + ' m³/s');
print('👥 POBLACIÓN BENEFICIADA: ' + poblacionTotal + ' habitantes');
print('💵 VALOR TRATAMIENTO EVITADO: ' + valorTratamientoEvitado + ' USD/año');
print('🏠 VALOR USO DOMÉSTICO: ' + valorUsoDomestico + ' USD/año');
print('⚠️  RELACIÓN OFERTA/DEMANDA: ' + relacionOfertaDemanda);
print('============================================================');

// 11. CONFIGURAR EXPORTACIÓN
Export.table.toDrive({
  collection: resultados,
  description: 'Valoracion_Hidrica_Bolivia',
  folder: 'GEE_Bolivia',
  fileNamePrefix: 'valoracion_agua_pirai',
  fileFormat: 'CSV'
});

// 12. INSTRUCCIONES PARA ANÁLISIS EN R
print('');
print('📈 PARA ANÁLISIS ECONÓMICO COMPLETO EN R:');
print('   1. Exportar este CSV a Google Drive');
print('   2. Descargar y subir a RStudio Cloud');
print('   3. Ejecutar análisis económico con:');
print('      • VPN a 20 años');
print('      • Tasa de descuento 8%');
print('   4. Generar reporte de política pública');
print('============================================================');