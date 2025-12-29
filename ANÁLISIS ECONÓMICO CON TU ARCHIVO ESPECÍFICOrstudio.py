# ============================================
# ANÁLISIS ECONÓMICO CON TU ARCHIVO ESPECÍFICO
# Archivo: datos_hidrologicos.csv
# ============================================

# 1. CARGAR PAQUETES NECESARIOS
if(!require("readr")) install.packages("readr", quiet = TRUE)
if(!require("ggplot2")) install.packages("ggplot2", quiet = TRUE)
if(!require("dplyr")) install.packages("dplyr", quiet = TRUE)
if(!require("scales")) install.packages("scales", quiet = TRUE)
if(!require("knitr")) install.packages("knitr", quiet = TRUE)

library(readr)
library(ggplot2)
library(dplyr)
library(scales)
library(knitr)

# 2. VERIFICAR QUE EL ARCHIVO EXISTE
cat("🔍 BUSCANDO TU ARCHIVO: datos_hidrologicos.csv\n")
cat("=============================================\n\n")

if(file.exists("datos_hidrologicos.csv")) {
  cat("✅ ARCHIVO ENCONTRADO\n")
  cat("   Tamaño:", round(file.size("datos_hidrologicos.csv")/1024, 1), "KB\n")
  
  # 3. LEER EL ARCHIVO
  cat("\n📥 LEYENDO EL ARCHIVO...\n")
  datos <- read_csv("datos_hidrologicos.csv", show_col_types = FALSE)
  
  cat("✅ ARCHIVO LEÍDO CORRECTAMENTE\n")
  cat("   Filas:", nrow(datos), "\n")
  cat("   Columnas:", ncol(datos), "\n")
  
  # 4. MOSTRAR ESTRUCTURA COMPLETA
  cat("\n📊 ESTRUCTURA DE TUS DATOS:\n")
  cat("=============================\n")
  
  # Mostrar nombres de columnas
  cat("\n🔠 NOMBRES DE COLUMNAS:\n")
  cat(paste("   ", paste(names(datos), collapse = " | "), "\n"))
  
  # Mostrar tipos de datos
  cat("\n🔧 TIPOS DE DATOS:\n")
  tipos <- sapply(datos, class)
  for(i in 1:length(tipos)) {
    cat(sprintf("   %-20s: %s\n", names(tipos)[i], tipos[i]))
  }
  
  # 5. MOSTRAR LOS DATOS COMPLETOS
  cat("\n📈 DATOS COMPLETOS DE TU ARCHIVO:\n")
  cat("==================================\n")
  print(datos)
  
  # 6. ADAPTAR NOMBRES DE COLUMNAS (por si GEE exportó con otros nombres)
  cat("\n🔄 ADAPTANDO NOMBRES DE COLUMNAS...\n")
  
  # Buscar nombres similares
  nombres_originales <- names(datos)
  nombres_corregidos <- nombres_originales
  
  # Mapear nombres posibles
  mapa_nombres <- list(
    "area_total_km2" = c("area", "area_km2", "area_total", "area_cuenca"),
    "caudal_m3_s" = c("caudal", "caudal_m3", "caudal_estimado"),
    "area_bosque_ha" = c("bosque", "area_bosque", "forest_area"),
    "ndvi_promedio" = c("ndvi", "ndvi_mean", "ndvi_promedio"),
    "precipitacion_mm_anual" = c("precipitacion", "precip", "rainfall"),
    "coef_escorrentia" = c("coeficiente", "coef", "runoff")
  )
  
  # Intentar encontrar las columnas correctas
  for(nombre_ideal in names(mapa_nombres)) {
    encontrado <- FALSE
    for(patron in mapa_nombres[[nombre_ideal]]) {
      coincidencias <- grep(patron, nombres_originales, ignore.case = TRUE)
      if(length(coincidencias) > 0) {
        nombres_corregidos[coincidencias[1]] <- nombre_ideal
        cat(sprintf("   ✅ '%s' → '%s'\n", 
                    nombres_originales[coincidencias[1]], nombre_ideal))
        encontrado <- TRUE
        break
      }
    }
    if(!encontrado) {
      cat(sprintf("   ⚠️  No se encontró columna para: %s\n", nombre_ideal))
    }
  }
  
  # Actualizar nombres
  names(datos) <- nombres_corregidos
  
  # 7. VERIFICAR QUE TENEMOS LAS COLUMNAS NECESARIAS
  cat("\n🔍 VERIFICANDO COLUMNAS NECESARIAS...\n")
  
  columnas_necesarias <- c("area_total_km2", "caudal_m3_s", "area_bosque_ha", "ndvi_promedio")
  columnas_faltantes <- setdiff(columnas_necesarias, names(datos))
  
  if(length(columnas_faltantes) > 0) {
    cat("❌ COLUMNAS FALTANTES:\n")
    cat(paste("   -", columnas_faltantes, collapse = "\n"), "\n")
    
    cat("\n💡 SOLUCIÓN: Ingresa los valores manualmente:\n")
    
    # Pedir valores faltantes
    for(col in columnas_faltantes) {
      valor <- readline(paste("Valor para", col, ": "))
      datos[[col]] <- as.numeric(valor)
    }
  } else {
    cat("✅ TODAS LAS COLUMNAS NECESARIAS ESTÁN PRESENTES\n")
  }
  
  # 8. ANÁLISIS ECONÓMICO
  cat("\n")
  cat("╔══════════════════════════════════════════════╗\n")
  cat("║      ANÁLISIS ECONÓMICO CON TUS DATOS        ║\n")
  cat("╚══════════════════════════════════════════════╝\n")
  
  # Parámetros económicos
  precio_agua <- 0.75      # USD por m³
  tasa_descuento <- 0.05   # 5% anual
  periodo_anios <- 20      # años
  
  biomasa_ha <- 150        # toneladas/ha
  fraccion_carbono <- 0.47 # 47% de la biomasa es carbono
  precio_co2 <- 50         # USD/ton CO₂
  
  # 9. CÁLCULOS DEL AGUA
  cat("\n💧 ANÁLISIS DEL RECURSO HÍDRICO\n")
  cat("================================\n")
  
  # Mostrar valores del archivo
  cat(sprintf("\n📋 DATOS DE TU ARCHIVO:\n"))
  cat(sprintf("   • Área total: %.1f km²\n", datos$area_total_km2))
  cat(sprintf("   • Caudal: %.3f m³/s\n", datos$caudal_m3_s))
  
  if("precipitacion_mm_anual" %in% names(datos)) {
    cat(sprintf("   • Precipitación: %.0f mm/año\n", datos$precipitacion_mm_anual))
  }
  if("coef_escorrentia" %in% names(datos)) {
    cat(sprintf("   • Coef. escorrentía: %.2f\n", datos$coef_escorrentia))
  }
  
  # Cálculos
  segundos_por_anio <- 365 * 24 * 60 * 60
  caudal_anual_m3 <- datos$caudal_m3_s * segundos_por_anio
  valor_anual_agua <- caudal_anual_m3 * precio_agua
  factor_vpn <- (1 - (1 + tasa_descuento)^(-periodo_anios)) / tasa_descuento
  vpn_agua <- valor_anual_agua * factor_vpn
  
  cat(sprintf("\n💰 VALORACIÓN ECONÓMICA DEL AGUA:\n"))
  cat(sprintf("   • Caudal anual: %s m³\n", 
              format(round(caudal_anual_m3, 0), big.mark = ",", scientific = FALSE)))
  cat(sprintf("   • Valor anual: $%s USD\n", 
              format(round(valor_anual_agua, 0), big.mark = ",", scientific = FALSE)))
  cat(sprintf("   • VPN (%d años, %.1f%%): $%s USD\n", 
              periodo_anios, tasa_descuento*100,
              format(round(vpn_agua, 0), big.mark = ",", scientific = FALSE)))
  
  # 10. CÁLCULOS DEL BOSQUE
  cat("\n🌳 ANÁLISIS DE LA COBERTURA FORESTAL\n")
  cat("=====================================\n")
  
  cat(sprintf("\n📋 DATOS DE TU ARCHIVO:\n"))
  cat(sprintf("   • Área de bosque: %s ha\n", 
              format(round(datos$area_bosque_ha, 0), big.mark = ",", scientific = FALSE)))
  cat(sprintf("   • NDVI promedio: %.3f\n", datos$ndvi_promedio))
  
  # Estimación basada en NDVI
  factor_ndvi <- datos$ndvi_promedio / 0.8  # Ajuste por NDVI máximo estimado
  
  carbono_ha <- biomasa_ha * fraccion_carbono * factor_ndvi
  carbono_total <- carbono_ha * datos$area_bosque_ha
  co2_equivalente <- carbono_total * 3.67  # Conversión C a CO₂
  valor_anual_bosque <- co2_equivalente * precio_co2
  vpn_bosque <- valor_anual_bosque * factor_vpn
  
  cat(sprintf("\n💰 VALORACIÓN ECONÓMICA DEL BOSQUE:\n"))
  cat(sprintf("   • Biomasa estimada: %.0f ton/ha\n", biomasa_ha * factor_ndvi))
  cat(sprintf("   • Carbono por ha: %.1f ton C/ha\n", carbono_ha))
  cat(sprintf("   • Carbono total: %s ton C\n", 
              format(round(carbono_total, 0), big.mark = ",", scientific = FALSE)))
  cat(sprintf("   • CO₂ equivalente: %s ton CO₂\n", 
              format(round(co2_equivalente, 0), big.mark = ",", scientific = FALSE)))
  cat(sprintf("   • Valor anual: $%s USD\n", 
              format(round(valor_anual_bosque, 0), big.mark = ",", scientific = FALSE)))
  cat(sprintf("   • VPN (%d años): $%s USD\n", 
              periodo_anios,
              format(round(vpn_bosque, 0), big.mark = ",", scientific = FALSE)))
  
  # 11. TABLA DE RESULTADOS
  cat("\n")
  cat("╔══════════════════════════════════════════════════════════╗\n")
  cat("║               RESULTADOS ECONÓMICOS FINALES              ║\n")
  cat("╚══════════════════════════════════════════════════════════╝\n")
  
  resultados <- data.frame(
    `Servicio Ecosistémico` = c(
      "Suministro de agua", 
      "Captura de carbono"
    ),
    `Método de Valoración` = c(
      "Costos evitados de tratamiento",
      "Precio de mercado del CO₂"
    ),
    `Unidad` = c("m³/s", "ha"),
    `Cantidad` = c(
      sprintf("%.3f", datos$caudal_m3_s),
      format(round(datos$area_bosque_ha, 0), big.mark = ",", scientific = FALSE)
    ),
    `Valor Anual (USD)` = c(
      format(round(valor_anual_agua, 0), big.mark = ",", scientific = FALSE),
      format(round(valor_anual_bosque, 0), big.mark = ",", scientific = FALSE)
    ),
    `VPN 20 años (USD)` = c(
      format(round(vpn_agua, 0), big.mark = ",", scientific = FALSE),
      format(round(vpn_bosque, 0), big.mark = ",", scientific = FALSE)
    ),
    `VPN (Millones USD)` = c(
      sprintf("%.2f", vpn_agua / 1000000),
      sprintf("%.2f", vpn_bosque / 1000000)
    ),
    check.names = FALSE
  )
  
  # Mostrar tabla formateada
  print(kable(resultados, align = c("l", "l", "c", "r", "r", "r", "r")))
  
  # 12. GRÁFICOS
  cat("\n📊 GENERANDO VISUALIZACIONES...\n")
  
  # Preparar datos para gráficos
  datos_grafico <- data.frame(
    Categoria = c("Agua", "Bosque"),
    VPN = c(vpn_agua, vpn_bosque),
    ValorAnual = c(valor_anual_agua, valor_anual_bosque)
  )
  
  # Gráfico 1: Comparación de VPN
  p1 <- ggplot(datos_grafico, aes(x = reorder(Categoria, -VPN), y = VPN / 1000000, 
                                  fill = Categoria)) +
    geom_col(width = 0.7) +
    geom_text(aes(label = paste0("$", round(VPN/1000000, 1), "M")), 
              vjust = -0.5, size = 4.5, fontface = "bold") +
    scale_fill_manual(values = c("Agua" = "#1E88E5", "Bosque" = "#2E7D32")) +
    labs(
      title = "VALOR PRESENTE NETO (20 AÑOS)",
      subtitle = paste("Área de estudio:", round(datos$area_total_km2, 1), "km²"),
      x = "", 
      y = "Millones de USD",
      caption = paste("Tasa de descuento:", tasa_descuento*100, "% | Fuente: Análisis GEE + R")
    ) +
    theme_minimal(base_size = 12) +
    theme(
      plot.title = element_text(face = "bold", size = 16, hjust = 0.5),
      plot.subtitle = element_text(size = 12, hjust = 0.5, color = "gray40"),
      axis.text.x = element_text(size = 11, face = "bold"),
      legend.position = "none",
      panel.grid.minor = element_blank(),
      panel.grid.major.x = element_blank()
    ) +
    scale_y_continuous(labels = scales::dollar_format(suffix = "M"))
  
  print(p1)
  
  # Gráfico 2: Relación NDVI - Valor
  ndvi_valores <- seq(0.1, 0.9, by = 0.1)
  valor_por_ndvi <- 150 * 0.47 * (ndvi_valores / 0.8) * 3.67 * 50 * 10000 / 1000  # Miles USD/km²
  
  datos_ndvi <- data.frame(
    NDVI = ndvi_valores,
    Valor = valor_por_ndvi
  )
  
  p2 <- ggplot(datos_ndvi, aes(x = NDVI, y = Valor)) +
    geom_area(fill = "#C8E6C9", alpha = 0.6) +
    geom_line(color = "#2E7D32", size = 1.2) +
    geom_vline(xintercept = datos$ndvi_promedio, 
               color = "#D32F2F", linetype = "dashed", size = 1) +
    geom_point(aes(x = datos$ndvi_promedio, 
                   y = 150 * 0.47 * (datos$ndvi_promedio / 0.8) * 3.67 * 50 * 10000 / 1000),
               color = "#D32F2F", size = 4, shape = 18) +
    geom_text(aes(x = datos$ndvi_promedio, 
                  y = 150 * 0.47 * (datos$ndvi_promedio / 0.8) * 3.67 * 50 * 10000 / 1000,
                  label = paste0("Tu área\nNDVI = ", round(datos$ndvi_promedio, 3))),
              vjust = -0.5, color = "#D32F2F", size = 3.5, fontface = "bold") +
    labs(
      title = "RELACIÓN ENTRE NDVI Y VALOR DEL BOSQUE",
      subtitle = paste("Área forestal:", format(round(datos$area_bosque_ha, 0), big.mark = ","), "ha"),
      x = "Índice de Vegetación (NDVI)", 
      y = "Valor potencial (miles USD/km²)",
      caption = "Nota: Valor calculado por captura de carbono"
    ) +
    theme_minimal(base_size = 11) +
    theme(
      plot.title = element_text(face = "bold", size = 14, hjust = 0.5),
      plot.subtitle = element_text(size = 11, hjust = 0.5, color = "gray40"),
      axis.title = element_text(size = 10)
    ) +
    scale_x_continuous(breaks = seq(0.1, 0.9, by = 0.1)) +
    scale_y_continuous(labels = scales::dollar_format(suffix = "K"))
  
  print(p2)
  
  # 13. GUARDAR RESULTADOS
  cat("\n💾 GUARDANDO RESULTADOS...\n")
  
  # Crear nombre con fecha
  fecha_hora <- format(Sys.time(), "%Y%m%d_%H%M")
  archivo_resultados <- paste0("resultados_analisis_", fecha_hora, ".csv")
  
  # Guardar datos originales + resultados
  datos_completos <- datos
  datos_completos$valor_anual_agua_usd <- round(valor_anual_agua, 0)
  datos_completos$vpn_agua_usd <- round(vpn_agua, 0)
  datos_completos$valor_anual_bosque_usd <- round(valor_anual_bosque, 0)
  datos_completos$vpn_bosque_usd <- round(vpn_bosque, 0)
  datos_completos$vpn_total_usd <- round(vpn_agua + vpn_bosque, 0)
  datos_completos$fecha_analisis <- as.character(Sys.time())
  
  write_csv(datos_completos, archivo_resultados)
  
  # Guardar gráficos
  ggsave("grafico_vpn_comparacion.png", p1, width = 10, height = 7, dpi = 300)
  ggsave("grafico_ndvi_valor.png", p2, width = 10, height = 7, dpi = 300)
  
  # 14. RESUMEN FINAL
  cat("\n")
  cat("╔══════════════════════════════════════════════════════════╗\n")
  cat("║                    🎉 ANÁLISIS COMPLETO 🎉               ║\n")
  cat("╠══════════════════════════════════════════════════════════╣\n")
  cat(sprintf("║ 📍 Archivo analizado: %-30s ║\n", "datos_hidrologicos.csv"))
  cat(sprintf("║ 📅 Fecha de análisis: %-30s ║\n", format(Sys.time(), "%Y-%m-%d %H:%M")))
  cat("╠══════════════════════════════════════════════════════════╣\n")
  cat("║                    RESULTADOS CLAVE                      ║\n")
  cat("╠══════════════════════════════════════════════════════════╣\n")
  cat(sprintf("║ 🔹 Área total: %-10.1f km²                      ║\n", datos$area_total_km2))
  cat(sprintf("║ 🔹 Caudal: %-10.3f m³/s                         ║\n", datos$caudal_m3_s))
  cat(sprintf("║ 🔹 Bosque: %-10s ha                           ║\n", 
              format(round(datos$area_bosque_ha, 0), big.mark = ",", scientific = FALSE)))
  cat(sprintf("║ 🔹 NDVI: %-10.3f                               ║\n", datos$ndvi_promedio))
  cat("╠══════════════════════════════════════════════════════════╣\n")
  cat(sprintf("║ 💰 VPN Agua (20 años):  %15s USD ║\n", 
              format(round(vpn_agua, 0), big.mark = ",", scientific = FALSE)))
  cat(sprintf("║ 🌿 VPN Bosque (20 años): %15s USD ║\n", 
              format(round(vpn_bosque, 0), big.mark = ",", scientific = FALSE)))
  cat(sprintf("║ 🏆 VPN TOTAL:           %15s USD ║\n", 
              format(round(vpn_agua + vpn_bosque, 0), big.mark = ",", scientific = FALSE)))
  cat("╠══════════════════════════════════════════════════════════╣\n")
  cat("║                    ARCHIVOS GENERADOS                    ║\n")
  cat("╠══════════════════════════════════════════════════════════╣\n")
  cat(sprintf("║ 📄 %-45s ║\n", archivo_resultados))
  cat("║ 📈 grafico_vpn_comparacion.png                           ║\n")
  cat("║ 📊 grafico_ndvi_valor.png                                ║\n")
  cat("╚══════════════════════════════════════════════════════════╝\n")
  
  cat("\n📋 INTERPRETACIÓN DE RESULTADOS:\n")
  cat("   1. El VPN representa el valor económico total de conservar\n")
  cat("      estos servicios ecosistémicos durante 20 años.\n")
  cat("   2. El valor del agua se basa en los costos evitados de\n")
  cat("      tratamiento que la sociedad no tendría que pagar.\n")
  cat("   3. El valor del bosque se estima por su capacidad de\n")
  cat("      capturar carbono y mitigar el cambio climático.\n")
  cat("   4. Un NDVI más alto indica mayor productividad forestal\n")
  cat("      y mayor potencial de captura de carbono.\n")
  
} else {
  cat("❌ ERROR: El archivo 'datos_hidrologicos.csv' NO existe\n\n")
  cat("💡 SOLUCIONES:\n")
  cat("   1. Verifica que el archivo esté en la carpeta correcta\n")
  cat("   2. Lista los archivos disponibles:\n")
  print(list.files())
  cat("\n   3. Si el archivo tiene otro nombre, cámbialo a 'datos_hidrologicos.csv'\n")
  cat("   4. O modifica el código con el nombre correcto\n")
}