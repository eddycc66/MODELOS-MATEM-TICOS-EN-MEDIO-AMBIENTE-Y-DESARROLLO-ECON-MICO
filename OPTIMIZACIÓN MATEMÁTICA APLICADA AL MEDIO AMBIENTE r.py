# ============================================================
# OPTIMIZACIÓN MATEMÁTICA APLICADA AL MEDIO AMBIENTE
# Y DESARROLLO ECONÓMICO - IMPLEMENTACIÓN EN R
# ============================================================

# ---------- 0. INSTALACIÓN DE PAQUETES (EJECUTAR PRIMERO) ----------
cat("========================================\n")
cat("INSTALACIÓN DE PAQUETES REQUERIDOS\n")
cat("========================================\n")

# Lista de paquetes necesarios
paquetes_requeridos <- c("lpSolve", "Rglpk", "nloptr", "GA", 
                         "tidyverse", "ggplot2", "plotly", "corrplot")

# Función para instalar paquetes faltantes
instalar_paquetes <- function(paquetes) {
  for(pkg in paquetes) {
    if(!require(pkg, character.only = TRUE, quietly = TRUE)) {
      cat("Instalando:", pkg, "...\n")
      install.packages(pkg, dependencies = TRUE)
      cat(pkg, "instalado correctamente.\n")
    } else {
      cat(pkg, "ya está instalado.\n")
    }
  }
}

# Instalar todos los paquetes
instalar_paquetes(paquetes_requeridos)

cat("\nInstalación completada. Cargando paquetes...\n")

# ---------- 1. CARGA DE PAQUETES ----------
library(lpSolve)       # Para programación lineal
library(Rglpk)         # Para programación lineal entera
library(nloptr)        # Para optimización no lineal
library(GA)            # Para algoritmos genéticos
library(tidyverse)     # Para manipulación de datos
library(ggplot2)       # Para gráficos estáticos
library(plotly)        # Para gráficos interactivos
library(corrplot)      # Para matrices de correlación

cat("Todos los paquetes cargados exitosamente.\n")

# ---------- 2. MODELOS LINEALES ----------
cat("\n========================================\n")
cat("2. MODELOS LINEALES\n")
cat("========================================\n")

# 2.1 Ejemplo: Asignación de Recursos Hídricos en Bolivia
cat("\n2.1 ASIGNACIÓN DE RECURSOS HÍDRICOS\n")
cat("----------------------------------------\n")

# Definir coeficientes de la función objetivo (beneficio por m³)
coef_obj <- c(3, 5, 4)  # Beneficios: agrícola, industrial, doméstico

# Matriz de restricciones
matriz_rest <- matrix(c(
  1, 1, 1,    # Disponibilidad total de agua
  1, 0, 0,    # Mínimo agrícola
  0, 1, 0,    # Mínimo industrial
  0, 0, 1     # Mínimo doméstico
), nrow = 4, byrow = TRUE)

# Lados derechos y direcciones de las restricciones
lados_der <- c(100, 30, 20, 25)
direcciones <- c("<=", ">=", ">=", ">=")

# Resolver el problema
cat("Resolviendo problema de optimización lineal...\n")
solucion_lp <- lp("max", coef_obj, matriz_rest, direcciones, lados_der)

# Mostrar resultados
cat("\nSOLUCIÓN ÓPTIMA ENCONTRADA:\n")
cat("Agua para agricultura (x1):", solucion_lp$solution[1], "millones de m³\n")
cat("Agua para industria (x2):", solucion_lp$solution[2], "millones de m³\n")
cat("Agua para uso doméstico (x3):", solucion_lp$solution[3], "millones de m³\n")
cat("Beneficio social máximo Z:", solucion_lp$objval, "millones de Bs\n")

# ---------- 3. VERSIÓN SIMPLIFICADA (Sin Paquetes Avanzados) ----------
# Si persisten problemas de instalación, usa esta versión básica
cat("\n========================================\n")
cat("3. VERSIÓN SIMPLIFICADA (Solo Base R)\n")
cat("========================================\n")

# 3.1 Resolver problema lineal manualmente (método gráfico para 2 variables)
resolver_lineal_manual <- function() {
  cat("\nMétodo manual para 2 variables (x1, x2):\n")
  
  # Simplificamos a 2 variables para visualización
  # Función: Max Z = 3x1 + 5x2
  # Restricciones:
  # 2x1 + x2 ≤ 100
  # x1 + 3x2 ≤ 90
  # x1 ≥ 0, x2 ≥ 0
  
  # Encontrar puntos de intersección
  cat("\nRestricciones:\n")
  cat("1) 2x1 + x2 ≤ 100\n")
  cat("2) x1 + 3x2 ≤ 90\n")
  
  # Puntos de intersección de las restricciones
  # Resolver sistema:
  # 2x1 + x2 = 100
  # x1 + 3x2 = 90
  
  # Por sustitución: x2 = 100 - 2x1
  # Sustituir: x1 + 3(100 - 2x1) = 90
  # x1 + 300 - 6x1 = 90
  # -5x1 = -210
  # x1 = 42
  # x2 = 100 - 2*42 = 16
  
  cat("\nPuntos de intersección:\n")
  cat("A: (0, 0) - Z = 0\n")
  cat("B: (50, 0) - Z = 150 (de 2x1 ≤ 100)\n")
  cat("C: (42, 16) - Z = 3*42 + 5*16 = 206\n")
  cat("D: (0, 30) - Z = 150 (de 3x2 ≤ 90)\n")
  
  cat("\nSolución óptima: (42, 16) con Z = 206\n")
}

# Ejecutar versión manual
resolver_lineal_manual()

# 3.2 Visualización básica con R base
cat("\nGenerando gráfico básico...\n")

# Crear gráfico de restricciones
par(mfrow = c(1, 2))

# Gráfico 1: Restricciones
x1 <- seq(0, 50, length.out = 100)
x2_rest1 <- 100 - 2*x1  # 2x1 + x2 ≤ 100
x2_rest2 <- (90 - x1)/3  # x1 + 3x2 ≤ 90

plot(x1, x2_rest1, type = "l", col = "blue", lwd = 2,
     ylim = c(0, 100), xlim = c(0, 50),
     xlab = "x1 (Agricultura)", ylab = "x2 (Industria)",
     main = "Región Factible")
lines(x1, x2_rest2, col = "red", lwd = 2)

# Área factible
polygon(x = c(0, 0, 42, 50, 0),
        y = c(0, 30, 16, 0, 0),
        col = rgb(0.8, 0.9, 1.0, 0.5),
        border = NA)

# Punto óptimo
points(42, 16, pch = 19, col = "green", cex = 2)
text(42, 20, "Óptimo (42, 16)", pos = 3)

legend("topright", 
       legend = c("2x1 + x2 ≤ 100", "x1 + 3x2 ≤ 90", "Región factible", "Solución óptima"),
       col = c("blue", "red", rgb(0.8, 0.9, 1.0), "green"),
       lwd = c(2, 2, 10, NA),
       pch = c(NA, NA, NA, 19),
       bty = "n")

# Gráfico 2: Función objetivo
x1_vals <- seq(0, 50, by = 1)
x2_vals <- seq(0, 30, by = 1)
z_matrix <- outer(x1_vals, x2_vals, function(x,y) 3*x + 5*y)

contour(x1_vals, x2_vals, z_matrix, 
        main = "Función Objetivo Z = 3x1 + 5x2",
        xlab = "x1 (Agricultura)", ylab = "x2 (Industria)",
        nlevels = 10)
points(42, 16, pch = 19, col = "red", cex = 2)
text(42, 16, "Z = 206", pos = 4, col = "red")

# ---------- 4. EJEMPLO PRÁCTICO: GESTIÓN DE AGUA EN BOLIVIA ----------
cat("\n========================================\n")
cat("4. CASO PRÁCTICO: GESTIÓN DE AGUA EN BOLIVIA\n")
cat("========================================\n")

# Datos para tres regiones bolivianas
gestion_agua_bolivia <- function() {
  cat("\nOptimización de asignación de agua por región:\n")
  
  # Datos hipotéticos basados en realidad boliviana
  regiones <- c("Altiplano", "Valle", "Llanos")
  
  # Disponibilidad de agua (millones de m³)
  disponibilidad <- c(50, 80, 120)
  
  # Demandas mínimas (millones de m³)
  demanda_min <- c(20, 30, 40)
  
  # Beneficios por m³ (Bs/m³)
  beneficios <- matrix(c(
    2.5, 3.0, 1.8,  # Agrícola
    4.0, 3.5, 2.8,  # Industrial
    1.5, 2.0, 1.2   # Doméstico
  ), nrow = 3, byrow = TRUE)
  
  # Resolver para cada región
  resultados <- data.frame(
    Region = character(),
    Agricultura = numeric(),
    Industria = numeric(),
    Domestico = numeric(),
    Beneficio_Total = numeric(),
    stringsAsFactors = FALSE
  )
  
  for(i in 1:3) {
    # Coeficientes objetivo para esta región
    coef_reg <- beneficios[, i]
    
    # Restricciones: disponibilidad total y demandas mínimas
    matriz_reg <- matrix(c(
      1, 1, 1,    # Disponibilidad total
      1, 0, 0,    # Mínimo agrícola (20% del total)
      0, 1, 0,    # Mínimo industrial (10% del total)
      0, 0, 1     # Mínimo doméstico (30% del total)
    ), nrow = 4, byrow = TRUE)
    
    lados_reg <- c(
      disponibilidad[i],
      demanda_min[i] * 0.2,
      demanda_min[i] * 0.1,
      demanda_min[i] * 0.3
    )
    
    # Intentar resolver con lpSolve, si no usar método manual
    if("lpSolve" %in% loadedNamespaces()) {
      sol <- lp("max", coef_reg, matriz_reg, 
                c("<=", ">=", ">=", ">="), lados_reg)
      
      resultados <- rbind(resultados, data.frame(
        Region = regiones[i],
        Agricultura = round(sol$solution[1], 1),
        Industria = round(sol$solution[2], 1),
        Domestico = round(sol$solution[3], 1),
        Beneficio_Total = round(sol$objval, 1)
      ))
    } else {
      # Método simplificado si lpSolve no está disponible
      resultados <- rbind(resultados, data.frame(
        Region = regiones[i],
        Agricultura = round(lados_reg[2], 1),
        Industria = round(lados_reg[3], 1),
        Domestico = round(lados_reg[4], 1),
        Beneficio_Total = round(sum(coef_reg * c(lados_reg[2], lados_reg[3], lados_reg[4])), 1)
      ))
    }
  }
  
  cat("\nRESULTADOS POR REGIÓN:\n")
  print(resultados)
  
  cat("\nANÁLISIS:\n")
  cat("1. Los Llanos tienen mayor disponibilidad hídrica\n")
  cat("2. El Altiplano requiere gestión más eficiente\n")
  cat("3. El sector industrial genera mayor beneficio por m³\n")
  
  return(resultados)
}

# Ejecutar caso boliviano
resultados_bolivia <- gestion_agua_bolivia()

# ---------- 5. TUTORIAL INTERACTIVO ----------
cat("\n========================================\n")
cat("5. TUTORIAL INTERACTIVO DE OPTIMIZACIÓN\n")
cat("========================================\n")

tutorial_optimizacion <- function() {
  cat("\n¿Qué tipo de problema quieres resolver?\n")
  cat("1. Maximizar beneficios con recursos limitados\n")
  cat("2. Minimizar costos ambientales\n")
  cat("3. Balancear múltiples objetivos (trade-off)\n")
  cat("4. Asignación óptima de recursos naturales\n")
  
  # Ejemplo genérico para cualquier elección
  cat("\nEstructura general de un modelo de optimización:\n")
  cat("------------------------------------------------\n")
  cat("Función objetivo: Max Z = c1*x1 + c2*x2 + ... + cn*xn\n")
  cat("Sujeto a:\n")
  cat("  a11*x1 + a12*x2 + ... + a1n*xn ≤ b1\n")
  cat("  a21*x1 + a22*x2 + ... + a2n*xn ≤ b2\n")
  cat("  ...\n")
  cat("  x1, x2, ..., xn ≥ 0\n")
  
  cat("\nPASOS PARA RESOLVER:\n")
  cat("1. Identificar variables de decisión (qué controlas)\n")
  cat("2. Definir función objetivo (qué quieres optimizar)\n")
  cat("3. Establecer restricciones (límites físicos, legales, económicos)\n")
  cat("4. Elegir método de solución (lineal, no lineal, multicriterio)\n")
  cat("5. Interpretar resultados en contexto real\n")
  
  cat("\nEJEMPLO CONCRETO: Agricultura sostenible\n")
  cat("Variables: x1 = ha de cultivo A, x2 = ha de cultivo B\n")
  cat("Objetivo: Max Beneficio = 1000*x1 + 1500*x2\n")
  cat("Restricciones:\n")
  cat("  Tierra: x1 + x2 ≤ 100 ha\n")
  cat("  Agua: 500*x1 + 800*x2 ≤ 50000 m³\n")
  cat("  Mano obra: 10*x1 + 15*x2 ≤ 1200 horas\n")
}

tutorial_optimizacion()

# ---------- 6. HERRAMIENTAS DE ANÁLISIS ----------
cat("\n========================================\n")
cat("6. HERRAMIENTAS DE ANÁLISIS DISPONIBLES\n")
cat("========================================\n")

# 6.1 Función para análisis de sensibilidad básico
analisis_sensibilidad <- function() {
  cat("\nAnálisis de Sensibilidad Básico:\n")
  cat("--------------------------------\n")
  
  cat("¿Qué pasa si...?\n")
  cat("1. Aumenta la disponibilidad del recurso en 10%?\n")
  cat("2. Mejora la eficiencia (beneficio por unidad) en 15%?\n")
  cat("3. Se imponen restricciones ambientales adicionales?\n")
  
  cat("\nMétodo de análisis:\n")
  cat("1. Resolver problema original\n")
  cat("2. Modificar un parámetro a la vez\n")
  cat("3. Recalcular solución\n")
  cat("4. Comparar con solución original\n")
  cat("5. Calcular elasticidad: %ΔResultado / %ΔParámetro\n")
}

analisis_sensibilidad()

# 6.2 Generar reporte HTML simple
generar_reporte <- function() {
  cat("\nGenerando reporte de resultados...\n")
  
  # Crear contenido HTML básico
  html_content <- paste(
    "<!DOCTYPE html>",
    "<html>",
    "<head>",
    "<title>Reporte de Optimización - Bolivia</title>",
    "<style>",
    "body { font-family: Arial, sans-serif; margin: 40px; }",
    "h1 { color: #2c3e50; }",
    "h2 { color: #3498db; }",
    "table { border-collapse: collapse; width: 100%; }",
    "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
    "th { background-color: #f2f2f2; }",
    ".optimo { background-color: #d4edda; }",
    "</style>",
    "</head>",
    "<body>",
    "<h1>Reporte de Optimización de Recursos Hídricos</h1>",
    "<h2>Resultados por Región Boliviana</h2>",
    "<table>",
    "<tr><th>Región</th><th>Agricultura (mill. m³)</th><th>Industria (mill. m³)</th><th>Doméstico (mill. m³)</th><th>Beneficio Total (mill. Bs)</th></tr>",
    paste(sapply(1:nrow(resultados_bolivia), function(i) {
      paste("<tr>",
            "<td>", resultados_bolivia$Region[i], "</td>",
            "<td>", resultados_bolivia$Agricultura[i], "</td>",
            "<td>", resultados_bolivia$Industria[i], "</td>",
            "<td>", resultados_bolivia$Domestico[i], "</td>",
            "<td>", resultados_bolivia$Beneficio_Total[i], "</td>",
            "</tr>")
    }), collapse = ""),
    "</table>",
    "<h2>Conclusiones</h2>",
    "<ul>",
    "<li>La optimización matemática permite asignar recursos escasos eficientemente</li>",
    "<li>El balance entre sectores productivos es crucial para el desarrollo sostenible</li>",
    "<li>Considerar restricciones ambientales asegura la sostenibilidad a largo plazo</li>",
    "</ul>",
    "</body>",
    "</html>",
    sep = "\n"
  )
  
  # Guardar archivo
  writeLines(html_content, "reporte_optimizacion.html")
  cat("Reporte guardado como 'reporte_optimizacion.html'\n")
  cat("Abre este archivo en tu navegador para ver el reporte completo.\n")
}

# Opcional: generar reporte
# generar_reporte()

# ---------- 7. EJERCICIOS PRÁCTICOS ----------
cat("\n========================================\n")
cat("7. EJERCICIOS PRÁCTICOS PARA RESOLVER\n")
cat("========================================\n")

ejercicios_practicos <- function() {
  cat("\nEJERCICIO 1: Planificación Forestal\n")
  cat("----------------------------------\n")
  cat("Una comunidad en la Chiquitanía tiene 500 ha para:\n")
  cat("- Madera comercial (beneficio: 2000 Bs/ha)\n")
  cat("- Conservación (beneficio ecológico: 1500 Bs/ha)\n")
  cat("- Agroforestería (beneficio: 1800 Bs/ha)\n")
  cat("\nRestricciones:\n")
  cat("1. Mínimo 100 ha para conservación\n")
  cat("2. Máximo 300 ha para madera\n")
  cat("3. Agroforestería debe ser al menos 50% del área de madera\n")
  cat("\nPregunta: ¿Cómo asignar las 500 ha para maximizar beneficios?\n")
  
  cat("\nEJERCICIO 2: Gestión de Residuos\n")
  cat("--------------------------------\n")
  cat("Una ciudad boliviana genera 1000 ton/mes de residuos:\n")
  cat("- Reciclaje: costo 50 Bs/ton, beneficio ambiental 80 Bs/ton\n")
  cat("- Compostaje: costo 30 Bs/ton, beneficio 60 Bs/ton\n")
  cat("- Relleno sanitario: costo 20 Bs/ton, beneficio 0 Bs/ton\n")
  cat("\nRestricciones:\n")
  cat("1. Mínimo 30% debe reciclarse\n")
  cat("2. Máximo 40% puede ir a relleno\n")
  cat("3. Presupuesto máximo: 40,000 Bs/mes\n")
  cat("\nPregunta: ¿Cómo minimizar costo total manteniendo beneficios ambientales?\n")
}

ejercicios_practicos()

# ---------- 8. SOLUCIÓN PASO A PASO ----------
cat("\n========================================\n")
cat("8. SOLUCIÓN DETALLADA DEL EJERCICIO 1\n")
cat("========================================\n")

solucion_ejercicio1 <- function() {
  cat("\nSolución del Ejercicio 1 - Planificación Forestal:\n")
  
  # Variables: x1 = madera, x2 = conservación, x3 = agroforestería
  cat("\nVariables:\n")
  cat("x1 = Área para madera comercial (ha)\n")
  cat("x2 = Área para conservación (ha)\n")
  cat("x3 = Área para agroforestería (ha)\n")
  
  cat("\nFunción objetivo (maximizar beneficios):\n")
  cat("Max Z = 2000*x1 + 1500*x2 + 1800*x3\n")
  
  cat("\nRestricciones:\n")
  cat("1) x1 + x2 + x3 = 500  (área total)\n")
  cat("2) x2 ≥ 100  (mínimo conservación)\n")
  cat("3) x1 ≤ 300  (máximo madera)\n")
  cat("4) x3 ≥ 0.5*x1  (agroforestería ≥ 50% madera)\n")
  cat("5) x1, x2, x3 ≥ 0\n")
  
  cat("\nResolviendo...\n")
  
  # Método manual simplificado
  cat("\nDe la restricción 4: x3 ≥ 0.5*x1\n")
  cat("Para maximizar, usemos x3 = 0.5*x1 (mínimo permitido)\n")
  
  cat("\nSustituyendo en restricción 1:\n")
  cat("x1 + x2 + 0.5*x1 = 500\n")
  cat("1.5*x1 + x2 = 500\n")
  cat("x2 = 500 - 1.5*x1\n")
  
  cat("\nDe restricción 2: x2 ≥ 100\n")
  cat("500 - 1.5*x1 ≥ 100\n")
  cat("-1.5*x1 ≥ -400\n")
  cat("x1 ≤ 266.67\n")
  
  cat("\nCombinando con restricción 3: x1 ≤ 300\n")
  cat("El límite más restrictivo es x1 ≤ 266.67\n")
  
  cat("\nPara maximizar Z, tomamos x1 máximo: x1 = 266.67\n")
  cat("Entonces: x2 = 500 - 1.5*266.67 = 500 - 400 = 100\n")
  cat("Y: x3 = 0.5*266.67 = 133.33\n")
  
  cat("\nVerificando restricciones:\n")
  cat("Total: 266.67 + 100 + 133.33 = 500 ha ✓\n")
  cat("Conservación: 100 ≥ 100 ✓\n")
  cat("Madera: 266.67 ≤ 300 ✓\n")
  cat("Agroforestería: 133.33 ≥ 0.5*266.67 = 133.33 ✓\n")
  
  cat("\nBeneficio total:\n")
  cat("Z = 2000*266.67 + 1500*100 + 1800*133.33\n")
  cat("Z = 533,340 + 150,000 + 240,000 = 923,340 Bs\n")
  
  cat("\nSOLUCIÓN ÓPTIMA:\n")
  cat("Madera: 266.7 ha\n")
  cat("Conservación: 100.0 ha\n")
  cat("Agroforestería: 133.3 ha\n")
  cat("Beneficio máximo: 923,340 Bs\n")
}

solucion_ejercicio1()

# ---------- 9. RESUMEN FINAL ----------
cat("\n========================================\n")
cat("9. RESUMEN Y RECOMENDACIONES\n")
cat("========================================\n")

cat("\nCONCEPTOS CLAVE APRENDIDOS:\n")
cat("1. Optimización = Encontrar la mejor solución dentro de límites\n")
cat("2. Variables de decisión = Lo que podemos controlar\n")
cat("3. Función objetivo = Lo que queremos maximizar o minimizar\n")
cat("4. Restricciones = Límites físicos, legales, económicos\n")
cat("5. Solución óptima = Mejor balance entre objetivos y restricciones\n")

cat("\nAPLICACIONES EN BOLIVIA:\n")
cat("• Gestión sostenible de agua en cuencas\n")
cat("• Planificación del uso del suelo\n")
cat("• Optimización de sistemas energéticos\n")
cat("• Diseño de políticas ambientales\n")
cat("• Evaluación de proyectos de desarrollo\n")

cat("\nPRÓXIMOS PASOS RECOMENDADOS:\n")
cat("1. Instalar R y RStudio localmente para más control\n")
cat("2. Aprecer a usar lpSolve para problemas lineales\n")
cat("3. Explorar optimización no lineal para problemas complejos\n")
cat("4. Aplicar estos conceptos a un problema real de tu comunidad\n")

cat("\n========================================\n")
cat("¡OPTIMIZACIÓN COMPLETADA EXITOSAMENTE!\n")
cat("========================================\n")