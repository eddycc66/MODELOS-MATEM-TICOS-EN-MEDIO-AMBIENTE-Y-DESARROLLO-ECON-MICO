/***************************************
 MODELO HIDROLÓGICO CONCEPTUAL EN GEE
 Autor: Edwin Calle Condori
***************************************/

// ===============================
// 1. ÁREA DE ESTUDIO
// ===============================
var aoi = ee.Geometry.Rectangle([-64.3, -17.9, -63.7, -17.4]); // AJUSTA
Map.centerObject(aoi, 9);
Map.addLayer(aoi, {color: 'red'}, 'Área de estudio');

// ===============================
// 2. PRECIPITACIÓN - CHIRPS
// ===============================
var chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
  .filterBounds(aoi)
  .filterDate('2018-01-01', '2023-12-31');

var P = chirps.mean().clip(aoi);
Map.addLayer(P, {min: 0, max: 10, palette: ['white','blue']}, 'Precipitación media');

// Serie temporal
var pptChart = ui.Chart.image.series({
  imageCollection: chirps,
  region: aoi,
  reducer: ee.Reducer.mean(),
  scale: 5000
}).setOptions({
  title: 'Serie temporal de precipitación (CHIRPS)',
  vAxis: {title: 'mm/día'},
  hAxis: {title: 'Fecha'}
});
print(pptChart);

// ===============================
// 3. DEM - PENDIENTE
// ===============================
var dem = ee.Image('USGS/SRTMGL1_003').clip(aoi);
var slope = ee.Terrain.slope(dem);

Map.addLayer(slope,
  {min: 0, max: 40, palette: ['green','yellow','red']},
  'Pendiente (%)'
);

// ===============================
// 4. SENTINEL-2 (SOLO BANDAS NECESARIAS)
// ===============================
var s2 = ee.ImageCollection('COPERNICUS/S2_SR')
  .filterBounds(aoi)
  .filterDate('2023-01-01', '2023-12-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .select(['B4','B8'])   // 🔴 CLAVE PARA EVITAR ERROR
  .median()
  .clip(aoi);

// NDVI
var ndvi = s2.normalizedDifference(['B8','B4']).rename('NDVI');
Map.addLayer(ndvi,
  {min: 0, max: 1, palette: ['brown','yellow','green']},
  'NDVI'
);

// ===============================
// 5. INFILTRACIÓN (I)
// ===============================
var I = ndvi.multiply(0.6).add(0.1).rename('Infiltration');
Map.addLayer(I,
  {min: 0.1, max: 0.7, palette: ['red','blue']},
  'Infiltración'
);

// ===============================
// 6. ESCORRENTÍA SUPERFICIAL (Q)
// ===============================
var runoffCoeff = slope.divide(45)
  .add(ndvi.multiply(-0.5))
  .clamp(0.05, 0.9);

var Q = P.multiply(runoffCoeff).rename('Runoff');
Map.addLayer(Q,
  {min: 0, max: 5, palette: ['lightblue','purple']},
  'Escorrentía'
);

// ===============================
// 7. MODELO HIDROLÓGICO
// dW/dt = P - Q - I
// ===============================
var dW = P.subtract(Q).subtract(I.multiply(P))
  .rename('dW_dt');

Map.addLayer(dW,
  {min: -5, max: 5, palette: ['red','white','blue']},
  'Cambio de almacenamiento (dW/dt)'
);

// ===============================
// 8. EVENTOS EXTREMOS
// ===============================
var P95 = chirps.reduce(ee.Reducer.percentile([95])).clip(aoi);
Map.addLayer(P95,
  {min: 10, max: 80, palette: ['yellow','red']},
  'Precipitación extrema (P95)'
);

// ===============================
// 9. ESCENARIO CAMBIO CLIMÁTICO
// ===============================
var climateScenario = P95.multiply(1.2).rename('ClimateScenario');
Map.addLayer(climateScenario,
  {min: 15, max: 100, palette: ['orange','darkred']},
  'Escenario CC (+20%)'
);

// ===============================
// 10. MAPA DE RIESGO DE INUNDACIÓN
// ===============================
var floodRisk = Q
  .add(P95)
  .multiply(slope.divide(30))
  .rename('FloodRisk');

Map.addLayer(floodRisk,
  {min: 0, max: 50, palette: ['green','yellow','red']},
  'Riesgo de inundación');
