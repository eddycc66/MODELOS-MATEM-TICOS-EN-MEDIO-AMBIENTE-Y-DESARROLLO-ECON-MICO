// ==============================================
// PRÁCTICA 2: MODELOS CON IMÁGENES SATELITALES
// ==============================================

// 1. DEFINIR ÁREAS DE ESTUDIO
var lagoTiticaca = ee.Geometry.Rectangle([-69.5, -16.0, -68.5, -15.0]);
var bosqueChiquitano = ee.Geometry.Rectangle([-62.0, -18.5, -59.0, -16.0]);

// 2. MODELO DE PESQUERÍA
print('=== MODELO DE PESQUERÍA - LAGO TITICACA ===');
var r = 0.65; // Tasa crecimiento
var K = 50000; // Capacidad carga kg
var q = 0.002; // Capturabilidad
var E_actual = 400; // Esfuerzo actual barcos

var MSY = (r * K) / 4;
var E_MSY = r / (2 * q);
var P_MSY = K / 2;
var captura_actual = q * E_actual * P_MSY;

print('MSY:', MSY.toFixed(0), 'kg/año');
print('Esfuerzo óptimo (E_MSY):', E_MSY.toFixed(0), 'barcos');
print('Biomasa objetivo (P_MSY):', P_MSY.toFixed(0), 'kg');
print('Captura actual:', captura_actual.toFixed(0), 'kg/año');
print('Estado:', E_actual > E_MSY ? 'SOBREPESCA' : 'SOSTENIBLE');

// 3. ANÁLISIS SATELITAL LAGO TITICACA
print('\n=== ANÁLISIS SATELITAL LAGO TITICACA ===');

// Cargar Sentinel-2 - usar años con datos disponibles
var sentinelCollection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(lagoTiticaca)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30));

// Probar diferentes años hasta encontrar imágenes
var years = [2023, 2022, 2021];
var sentinel2 = null;

for (var i = 0; i < years.length; i++) {
  var year = years[i];
  var filtered = sentinelCollection
    .filterDate(year + '-06-01', year + '-09-30') // Época seca
    .median();
    
  if (filtered.bandNames().size().getInfo() > 0) {
    sentinel2 = filtered.clip(lagoTiticaca);
    print('Usando imágenes del año:', year);
    break;
  }
}

if (!sentinel2) {
  // Si no hay imágenes medianas, usar la primera disponible
  sentinel2 = sentinelCollection.first().clip(lagoTiticaca);
  print('Usando primera imagen disponible');
}

// Calcular NDWI
var ndwi = sentinel2.normalizedDifference(['B3', 'B8']).rename('NDWI');

// Configurar visualización Lago Titicaca
var visParamsLago = {
  bands: ['B4', 'B3', 'B2'],
  min: 0,
  max: 3000,
  gamma: 1.4
};

var visParamsNDWI = {
  min: -0.5,
  max: 0.5,
  palette: ['FF0000', 'FFFF00', '00FF00', '0000FF']
};

// Crear mapa para Lago Titicaca
var mapaLago = ui.Map();
mapaLago.centerObject(lagoTiticaca, 10);

// Añadir todas las capas VISIBLES
mapaLago.addLayer(sentinel2, visParamsLago, 'Sentinel-2 RGB', true);
mapaLago.addLayer(ndwi, visParamsNDWI, 'NDWI - Índice de Agua', true);

// Clasificar agua
var agua = ndwi.gt(0.1); // Umbral ajustado
mapaLago.addLayer(agua, {palette: ['000000', '0066FF']}, 'Agua (NDWI > 0.1)', true);

// Calcular área de agua
var area_agua_m2 = agua.multiply(ee.Image.pixelArea())
  .reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: lagoTiticaca,
    scale: 100,
    maxPixels: 1e9
  }).get('NDWI');

var area_agua_km2 = ee.Number(area_agua_m2).divide(1e6);
print('Área de agua detectada:', area_agua_km2.getInfo(), 'km²');

// 4. MODELO FORESTAL
print('\n=== MODELO FORESTAL - BOSQUE CHIQUITANO ===');

var area_total = 10000; // ha
var crecimiento = 0.03; // 3%
var stock_ha = 150; // m³/ha
var valor_madera = 80; // USD/m³
var costo_cosecha = 20; // USD/m³
var tasa_descuento = 0.05; // 5%

var volumen_total = area_total * stock_ha;
var valor_total = volumen_total * (valor_madera - costo_cosecha);
var T_optimo = Math.round(1 / tasa_descuento * Math.log(1 + crecimiento / tasa_descuento));
var area_cosecha_anual = area_total / T_optimo;
var volumen_anual = area_cosecha_anual * stock_ha;

print('Volumen total:', volumen_total.toLocaleString(), 'm³');
print('Valor económico total: $', valor_total.toLocaleString());
print('Rotación óptima:', T_optimo, 'años');
print('Cosecha sostenible anual:', area_cosecha_anual.toFixed(0), 'ha');
print('Volumen anual:', volumen_anual.toFixed(0), 'm³');

// 5. ANÁLISIS SATELITAL BOSQUE CHIQUITANO
print('\n=== ANÁLISIS SATELITAL BOSQUE CHIQUITANO ===');

// Cargar Landsat 8
var landsatCollection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
  .filterBounds(bosqueChiquitano);

// Buscar imágenes por año
var landsat = null;
for (var j = 0; j < years.length; j++) {
  var year = years[j];
  var filteredLandsat = landsatCollection
    .filterDate(year + '-01-01', year + '-12-31')
    .filter(ee.Filter.lt('CLOUD_COVER', 30))
    .median();
    
  if (filteredLandsat.bandNames().size().getInfo() > 0) {
    landsat = filteredLandsat.clip(bosqueChiquitano);
    print('Landsat año:', year);
    break;
  }
}

if (!landsat) {
  landsat = landsatCollection.first().clip(bosqueChiquitano);
}

// Calcular NDVI
var ndvi = landsat.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI');

// Configurar visualización Bosque
var visParamsLandsat = {
  bands: ['SR_B4', 'SR_B3', 'SR_B2'],
  min: 0,
  max: 30000,
  gamma: 1.4
};

var visParamsNDVI = {
  min: -0.2,
  max: 0.8,
  palette: ['8B4513', 'F4A460', '90EE90', '228B22', '006400']
};

// Crear mapa para Bosque Chiquitano
var mapaBosque = ui.Map();
mapaBosque.centerObject(bosqueChiquitano, 8);

// Añadir todas las capas VISIBLES
mapaBosque.addLayer(landsat, visParamsLandsat, 'Landsat 8 RGB', true);
mapaBosque.addLayer(ndvi, visParamsNDVI, 'NDVI - Índice Vegetación', true);

// Clasificar vegetación
var veg_muy_densa = ndvi.gt(0.6);
var veg_densa = ndvi.gt(0.4).and(ndvi.lte(0.6));
var veg_moderada = ndvi.gt(0.2).and(ndvi.lte(0.4));
var veg_baja = ndvi.lte(0.2);

// Añadir capas clasificadas VISIBLES
mapaBosque.addLayer(veg_muy_densa, {palette: ['000000', '006400']}, 'Vegetación muy densa (NDVI > 0.6)', true);
mapaBosque.addLayer(veg_densa, {palette: ['000000', '228B22']}, 'Vegetación densa (NDVI 0.4-0.6)', true);
mapaBosque.addLayer(veg_moderada, {palette: ['000000', '90EE90']}, 'Vegetación moderada (NDVI 0.2-0.4)', true);
mapaBosque.addLayer(veg_baja, {palette: ['000000', 'F4A460']}, 'Vegetación baja (NDVI < 0.2)', true);

// Calcular áreas
function calcularArea(categoria) {
  var area_m2 = categoria.multiply(ee.Image.pixelArea())
    .reduceRegion({
      reducer: ee.Reducer.sum(),
      geometry: bosqueChiquitano,
      scale: 100,
      maxPixels: 1e9
    }).get(categoria.bandNames().get(0));
  return ee.Number(area_m2).divide(10000); // Convertir a hectáreas
}

var area_total_bosque = ee.Number(bosqueChiquitano.area()).divide(10000);
var area_veg_densa = calcularArea(veg_densa);
var area_veg_muy_densa = calcularArea(veg_muy_densa);

print('Área total bosque:', area_total_bosque.getInfo(), 'ha');
print('Área vegetación densa:', area_veg_densa.getInfo(), 'ha');
print('Área vegetación muy densa:', area_veg_muy_densa.getInfo(), 'ha');

// 6. INTERFAZ CON PANEL DE CONTROL
print('\n=== INTERFAZ INTERACTIVA ===');

// Crear panel de control
var panelControl = ui.Panel({
  widgets: [
    ui.Label('🌍 PRÁCTICA 2 - CONTROL', {
      fontWeight: 'bold',
      fontSize: '16px',
      color: 'white',
      backgroundColor: '#1a73e8',
      padding: '10px',
      textAlign: 'center'
    }),
    ui.Label('LAGO TITICACA:', {fontWeight: 'bold', margin: '10px 0 5px 0'}),
    ui.Label('MSY: ' + MSY.toFixed(0) + ' kg/año'),
    ui.Label('Esf. óptimo: ' + E_MSY.toFixed(0) + ' barcos'),
    ui.Label('Agua detectada: ' + area_agua_km2.getInfo() + ' km²'),
    
    ui.Label('BOSQUE CHIQUITANO:', {fontWeight: 'bold', margin: '10px 0 5px 0'}),
    ui.Label('Rotación: ' + T_optimo + ' años'),
    ui.Label('Cosecha anual: ' + area_cosecha_anual.toFixed(0) + ' ha'),
    ui.Label('Veg. densa: ' + area_veg_densa.getInfo() + ' ha')
  ],
  style: {
    position: 'top-right',
    padding: '10px',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    border: '2px solid #1a73e8',
    borderRadius: '10px',
    width: '300px'
  }
});

// Botón para cambiar mapas
var botonCambiar = ui.Button({
  label: '🔄 VER BOSQUE CHIQUITANO',
  onClick: function() {
    ui.root.widgets().reset([mapaBosque, panelControl]);
    botonCambiar.setLabel('🔄 VER LAGO TITICACA');
  },
  style: {
    backgroundColor: '#4285F4',
    color: 'white',
    padding: '10px',
    margin: '10px 0',
    border: 'none',
    borderRadius: '5px',
    fontWeight: 'bold',
    width: '100%'
  }
});

panelControl.add(botonCambiar);

// Botón para exportar
var botonExportar = ui.Button({
  label: '💾 EXPORTAR IMÁGENES',
  onClick: function() {
    print('Exportando imágenes...');
    
    // Exportar NDWI
    Export.image.toDrive({
      image: ndwi,
      description: 'NDWI_Lago_Titicaca',
      scale: 100,
      region: lagoTiticaca,
      maxPixels: 1e9,
      folder: 'GEE_Practica2',
      fileFormat: 'GeoTIFF'
    });
    
    // Exportar NDVI
    Export.image.toDrive({
      image: ndvi,
      description: 'NDVI_Bosque_Chiquitano',
      scale: 100,
      region: bosqueChiquitano,
      maxPixels: 1e9,
      folder: 'GEE_Practica2',
      fileFormat: 'GeoTIFF'
    });
    
    print('✅ Revise la pestaña "Tasks" para ejecutar exportaciones');
  },
  style: {
    backgroundColor: '#34A853',
    color: 'white',
    padding: '10px',
    margin: '5px 0',
    border: 'none',
    borderRadius: '5px',
    fontWeight: 'bold',
    width: '100%'
  }
});

panelControl.add(botonExportar);

// 7. INICIALIZAR INTERFAZ
ui.root.widgets().reset([mapaLago, panelControl]);

print('✅ Código ejecutado correctamente');
print('✅ Use el panel de control para cambiar entre mapas');
print('✅ Todas las capas están VISIBLES por defecto');

// 8. LEYENDA VISUAL
var leyenda = ui.Panel({
  widgets: [
    ui.Label('🎨 LEYENDA', {fontWeight: 'bold', margin: '0 0 5px 0'}),
    ui.Label('🌊 Azul = Agua (NDWI > 0.1)'),
    ui.Label('🌿 Verde oscuro = Veg. muy densa'),
    ui.Label('🌿 Verde claro = Veg. densa'),
    ui.Label('🟡 Amarillo = Veg. moderada'),
    ui.Label('🟤 Café = Veg. baja/suelo')
  ],
  style: {
    position: 'bottom-left',
    padding: '10px',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    border: '1px solid #ddd',
    borderRadius: '5px'
  }
});

ui.root.add(leyenda);