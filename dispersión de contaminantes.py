import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.patches import Circle, Rectangle
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
from scipy.special import erf
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 1. IMPLEMENTACIÓN DEL MODELO GAUSSIANO DE PLUMA
# ============================================================================

def coeficientes_dispersion_pasquill_gifford(x, clase_estabilidad='D'):
    """
    Calcula los coeficientes de dispersión σy y σz según el método
    de Pasquill-Gifford para diferentes clases de estabilidad atmosférica.

    Clases de estabilidad:
    A: Extremadamente inestable
    B: Moderadamente inestable
    C: Ligeramente inestable
    D: Neutra (condiciones nubladas/viento moderado)
    E: Ligeramente estable
    F: Moderadamente estable
    """
    # Coeficientes para σy (horizontal) en metros
    # Forma: σy = a * x^b (x en metros)
    if clase_estabilidad == 'A':  # Extremadamente inestable
        a_y, b_y = 0.22, 0.88
        a_z, b_z = 0.20, 0.78
    elif clase_estabilidad == 'B':  # Moderadamente inestable
        a_y, b_y = 0.16, 0.89
        a_z, b_z = 0.12, 0.91
    elif clase_estabilidad == 'C':  # Ligeramente inestable
        a_y, b_y = 0.11, 0.91
        a_z, b_z = 0.08, 0.92
    elif clase_estabilidad == 'D':  # Neutra
        a_y, b_y = 0.08, 0.92
        a_z, b_z = 0.06, 0.92
    elif clase_estabilidad == 'E':  # Ligeramente estable
        a_y, b_y = 0.06, 0.92
        a_z, b_z = 0.03, 0.92
    elif clase_estabilidad == 'F':  # Moderadamente estable
        a_y, b_y = 0.04, 0.92
        a_z, b_z = 0.016, 0.89
    else:  # Default: clase D
        a_y, b_y = 0.08, 0.92
        a_z, b_z = 0.06, 0.92

    σy = a_y * (x/1000)**b_y * 1000  # Convertir de km a m
    σz = a_z * (x/1000)**b_z * 1000  # Convertir de km a m

    # Límite inferior para evitar valores muy pequeños
    σy = np.maximum(σy, 10.0)
    σz = np.maximum(σz, 5.0)

    return σy, σz

def modelo_gaussiano_pluma(x, y, z, Q, u, H, σy, σz):
    """
    Modelo Gaussiano de pluma para concentración de contaminantes

    C(x,y,z) = (Q/(2πσyσzu)) × exp(-y²/(2σy²)) ×
               [exp(-(z-H)²/(2σz²)) + exp(-(z+H)²/(2σz²))]

    Parámetros:
    x, y, z: Coordenadas (m)
    Q: Tasa de emisión (g/s)
    u: Velocidad del viento (m/s)
    H: Altura efectiva de emisión (m)
    σy, σz: Coeficientes de dispersión (m)
    """
    # Prevenir división por cero
    if u <= 0 or σy <= 0 or σz <= 0:
        return 0.0

    term1 = Q / (2 * np.pi * σy * σz * u)
    term2 = np.exp(-y**2 / (2 * σy**2))
    term3 = np.exp(-(z - H)**2 / (2 * σz**2)) + np.exp(-(z + H)**2 / (2 * σz**2))

    return term1 * term2 * term3

# ============================================================================
# 2. ESCENARIO DE APLICACIÓN: PLANTA INDUSTRIAL EN EL ALTO, BOLIVIA
# ============================================================================

def escenario_planta_alto():
    """Escenario de una planta industrial en El Alto, Bolivia"""
    escenario = {
        'nombre': 'Planta Industrial - Ciudad de El Alto',
        'ubicacion': 'El Alto, Departamento de La Paz',
        'altitud': 4150,  # metros sobre el nivel del mar
        'emisor': {
            'tipo': 'Chimenea industrial',
            'altura_fisica': 50,  # m
            'diametro': 2.5,  # m
            'velocidad_salida': 15,  # m/s
            'temperatura_salida': 150,  # °C
        },
        'emisiones': {
            'SO2': {'Q': 100, 'unidad': 'g/s'},  # Dióxido de azufre
            'PM10': {'Q': 50, 'unidad': 'g/s'},   # Material particulado
            'NOx': {'Q': 80, 'unidad': 'g/s'},    # Óxidos de nitrógeno
        },
        'meteorologia': {
            'velocidad_viento_promedio': 4.0,  # m/s (típico en El Alto)
            'direccion_viento_predominante': 270,  # grados (Oeste)
            'temperatura_ambiente': 10,  # °C (promedio anual)
            'clase_estabilidad': 'D',  # Neutra (común en altiplano)
        },
        'receptores_sensibles': [
            {'nombre': 'Zona Residencial Norte', 'x': 1000, 'y': 500, 'z': 0},
            {'nombre': 'Escuela Pública', 'x': 2000, 'y': 0, 'z': 0},
            {'nombre': 'Hospital Municipal', 'x': 1500, 'y': -300, 'z': 0},
            {'nombre': 'Área Agrícola', 'x': 3000, 'y': 1000, 'z': 0},
        ]
    }
    return escenario

# ============================================================================
# 3. CÁLCULO DE ALTURA EFECTIVA DE LA CHIMENEA (Corrección Briggs)
# ============================================================================

def altura_efectiva_chimenea(H_fisica, v_s, d, T_s, T_a, u):
    """
    Calcula la altura efectiva de la chimenea usando la fórmula de Briggs
    H = H_fisica + Δh
    Δh: Ascenso de la pluma por flotación y momento
    """
    # Distancia característica para el ascenso de la pluma (m)
    x_max = 2000 # Un valor representativo, se puede ajustar

    # Diferencia de temperatura
    ΔT = T_s - T_a

    # Flujo de calor
    Q_h = (np.pi/4) * d**2 * v_s * 1005 * ΔT  # J/s (Cp aire ≈ 1005 J/kg·K)

    # Parámetros para condiciones neutras (clase D)
    if ΔT > 0:
        # Ascenso por flotación
        F_b = 9.81 * (d**2/4) * v_s * (ΔT/T_a)
        Δh_flotacion = 1.6 * F_b**(1/3) * (x_max/u)**(2/3) if u > 0 else 0
    else:
        Δh_flotacion = 0

    # Ascenso por momento
    F_m = (d**2/4) * v_s**2 * (T_s/T_a)
    Δh_momento = 3.0 * d * (v_s/u) if u > 0 else 0

    # Altura efectiva total
    Δh_total = max(Δh_flotacion, Δh_momento)
    H_efectiva = H_fisica + Δh_total

    return min(H_efectiva, H_fisica * 2)  # Límite superior razonable

# ============================================================================
# 4. VISUALIZACIÓN 2D: MAPA DE CONCENTRACIONES
# ============================================================================

def visualizar_mapa_concentracion(contaminante='SO2', z_nivel=1.8):
    """Visualización 2D de la dispersión del contaminante"""

    # Configurar escenario
    escenario = escenario_planta_alto()
    Q = escenario['emisiones'][contaminante]['Q']
    u = escenario['meteorologia']['velocidad_viento_promedio']
    H_fisica = escenario['emisor']['altura_fisica']

    # Calcular altura efectiva
    H_efectiva = altura_efectiva_chimenea(
        H_fisica,
        escenario['emisor']['velocidad_salida'],
        escenario['emisor']['diametro'],
        escenario['emisor']['temperatura_salida'],
        escenario['meteorologia']['temperatura_ambiente'],
        u
    )

    # Crear malla espacial
    x = np.linspace(100, 5000, 100)  # Distancia desde la fuente (m)
    y = np.linspace(-1000, 1000, 80)  # Ancho transversal (m)
    X, Y = np.meshgrid(x, y)

    # Calcular concentraciones
    C = np.zeros_like(X)

    for i in range(len(x)):
        for j in range(len(y)):
            σy, σz = coeficientes_dispersion_pasquill_gifford(
                x[i],
                escenario['meteorologia']['clase_estabilidad']
            )
            C[j, i] = modelo_gaussiano_pluma(
                x[i], Y[j, i], z_nivel, Q, u, H_efectiva, σy, σz
            )

    # Convertir a μg/m³ para mejor interpretación
    C_ug = C * 1e6  # g/m³ a μg/m³

    # Crear figura
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Dispersión de {contaminante} - {escenario["nombre"]}\n'
                 f'Q={Q} g/s, u={u} m/s, H_ef={H_efectiva:.1f} m, Estabilidad: {escenario["meteorologia"]["clase_estabilidad"]}',
                 fontsize=14, fontweight='bold')

    # ========== Subplot 1: Mapa de concentraciones ==========
    ax1 = axes[0, 0]
    contour = ax1.contourf(X, Y, C_ug, levels=50, cmap='YlOrRd', alpha=0.8)
    ax1.contour(X, Y, C_ug, levels=10, colors='k', alpha=0.3, linewidths=0.5)

    # Marcar la fuente
    ax1.plot(0, 0, 'r^', markersize=12, label='Fuente', markeredgecolor='k')

    # Marcar receptores sensibles
    for receptor in escenario['receptores_sensibles']:
        ax1.plot(receptor['x'], receptor['y'], 'bs', markersize=8,
                markeredgecolor='k', label=receptor['nombre'])
        ax1.annotate(receptor['nombre'],
                    xy=(receptor['x'], receptor['y']),
                    xytext=(receptor['x']+50, receptor['y']+50),
                    fontsize=9, color='blue')

    # Línea de la pluma central
    ax1.axhline(y=0, color='k', linestyle='--', alpha=0.5, linewidth=1)

    ax1.set_xlabel('Distancia desde la fuente (m)', fontsize=11)
    ax1.set_ylabel('Distancia transversal (m)', fontsize=11)
    ax1.set_title(f'Mapa de Concentración de {contaminante} (μg/m³) a {z_nivel} m de altura',
                  fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3)

    # Barra de color
    cbar = plt.colorbar(contour, ax=ax1)
    cbar.set_label(f'Concentración de {contaminante} (μg/m³)', fontsize=11)

    # ========== Subplot 2: Perfil longitudinal ==========
    ax2 = axes[0, 1]
    # Concentración en el eje central (y=0)
    C_eje = np.zeros_like(x)
    for i in range(len(x)):
        σy, σz = coeficientes_dispersion_pasquill_gifford(
            x[i], escenario['meteorologia']['clase_estabilidad']
        )
        C_eje[i] = modelo_gaussiano_pluma(
            x[i], 0, z_nivel, Q, u, H_efectiva, σy, σz
        ) * 1e6  # Convertir a μg/m³

    ax2.plot(x, C_eje, 'b-', linewidth=2.5)
    ax2.fill_between(x, 0, C_eje, alpha=0.3, color='blue')

    # Límites permisibles (ejemplo: OMS para SO2 - 24h: 20 μg/m³)
    if contaminante == 'SO2':
        limite_OMS = 20  # μg/m³ (promedio 24h)
        ax2.axhline(y=limite_OMS, color='r', linestyle='--', 
                   label=f'Límite OMS ({limite_OMS} μg/m³)')

    # Marcar receptores en el eje
    for receptor in escenario['receptores_sensibles']:
        if abs(receptor['y']) < 50:  # Cerca del eje central
            idx = np.argmin(np.abs(x - receptor['x']))
            ax2.plot(receptor['x'], C_eje[idx], 'ro', markersize=8)
            ax2.annotate(receptor['nombre'],
                        xy=(receptor['x'], C_eje[idx]),
                        xytext=(receptor['x']+100, C_eje[idx]*1.1),
                        fontsize=9, color='red')

    ax2.set_xlabel('Distancia desde la fuente (m)', fontsize=11)
    ax2.set_ylabel(f'Concentración de {contaminante} (μg/m³)', fontsize=11)
    ax2.set_title('Perfil Longitudinal en el Eje Central (y=0)',
                  fontsize=12, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # ========== Subplot 3: Perfil transversal ==========
    ax3 = axes[1, 0]
    # Distancia fija: 2000 m
    x_fijo = 2000
    σy_fijo, σz_fijo = coeficientes_dispersion_pasquill_gifford(
        x_fijo, escenario['meteorologia']['clase_estabilidad']
    )

    C_transversal = np.zeros_like(y)
    for j in range(len(y)):
        C_transversal[j] = modelo_gaussiano_pluma(
            x_fijo, y[j], z_nivel, Q, u, H_efectiva, σy_fijo, σz_fijo
        ) * 1e6

    ax3.plot(y, C_transversal, 'g-', linewidth=2.5)
    ax3.fill_between(y, 0, C_transversal, alpha=0.3, color='green')

    # Mostrar ancho de la pluma (2σy)
    ancho_pluma = 2 * σy_fijo
    ax3.axvline(x=-ancho_pluma/2, color='k', linestyle=':', alpha=0.7,
               label=f'Ancho pluma (2σy = {ancho_pluma:.0f} m)')
    ax3.axvline(x=ancho_pluma/2, color='k', linestyle=':', alpha=0.7)

    ax3.set_xlabel('Distancia transversal (m)', fontsize=11)
    ax3.set_ylabel(f'Concentración de {contaminante} (μg/m³)', fontsize=11)
    ax3.set_title(f'Perfil Transversal a x = {x_fijo} m',
                  fontsize=12, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # ========== Subplot 4: Efecto de la altura ==========
    ax4 = axes[1, 1]
    # Concentración a diferentes alturas
    alturas = [0, 10, 20, 50, 100]
    x_perfil = np.linspace(100, 3000, 50)

    for altura in alturas:
        C_altura = np.zeros_like(x_perfil)
        for i in range(len(x_perfil)):
            σy, σz = coeficientes_dispersion_pasquill_gifford(
                x_perfil[i], escenario['meteorologia']['clase_estabilidad']
            )
            C_altura[i] = modelo_gaussiano_pluma(
                x_perfil[i], 0, altura, Q, u, H_efectiva, σy, σz
            ) * 1e6

        ax4.plot(x_perfil, C_altura, linewidth=2,
                label=f'z = {altura} m')

    ax4.set_xlabel('Distancia desde la fuente (m)', fontsize=11)
    ax4.set_ylabel(f'Concentración de {contaminante} (μg/m³)', fontsize=11)
    ax4.set_title('Concentración a Diferentes Alturas (y=0)',
                  fontsize=12, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig, C_ug, escenario

# ============================================================================
# 5. DISEÑO DE RED DE MONITOREO
# ============================================================================

def diseñar_red_monitoreo(escenario, C_max, umbral_alerta=50):
    """Diseña una red óptima de monitoreo basada en el modelo"""

    print("=" * 80)
    print("DISEÑO DE RED DE MONITOREO DE CALIDAD DEL AIRE")
    print("=" * 80)
    print(f"Escenario: {escenario['nombre']}")
    print(f"Ubicación: {escenario['ubicacion']}")
    print("-" * 80)

    # Ubicaciones recomendadas para monitores
    ubicaciones_monitores = []

    # 1. Monitor en dirección del viento predominante
    direccion_viento = escenario['meteorologia']['direccion_viento_predominante']
    distancia_max = 3000  # m

    # Convertir dirección a coordenadas
    rad = np.radians(90 - direccion_viento)  # 0° = Norte, 90° = Este
    x_monitor = distancia_max * np.cos(rad)
    y_monitor = distancia_max * np.sin(rad)

    ubicaciones_monitores.append({
        'nombre': 'Monitor Principal - Dirección viento',
        'x': x_monitor,
        'y': y_monitor,
        'tipo': 'Estación fija',
        'parametros': ['SO2', 'PM10', 'NOx', 'O3', 'CO'],
        'justificacion': 'Capta máxima concentración en dirección del viento'
    })

    # 2. Monitores en zonas sensibles
    for receptor in escenario['receptores_sensibles']:
        ubicaciones_monitores.append({
            'nombre': f'Monitor - {receptor["nombre"]}',
            'x': receptor['x'],
            'y': receptor['y'],
            'tipo': 'Estación fija',
            'parametros': ['SO2', 'PM10', 'NOx'],
            'justificacion': f'Protección de {receptor["nombre"].lower()}'
        })

    # 3. Monitor de fondo (contra-viento)
    ubicaciones_monitores.append({
        'nombre': 'Monitor de Fondo',
        'x': -1000,  # Contra-viento
        'y': 0,
        'tipo': 'Estación de referencia',
        'parametros': ['SO2', 'PM10', 'NOx', 'O3', 'CO', 'Meteorología'],
        'justificacion': 'Mide concentraciones de fondo sin influencia directa'
    })

    # 4. Monitores móviles para validación
    for angulo in [45, 135, 225, 315]:
        rad = np.radians(90 - angulo)
        x_movil = 1500 * np.cos(rad)
        y_movil = 1500 * np.sin(rad)

        ubicaciones_monitores.append({
            'nombre': f'Monitor Móvil - Sector {angulo}°',
            'x': x_movil,
            'y': y_movil,
            'tipo': 'Unidad móvil',
            'parametros': ['SO2', 'PM10'],
            'justificacion': f'Validación en sector {angulo}° desde la fuente'
        })

    # Mostrar recomendaciones
    print("\nRECOMENDACIONES PARA LA RED DE MONITOREO:")
    print("-" * 80)

    df_monitoreo = pd.DataFrame(ubicaciones_monitores)
    print(df_monitoreo[['nombre', 'tipo', 'parametros', 'justificacion']].to_string(index=False))

    print("\nESPECIFICACIONES TÉCNICAS RECOMENDADAS:")
    print("-" * 80)
    print("• Frecuencia de muestreo: Cada 1 hora (promedios horarios)")
    print("• Parámetros mínimos: SO2, PM10, NOx")
    print("• Métodos de medición:")
    print("  - SO2: Fluorescencia UV")
    print("  - PM10: Beta atenuación")
    print("  - NOx: Quimiluminiscencia")
    print("• Control de calidad: Calibración diaria, validación de datos")
    print("• Umbral de alerta: Concentración >", umbral_alerta, "μg/m³ (SO2)")
    print("• Protocolo de acción: Notificar autoridades si se superan límites")

    return ubicaciones_monitores

# ============================================================================
# 6. EVALUACIÓN DE IMPACTO AMBIENTAL
# ============================================================================

def evaluacion_impacto_ambiental(escenario, concentraciones, contaminante='SO2'):
    """Realiza evaluación de impacto ambiental basada en concentraciones"""

    print("\n" + "=" * 80)
    print("EVALUACIÓN DE IMPACTO AMBIENTAL")
    print("=" * 80)

    # Estándares de calidad del aire (μg/m³)
    # Valores basados en normativa boliviana y recomendaciones OMS
    estandares = {
        'SO2': {
            'OMS_24h': 20,      # OMS: promedio 24 horas
            'OMS_1h': 40,       # OMS: promedio 1 hora
            'Bolivia_24h': 80,  # Normativa boliviana
            'alerta': 150       # Nivel de alerta
        },
        'PM10': {
            'OMS_24h': 45,
            'Bolivia_24h': 150,
            'alerta': 250
        },
        'NOx': {
            'OMS_1h': 200,
            'Bolivia_1h': 400,
            'alerta': 600
        }
    }

    # Análisis de concentraciones
    C_max = np.max(concentraciones)
    C_promedio = np.mean(concentraciones[concentraciones > 0])

    # Determinar nivel de impacto
    if contaminante in estandares:
        limites = estandares[contaminante]

        print(f"\nCONTAMINANTE ANALIZADO: {contaminante}")
        print("-" * 80)
        print(f"Concentración máxima modelada: {C_max:.2f} μg/m³")
        print(f"Concentración promedio modelada: {C_promedio:.2f} μg/m³")

        print(f"\nCOMPARACIÓN CON ESTÁNDARES:")
        print("-" * 80)
        for estandar, valor in limites.items():
            cumplimiento = "CUMPLE" if C_max <= valor else "EXCEDE"
            color = "✓" if C_max <= valor else "✗"
            print(f"{color} {estandar}: {valor} μg/m³ → {cumplimiento}")

        # Evaluación de impacto
        print(f"\nEVALUACIÓN DE IMPACTO:")
        print("-" * 80)

        if C_max <= limites.get('OMS_24h', 100):
            impacto = "BAJO"
            descripcion = "Concentraciones dentro de límites saludables"
            recomendaciones = ["Mantenimiento preventivo", "Monitoreo continuo"]
        elif C_max <= limites.get('Bolivia_24h', 200):
            impacto = "MODERADO"
            descripcion = "Concentraciones dentro de límites legales pero cercanas a límites de salud"
            recomendaciones = ["Optimizar procesos", "Evaluar mejoras tecnológicas", "Reforzar monitoreo"]
        elif C_max <= limites.get('alerta', 300):
            impacto = "ALTO"
            descripcion = "Concentraciones superan límites de salud"
            recomendaciones = ["Implementar medidas correctivas", "Evaluar reducción de operaciones", "Informar a población"]
        else:
            impacto = "MUY ALTO"
            descripcion = "Concentraciones en niveles de alerta"
            recomendaciones = ["Reducir operaciones inmediatamente", "Activar protocolo de emergencia", "Evacuación si es necesario"]

        print(f"Nivel de impacto: {impacto}")
        print(f"Descripción: {descripcion}")

        print(f"\nRECOMENDACIONES:")
        print("-" * 80)
        for i, rec in enumerate(recomendaciones, 1):
            print(f"{i}. {rec}")

    # Análisis de receptores sensibles
    print(f"\nANÁLISIS DE RECEPTORES SENSIBLES:")
    print("-" * 80)

    for receptor in escenario['receptores_sensibles']:
        # Estimación simple de concentración en receptor
        # (En un caso real, se usarían las coordenadas exactas del grid)
        print(f"\n{receptor['nombre']}:")
        if 'Escuela' in receptor['nombre'] or 'Hospital' in receptor['nombre']:
            print("  ☛ Población vulnerable (niños, enfermos)")
            print("  ☛ Se recomienda monitoreo especializado")
            print("  ☛ Considerar filtros de aire en instalaciones")
        elif 'Residencial' in receptor['nombre']:
            print("  ☛ Exposición crónica de población general")
            print("  ☛ Informar a residentes sobre calidad del aire")
        elif 'Agrícola' in receptor['nombre']:
            print("  ☛ Posible afectación a cultivos")
            print("  ☛ Monitorear daños en vegetación")

    print("\n" + "=" * 80)

# ============================================================================
# 7. PLANIFICACIÓN URBANA - ZONAS DE PROTECCIÓN
# ============================================================================

def planificacion_urbana_zona_proteccion(escenario):
    """Define zonas de protección para planificación urbana"""

    print("\n" + "=" * 80)
    print("PLANIFICACIÓN URBANA - ZONIFICACIÓN DE PROTECCIÓN")
    print("=" * 80)

    # Definir zonas de protección basadas en distancia
    zonas = [
        {
            'nombre': 'ZONA DE EXCLUSIÓN (0-500 m)',
            'radio': 500,
            'restricciones': [
                'Prohibida construcción de viviendas',
                'Prohibida ubicación de escuelas/hospitales',
                'Permitido solo uso industrial controlado',
                'Área verde obligatoria (30% mínimo)',
                'Monitoreo continuo obligatorio'
            ],
            'color': 'rojo'
        },
        {
            'nombre': 'ZONA DE RESTRICCIÓN (500-1500 m)',
            'radio': 1500,
            'restricciones': [
                'Viviendas con estudios de impacto ambiental',
                'Escuelas/hospitales con sistemas de filtración',
                'Densidad poblacional limitada',
                'Áreas verdes obligatorias (40% mínimo)',
                'Monitoreo periódico obligatorio'
            ],
            'color': 'naranja'
        },
        {
            'nombre': 'ZONA DE VIGILANCIA (1500-3000 m)',
            'radio': 3000,
            'restricciones': [
                'Desarrollo urbano con plan de mitigación',
                'Sistemas de alerta temprana',
                'Monitoreo recomendado',
                'Estudios epidemiológicos periódicos'
            ],
            'color': 'amarillo'
        },
        {
            'nombre': 'ZONA DE INFLUENCIA (>3000 m)',
            'radio': 5000,
            'restricciones': [
                'Monitoreo ocasional',
                'Considerar en planes de expansión urbana',
                'Evaluar impacto acumulativo con otras fuentes'
            ],
            'color': 'verde'
        }
    ]

    print("\nPROPUESTA DE ZONIFICACIÓN AMBIENTAL:")
    print("-" * 80)

    for zona in zonas:
        print(f"\n{zona['nombre']} (Radio: {zona['radio']} m):")
        for restriccion in zona['restricciones']:
            print(f"  • {restriccion}")

    print("\nRECOMENDACIONES DE PLANIFICACIÓN URBANA:")
    print("-" * 80)
    print("1. Incorporar zonas de protección en planes reguladores")
    print("2. Establecer corredores de viento para ventilación natural")
    print("3. Diseñar áreas verdes como barreras naturales")
    print("4. Implementar sistemas de transporte sostenible")
    print("5. Desarrollar planes de contingencia para episodios críticos")
    print("6. Fomentar tecnologías limpias en nuevas industrias")

    return zonas

# ============================================================================
# 8. VISUALIZACIÓN 3D DE LA PLUMA
# ============================================================================

def visualizacion_3d_pluma(contaminante='SO2'):
    """Visualización 3D de la dispersión de la pluma"""

    escenario = escenario_planta_alto()
    Q = escenario['emisiones'][contaminante]['Q']
    u = escenario['meteorologia']['velocidad_viento_promedio']
    H_fisica = escenario['emisor']['altura_fisica']

    # Calcular altura efectiva
    H_efectiva = altura_efectiva_chimenea(
        H_fisica,
        escenario['emisor']['velocidad_salida'],
        escenario['emisor']['diametro'],
        escenario['emisor']['temperatura_salida'],
        escenario['meteorologia']['temperatura_ambiente'],
        u
    )

    # Crear malla 3D
    x = np.linspace(100, 2000, 30)
    y = np.linspace(-500, 500, 20)
    z = np.linspace(0, 200, 15)

    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    C = np.zeros_like(X)

    # Calcular concentraciones en malla 3D
    for i in range(len(x)):
        σy, σz = coeficientes_dispersion_pasquill_gifford(
            x[i], escenario['meteorologia']['clase_estabilidad']
        )

        for j in range(len(y)):
            for k in range(len(z)):
                C[i, j, k] = modelo_gaussiano_pluma(
                    x[i], y[j], z[k], Q, u, H_efectiva, σy, σz
                ) * 1e6  # μg/m³

    # Crear figura 3D
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Visualizar solo puntos con concentración significativa
    umbral_viz = 0.1  # % de concentración máxima
    C_max = np.max(C)
    mask = C > (C_max * umbral_viz/100)

    # Gráfico de dispersión 3D
    scatter = ax.scatter(X[mask], Y[mask], Z[mask],
                        c=C[mask], cmap='hot',
                        s=10, alpha=0.6,
                        vmin=0, vmax=C_max)

    # Marcar la fuente
    ax.scatter([0], [0], [H_efectiva], c='red', s=200, marker='^',
              label=f'Fuente (H={H_efectiva:.0f} m)', edgecolors='k')

    # Marcar el suelo
    xx, yy = np.meshgrid(np.linspace(-200, 2000, 10),
                         np.linspace(-600, 600, 10))
    zz = np.zeros_like(xx)
    ax.plot_surface(xx, yy, zz, alpha=0.3, color='green',
                   label='Superficie del terreno')

    # Configuración del gráfico
    ax.set_xlabel('Distancia (m)', fontsize=11, labelpad=10)
    ax.set_ylabel('Ancho (m)', fontsize=11, labelpad=10)
    ax.set_zlabel('Altura (m)', fontsize=11, labelpad=10)
    ax.set_title(f'Visualización 3D de la Pluma de {contaminante}\n'
                 f'{escenario["nombre"]}', fontsize=14, fontweight='bold')

    # Barra de color
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.5, aspect=20)
    cbar.set_label(f'Concentración de {contaminante} (μg/m³)', fontsize=11)

    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)

    # Ajustar ángulo de vista
    ax.view_init(elev=30, azim=225)

    plt.tight_layout()
    return fig

# ============================================================================
# 9. EJECUCIÓN PRINCIPAL
# ============================================================================

def main():
    """Función principal que ejecuta todas las aplicaciones"""

    print("=" * 100)
    print("MODELO GAUSSIANO DE PLUMA - APLICACIONES EN BOLIVIA")
    print("=" * 100)

    # 1. Generar visualización 2D
    print("\n1. GENERANDO MODELO DE DISPERSIÓN...")
    contaminante = 'SO2'  # Puedes cambiar a 'PM10' o 'NOx'
    fig_2d, concentraciones, escenario = visualizar_mapa_concentracion(contaminante)

    # 2. Diseñar red de monitoreo
    print("\n2. DISEÑANDO RED DE MONITOREO...")
    ubicaciones_monitores = diseñar_red_monitoreo(escenario, np.max(concentraciones))

    # 3. Evaluación de impacto ambiental
    print("\n3. REALIZANDO EVALUACIÓN DE IMPACTO AMBIENTAL...")
    evaluacion_impacto_ambiental(escenario, concentraciones, contaminante)

    # 4. Planificación urbana
    print("\n4. PROPUESTAS PARA PLANIFICACIÓN URBANA...")
    zonas_proteccion = planificacion_urbana_zona_proteccion(escenario)

    # 5. Generar visualización 3D
    print("\n5. GENERANDO VISUALIZACIÓN 3D...")
    fig_3d = visualizacion_3d_pluma(contaminante)

    print("\n" + "=" * 100)
    print("ANÁLISIS COMPLETADO EXITOSAMENTE")
    print("=" * 100)

    # Guardar resultados
    fig_2d.savefig(f'dispersión_{contaminante}_bolivia.png', dpi=300, bbox_inches='tight')
    fig_3d.savefig(f'pluma_3d_{contaminante}_bolivia.png', dpi=300, bbox_inches='tight')

    print("\nResultados guardados en archivos PNG")
    print(f"- dispersión_{contaminante}_bolivia.png")
    print(f"- pluma_3d_{contaminante}_bolivia.png")

    plt.show()

# ============================================================================
# EJECUTAR EL PROGRAMA
# ============================================================================

if __name__ == "__main__":
    main()