// ======================================================================
// ANÁLISIS CORREGIDO DE CAMBIO FORESTAL EN BOLIVIA (2001-2023)
// Google Earth Engine - Código ejecutable completo
// Versión corregida sin errores de sintaxis
// ======================================================================

// ---------- 1. CONFIGURACIÓN INICIAL ----------
// Limpiar consola y mapa
Map.clear();
print('🚀 INICIANDO ANÁLISIS DE CAMBIO FORESTAL - BOLIVIA');

// ---------- 2. CARGAR DATOS PRINCIPALES ----------
// Dataset de Cambio Forestal Global (Hansen)
var gfc = ee.Image('UMD/hansen/global_forest_change_2023_v1_11');

// Extraer bandas importantes
var loss = gfc.select(['loss']);           // Pérdida acumulada 2001-2023
var lossYear = gfc.select(['lossyear']);   // Año de pérdida (0-23)
var treeCover2000 = gfc.select(['treecover2000']); // Cobertura arbórea año 2000
var gain = gfc.select(['gain']);           // Ganancia forestal 2000-2012

// ---------- 3. DEFINIR ÁREA DE ESTUDIO: BOLIVIA ----------
var bolivia = ee.FeatureCollection('FAO/GAUL/2015/level0')
  .filter(ee.Filter.eq('ADM0_NAME', 'Bolivia'));

var boliviaGeometry = bolivia.geometry();
Map.centerObject(boliviaGeometry, 5);

print('✅ Bolivia cargada correctamente');
print('Área aproximada:', ee.Number(boliviaGeometry.area()).divide(1000000), 'km²');

// ---------- 4. FUNCIÓN AUXILIAR PARA CALCULAR ÁREAS ----------
// Función robusta para calcular áreas en hectáreas
var calcularArea = function(imagen, geometria) {
  // Crear imagen de área por píxel (en metros cuadrados)
  var areaPorPixel = ee.Image.pixelArea();
  
  // Multiplicar por la máscara de interés y sumar
  var areaTotal = imagen
    .multiply(areaPorPixel)
    .reduceRegion({
      reducer: ee.Reducer.sum(),
      geometry: geometria,
      scale: 30,
      maxPixels: 1e13
    });
  
  // Convertir m² a hectáreas (1 ha = 10,000 m²)
  var areaHa = ee.Number(areaTotal.get(imagen.bandNames().get(0))).divide(10000);
  
  return areaHa;
};

// ---------- 5. CÁLCULO DE ESTADÍSTICAS NACIONALES ----------
print('');
print('📊 ===========================================');
print('ESTADÍSTICAS NACIONALES DE BOLIVIA');
print('===========================================');

// 5.1 Área total de Bolivia
var areaBoliviaHa = ee.Number(boliviaGeometry.area()).divide(10000);
print('Área total de Bolivia:', areaBoliviaHa, 'ha');

// 5.2 Cobertura arbórea año 2000 (considerando >30% como bosque)
var umbralBosque = 30;
var bosque2000 = treeCover2000.gt(umbralBosque);
var areaBosque2000Ha = calcularArea(bosque2000, boliviaGeometry);
print('Área de bosque año 2000 (>' + umbralBosque + '% cobertura):', areaBosque2000Ha, 'ha');

var porcentajeBosque2000 = areaBosque2000Ha.divide(areaBoliviaHa).multiply(100);
print('Porcentaje de territorio con bosque (2000):', porcentajeBosque2000, '%');

// 5.3 Pérdida forestal acumulada 2001-2023
var areaPerdidaHa = calcularArea(loss, boliviaGeometry);
print('Pérdida forestal acumulada (2001-2023):', areaPerdidaHa, 'ha');

var porcentajePerdida = areaPerdidaHa.divide(areaBosque2000Ha).multiply(100);
print('Porcentaje de bosque 2000 perdido:', porcentajePerdida, '%');

// 5.4 Tasa anual de deforestación
var tasaAnualHa = areaPerdidaHa.divide(23); // 23 años (2001-2023)
print('Tasa anual promedio de deforestación:', tasaAnualHa, 'ha/año');

// 5.5 Ganancia forestal 2000-2012
var areaGananciaHa = calcularArea(gain, boliviaGeometry);
print('Ganancia forestal (2000-2012):', areaGananciaHa, 'ha');

// 5.6 Pérdida neta
var perdidaNetaHa = areaPerdidaHa.subtract(areaGananciaHa);
print('Pérdida neta (ganancia - pérdida):', perdidaNetaHa, 'ha');

// ---------- 6. ANÁLISIS TEMPORAL POR AÑO ----------
print('');
print('📈 ===========================================');
print('ANÁLISIS TEMPORAL (2001-2023)');
print('===========================================');

// Crear lista para almacenar resultados anuales
var resultadosAnuales = ee.List.sequence(1, 23).map(function(year) {
  var añoReal = ee.Number(year).add(2000);
  var mascaraAnual = lossYear.eq(year);
  var areaAnualHa = calcularArea(mascaraAnual, boliviaGeometry);
  
  return ee.Feature(null, {
    'Año': añoReal,
    'Perdida_ha': areaAnualHa,
    'Perdida_km2': areaAnualHa.divide(100)
  });
});

// Convertir a FeatureCollection para análisis
var resultadosAnualesFC = ee.FeatureCollection(resultadosAnuales);

// Calcular estadísticas
var perdidasList = resultadosAnualesFC.aggregate_array('Perdida_ha');
var maxPerdida = perdidasList.reduce(ee.Reducer.max());
var minPerdida = perdidasList.reduce(ee.Reducer.min());
var avgPerdida = perdidasList.reduce(ee.Reducer.mean());

// Encontrar año con máxima pérdida
var añoMaxPerdidaFC = resultadosAnualesFC.filter(ee.Filter.eq('Perdida_ha', maxPerdida));
var añoMaxPerdida = añoMaxPerdidaFC.first().get('Año');

print('Año de máxima pérdida:', añoMaxPerdida, '(', maxPerdida, 'ha)');
print('Mínima pérdida anual:', minPerdida, 'ha');
print('Promedio anual:', avgPerdida, 'ha');

// Mostrar primeros 5 años
print('Primeros 5 años de análisis:');
var primeros5 = resultadosAnualesFC.limit(5);
primeros5.evaluate(function(resultados) {
  if (resultados && resultados.features) {
    resultados.features.forEach(function(feature) {
      var props = feature.properties;
      print('  ' + props.Año + ': ' + Math.round(props.Perdida_ha) + ' ha');
    });
  }
});

// ---------- 7. ANÁLISIS POR REGIONES ECOLÓGICAS ----------
print('');
print('🌳 ===========================================');
print('ANÁLISIS POR REGIÓN ECOLÓGICA');
print('===========================================');

// Definir regiones ecológicas de Bolivia
var regiones = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Rectangle([-69.0, -11.0, -65.0, -9.0]), {'nombre': 'Amazonía Norte'}),
  ee.Feature(ee.Geometry.Rectangle([-66.0, -16.0, -62.0, -12.0]), {'nombre': 'Amazonía Sur'}),
  ee.Feature(ee.Geometry.Rectangle([-62.5, -18.0, -59.0, -15.0]), {'nombre': 'Chiquitanía'}),
  ee.Feature(ee.Geometry.Rectangle([-62.5, -21.0, -59.0, -18.0]), {'nombre': 'Chaco'}),
  ee.Feature(ee.Geometry.Rectangle([-65.5, -19.0, -63.5, -16.0]), {'nombre': 'Valles Mesotérmicos'}),
  ee.Feature(ee.Geometry.Rectangle([-69.0, -19.0, -66.5, -16.0]), {'nombre': 'Altiplano'})
]);

// Intersectar con Bolivia
var regionesBolivia = regiones.map(function(feature) {
  return feature.intersection(boliviaGeometry, 100);
});

// Función para analizar cada región
var analizarRegion = function(feature) {
  var geom = feature.geometry();
  var nombre = feature.get('nombre');
  
  // Calcular áreas
  var areaRegionHa = ee.Number(geom.area()).divide(10000);
  var bosqueRegionHa = calcularArea(bosque2000, geom);
  var perdidaRegionHa = calcularArea(loss, geom);
  
  // Calcular porcentajes
  var porcBosque = bosqueRegionHa.divide(areaRegionHa).multiply(100);
  var porcPerdida = perdidaRegionHa.divide(bosqueRegionHa).multiply(100);
  
  return feature.set({
    'Area_total_ha': areaRegionHa,
    'Bosque_2000_ha': bosqueRegionHa,
    'Porc_Bosque': porcBosque,
    'Perdida_ha': perdidaRegionHa,
    'Porc_Perdida': porcPerdida,
    'Tasa_anual_ha': perdidaRegionHa.divide(23)
  });
};

// Aplicar análisis a todas las regiones
var regionesAnalizadas = regionesBolivia.map(analizarRegion);

// Mostrar resultados
print('Resultados por región ecológica:');
regionesAnalizadas.evaluate(function(resultados) {
  if (resultados && resultados.features) {
    resultados.features.forEach(function(feature) {
      var props = feature.properties;
      print('');
      print(props.nombre + ':');
      print('  Área total: ' + Math.round(props.Area_total_ha) + ' ha');
      print('  Bosque 2000: ' + Math.round(props.Bosque_2000_ha) + ' ha (' + props.Porc_Bosque.toFixed(1) + '%)');
      print('  Pérdida 2001-2023: ' + Math.round(props.Perdida_ha) + ' ha (' + props.Porc_Perdida.toFixed(1) + '%)');
    });
  }
});

// ---------- 8. CÁLCULO DE CARBONO PERDIDO ----------
print('');
print('💰 ===========================================');
print('VALORACIÓN ECONÓMICA DEL CARBONO PERDIDO');
print('===========================================');

// 8.1 Estimación de biomasa
var biomasaPromedio = 150; // Mg/ha (toneladas métricas por hectárea)
print('Biomasa aérea promedio asumida:', biomasaPromedio, 'Mg/ha');

// Factores de conversión (según IPCC)
var factorExpansionBiomasa = 1.74; // Para incluir raíces
var fraccionCarbono = 0.47; // 47% de carbono en la biomasa

// 8.2 Cálculo de carbono perdido
var carbonoPerdidoMg = areaPerdidaHa
  .multiply(biomasaPromedio)
  .multiply(factorExpansionBiomasa)
  .multiply(fraccionCarbono);

print('Carbono perdido (2001-2023):', carbonoPerdidoMg, 'Mg C');

// 8.3 Conversión a CO₂ equivalente
var carbonoCO2eq = carbonoPerdidoMg.multiply(44/12); // Peso molecular CO2/C
print('Equivalente en CO₂:', carbonoCO2eq, 'Mg CO₂eq');

// 8.4 Valoración económica
var precioCarbono = 50; // USD por Mg CO₂ (valor conservador)
var valorEconomicoUSD = carbonoCO2eq.multiply(precioCarbono);
var valorMillonesUSD = valorEconomicoUSD.divide(1000000);

print('Valor económico (@' + precioCarbono + ' USD/Mg CO₂):');
print('  Total:', valorEconomicoUSD, 'USD');
print('  En millones:', valorMillonesUSD, 'millones USD');

// Valor por hectárea deforestada
var valorPorHa = valorEconomicoUSD.divide(areaPerdidaHa);
print('Valor promedio por hectárea deforestada:', valorPorHa, 'USD/ha');

// ---------- 9. VISUALIZACIÓN DE MAPAS ----------
print('');
print('🗺️ ===========================================');
print('GENERANDO VISUALIZACIONES CARTOGRÁFICAS');
print('===========================================');

// Configurar el mapa centrado en Bolivia
Map.centerObject(boliviaGeometry, 5);

// 9.1 Mapa de cobertura arbórea 2000
var visBosque2000 = {
  min: 0,
  max: 100,
  palette: ['FFFFFF', 'CCEBC5', 'A8DDB5', '7BCCC4', '4EB3D3', '2B8CBE', '08589E']
};
Map.addLayer(
  treeCover2000.clip(boliviaGeometry),
  visBosque2000,
  'Cobertura arbórea 2000 (%)',
  false
);

// 9.2 Mapa de pérdida forestal acumulada
Map.addLayer(
  loss.selfMask().clip(boliviaGeometry),
  {palette: ['FF0000']},
  'Pérdida forestal (2001-2023)',
  true
);

// 9.3 Mapa de año de pérdida (gradiente temporal)
var visAnoPerdida = {
  min: 1,
  max: 23,
  palette: [
    'FFFFCC', 'FFEDA0', 'FED976', 'FEB24C', 'FD8D3C', 
    'FC4E2A', 'E31A1C', 'BD0026', '800026'
  ]
};
Map.addLayer(
  lossYear.clip(boliviaGeometry),
  visAnoPerdida,
  'Año de pérdida',
  false
);

// 9.4 Mapa compuesto: Bosque 2000 + Pérdida
// Crear imagen RGB compuesta
var compuesto = ee.Image.cat([
  treeCover2000.divide(100).clip(boliviaGeometry),  // Rojo: bosque 2000
  loss.clip(boliviaGeometry),                       // Verde: pérdida
  lossYear.divide(23).clip(boliviaGeometry)         // Azul: año de pérdida
]).float();

Map.addLayer(
  compuesto,
  {min: 0, max: 1},
  'Composición RGB: Bosque2000/Pérdida/Año',
  false
);

// 9.5 Mapa de regiones ecológicas
Map.addLayer(
  regionesBolivia.style({color: 'black', fillColor: '00000000'}),
  {},
  'Regiones ecológicas',
  false
);

// 9.6 Mapa de límites de Bolivia
Map.addLayer(
  bolivia.style({color: 'yellow', fillColor: '00000000'}),
  {},
  'Límites de Bolivia',
  true
);

// 9.7 Añadir controles de capas
Map.setOptions('SATELLITE'); // Fondo satelital

print('✅ Capas de mapa cargadas. Use el panel de capas para activar/desactivar.');

// ---------- 10. GRÁFICOS Y VISUALIZACIONES ----------
print('');
print('📉 ===========================================');
print('GRÁFICOS ESTADÍSTICOS');
print('===========================================');

// 10.1 Gráfico de serie temporal
var chartTemporal = ui.Chart.feature.byFeature({
  features: resultadosAnualesFC,
  xProperty: 'Año',
  yProperties: ['Perdida_ha', 'Perdida_km2']
})
.setChartType('ColumnChart')
.setOptions({
  title: 'Pérdida Forestal Anual en Bolivia (2001-2023)',
  hAxis: {title: 'Año'},
  vAxis: {title: 'Hectáreas perdidas'},
  colors: ['#e41a1c', '#377eb8'],
  legend: {position: 'top'}
});

print(chartTemporal);

// 10.2 Gráfico de regiones (pérdida total)
var chartRegiones = ui.Chart.feature.byFeature({
  features: regionesAnalizadas,
  xProperty: 'nombre',
  yProperties: ['Perdida_ha', 'Bosque_2000_ha']
})
.setChartType('BarChart')
.setOptions({
  title: 'Comparación por Región Ecológica',
  hAxis: {title: 'Hectáreas'},
  vAxis: {title: 'Región'},
  colors: ['#e41a1c', '#4daf4a'],
  legend: {position: 'top'}
});

print(chartRegiones);

// 10.3 Gráfico de porcentaje de pérdida
var chartPorcentaje = ui.Chart.feature.byFeature({
  features: regionesAnalizadas,
  xProperty: 'nombre',
  yProperties: ['Porc_Perdida']
})
.setChartType('ColumnChart')
.setOptions({
  title: 'Porcentaje de Bosque Perdido por Región (2001-2023)',
  hAxis: {title: 'Región'},
  vAxis: {title: 'Porcentaje (%)'},
  colors: ['#984ea3'],
  legend: {position: 'none'}
});

print(chartPorcentaje);

// ---------- 11. EXPORTACIÓN DE RESULTADOS ----------
print('');
print('💾 ===========================================');
print('EXPORTACIÓN DE RESULTADOS');
print('===========================================');

// 11.1 Exportar imagen de pérdida anual
Export.image.toDrive({
  image: lossYear.clip(boliviaGeometry),
  description: 'Perdida_Anual_Bolivia_30m',
  scale: 30,
  region: boliviaGeometry,
  maxPixels: 1e13,
  fileFormat: 'GeoTIFF',
  folder: 'GEE_Exports_Bolivia'
});

print('✅ Tarea 1/4: Imagen de pérdida anual lista para exportar');

// 11.2 Exportar estadísticas por región
Export.table.toDrive({
  collection: regionesAnalizadas,
  description: 'Estadisticas_Regiones_Bolivia',
  fileFormat: 'CSV',
  folder: 'GEE_Exports_Bolivia'
});

print('✅ Tarea 2/4: Tabla de regiones lista para exportar');

// 11.3 Exportar serie temporal anual
Export.table.toDrive({
  collection: resultadosAnualesFC,
  description: 'Serie_Temporal_Perdida_Bolivia',
  fileFormat: 'CSV',
  folder: 'GEE_Exports_Bolivia'
});

print('✅ Tarea 3/4: Serie temporal lista para exportar');

// 11.4 Exportar resumen ejecutivo
// Crear FeatureCollection con resumen
var resumenEjecutivo = ee.FeatureCollection([
  ee.Feature(null, {
    'indicador': 'Area_total_Bolivia',
    'valor': areaBoliviaHa,
    'unidad': 'ha'
  }),
  ee.Feature(null, {
    'indicador': 'Bosque_2000',
    'valor': areaBosque2000Ha,
    'unidad': 'ha'
  }),
  ee.Feature(null, {
    'indicador': 'Porc_Bosque_2000',
    'valor': porcentajeBosque2000,
    'unidad': '%'
  }),
  ee.Feature(null, {
    'indicador': 'Perdida_total',
    'valor': areaPerdidaHa,
    'unidad': 'ha'
  }),
  ee.Feature(null, {
    'indicador': 'Porc_Perdida',
    'valor': porcentajePerdida,
    'unidad': '%'
  }),
  ee.Feature(null, {
    'indicador': 'Tasa_anual',
    'valor': tasaAnualHa,
    'unidad': 'ha/año'
  }),
  ee.Feature(null, {
    'indicador': 'Carbono_perdido',
    'valor': carbonoPerdidoMg,
    'unidad': 'Mg C'
  }),
  ee.Feature(null, {
    'indicador': 'Valor_economico',
    'valor': valorEconomicoUSD,
    'unidad': 'USD'
  })
]);

Export.table.toDrive({
  collection: resumenEjecutivo,
  description: 'Resumen_Ejecutivo_Bolivia',
  fileFormat: 'CSV',
  folder: 'GEE_Exports_Bolivia'
});

print('✅ Tarea 4/4: Resumen ejecutivo lista para exportar');

// ---------- 12. RESUMEN FINAL ----------
print('');
print('🎯 ===========================================');
print('RESUMEN EJECUTIVO');
print('===========================================');

print('📋 METODOLOGÍA:');
print('   • Datos: Hansen Global Forest Change v1.11 (2023)');
print('   • Resolución: 30 metros');
print('   • Período: 2001-2023');
print('   • Bosque definido como >' + umbralBosque + '% cobertura arbórea');
print('   • Biomasa promedio: ' + biomasaPromedio + ' Mg/ha');
print('   • Precio carbono: ' + precioCarbono + ' USD/Mg CO₂');

print('');
print('🔑 HALLAZGOS PRINCIPALES:');
print('   1. Bolivia perdió aproximadamente ' + areaPerdidaHa.getInfo().toFixed(0) + ' ha de bosque');
print('   2. Esto representa el ' + porcentajePerdida.getInfo().toFixed(1) + '% del bosque existente en 2000');
print('   3. Tasa anual promedio: ' + tasaAnualHa.getInfo().toFixed(0) + ' ha/año');
print('   4. Valor económico estimado: ' + valorMillonesUSD.getInfo().toFixed(0) + ' millones USD');

print('');
print('🗺️ VISUALIZACIÓN DISPONIBLE:');
print('   • Mapa 1: Pérdida forestal 2001-2023 (rojo) - ACTIVO');
print('   • Mapa 2: Cobertura arbórea 2000 (gradiente verde-azul)');
print('   • Mapa 3: Año de pérdida (gradiente temporal)');
print('   • Mapa 4: Composición RGB (bosque/pérdida/año)');
print('   • Mapa 5: Regiones ecológicas');
print('   • Mapa 6: Límites nacionales - ACTIVO');

print('');
print('📊 GRÁFICOS GENERADOS:');
print('   1. Pérdida forestal anual (2001-2023)');
print('   2. Comparación por región ecológica');
print('   3. Porcentaje de pérdida por región');

print('');
print('💾 EXPORTACIONES DISPONIBLES (pestaña "Tasks"):');
print('   1. GeoTIFF de pérdida anual (30m resolución)');
print('   2. CSV de estadísticas por región');
print('   3. CSV de serie temporal 2001-2023');
print('   4. CSV de resumen ejecutivo');

print('');
print('✅ ANÁLISIS COMPLETADO EXITOSAMENTE');
print('===========================================');

// Mostrar mensaje final con información útil
print('');
print('📌 INFORMACIÓN ADICIONAL:');
print('   • Para exportar: Vaya a la pestaña "Tasks" y haga clic en RUN');
print('   • Para ver mapas: Use el panel de capas en el visor');
print('   • Para más detalles: Expanda los gráficos en la consola');
print('   • Datos se guardarán en: Google Drive → GEE_Exports_Bolivia');