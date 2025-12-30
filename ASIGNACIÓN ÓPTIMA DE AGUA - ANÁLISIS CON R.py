# ============================================
# ASIGNACIÓN ÓPTIMA DE AGUA - ANÁLISIS CON R
# ============================================

# Limpiar entorno de trabajo
rm(list = ls())
cat("\014") # Limpiar consola

# 1. INSTALAR Y CARGAR PAQUETES NECESARIOS
# ============================================

# Verificar e instalar paquetes si es necesario
paquetes_requeridos <- c("lpSolve", "ggplot2", "dplyr", "reshape2", "scales", "ggcorrplot")
paquetes_nuevos <- paquetes_requeridos[!(paquetes_requeridos %in% installed.packages()[,"Package"])]

if(length(paquetes_nuevos)) {
  install.packages(paquetes_nuevos)
}

# Cargar paquetes
library(lpSolve)     # Para programación lineal
library(ggplot2)     # Para gráficos
library(dplyr)       # Para manipulación de datos
library(reshape2)    # Para transformación de datos
library(scales)      # Para escalas en gráficos
library(ggcorrplot)  # Para gráficos de correlación

# 2. DEFINIR EL MODELO DE PROGRAMACIÓN LINEAL
# ============================================

cat("============================================\n")
cat("MODELO DE ASIGNACIÓN ÓPTIMA DE AGUA\n")
cat("============================================\n\n")

# Definir parámetros del problema
disponibilidad_total <- 100
min_agricola <- 30
min_industrial <- 20
min_domestico <- 25

# Coeficientes de la función objetivo (beneficios)
coef_objetivo <- c(3, 5, 4)  # c(x1, x2, x3)

# Matriz de restricciones
matriz_restricciones <- matrix(c(
  # x1, x2, x3
  1,  1,  1,  # Disponibilidad total
  1,  0,  0,  # Mínimo agrícola
  0,  1,  0,  # Mínimo industrial
  0,  0,  1   # Mínimo doméstico
), nrow = 4, byrow = TRUE)

# Dirección de las restricciones
direccion_restricciones <- c("<=", ">=", ">=", ">=")

# Lado derecho de las restricciones
lado_derecho <- c(disponibilidad_total, min_agricola, min_industrial, min_domestico)

# 3. RESOLVER EL MODELO DE PROGRAMACIÓN LINEAL
# ============================================

cat("Resolviendo el modelo de programación lineal...\n")

# Resolver el problema de maximización
solucion <- lp(direction = "max",
               objective.in = coef_objetivo,
               const.mat = matriz_restricciones,
               const.dir = direccion_restricciones,
               const.rhs = lado_derecho)

# Extraer resultados
valores_optimos <- solucion$solution
valor_optimo <- solucion$objval

# Mostrar resultados
cat("\nSOLUCIÓN ÓPTIMA:\n")
cat("================\n")
cat(sprintf("Agua asignada a uso agrícola (x₁): %.0f unidades\n", valores_optimos[1]))
cat(sprintf("Agua asignada a uso industrial (x₂): %.0f unidades\n", valores_optimos[2]))
cat(sprintf("Agua asignada a uso doméstico (x₃): %.0f unidades\n", valores_optimos[3]))
cat(sprintf("Beneficio social máximo (Z): %.0f unidades\n", valor_optimo))

# 4. ANÁLISIS DE SENSIBILIDAD
# ============================================

cat("\n\nANÁLISIS DE SENSIBILIDAD:\n")
cat("==========================\n")

# Obtener análisis de sensibilidad
sensibilidad <- lp(direction = "max",
                   objective.in = coef_objetivo,
                   const.mat = matriz_restricciones,
                   const.dir = direccion_restricciones,
                   const.rhs = lado_derecho,
                   compute.sens = TRUE)

# Mostrar precios duales (sensibilidad de las restricciones)
cat("\nPrecios duales (sensibilidad de restricciones):\n")
cat("-----------------------------------------------\n")
cat("Restricción 1 (Disponibilidad total):", sensibilidad$duals[1], "\n")
cat("  - Aumentar en 1 unidad la disponibilidad incrementaría Z en:", sensibilidad$duals[1], "\n")
cat("Restricción 2 (Mínimo agrícola):", sensibilidad$duals[2], "\n")
cat("Restricción 3 (Mínimo industrial):", sensibilidad$duals[3], "\n")
cat("Restricción 4 (Mínimo doméstico):", sensibilidad$duals[4], "\n")

# Mostrar rangos de optimalidad para coeficientes de la función objetivo
cat("\nRangos de optimalidad para coeficientes objetivo:\n")
cat("--------------------------------------------------\n")
for (i in 1:3) {
  cat(sprintf("Coeficiente %d (x%d): [%.2f, %.2f]\n", 
              i, i, 
              sensibilidad$sens.coef.from[i], 
              sensibilidad$sens.coef.to[i]))
}

# 5. ANÁLISIS ESTADÍSTICO Y VISUALIZACIÓN
# ============================================

# Crear data frame con los resultados
datos_asignacion <- data.frame(
  Uso = c("Agrícola", "Industrial", "Doméstico", "No asignado"),
  Asignacion = c(valores_optimos[1], valores_optimos[2], valores_optimos[3], 
                 disponibilidad_total - sum(valores_optimos)),
  Beneficio_Unitario = c(3, 5, 4, 0),
  Beneficio_Total = c(valores_optimos[1]*3, valores_optimos[2]*5, 
                      valores_optimos[3]*4, 0)
)

# Calcular porcentajes
datos_asignacion$Porcentaje <- round(datos_asignacion$Asignacion / disponibilidad_total * 100, 1)
datos_asignacion$Porcentaje_Beneficio <- round(datos_asignacion$Beneficio_Total / valor_optimo * 100, 1)

cat("\n\nESTADÍSTICAS DETALLADAS:\n")
cat("========================\n")
print(datos_asignacion)

# 6. VISUALIZACIONES
# ============================================

# Configurar tema para gráficos
theme_set(theme_minimal())

# Gráfico 1: Distribución del agua
grafico1 <- ggplot(datos_asignacion[1:3,], aes(x = reorder(Uso, -Asignacion), y = Asignacion, fill = Uso)) +
  geom_bar(stat = "identity", width = 0.7) +
  geom_text(aes(label = paste(Asignacion, "unidades\n(", Porcentaje, "%)")), 
            vjust = -0.5, size = 3.5) +
  labs(title = "Distribución Óptima del Agua",
       subtitle = paste("Beneficio total:", valor_optimo, "unidades"),
       x = "Uso del Agua",
       y = "Unidades Asignadas",
       caption = "Modelo de Programación Lineal") +
  scale_fill_manual(values = c("Agrícola" = "#4CAF50", 
                               "Industrial" = "#2196F3", 
                               "Doméstico" = "#FF9800")) +
  theme(legend.position = "none",
        plot.title = element_text(hjust = 0.5, size = 16, face = "bold"),
        plot.subtitle = element_text(hjust = 0.5, size = 12),
        axis.text.x = element_text(size = 11))

# Gráfico 2: Beneficio por uso
datos_beneficio <- melt(datos_asignacion[1:3, c("Uso", "Asignacion", "Beneficio_Total")], 
                        id.vars = "Uso")

grafico2 <- ggplot(datos_beneficio, aes(x = Uso, y = value, fill = variable)) +
  geom_bar(stat = "identity", position = "dodge") +
  labs(title = "Comparación: Asignación vs Beneficio por Uso",
       x = "Uso del Agua",
       y = "Valor",
       fill = "Variable") +
  scale_fill_manual(values = c("Asignacion" = "#9E9E9E", 
                               "Beneficio_Total" = "#673AB7"),
                    labels = c("Agua Asignada", "Beneficio Obtenido")) +
  theme(plot.title = element_text(hjust = 0.5, size = 14, face = "bold"))

# Gráfico 3: Eficiencia del uso del agua (beneficio por unidad)
datos_eficiencia <- datos_asignacion[1:3,]
datos_eficiencia$Eficiencia <- datos_eficiencia$Beneficio_Total / datos_eficiencia$Asignacion

grafico3 <- ggplot(datos_eficiencia, aes(x = reorder(Uso, -Eficiencia), y = Eficiencia, fill = Uso)) +
  geom_bar(stat = "identity", width = 0.6) +
  geom_text(aes(label = round(Eficiencia, 2)), vjust = -0.5, size = 4) +
  labs(title = "Eficiencia en el Uso del Agua",
       subtitle = "Beneficio por unidad de agua",
       x = "Uso del Agua",
       y = "Beneficio por Unidad") +
  scale_fill_manual(values = c("Agrícola" = "#4CAF50", 
                               "Industrial" = "#2196F3", 
                               "Doméstico" = "#FF9800")) +
  theme(legend.position = "none",
        plot.title = element_text(hjust = 0.5, size = 14, face = "bold"))

# 7. ANÁLISIS DE ESCENARIOS ALTERNATIVOS
# ============================================

cat("\n\nANÁLISIS DE ESCENARIOS ALTERNATIVOS:\n")
cat("====================================\n")

# Función para analizar diferentes escenarios
analizar_escenario <- function(disponibilidad, min_agri, min_ind, min_dom) {
  coef_obj <- c(3, 5, 4)
  mat_res <- matrix(c(1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1), nrow = 4, byrow = TRUE)
  dir_res <- c("<=", ">=", ">=", ">=")
  lad_der <- c(disponibilidad, min_agri, min_ind, min_dom)
  
  sol <- lp(direction = "max",
            objective.in = coef_obj,
            const.mat = mat_res,
            const.dir = dir_res,
            const.rhs = lad_der)
  
  return(list(
    asignacion = sol$solution,
    beneficio = sol$objval,
    factible = sol$status == 0
  ))
}

# Definir escenarios alternativos
escenarios <- list(
  "Escenario Base" = c(100, 30, 20, 25),
  "Sequía Moderada" = c(80, 25, 15, 20),
  "Sequía Severa" = c(60, 20, 10, 15),
  "Abundancia" = c(120, 35, 25, 30)
)

# Analizar cada escenario
resultados_escenarios <- data.frame()

for (nombre_esc in names(escenarios)) {
  params <- escenarios[[nombre_esc]]
  res <- analizar_escenario(params[1], params[2], params[3], params[4])
  
  if (res$factible) {
    fila <- data.frame(
      Escenario = nombre_esc,
      Disponibilidad = params[1],
      Agricola = res$asignacion[1],
      Industrial = res$asignacion[2],
      Domestico = res$asignacion[3],
      Beneficio = res$beneficio,
      Eficiencia_Global = res$beneficio / params[1]
    )
    resultados_escenarios <- rbind(resultados_escenarios, fila)
  }
}

cat("\nComparación de Escenarios:\n")
print(resultados_escenarios)

# 8. REPORTE FINAL
# ============================================

cat("\n\n============================================\n")
cat("REPORTE FINAL - ASIGNACIÓN ÓPTIMA DE AGUA\n")
cat("============================================\n\n")

cat("RESUMEN EJECUTIVO:\n")
cat("------------------\n")
cat(sprintf("1. Se han asignado %.0f unidades de agua de las %.0f disponibles (%.1f%%)\n", 
            sum(valores_optimos), disponibilidad_total, 
            sum(valores_optimos)/disponibilidad_total*100))
cat(sprintf("2. El beneficio social máximo alcanzado es: %.0f unidades\n", valor_optimo))
cat(sprintf("3. El uso más eficiente es el industrial con %.2f unidades de beneficio por unidad de agua\n", 
            datos_eficiencia$Eficiencia[datos_eficiencia$Uso == "Industrial"]))
cat(sprintf("4. La restricción más crítica es: Disponibilidad total (precio dual: %.2f)\n", 
            sensibilidad$duals[1]))

# 9. EXPORTAR RESULTADOS
# ============================================

# Crear directorio para resultados si no existe
if (!dir.exists("resultados_agua")) {
  dir.create("resultados_agua")
}

# Guardar resultados en CSV
write.csv(datos_asignacion, "resultados_agua/asignacion_optima.csv", row.names = FALSE)
write.csv(resultados_escenarios, "resultados_agua/escenarios_comparacion.csv", row.names = FALSE)

# Guardar gráficos
ggsave("resultados_agua/grafico_distribucion.png", grafico1, width = 8, height = 6, dpi = 300)
ggsave("resultados_agua/grafico_comparacion.png", grafico2, width = 9, height = 6, dpi = 300)
ggsave("resultados_agua/grafico_eficiencia.png", grafico3, width = 8, height = 6, dpi = 300)

# Guardar resumen en texto
sink("resultados_agua/resumen_analisis.txt")
cat("RESUMEN DEL ANÁLISIS DE ASIGNACIÓN ÓPTIMA DE AGUA\n")
cat("=================================================\n\n")
cat("Fecha de análisis:", format(Sys.Date(), "%d/%m/%Y"), "\n")
cat("\nSOLUCIÓN ÓPTIMA:\n")
cat("Agrícola:", valores_optimos[1], "unidades\n")
cat("Industrial:", valores_optimos[2], "unidades\n")
cat("Doméstico:", valores_optimos[3], "unidades\n")
cat("Beneficio máximo:", valor_optimo, "unidades\n")
sink()

cat("\n\nAnálisis completado exitosamente.\n")
cat("Resultados guardados en la carpeta 'resultados_agua'\n")

# Mostrar gráficos
print(grafico1)
print(grafico2)
print(grafico3)