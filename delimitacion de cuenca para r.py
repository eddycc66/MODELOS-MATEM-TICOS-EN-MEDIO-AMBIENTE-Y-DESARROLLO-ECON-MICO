# Cargar librerías
library(whitebox)
library(terra)
library(sf)
library(raster)
library(mapview)
library(dplyr)
library(purrr)

# Configurar directorios
input_dir <- "D:/DOCENCIA UNIVERSITARIA/Siglo XX/Módulo 10/dato/input"
output_dir <- "D:/DOCENCIA UNIVERSITARIA/Siglo XX/Módulo 10/dato/output"

# Crear directorio de salida si no existe
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

# Inicializar WhiteboxTools
wbt_init()

# Cargar DEM
dem <- rast(file.path(input_dir, "dem.tif"))

# Obtener el CRS del DEM
dem_crs <- crs(dem)
print(paste("CRS del DEM:", dem_crs))

# Preprocesamiento del DEM
# Rellenar depresiones
wbt_fill_depressions(
  dem = file.path(input_dir, "dem.tif"),
  output = file.path(output_dir, "dem_filled.tif")
)
dem_filled <- rast(file.path(output_dir, "dem_filled.tif"))

# Calcular dirección de flujo (D8)
wbt_d8_pointer(
  dem = file.path(output_dir, "dem_filled.tif"),
  output = file.path(output_dir, "flow_direction.tif")
)

# Calcular acumulación de flujo
wbt_d8_flow_accumulation(
  input = file.path(output_dir, "dem_filled.tif"),
  output = file.path(output_dir, "flow_accumulation.tif")
)
flow_accum <- rast(file.path(output_dir, "flow_accumulation.tif"))

# Extraer red de drenaje (umbral de 1000 celdas)
wbt_extract_streams(
  flow_accum = file.path(output_dir, "flow_accumulation.tif"),
  output = file.path(output_dir, "stream_network.tif"),
  threshold = 1000
)
streams <- rast(file.path(output_dir, "stream_network.tif"))

# Convertir a vector
wbt_raster_streams_to_vector(
  streams = file.path(output_dir, "stream_network.tif"),
  d8_pntr = file.path(output_dir, "flow_direction.tif"),
  output = file.path(output_dir, "stream_network.shp")
)
stream_vect <- st_read(file.path(output_dir, "stream_network.shp"))

# Asegurar que el stream_vect tenga el mismo CRS que el DEM
st_crs(stream_vect) <- st_crs(dem)

# CORRECCIÓN: Crear punto de aforo con el CRS correcto
# Primero crear en WGS84 (coordenadas geográficas)
aforo_point_wgs84 <- st_sfc(st_point(c(-78.35130, -8.83242)), crs = 4326)

# Transformar al CRS del DEM
aforo_point <- st_transform(aforo_point_wgs84, crs = st_crs(dem))
aforo_sf <- st_sf(geometry = aforo_point)

# Verificar la ubicación del punto de aforo
print("Coordenadas del punto de aforo (en CRS del DEM):")
print(st_coordinates(aforo_point))

# Verificar si el punto está dentro de la extensión del DEM
dem_extent <- ext(dem)
aforo_coords <- st_coordinates(aforo_point)

if (aforo_coords[1, "X"] >= dem_extent[1] && aforo_coords[1, "X"] <= dem_extent[2] &&
    aforo_coords[1, "Y"] >= dem_extent[3] && aforo_coords[1, "Y"] <= dem_extent[4]) {
  print("✅ El punto de aforo está dentro de la extensión del DEM")
} else {
  print("❌ El punto de aforo está fuera de la extensión del DEM")
  print(paste("Extensión del DEM:", paste(dem_extent, collapse = ", ")))
  print(paste("Coordenadas del punto:", paste(aforo_coords[1,], collapse = ", ")))
}

st_write(aforo_sf, file.path(output_dir, "punto_aforo.shp"), delete_dsn = TRUE)

# Delimitar cuenca usando el punto de aforo
wbt_watershed(
  d8_pntr = file.path(output_dir, "flow_direction.tif"),
  pour_pts = file.path(output_dir, "punto_aforo.shp"),
  output = file.path(output_dir, "watershed.tif")
)
watershed <- rast(file.path(output_dir, "watershed.tif"))

# Recortar DEM a la cuenca
dem_cropped <- mask(dem_filled, watershed)
writeRaster(dem_cropped, file.path(output_dir, "dem_cropped.tif"), overwrite = TRUE)

# Encontrar el canal principal más cercano al punto de aforo
stream_points <- st_cast(stream_vect, "POINT")
closest_point <- stream_points[st_nearest_feature(aforo_point, stream_points),]
main_channel <- stream_vect[st_intersects(stream_vect, closest_point, sparse = FALSE),]

# Simulación de inundación de 2 metros
# Extraer elevación en el punto de aforo
aforo_elevation <- extract(dem_cropped, vect(aforo_point))

# Si no hay valor en el punto exacto, usar el valor más cercano
if (is.na(aforo_elevation[1,2])) {
  aforo_elevation <- terra::extract(dem_cropped, vect(aforo_point), method = "bilinear")
}

# Calcular nivel de inundación (elevación + 2 metros)
flood_level <- aforo_elevation[1,2] + 2

# Crear raster de áreas inundadas
flooded_areas <- dem_cropped < flood_level
writeRaster(flooded_areas, file.path(output_dir, "flooded_areas.tif"), overwrite = TRUE)

# Calcular estadísticas de inundación
flooded_values <- values(flooded_areas)
cell_area <- res(dem_cropped)[1] * res(dem_cropped)[2]  # m²
area_inundada_m2 <- sum(flooded_values, na.rm = TRUE) * cell_area
volumen_agua_m3 <- sum(flood_level - dem_cropped[flooded_areas], na.rm = TRUE) * cell_area

flood_stats <- data.frame(
  area_inundada_km2 = area_inundada_m2 / 1e6,
  volumen_agua_m3 = volumen_agua_m3
)

# Guardar estadísticas
write.csv(flood_stats, file.path(output_dir, "estadisticas_inundacion.csv"))

# Convertir áreas inundadas a polígonos para una mejor visualización
flooded_polygons <- as.polygons(flooded_areas)
flooded_polygons <- flooded_polygons[flooded_polygons$lyr.1 == 1,]

# Visualización con mapview - solución a los problemas de píxeles
visualizations <- list()

# Función para limpiar rasters para visualización
clean_raster_for_visualization <- function(raster_obj) {
  values(raster_obj)[!is.finite(values(raster_obj))] <- NA
  return(raster_obj)
}

# Limpiar los rasters
dem_clean <- clean_raster_for_visualization(dem)
dem_filled_clean <- clean_raster_for_visualization(dem_filled)
flow_accum_clean <- clean_raster_for_visualization(flow_accum)
watershed_clean <- clean_raster_for_visualization(watershed)
dem_cropped_clean <- clean_raster_for_visualization(dem_cropped)

# Agregar cada capa por separado con manejo de errores
tryCatch({
  visualizations <- c(visualizations, 
                      list(mapview(dem_clean, layer.name = "DEM Original", maxpixels = 500000)))
}, error = function(e) {
  message("Error al visualizar DEM Original: ", e$message)
})

tryCatch({
  visualizations <- c(visualizations, 
                      list(mapview(dem_filled_clean, layer.name = "DEM Rellenado", maxpixels = 500000)))
}, error = function(e) {
  message("Error al visualizar DEM Rellenado: ", e$message)
})

tryCatch({
  visualizations <- c(visualizations, 
                      list(mapview(flow_accum_clean, layer.name = "Acumulación de Flujo", maxpixels = 500000)))
}, error = function(e) {
  message("Error al visualizar Acumulación de Flujo: ", e$message)
})

tryCatch({
  visualizations <- c(visualizations, 
                      list(mapview(stream_vect, layer.name = "Red de Drenaje")))
}, error = function(e) {
  message("Error al visualizar Red de Drenaje: ", e$message)
})

tryCatch({
  visualizations <- c(visualizations, 
                      list(mapview(watershed_clean, layer.name = "Cuenca Delimitada", maxpixels = 500000)))
}, error = function(e) {
  message("Error al visualizar Cuenca Delimitada: ", e$message)
})

tryCatch({
  visualizations <- c(visualizations, 
                      list(mapview(dem_cropped_clean, layer.name = "DEM Recortado", maxpixels = 500000)))
}, error = function(e) {
  message("Error al visualizar DEM Recortado: ", e$message)
})

tryCatch({
  visualizations <- c(visualizations, 
                      list(mapview(main_channel, color = "blue", layer.name = "Canal Principal")))
}, error = function(e) {
  message("Error al visualizar Canal Principal: ", e$message)
})

tryCatch({
  visualizations <- c(visualizations, 
                      list(mapview(aforo_sf, col.regions = "red", layer.name = "Punto de Aforo")))
}, error = function(e) {
  message("Error al visualizar Punto de Aforo: ", e$message)
})

tryCatch({
  if (nrow(flooded_polygons) > 0) {
    visualizations <- c(visualizations, 
                        list(mapview(flooded_polygons, col.regions = "blue", 
                                     layer.name = paste0("Áreas Inundadas (", round(flood_level, 1), " m)"))))
  } else {
    message("No hay áreas inundadas para visualizar")
  }
}, error = function(e) {
  message("Error al visualizar Áreas Inundadas: ", e$message)
})

# Combinar visualizaciones si hay al menos una capa
if (length(visualizations) > 0) {
  final_map <- reduce(visualizations, `+`)
  print(final_map)
} else {
  message("No se pudo generar ninguna visualización")
}

# Guardar resultados
st_write(stream_vect, file.path(output_dir, "stream_network.gpkg"), delete_dsn = TRUE)
st_write(main_channel, file.path(output_dir, "main_channel.gpkg"), delete_dsn = TRUE)
st_write(aforo_sf, file.path(output_dir, "punto_aforo.gpkg"), delete_dsn = TRUE)

# Exportar reporte en PDF
pdf(file.path(output_dir, "resultados_inundacion.pdf"), width = 10, height = 8)
plot(dem, main = "DEM Original")
plot(dem_filled, main = "DEM Rellenado")
plot(flow_accum, main = "Acumulación de Flujo")
plot(stream_vect, main = "Red de Drenaje")
plot(watershed, main = "Cuenca Delimitada")
plot(dem_cropped, main = "DEM Recortado")
plot(main_channel, main = "Canal Principal")
plot(aforo_point, add = TRUE, col = "red", pch = 16, cex = 1.5)
if (nrow(flooded_polygons) > 0) {
  plot(flooded_polygons, main = paste0("Áreas Inundadas (Nivel: ", round(flood_level, 1), " m)"))
} else {
  plot.new()
  title(main = "No hay áreas inundadas")
}
dev.off()

# Mostrar resumen de resultados
cat("RESUMEN DE SIMULACIÓN DE INUNDACIÓN\n")
cat("==================================\n")
cat("Punto de aforo: Longitud = -78.35130, Latitud = -8.83242\n")
cat("Elevación en punto de aforo:", round(aforo_elevation[1,2], 2), "m\n")
cat("Nivel de inundación:", round(flood_level, 2), "m\n")
cat("Área inundada:", round(flood_stats$area_inundada_km2, 2), "km²\n")
cat("Volumen de agua:", round(flood_stats$volumen_agua_m3, 2), "m³\n")