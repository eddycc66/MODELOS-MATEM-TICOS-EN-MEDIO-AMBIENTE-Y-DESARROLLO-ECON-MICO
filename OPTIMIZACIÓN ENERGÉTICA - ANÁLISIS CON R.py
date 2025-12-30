# ===================================================
# OPTIMIZACIÓN ENERGÉTICA - ANÁLISIS CON R
# Modelo con fuentes solar, eólica y térmica
# ===================================================

# Limpiar entorno de trabajo
rm(list = ls())
cat("\014") # Limpiar consola

# 1. INSTALAR Y CARGAR PAQUETES NECESARIOS
# ===================================================

paquetes_requeridos <- c("lpSolve", "ggplot2", "dplyr", "tidyr", 
                         "plotly", "reshape2", "scales", "gridExtra",
                         "RColorBrewer", "kableExtra", "corrplot")

paquetes_nuevos <- paquetes_requeridos[!(paquetes_requeridos %in% installed.packages()[,"Package"])]

if(length(paquetes_nuevos)) {
  install.packages(paquetes_nuevos)
}

# Cargar paquetes
library(lpSolve)        # Para programación lineal
library(ggplot2)        # Para gráficos
library(dplyr)          # Para manipulación de datos
library(tidyr)          # Para datos tidy
library(plotly)         # Para gráficos interactivos
library(reshape2)       # Para transformación de datos
library(scales)         # Para escalas en gráficos
library(gridExtra)      # Para múltiples gráficos
library(RColorBrewer)   # Para paletas de colores
library(kableExtra)     # Para tablas formateadas
library(corrplot)       # Para gráficos de correlación

# 2. DEFINIR EL MODELO DE OPTIMIZACIÓN ENERGÉTICA
# ===================================================

cat("===================================================\n")
cat("MODELO DE OPTIMIZACIÓN ENERGÉTICA\n")
cat("Fuentes: Solar, Eólica y Térmica\n")
cat("===================================================\n\n")

# Definir parámetros del problema
demanda_energetica <- 150  # MW
capacidad_solar <- 80      # MW
capacidad_eolica <- 70     # MW
limite_emisiones <- 60     # toneladas

# Coeficientes de costos [$/MW]
costos <- c(
  solar = 2,    # x1
  eolica = 3,   # x2
  termica = 5   # x3
)

# Coeficientes de emisiones [ton/MW]
emisiones <- c(
  solar = 0.2,  # x1
  eolica = 0.1, # x2
  termica = 0.8 # x3
)

# 3. RESOLVER EL MODELO DE PROGRAMACIÓN LINEAL
# ===================================================

# Definir la función objetivo (minimizar costos)
funcion_objetivo <- costos

# Definir matriz de restricciones
matriz_restricciones <- matrix(c(
  # x1  x2  x3
  1,   1,   1,   # Demanda energética (>= 150)
  1,   0,   0,   # Capacidad solar (<= 80)
  0,   1,   0,   # Capacidad eólica (<= 70)
  emisiones[1], emisiones[2], emisiones[3]  # Límite emisiones (<= 60)
), nrow = 4, byrow = TRUE)

# Dirección de las restricciones
direccion_restricciones <- c(">=", "<=", "<=", "<=")

# Lado derecho de las restricciones
lado_derecho <- c(demanda_energetica, capacidad_solar, capacidad_eolica, limite_emisiones)

# Resolver el problema de minimización
solucion <- lp(direction = "min",
               objective.in = funcion_objetivo,
               const.mat = matriz_restricciones,
               const.dir = direccion_restricciones,
               const.rhs = lado_derecho)

# 4. ANÁLISIS DE LA SOLUCIÓN ÓPTIMA
# ===================================================

# Extraer resultados
generacion_optima <- solucion$solution
names(generacion_optima) <- c("Solar", "Eólica", "Térmica")
costo_total <- solucion$objval

# Calcular métricas adicionales
emisiones_totales <- sum(generacion_optima * emisiones)
porcentaje_renovable <- sum(generacion_optima[1:2]) / demanda_energetica * 100
costo_promedio <- costo_total / demanda_energetica

# Mostrar resultados principales
cat("\nSOLUCIÓN ÓPTIMA ENCONTRADA:\n")
cat("============================\n")
cat(sprintf("Generación Solar (x₁): %.1f MW (%.1f%%)\n", 
            generacion_optima[1], generacion_optima[1]/demanda_energetica*100))
cat(sprintf("Generación Eólica (x₂): %.1f MW (%.1f%%)\n", 
            generacion_optima[2], generacion_optima[2]/demanda_energetica*100))
cat(sprintf("Generación Térmica (x₃): %.1f MW (%.1f%%)\n", 
            generacion_optima[3], generacion_optima[3]/demanda_energetica*100))
cat("\n")
cat(sprintf("Costo total mínimo (Z): $%.2f millones\n", costo_total))
cat(sprintf("Costo promedio por MW: $%.2f\n", costo_promedio))
cat(sprintf("Emisiones totales: %.1f toneladas\n", emisiones_totales))
cat(sprintf("Porcentaje de energía renovable: %.1f%%\n", porcentaje_renovable))

# 5. ANÁLISIS DE SENSIBILIDAD COMPLETO
# ===================================================

cat("\n\nANÁLISIS DE SENSIBILIDAD:\n")
cat("==========================\n")

# Obtener análisis de sensibilidad
sensibilidad <- lp(direction = "min",
                   objective.in = funcion_objetivo,
                   const.mat = matriz_restricciones,
                   const.dir = direccion_restricciones,
                   const.rhs = lado_derecho,
                   compute.sens = TRUE)

# Análisis de precios duales (precios sombra)
precios_sombra <- sensibilidad$duals[1:4]
nombres_restricciones <- c("Demanda", "Capacidad Solar", "Capacidad Eólica", "Emisiones")

cat("\nPrecios Sombra (Duales):\n")
cat("------------------------\n")
for(i in 1:4) {
  interpretacion <- ifelse(direccion_restricciones[i] == ">=", 
                           "aumentar", 
                           "reducir")
  cat(sprintf("%s: %.4f (cada unidad que se %s esta restricción", 
              nombres_restricciones[i], 
              precios_sombra[i],
              interpretacion))
  cat(sprintf(" %s el costo total en $%.4f millones)\n",
              ifelse(direccion_restricciones[i] == ">=", "reduce", "aumenta"),
              abs(precios_sombra[i])))
}

# Rangos de optimalidad para costos
cat("\nRangos de Optimalidad para Costos:\n")
cat("----------------------------------\n")
for(i in 1:3) {
  cat(sprintf("%s: [$%.2f, $%.2f] (actual: $%.2f)\n",
              names(generacion_optima)[i],
              sensibilidad$sens.coef.from[i],
              sensibilidad$sens.coef.to[i],
              costos[i]))
}

# 6. ANÁLISIS DE ESCENARIOS
# ===================================================

cat("\n\nANÁLISIS DE ESCENARIOS:\n")
cat("=======================\n")

# Función para analizar diferentes escenarios
analizar_escenario <- function(demanda, cap_solar, cap_eolica, lim_emisiones) {
  # Actualizar restricciones
  rhs_actual <- c(demanda, cap_solar, cap_eolica, lim_emisiones)
  
  # Resolver
  sol <- lp(direction = "min",
            objective.in = funcion_objetivo,
            const.mat = matriz_restricciones,
            const.dir = direccion_restricciones,
            const.rhs = rhs_actual)
  
  if(sol$status == 0) {
    gen <- sol$solution
    emis <- sum(gen * emisiones)
    renov <- sum(gen[1:2]) / demanda * 100
    
    return(list(
      generacion = gen,
      costo = sol$objval,
      emisiones = emis,
      renovable = renov,
      costo_promedio = sol$objval / demanda
    ))
  } else {
    return(NULL)
  }
}

# Definir escenarios
escenarios <- list(
  "Base" = c(150, 80, 70, 60),
  "Alta Demanda" = c(200, 80, 70, 60),
  "Bajas Emisiones" = c(150, 80, 70, 40),
  "Más Solar" = c(150, 100, 70, 60),
  "Más Eólica" = c(150, 80, 100, 60),
  "Crisis" = c(150, 50, 40, 50)
)

# Analizar cada escenario
resultados_escenarios <- data.frame()

for(nombre in names(escenarios)) {
  params <- escenarios[[nombre]]
  res <- analizar_escenario(params[1], params[2], params[3], params[4])
  
  if(!is.null(res)) {
    df_esc <- data.frame(
      Escenario = nombre,
      Demanda = params[1],
      Solar = res$generacion[1],
      Eolica = res$generacion[2],
      Termica = res$generacion[3],
      Costo_Total = res$costo,
      Emisiones = res$emisiones,
      Renovable = res$renovable,
      Costo_Promedio = res$costo_promedio
    )
    resultados_escenarios <- rbind(resultados_escenarios, df_esc)
  }
}

# Mostrar resultados de escenarios
cat("\nComparativa de Escenarios:\n")
print(kable(resultados_escenarios, format = "simple", digits = 2) %>%
        kable_styling(bootstrap_options = c("striped", "hover")))

# 7. VISUALIZACIONES AVANZADAS
# ===================================================

# Configurar tema para gráficos
theme_custom <- theme_minimal() +
  theme(
    plot.title = element_text(size = 16, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(size = 12, hjust = 0.5),
    axis.title = element_text(size = 12, face = "bold"),
    legend.title = element_text(size = 11, face = "bold"),
    panel.grid.minor = element_blank()
  )

# Gráfico 1: Mix Energético Óptimo
df_mix <- data.frame(
  Fuente = names(generacion_optima),
  Generacion = generacion_optima,
  Costo_Unitario = costos,
  Emisiones_Unitarias = emisiones
)

g1 <- ggplot(df_mix, aes(x = "", y = Generacion, fill = Fuente)) +
  geom_bar(stat = "identity", width = 1, color = "white") +
  coord_polar("y", start = 0) +
  geom_text(aes(label = paste0(round(Generacion), " MW\n", 
                               round(Generacion/demanda_energetica*100, 1), "%")), 
            position = position_stack(vjust = 0.5), 
            size = 4.5, color = "white") +
  scale_fill_manual(values = c("Solar" = "#FFD700", 
                               "Eólica" = "#87CEEB", 
                               "Térmica" = "#8B0000")) +
  labs(title = "Mix Energético Óptimo",
       subtitle = paste("Costo total: $", round(costo_total), "millones",
                        "| Emisiones:", round(emisiones_totales, 1), "ton")) +
  theme_custom +
  theme_void() +
  theme(legend.position = "right")

# Gráfico 2: Comparación de Costos y Emisiones
df_comparacion <- data.frame(
  Fuente = rep(names(generacion_optima), 2),
  Metrica = rep(c("Costo Total", "Emisiones Totales"), each = 3),
  Valor = c(generacion_optima * costos, generacion_optima * emisiones)
)

g2 <- ggplot(df_comparacion, aes(x = Fuente, y = Valor, fill = Metrica)) +
  geom_bar(stat = "identity", position = "dodge", width = 0.7) +
  geom_text(aes(label = round(Valor, 1)), 
            position = position_dodge(width = 0.7),
            vjust = -0.5, size = 3.5) +
  scale_fill_manual(values = c("Costo Total" = "#4CAF50", 
                               "Emisiones Totales" = "#F44336")) +
  labs(title = "Contribución por Fuente",
       subtitle = "Costo y emisiones desglosados",
       x = "Fuente Energética",
       y = "Valor",
       fill = "Métrica") +
  theme_custom

# Gráfico 3: Análisis de Sensibilidad de Costos
df_sensibilidad <- data.frame(
  Fuente = names(costos),
  Costo_Actual = costos,
  Limite_Inferior = sensibilidad$sens.coef.from,
  Limite_Superior = sensibilidad$sens.coef.to
)

g3 <- ggplot(df_sensibilidad, aes(x = Fuente)) +
  geom_point(aes(y = Costo_Actual), size = 4, color = "blue") +
  geom_errorbar(aes(ymin = Limite_Inferior, ymax = Limite_Superior), 
                width = 0.1, color = "red", size = 1) +
  geom_hline(yintercept = costos, linetype = "dashed", alpha = 0.3) +
  labs(title = "Rangos de Sensibilidad de Costos",
       subtitle = "Los costos pueden variar dentro de estos rangos manteniendo la solución óptima",
       x = "Fuente Energética",
       y = "Costo Unitario ($/MW)") +
  theme_custom

# Gráfico 4: Comparativa de Escenarios
df_escenarios_plot <- melt(resultados_escenarios[,c("Escenario", "Costo_Total", "Emisiones", "Renovable")], 
                           id.vars = "Escenario")

g4 <- ggplot(df_escenarios_plot, aes(x = Escenario, y = value, fill = variable)) +
  geom_bar(stat = "identity", position = "dodge", width = 0.7) +
  facet_wrap(~variable, scales = "free_y", ncol = 1) +
  scale_fill_brewer(palette = "Set2") +
  labs(title = "Comparativa de Escenarios",
       x = "Escenario",
       y = "Valor",
       fill = "Indicador") +
  theme_custom +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))

# 8. ANÁLISIS DE EFICIENCIA Y PUNTO DE EQUILIBRIO
# ===================================================

cat("\n\nANÁLISIS DE EFICIENCIA:\n")
cat("======================\n")

# Calcular eficiencia económica por fuente
eficiencia <- data.frame(
  Fuente = names(generacion_optima),
  Generacion = generacion_optima,
  Costo_Total = generacion_optima * costos,
  Emisiones_Total = generacion_optima * emisiones,
  Costo_por_MW = costos,
  Emisiones_por_MW = emisiones,
  Eficiencia_Economica = 1/costos,  # MW por $ (inversa del costo)
  Eficiencia_Ambiental = 1/emisiones  # MW por ton (inversa de emisiones)
)

# Normalizar eficiencias para comparación
eficiencia$Eco_Norm <- eficiencia$Eficiencia_Economica / max(eficiencia$Eficiencia_Economica)
eficiencia$Amb_Norm <- eficiencia$Eficiencia_Ambiental / max(eficiencia$Eficiencia_Ambiental)
eficiencia$Puntuacion_Total <- (eficiencia$Eco_Norm + eficiencia$Amb_Norm) / 2

cat("\nTabla de Eficiencia Comparativa:\n")
print(kable(eficiencia, format = "simple", digits = 3) %>%
        kable_styling(bootstrap_options = c("striped", "hover")))

# 9. SIMULACIÓN MONTE CARLO PARA ANÁLISIS DE RIESGO
# ===================================================

cat("\n\nANÁLISIS DE RIESGO CON SIMULACIÓN MONTE CARLO:\n")
cat("===============================================\n")

# Configurar parámetros de simulación
n_simulaciones <- 1000
variacion_costo <- 0.2  # ±20% de variación en costos
variacion_demanda <- 0.15  # ±15% de variación en demanda

# Inicializar resultados de simulación
resultados_simulacion <- matrix(0, nrow = n_simulaciones, ncol = 6)
colnames(resultados_simulacion) <- c("Costo_Total", "Solar", "Eolica", "Termica", "Emisiones", "Renovable")

set.seed(123)  # Para reproducibilidad
pb <- txtProgressBar(min = 0, max = n_simulaciones, style = 3)

for(i in 1:n_simulaciones) {
  # Generar variaciones aleatorias
  costos_sim <- costos * runif(3, 1-variacion_costo, 1+variacion_costo)
  demanda_sim <- demanda_energetica * runif(1, 1-variacion_demanda, 1+variacion_demanda)
  
  # Resolver con parámetros simulados
  sol_sim <- lp(direction = "min",
                objective.in = costos_sim,
                const.mat = matriz_restricciones,
                const.dir = direccion_restricciones,
                const.rhs = c(demanda_sim, capacidad_solar, capacidad_eolica, limite_emisiones))
  
  if(sol_sim$status == 0) {
    gen_sim <- sol_sim$solution
    resultados_simulacion[i,] <- c(
      sol_sim$objval,
      gen_sim[1],
      gen_sim[2],
      gen_sim[3],
      sum(gen_sim * emisiones),
      sum(gen_sim[1:2]) / demanda_sim * 100
    )
  }
  setTxtProgressBar(pb, i)
}
close(pb)

# Convertir a data frame
df_simulacion <- as.data.frame(resultados_simulacion)

# Calcular estadísticas de riesgo
estadisticas_riesgo <- data.frame(
  Metrica = c("Costo Total", "% Solar", "% Eólica", "% Térmica", "Emisiones", "% Renovable"),
  Media = c(mean(df_simulacion$Costo_Total),
            mean(df_simulacion$Solar/demanda_energetica*100),
            mean(df_simulacion$Eolica/demanda_energetica*100),
            mean(df_simulacion$Termica/demanda_energetica*100),
            mean(df_simulacion$Emisiones),
            mean(df_simulacion$Renovable)),
  Desviacion = c(sd(df_simulacion$Costo_Total),
                 sd(df_simulacion$Solar/demanda_energetica*100),
                 sd(df_simulacion$Eolica/demanda_energetica*100),
                 sd(df_simulacion$Termica/demanda_energetica*100),
                 sd(df_simulacion$Emisiones),
                 sd(df_simulacion$Renovable)),
  Minimo = c(min(df_simulacion$Costo_Total),
             min(df_simulacion$Solar/demanda_energetica*100),
             min(df_simulacion$Eolica/demanda_energetica*100),
             min(df_simulacion$Termica/demanda_energetica*100),
             min(df_simulacion$Emisiones),
             min(df_simulacion$Renovable)),
  Maximo = c(max(df_simulacion$Costo_Total),
             max(df_simulacion$Solar/demanda_energetica*100),
             max(df_simulacion$Eolica/demanda_energetica*100),
             max(df_simulacion$Termica/demanda_energetica*100),
             max(df_simulacion$Emisiones),
             max(df_simulacion$Renovable))
)

cat("\nEstadísticas de Riesgo (Simulación Monte Carlo):\n")
print(kable(estadisticas_riesgo, format = "simple", digits = 2) %>%
        kable_styling(bootstrap_options = c("striped", "hover")))

# 10. GRÁFICO DE DISTRIBUCIÓN DE COSTOS (SIMULACIÓN)
# ===================================================

g5 <- ggplot(df_simulacion, aes(x = Costo_Total)) +
  geom_histogram(aes(y = ..density..), bins = 30, fill = "steelblue", alpha = 0.7) +
  geom_density(color = "red", size = 1) +
  geom_vline(xintercept = costo_total, color = "green", size = 1.5, linetype = "dashed") +
  annotate("text", x = costo_total, y = max(hist(df_simulacion$Costo_Total, plot=F)$density)*0.9,
           label = paste("Costo óptimo:\n$", round(costo_total)), 
           hjust = 1.1, vjust = 1, color = "green", size = 4) +
  labs(title = "Distribución de Costos Totales",
       subtitle = paste("Simulación Monte Carlo (n =", n_simulaciones, "iteraciones)"),
       x = "Costo Total ($ millones)",
       y = "Densidad de Probabilidad") +
  theme_custom

# 11. REPORTE COMPLETO Y EXPORTACIÓN
# ===================================================

# Crear directorio para resultados
if(!dir.exists("resultados_energia")) {
  dir.create("resultados_energia")
}

# Exportar todos los resultados
write.csv(df_mix, "resultados_energia/mix_energetico.csv", row.names = FALSE)
write.csv(resultados_escenarios, "resultados_energia/escenarios.csv", row.names = FALSE)
write.csv(eficiencia, "resultados_energia/eficiencia.csv", row.names = FALSE)
write.csv(df_simulacion, "resultados_energia/simulacion_montecarlo.csv", row.names = FALSE)
write.csv(estadisticas_riesgo, "resultados_energia/estadisticas_riesgo.csv", row.names = FALSE)

# Guardar gráficos
ggsave("resultados_energia/grafico_mix.png", g1, width = 8, height = 7, dpi = 300)
ggsave("resultados_energia/grafico_comparacion.png", g2, width = 9, height = 6, dpi = 300)
ggsave("resultados_energia/grafico_sensibilidad.png", g3, width = 9, height = 6, dpi = 300)
ggsave("resultados_energia/grafico_escenarios.png", g4, width = 10, height = 8, dpi = 300)
ggsave("resultados_energia/grafico_riesgo.png", g5, width = 9, height = 6, dpi = 300)

# 12. GENERAR REPORTE HTML INTERACTIVO
# ===================================================

cat("\n\nGENERANDO REPORTE INTERACTIVO...\n")

# Crear contenido HTML
html_content <- paste('
<!DOCTYPE html>
<html>
<head>
    <title>Reporte de Optimización Energética</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #2c3e50; }
        h2 { color: #3498db; }
        .result { background-color: #f8f9fa; padding: 15px; border-radius: 5px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Reporte de Optimización Energética</h1>
    <p><strong>Fecha de análisis:</strong> ', format(Sys.Date(), "%d/%m/%Y"), '</p>
    
    <h2>Solución Óptima</h2>
    <div class="result">
        <p><strong>Generación Solar (x₁):</strong> ', round(generacion_optima[1], 1), ' MW</p>
        <p><strong>Generación Eólica (x₂):</strong> ', round(generacion_optima[2], 1), ' MW</p>
        <p><strong>Generación Térmica (x₃):</strong> ', round(generacion_optima[3], 1), ' MW</p>
        <p><strong>Costo Total Mínimo:</strong> $', round(costo_total, 2), ' millones</p>
        <p><strong>Emisiones Totales:</strong> ', round(emisiones_totales, 1), ' toneladas</p>
        <p><strong>Porcentaje Renovable:</strong> ', round(porcentaje_renovable, 1), '%</p>
    </div>
    
    <h2>Indicadores de Eficiencia</h2>
    <table>
        <tr>
            <th>Fuente</th>
            <th>Costo por MW</th>
            <th>Emisiones por MW</th>
            <th>Puntuación Total</th>
        </tr>',
                      paste(sapply(1:nrow(eficiencia), function(i) {
                        paste('<tr>
                  <td>', eficiencia$Fuente[i], '</td>
                  <td>$', round(eficiencia$Costo_por_MW[i], 2), '</td>
                  <td>', round(eficiencia$Emisiones_por_MW[i], 2), ' ton</td>
                  <td>', round(eficiencia$Puntuacion_Total[i], 3), '</td>
                </tr>', sep = "")
                      }), collapse = ""),
                      '</table>
</body>
</html>', sep = "")

# Guardar reporte HTML
writeLines(html_content, "resultados_energia/reporte.html")

# 13. MOSTRAR GRÁFICOS EN RSTUDIO
# ===================================================

cat("\nMostrando gráficos...\n\n")

# Mostrar gráficos en RStudio
print(g1)
print(g2)
print(g3)
print(g4)
print(g5)

# 14. RESUMEN EJECUTIVO
# ===================================================

cat("\n\n===================================================\n")
cat("RESUMEN EJECUTIVO - OPTIMIZACIÓN ENERGÉTICA\n")
cat("===================================================\n\n")

cat("CONCLUSIONES PRINCIPALES:\n")
cat("1. La solución óptima utiliza ", round(porcentaje_renovable, 1), "% de energías renovables\n")
cat("2. El costo mínimo alcanzable es de $", round(costo_total), " millones\n")
cat("3. Las emisiones totales son de ", round(emisiones_totales, 1), " toneladas\n")
cat("4. La fuente más sensible a cambios de costo es: ")
if(which.min(abs(sensibilidad$sens.coef.to - sensibilidad$sens.coef.from)) == 1) {
  cat("SOLAR\n")
} else if(which.min(abs(sensibilidad$sens.coef.to - sensibilidad$sens.coef.from)) == 2) {
  cat("EÓLICA\n")
} else {
  cat("TÉRMICA\n")
}

cat("5. La restricción más crítica es: ")
restriccion_critica <- which.max(abs(precios_sombra))
cat(nombres_restricciones[restriccion_critica], "\n")

cat("\nRECOMENDACIONES:\n")
cat("1. Invertir en aumentar la capacidad ", 
    ifelse(generacion_optima[1] == capacidad_solar, "solar", 
           ifelse(generacion_optima[2] == capacidad_eolica, "eólica", "térmica")),
    "\n")
cat("2. Considerar flexibilizar la restricción de ", 
    tolower(nombres_restricciones[restriccion_critica]), "\n")
cat("3. Explorar tecnologías para reducir emisiones de la fuente térmica\n")

cat("\n===================================================\n")
cat("Análisis completado exitosamente.\n")
cat("Todos los resultados se han guardado en la carpeta 'resultados_energia'\n")
cat("===================================================\n")