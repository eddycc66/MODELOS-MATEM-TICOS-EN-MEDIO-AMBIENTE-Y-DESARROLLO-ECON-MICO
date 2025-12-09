import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
import matplotlib.gridspec as gridspec
import pandas as pd

# Configuración de estilo
plt.style.use('seaborn-v0_8-darkgrid')
np.random.seed(42)

# ============================================================================
# 1. FUNCIONES PARA LOS MODELOS POBLACIONALES
# ============================================================================

def modelo_exponencial(P, t, r):
    """Modelo de crecimiento exponencial: dP/dt = rP"""
    return r * P

def modelo_logistico(P, t, r, K):
    """Modelo de crecimiento logístico: dP/dt = rP(1-P/K)"""
    return r * P * (1 - P/K)

def resolver_modelo(modelo, P0, t, args):
    """Resuelve el modelo diferencial"""
    sol = odeint(modelo, P0, t, args=args)
    return sol.flatten()

# ============================================================================
# 2. DATOS Y PARÁMETROS PARA BOLIVIA
# ============================================================================

# Datos poblacionales históricos aproximados de Bolivia (en millones)
# Fuente: estimaciones basadas en datos del INE Bolivia
anos_historicos = np.array([1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020])
poblacion_historica = np.array([3.0, 3.7, 4.5, 5.6, 6.9, 8.5, 10.5, 11.8])

# Parámetros estimados para Bolivia
r_exponencial = 0.022  # Tasa de crecimiento anual aproximada (2.2%)
r_logistico = 0.025    # Tasa de crecimiento intrínseca
K_bolivia = 20.0       # Capacidad de carga estimada para Bolivia (en millones)

# Tiempo para proyecciones futuras (1950-2100)
t_futuro = np.linspace(1950, 2100, 151)

# ============================================================================
# 3. SIMULACIONES DE LOS MODELOS
# ============================================================================

# Población inicial en 1950
P0 = poblacion_historica[0]

# Resolver modelos
poblacion_exp = resolver_modelo(modelo_exponencial, P0, t_futuro, (r_exponencial,))
poblacion_log = resolver_modelo(modelo_logistico, P0, t_futuro, (r_logistico, K_bolivia))

# ============================================================================
# 4. APLICACIONES PRÁCTICAS EN BOLIVIA
# ============================================================================

def calcular_necesidades_vivienda(poblacion, personas_por_vivienda=4.5):
    """Calcula necesidades de vivienda para planificación urbana"""
    return poblacion / personas_por_vivienda

def calcular_demanda_agua(poblacion, consumo_per_capita=100):  # litros/persona/día
    """Calcula demanda de agua para gestión de recursos"""
    return poblacion * consumo_per_capita * 365 / 1000000  # Millones de m³/año

def calcular_emisiones_co2(poblacion, emisiones_per_capita=1.8):  # toneladas CO2/persona/año
    """Calcula emisiones de CO2 para evaluación ambiental"""
    return poblacion * emisiones_per_capita

# Aplicaciones para el año 2030 y 2050
idx_2030 = np.where(t_futuro == 2030)[0][0]
idx_2050 = np.where(t_futuro == 2050)[0][0]

# Datos para aplicaciones
aplicaciones = {
    'Año': [2030, 2050],
    'Población Logística (millones)': [poblacion_log[idx_2030], poblacion_log[idx_2050]],
    'Viviendas necesarias (millones)': [
        calcular_necesidades_vivienda(poblacion_log[idx_2030]),
        calcular_necesidades_vivienda(poblacion_log[idx_2050])
    ],
    'Demanda de agua (millones m³/año)': [
        calcular_demanda_agua(poblacion_log[idx_2030]),
        calcular_demanda_agua(poblacion_log[idx_2050])
    ],
    'Emisiones CO2 (millones ton/año)': [
        calcular_emisiones_co2(poblacion_log[idx_2030]),
        calcular_emisiones_co2(poblacion_log[idx_2050])
    ]
}

df_aplicaciones = pd.DataFrame(aplicaciones)

# ============================================================================
# 5. VISUALIZACIÓN DE RESULTADOS
# ============================================================================

fig = plt.figure(figsize=(16, 12))
fig.suptitle('Modelos de Evolución Poblacional y sus Aplicaciones en Bolivia', 
             fontsize=18, fontweight='bold', y=0.98)

# Crear una cuadrícula para los subplots
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.3)

# ============================================================================
# Gráfico 1: Comparación de modelos poblacionales
# ============================================================================
ax1 = fig.add_subplot(gs[0, :2])
ax1.plot(t_futuro, poblacion_exp, 'b-', linewidth=2.5, alpha=0.7, 
         label=f'Modelo Exponencial (r={r_exponencial:.3f})')
ax1.plot(t_futuro, poblacion_log, 'r-', linewidth=2.5, alpha=0.7,
         label=f'Modelo Logístico (r={r_logistico:.3f}, K={K_bolivia:.1f})')
ax1.scatter(anos_historicos, poblacion_historica, color='darkgreen', 
            s=80, zorder=5, label='Datos históricos')
ax1.axhline(y=K_bolivia, color='gray', linestyle='--', alpha=0.7, 
            label=f'Capacidad de carga (K={K_bolivia}M)')
ax1.set_xlabel('Año', fontsize=12)
ax1.set_ylabel('Población (millones)', fontsize=12)
ax1.set_title('Comparación de Modelos Poblacionales para Bolivia', fontsize=14, fontweight='bold')
ax1.legend(loc='upper left')
ax1.grid(True, alpha=0.3)
ax1.set_xlim([1950, 2100])

# Añadir anotaciones
ax1.annotate('Crecimiento ilimitado\n(modelo exponencial)', 
             xy=(2070, poblacion_exp[-1]), xytext=(2040, 35),
             arrowprops=dict(arrowstyle='->', color='blue', alpha=0.7),
             fontsize=10, color='blue')

ax1.annotate('Estabilización cerca de K\n(modelo logístico)', 
             xy=(2070, poblacion_log[-1]), xytext=(2040, 15),
             arrowprops=dict(arrowstyle='->', color='red', alpha=0.7),
             fontsize=10, color='red')

# ============================================================================
# Gráfico 2: Tasas de crecimiento
# ============================================================================
ax2 = fig.add_subplot(gs[0, 2])
tasa_crecimiento_exp = r_exponencial * np.ones_like(t_futuro)
tasa_crecimiento_log = r_logistico * (1 - poblacion_log/K_bolivia)

ax2.plot(t_futuro, tasa_crecimiento_exp * 100, 'b-', linewidth=2, alpha=0.7, 
         label='Exponencial')
ax2.plot(t_futuro, tasa_crecimiento_log * 100, 'r-', linewidth=2, alpha=0.7,
         label='Logístico')
ax2.set_xlabel('Año', fontsize=12)
ax2.set_ylabel('Tasa de crecimiento (%)', fontsize=12)
ax2.set_title('Tasas de Crecimiento Poblacional', fontsize=14, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_xlim([1950, 2100])

# ============================================================================
# Gráfico 3: Aplicación - Necesidades de vivienda
# ============================================================================
ax3 = fig.add_subplot(gs[1, 0])
viviendas_necesarias = calcular_necesidades_vivienda(poblacion_log)
ax3.plot(t_futuro, viviendas_necesarias, 'green', linewidth=2.5)
ax3.fill_between(t_futuro, 0, viviendas_necesarias, alpha=0.3, color='green')
ax3.set_xlabel('Año', fontsize=11)
ax3.set_ylabel('Viviendas necesarias (millones)', fontsize=11)
ax3.set_title('Planificación Urbana:\nNecesidades de Vivienda', fontsize=13, fontweight='bold')
ax3.grid(True, alpha=0.3)
ax3.set_xlim([2020, 2100])

# Destacar años específicos
for year in [2030, 2050, 2070]:
    idx = np.where(t_futuro == year)[0][0]
    ax3.plot(year, viviendas_necesarias[idx], 'ro', markersize=8)
    ax3.annotate(f'{viviendas_necesarias[idx]:.1f}M', 
                 xy=(year, viviendas_necesarias[idx]),
                 xytext=(year-5, viviendas_necesarias[idx]+0.5),
                 fontsize=9)

# ============================================================================
# Gráfico 4: Aplicación - Demanda de agua
# ============================================================================
ax4 = fig.add_subplot(gs[1, 1])
demanda_agua = calcular_demanda_agua(poblacion_log)
ax4.plot(t_futuro, demanda_agua, 'blue', linewidth=2.5)
ax4.fill_between(t_futuro, 0, demanda_agua, alpha=0.3, color='blue')
ax4.set_xlabel('Año', fontsize=11)
ax4.set_ylabel('Demanda de agua (millones m³/año)', fontsize=11)
ax4.set_title('Gestión de Recursos:\nDemanda de Agua', fontsize=13, fontweight='bold')
ax4.grid(True, alpha=0.3)
ax4.set_xlim([2020, 2100])

# Línea de referencia (capacidad actual estimada de suministro)
capacidad_agua_actual = 650  # Millones de m³/año (estimado)
ax4.axhline(y=capacidad_agua_actual, color='red', linestyle='--', alpha=0.7,
            label=f'Capacidad actual estimada\n({capacidad_agua_actual}M m³/año)')
ax4.legend(loc='upper left', fontsize=9)

# ============================================================================
# Gráfico 5: Aplicación - Emisiones de CO2
# ============================================================================
ax5 = fig.add_subplot(gs[1, 2])
emisiones = calcular_emisiones_co2(poblacion_log)
ax5.plot(t_futuro, emisiones, 'brown', linewidth=2.5)
ax5.fill_between(t_futuro, 0, emisiones, alpha=0.3, color='brown')
ax5.set_xlabel('Año', fontsize=11)
ax5.set_ylabel('Emisiones de CO₂ (millones ton/año)', fontsize=11)
ax5.set_title('Evaluación Ambiental:\nEmisiones de CO₂', fontsize=13, fontweight='bold')
ax5.grid(True, alpha=0.3)
ax5.set_xlim([2020, 2100])

# Meta de reducción (ejemplo: 50% de las emisiones actuales)
meta_reduccion = emisiones[np.where(t_futuro == 2020)[0][0]] * 0.5
ax5.axhline(y=meta_reduccion, color='green', linestyle='--', alpha=0.7,
            label='Meta de reducción 50%')
ax5.legend(loc='upper left', fontsize=9)

# ============================================================================
# Gráfico 6: Tabla de aplicaciones prácticas
# ============================================================================
ax6 = fig.add_subplot(gs[2, :])
ax6.axis('tight')
ax6.axis('off')

# Crear tabla
table_data = []
headers = ['Año', 'Población (M)', 'Viviendas (M)', 'Agua (M m³/año)', 'CO₂ (M ton/año)']

for i, row in df_aplicaciones.iterrows():
    table_data.append([
        int(row['Año']),
        f"{row['Población Logística (millones)']:.1f}",
        f"{row['Viviendas necesarias (millones)']:.1f}",
        f"{row['Demanda de agua (millones m³/año)']:.1f}",
        f"{row['Emisiones CO2 (millones ton/año)']:.1f}"
    ])

# Añadir datos actuales (2020) para comparación
poblacion_2020 = poblacion_historica[-1]
table_data.insert(0, [
    2020,
    f"{poblacion_2020:.1f}",
    f"{calcular_necesidades_vivienda(poblacion_2020):.1f}",
    f"{calcular_demanda_agua(poblacion_2020):.1f}",
    f"{calcular_emisiones_co2(poblacion_2020):.1f}"
])

table = ax6.table(cellText=table_data, colLabels=headers, 
                  cellLoc='center', loc='center',
                  colColours=['#f0f0f0']*5)

table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1.2, 1.8)

ax6.set_title('Aplicaciones Prácticas de los Modelos Poblacionales en Bolivia', 
              fontsize=14, fontweight='bold', pad=20)

# ============================================================================
# 6. ANÁLISIS DE ESCENARIOS
# ============================================================================

# Crear un gráfico adicional para análisis de sensibilidad
fig2, axes = plt.subplots(2, 2, figsize=(14, 10))
fig2.suptitle('Análisis de Sensibilidad: Efecto de Parámetros en el Modelo Logístico', 
              fontsize=16, fontweight='bold')

# Escenario 1: Variación de la tasa de crecimiento (r)
axes[0, 0].set_title('Variación de la tasa de crecimiento (r)')
for r in [0.015, 0.020, 0.025, 0.030]:
    poblacion_escenario = resolver_modelo(modelo_logistico, P0, t_futuro, (r, K_bolivia))
    axes[0, 0].plot(t_futuro, poblacion_escenario, linewidth=2, 
                   label=f'r = {r:.3f}')
axes[0, 0].set_xlabel('Año')
axes[0, 0].set_ylabel('Población (millones)')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Escenario 2: Variación de la capacidad de carga (K)
axes[0, 1].set_title('Variación de la capacidad de carga (K)')
for K in [15.0, 20.0, 25.0, 30.0]:
    poblacion_escenario = resolver_modelo(modelo_logistico, P0, t_futuro, (r_logistico, K))
    axes[0, 1].plot(t_futuro, poblacion_escenario, linewidth=2, 
                   label=f'K = {K:.1f}M')
axes[0, 1].set_xlabel('Año')
axes[0, 1].set_ylabel('Población (millones)')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Escenario 3: Cambio en población inicial
axes[1, 0].set_title('Variación de población inicial (P₀)')
for P0_esc in [2.0, 3.0, 4.0, 5.0]:
    poblacion_escenario = resolver_modelo(modelo_logistico, P0_esc, t_futuro, (r_logistico, K_bolivia))
    axes[1, 0].plot(t_futuro, poblacion_escenario, linewidth=2, 
                   label=f'P₀ = {P0_esc:.1f}M')
axes[1, 0].set_xlabel('Año')
axes[1, 0].set_ylabel('Población (millones)')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Escenario 4: Comparación con otros países sudamericanos
axes[1, 1].set_title('Comparación con países vecinos (K diferentes)')
paises = {
    'Bolivia (K=20M)': (r_logistico, 20.0),
    'Perú (K=40M)': (0.022, 40.0),
    'Chile (K=25M)': (0.015, 25.0),
    'Paraguay (K=15M)': (0.018, 15.0)
}

for pais, params in paises.items():
    r, K = params
    poblacion_escenario = resolver_modelo(modelo_logistico, 3.0, t_futuro, (r, K))
    axes[1, 1].plot(t_futuro, poblacion_escenario, linewidth=2, label=pais)

axes[1, 1].set_xlabel('Año')
axes[1, 1].set_ylabel('Población (millones)')
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()

# ============================================================================
# 7. IMPRIMIR RESULTADOS CLAVE
# ============================================================================

print("=" * 80)
print("MODELOS DE EVOLUCIÓN POBLACIONAL - APLICACIONES EN BOLIVIA")
print("=" * 80)

print("\n1. PROYECCIONES POBLACIONALES (Modelo Logístico):")
print("-" * 60)
print(f"Población 2020: {poblacion_historica[-1]:.2f} millones")
print(f"Población 2030: {poblacion_log[idx_2030]:.2f} millones")
print(f"Población 2050: {poblacion_log[idx_2050]:.2f} millones")
print(f"Población 2100: {poblacion_log[-1]:.2f} millones")
print(f"Capacidad de carga estimada (K): {K_bolivia:.1f} millones")

print("\n2. APLICACIONES PRÁCTICAS:")
print("-" * 60)
print(df_aplicaciones.to_string(index=False))

print("\n3. COMPARACIÓN DE MODELOS (2100):")
print("-" * 60)
print(f"Modelo exponencial: {poblacion_exp[-1]:.2f} millones")
print(f"Modelo logístico: {poblacion_log[-1]:.2f} millones")
print(f"Diferencia: {poblacion_exp[-1] - poblacion_log[-1]:.2f} millones")

print("\n4. IMPLICACIONES PARA PLANIFICACIÓN:")
print("-" * 60)
print(f"• Entre 2020 y 2050, Bolivia necesitará aproximadamente ")
print(f"  {aplicaciones['Viviendas necesarias (millones)'][1] - calcular_necesidades_vivienda(poblacion_2020):.1f} millones")
print(f"  de nuevas viviendas.")
print(f"• La demanda de agua aumentará en aproximadamente ")
print(f"  {aplicaciones['Demanda de agua (millones m³/año)'][1] - calcular_demanda_agua(poblacion_2020):.1f} millones de m³/año.")
print(f"• Las emisiones de CO₂ podrían aumentar en ")
print(f"  {aplicaciones['Emisiones CO2 (millones ton/año)'][1] - calcular_emisiones_co2(poblacion_2020):.1f} millones de toneladas anuales.")
print(f"  si no se implementan medidas de mitigación.")

print("\n" + "=" * 80)
print("CONCLUSIÓN: El modelo logístico proporciona proyecciones más realistas")
print("para la planificación a largo plazo, considerando los límites de recursos")
print("y capacidad de carga del territorio boliviano.")
print("=" * 80)

# Mostrar gráficos
plt.show()