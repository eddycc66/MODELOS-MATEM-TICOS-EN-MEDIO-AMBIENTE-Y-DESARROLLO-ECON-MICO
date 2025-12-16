// ==============================================
// VALORACIÓN ECONÓMICA DE DEGRADACIÓN AMBIENTAL
// Modelo NDVI-Costo para Santa Cruz, Bolivia
// Google Earth Engine Script - Ejemplo Académico
// ==============================================

// 1. DEFINICIÓN DEL ÁREA DE ESTUDIO
// Polígono representativo de zonas agrícolas/periurbanas de Santa Cruz
var areaEstudio = ee.Geometry.Rectangle({
  coords: [-63.3, -17.9, -62.8, -17.6],
  geodesic: false,
  proj: 'EPSG:4326'
});

// Centrar el mapa en el área de estudio
Map.centerObject(areaEstudio, 10);

// 2. PARÁMETROS TEMPORALES
var fechaInicio = '2022-01-01';
var fechaFin = '2023-12-31';

// 3. VALOR ECONÓMICO ACADÉMICO (USD por hectárea)
var costoPorHectarea = 500; // Valor referencial para Bolivia

// 4. CARGA DE DATOS SENTINEL-2
var coleccionSentinel = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(areaEstudio)
  .filterDate(fechaInicio, fechaFin)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30));

print('Número de imágenes disponibles:', coleccionSentinel.size());

// 5. FUNCIÓN PARA ENMASCARAR NUBES Y SOMBRAS
function mascaraNubesS2(image) {
  // Banda SCL (Scene Classification Layer)
  var scl = image.select('SCL');
  
  // Máscara para:
  // 3: sombra de nubes
  // 8-9: nubes medias/altas
  // 10: cirros
  var mascaraNubes = scl.neq(3)
    .and(scl.neq(8))
    .and(scl.neq(9))
    .and(scl.neq(10));
  
  return image.updateMask(mascaraNubes);
}

// 6. APLICAR MÁSCARA A LA COLECCIÓN
var coleccionFiltrada = coleccionSentinel.map(mascaraNubesS2);

// 7. FUNCIÓN PARA CALCULAR NDVI
function calcularNDVI(imagen) {
  // B8: NIR (Banda 8A en S2 Harmonized)
  // B4: Rojo (Banda 4)
  var nir = imagen.select('B8');
  var rojo = imagen.select('B4');
  
  var ndvi = nir.subtract(rojo).divide(nir.add(rojo)).rename('NDVI');
  return imagen.addBands(ndvi);
}

// 8. APLICAR CÁLCULO DE NDVI
var coleccionNDVI = coleccionFiltrada.map(calcularNDVI);

// 9. COMPUESTO MEDIANO DE NDVI
var compuestoMediano = coleccionNDVI.median().clip(areaEstudio);
var ndviCompuesto = compuestoMediano.select('NDVI');

// 10. UMBRAL DE DEGRADACIÓN (NDVI < 0.3)
var umbralDegradacion = 0.3;
var areasDegradadas = ndviCompuesto.lt(umbralDegradacion);

// 11. CÁLCULO DE ÁREA DEGRADADA
// Calcular área por pixel (metros cuadrados)
var areaPixel = areasDegradadas.multiply(ee.Image.pixelArea());

// Sumar área total en metros cuadrados
var areaTotalM2 = areaPixel.reduceRegion({
  reducer: ee.Reducer.sum(),
  geometry: areaEstudio,
  scale: 10,
  maxPixels: 1e12,
  bestEffort: true
});

// Convertir a hectáreas (1 ha = 10,000 m²)
var areaTotalHa = ee.Number(areaTotalM2.get('NDVI')).divide(10000);

// 12. MODELO DE VALORACIÓN ECONÓMICA
// Cr = A × cs (Costo total = Área × costo por hectárea)
var costoTotal = areaTotalHa.multiply(costoPorHectarea);

// 13. IMPRIMIR RESULTADOS EN CONSOLA
print('==========================================');
print('RESULTADOS DE VALORACIÓN ECONÓMICA');
print('Departamento de Santa Cruz, Bolivia');
print('Período: ' + fechaInicio + ' a ' + fechaFin);
print('==========================================');
print('Área total degradada (NDVI < 0.3):', areaTotalHa, 'hectáreas');
print('Costo por hectárea:', costoPorHectarea, 'USD/ha');
print('COSTO TOTAL ESTIMADO DE REMEDIACIÓN:', costoTotal, 'USD');
print('==========================================');

// 14. VISUALIZACIÓN EN EL MAPA
// 14.1. Definir rangos de colores basados en la interpretación
var rangosNDVI = [
  {min: -1.0, max: 0.0, color: 'red', label: 'Suelo/Agua'},
  {min: 0.0, max: 0.2, color: 'orange', label: 'Vegetación escasa'},
  {min: 0.2, max: 0.3, color: 'yellow', label: 'Vegetación pobre'},
  {min: 0.3, max: 0.6, color: 'greenyellow', label: 'Vegetación moderada'},
  {min: 0.6, max: 0.8, color: 'green', label: 'Vegetación densa'},
  {min: 0.8, max: 1.0, color: 'darkgreen', label: 'Vegetación muy densa'}
];

// 14.2. Crear una paleta que coincida exactamente con los rangos
var paletaNDVI = rangosNDVI.map(function(rango) {
  return rango.color;
});

// 14.3. Mostrar NDVI en el mapa con los rangos específicos
// Crear una imagen clasificada basada en los rangos
var ndviClasificado = ndviCompuesto;
// Inicializar con valores NaN
ndviClasificado = ndviClasificado.where(ndviCompuesto.lt(-1), -9999);

// Aplicar cada rango
for (var i = 0; i < rangosNDVI.length; i++) {
  var rango = rangosNDVI[i];
  var mascara = ndviCompuesto.gte(rango.min).and(ndviCompuesto.lt(rango.max));
  // Asignar el valor medio del rango para visualización
  var valorClase = (rango.min + rango.max) / 2;
  ndviClasificado = ndviClasificado.where(mascara, valorClase);
}

// Manejar el valor máximo (1.0)
ndviClasificado = ndviClasificado.where(ndviCompuesto.eq(1.0), 0.9);

// 14.4. Mostrar NDVI clasificado con la paleta específica
Map.addLayer(ndviClasificado, {
  min: -0.5, // Ajustado para mejor visualización
  max: 0.9,  // Ajustado para mejor visualización
  palette: paletaNDVI,
  opacity: 0.8
}, 'NDVI 2022-2023 (Clasificado)');

// 14.5. Mostrar áreas degradadas (naranja semitransparente)
Map.addLayer(areasDegradadas.selfMask(), {
  palette: ['#FF4500'], // Naranja intenso
  opacity: 0.7
}, 'Áreas Degradadas (NDVI < 0.3)');

// 14.6. Mostrar área de estudio
Map.addLayer(areaEstudio, {
  color: 'blue',
  fillColor: '00000000',
  width: 2
}, 'Área de Estudio');

// 15. LEYENDA PERSONALIZADA
var leyenda = ui.Panel({
  style: {
    position: 'bottom-left',
    padding: '8px 15px',
    backgroundColor: 'white',
    border: '1px solid gray',
    borderRadius: '5px'
  }
});

// Título de la leyenda
var tituloLeyenda = ui.Label({
  value: 'Interpretación NDVI',
  style: {
    fontWeight: 'bold',
    fontSize: '14px',
    margin: '0px 0px 8px 0px',
    padding: '0px'
  }
});

leyenda.add(tituloLeyenda);

// Agregar cada rango a la leyenda
for (var i = 0; i < rangosNDVI.length; i++) {
  var rango = rangosNDVI[i];
  
  var fila = ui.Panel({
    layout: ui.Panel.Layout.Flow('horizontal'),
    style: {margin: '0px 0px 4px 0px'}
  });
  
  var colorBox = ui.Label({
    style: {
      backgroundColor: rango.color,
      padding: '10px',
      margin: '0px 8px 0px 0px',
      width: '20px',
      height: '10px'
    }
  });
  
  var descripcion = ui.Label({
    value: rango.label + ' (' + rango.min.toFixed(1) + ' a ' + rango.max.toFixed(1) + ')',
    style: {
      margin: '0px',
      fontSize: '12px'
    }
  });
  
  fila.add(colorBox);
  fila.add(descripcion);
  leyenda.add(fila);
}

// Agregar línea separadora
var separador = ui.Label({
  value: '─────────────────────────',
  style: {margin: '4px 0px', color: '#666', fontSize: '12px'}
});
leyenda.add(separador);

// Información sobre áreas degradadas
var infoDegradacion = ui.Label({
  value: 'Áreas degradadas: NDVI < 0.3',
  style: {
    fontWeight: 'bold',
    fontSize: '12px',
    margin: '4px 0px 2px 0px',
    color: '#FF4500'
  }
});
leyenda.add(infoDegradacion);

var ejemplosDegradacion = ui.Label({
  value: '(Suelo expuesto, vegetación muy pobre)',
  style: {fontSize: '11px', margin: '0px 0px 4px 0px', color: '#666'}
});
leyenda.add(ejemplosDegradacion);

// 16. PANEL DE RESULTADOS NUMÉRICOS
var panelResultados = ui.Panel({
  style: {
    position: 'top-right',
    padding: '10px 15px',
    backgroundColor: 'white',
    border: '2px solid darkred',
    borderRadius: '5px',
    width: '320px'
  }
});

var tituloResultados = ui.Label({
  value: 'Resultados Económicos',
  style: {
    fontWeight: 'bold',
    fontSize: '16px',
    color: 'darkred',
    margin: '0px 0px 10px 0px'
  }
});

panelResultados.add(tituloResultados);

// Función para formatear números con separadores de miles
function formatNumber(num, decimals) {
  var numValue = ee.Number(num).getInfo();
  return numValue.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Obtener valores formateados
var areaFormateada = formatNumber(areaTotalHa, 2);
var costoFormateado = formatNumber(costoTotal, 0);

// Crear panel para área degradada
var panelArea = ui.Panel({
  layout: ui.Panel.Layout.Flow('vertical'),
  style: {margin: '0px 0px 12px 0px'}
});

var labelAreaTitulo = ui.Label({
  value: 'Área degradada (NDVI < 0.3):',
  style: {
    fontWeight: 'bold',
    margin: '0px 0px 3px 0px',
    fontSize: '13px'
  }
});

var labelAreaValor = ui.Label({
  value: areaFormateada + ' hectáreas',
  style: {
    margin: '0px',
    fontSize: '14px',
    color: '#B22222'
  }
});

panelArea.add(labelAreaTitulo);
panelArea.add(labelAreaValor);

// Crear panel para costo total
var panelCosto = ui.Panel({
  layout: ui.Panel.Layout.Flow('vertical'),
  style: {margin: '0px 0px 12px 0px'}
});

var labelCostoTitulo = ui.Label({
  value: 'Costo estimado de remediación:',
  style: {
    fontWeight: 'bold',
    margin: '0px 0px 3px 0px',
    fontSize: '13px'
  }
});

var labelCostoValor = ui.Label({
  value: 'US$ ' + costoFormateado,
  style: {
    margin: '0px',
    fontSize: '16px',
    fontWeight: 'bold',
    color: '#006400'
  }
});

panelCosto.add(labelCostoTitulo);
panelCosto.add(labelCostoValor);

// Información del modelo
var labelModelo = ui.Label({
  value: 'Modelo: Cr = A × cs',
  style: {
    fontStyle: 'italic',
    fontSize: '12px',
    margin: '8px 0px 3px 0px',
    color: '#555'
  }
});

var labelCostoHectarea = ui.Label({
  value: 'cs = 500 USD/hectárea (valor referencial)',
  style: {
    fontSize: '11px',
    margin: '0px 0px 8px 0px',
    color: '#666'
  }
});

// Agregar paneles al panel principal
panelResultados.add(panelArea);
panelResultados.add(panelCosto);
panelResultados.add(labelModelo);
panelResultados.add(labelCostoHectarea);

// 17. AGREGAR LEYENDA Y PANEL AL MAPA
Map.add(leyenda);
Map.add(panelResultados);

// 18. EXPORTACIÓN OPcional (GeoTIFF)
// Preparar imagen para exportación
var imagenExportar = ndviCompuesto
  .addBands(areasDegradadas.rename('degradacion'))
  .addBands(ndviClasificado.rename('ndvi_clasificado'));

// Configuración de exportación (comentada por defecto)
/*
Export.image.toDrive({
  image: imagenExportar,
  description: 'NDVI_Degradacion_SantaCruz',
  scale: 10,
  region: areaEstudio,
  fileFormat: 'GeoTIFF',
  maxPixels: 1e12
});
*/

print('Nota: Para activar la exportación a Google Drive, descomenta las líneas de Export.image.toDrive');
print('==========================================');

// 19. INFORMACIÓN ACADÉMICA
print('INFORMACIÓN ACADÉMICA:');
print('Modelo matemático implementado: Cr = A × cs');
print('Cr = Costo total de remediación (USD)');
print('A = Área degradada (hectáreas)');
print('cs = Costo por hectárea (500 USD/ha, valor académico referencial)');
print('==========================================');
print('Interpretación NDVI:');
print('- NDVI < 0.0: Cuerpos de agua');
print('- NDVI 0.0 - 0.2: Suelo desnudo/vegetación muy escasa');
print('- NDVI 0.2 - 0.3: Vegetación pobre (umbral de degradación)');
print('- NDVI 0.3 - 0.6: Vegetación moderada (pastizales, cultivos)');
print('- NDVI 0.6 - 0.8: Vegetación densa (bosques, cultivos maduros)');
print('- NDVI > 0.8: Vegetación muy densa (bosques tropicales)');
print('==========================================');
print('Relación con contaminación/degradación:');
print('NDVI bajo (<0.3) puede indicar:');
print('1. Contaminación del suelo por agroquímicos');
print('2. Degradación por sobrepastoreo');
print('3. Pérdida de cobertura vegetal por expansión urbana');
print('4. Erosión hídrica o eólica');
print('5. Salinización de suelos');
print('==========================================');