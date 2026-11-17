import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Configuración de la página
st.set_page_config(page_title="Simulador de Sedimentador Continuo", layout="wide")
st.title("Simulador Interactivo de Sedimentador Continuo")
st.markdown("Modifica las condiciones de operación en el menú izquierdo para observar el balance de materia y determinar el **área mínima** mediante el método del flujo límite de sólidos.")

# --- PANEL LATERAL: CONTROLES DEL ALUMNO ---
st.sidebar.header("Parámetros de Operación")
Q0 = st.sidebar.slider("Caudal de alimentación, Q₀ (m³/h)", min_value=10.0, max_value=200.0, value=50.0, step=5.0)
C0 = st.sidebar.slider("Concentración de entrada, C₀ (kg/m³)", min_value=1.0, max_value=15.0, value=4.0, step=0.5)
Cu = st.sidebar.slider("Concentración deseada de lodos, Cᵤ (kg/m³)", min_value=15.0, max_value=60.0, value=30.0, step=1.0)

st.sidebar.header("Parámetros de Sedimentación (Modelo Vesilind)")
st.sidebar.latex(r"v_s = v_0 \cdot e^{-k \cdot C}")
v0 = st.sidebar.slider("Velocidad inicial, v₀ (m/h)", min_value=2.0, max_value=15.0, value=8.0, step=0.5)
k = st.sidebar.slider("Constante de sedimentación, k (m³/kg)", min_value=0.05, max_value=0.30, value=0.12, step=0.01)

# --- CÁLCULOS DE BALANCE DE MATERIA ---
# Suponemos clarificación ideal (Ce = 0 kg/m³)
Ce = 0.0
Qu = (Q0 * C0) / Cu  # Caudal de purga de lodos (m³/h)
Qe = Q0 - Qu         # Caudal de rebose clarificado (m³/h)

# --- CÁLCULOS DE FLUJO DE SÓLIDOS Y ÁREA MÍNIMA ---
C_vals = np.linspace(0.1, Cu * 1.15, 500)
vs_vals = v0 * np.exp(-k * C_vals)
G_vals = C_vals * vs_vals  # Flujo de sedimentación (kg / m²·h)

# Cálculo de la tangente desde (Cu, 0) a la curva G(C)
# La pendiente de la recta que une (Cu, 0) con (C, G(C)) es G(C) / (C - Cu)
# Buscamos el punto de tangencia en la zona descendente/inflexión (C < Cu)
valid_idx = np.where((C_vals > 1.0/k) & (C_vals < Cu))[0]

if len(valid_idx) > 0:
    slopes = G_vals[valid_idx] / (Cu - C_vals[valid_idx])
    # El flujo límite GL es el intercepto con el eje Y (C=0): GL = pendiente * Cu
    # Buscamos el mínimo local de la pendiente para garantizar la tangente crítica
    min_slope_idx = valid_idx[np.argmin(slopes)]
    C_lim = C_vals[min_slope_idx]
    G_lim_point = G_vals[min_slope_idx]
    slope = G_lim_point / (Cu - C_lim)
    GL = slope * Cu  # Flujo límite (kg / m²·h)
    Area_min = (Q0 * C0) / GL
    Diametro = np.sqrt((4 * Area_min) / np.pi)
    error_tangente = False
else:
    error_tangente = True

# --- INTERFAZ VISUAL EN DOS COLUMNAS ---
col1, col2 = st.columns([1.1, 1.2])

# COLUMNA 1: DIBUJO ESQUEMÁTICO DEL SEDIMENTADOR
with col1:
    st.subheader("1. Esquema y Balance de Materia")
    fig_tank, ax_tank = plt.subplots(figsize=(6, 5))
    ax_tank.set_xlim(0, 10)
    ax_tank.set_ylim(0, 10)
    ax_tank.axis('off')

    # Cuerpo cilíndrico y fondo cónico del sedimentador
    rect = patches.Rectangle((2.5, 4), 5, 4, linewidth=2, edgecolor='#1f77b4', facecolor='#d9edf7')
    cone = patches.Polygon([[2.5, 4], [7.5, 4], [5.5, 2], [4.5, 2]], closed=True, linewidth=2, edgecolor='#1f77b4', facecolor='#b0c4de')
    ax_tank.add_patch(rect)
    ax_tank.add_patch(cone)

    # Campana de alimentación central
    feed_well = patches.Rectangle((4.6, 5.5), 0.8, 2.5, linewidth=1.5, edgecolor='#333333', facecolor='#eeeeee')
    ax_tank.add_patch(feed_well)

    # Flechas de corrientes
    # Entrada (Alimentación)
    ax_tank.annotate('', xy=(5, 7.5), xytext=(5, 9.2), arrowprops=dict(arrowstyle="->", lw=2.5, color='black'))
    ax_tank.text(5.2, 8.6, f"Alimentación\nQ₀ = {Q0:.1f} m³/h\nC₀ = {C0:.1f} kg/m³", fontsize=9, fontweight='bold')

    # Salida superior (Rebose clarificado)
    ax_tank.annotate('', xy=(9.2, 7.8), xytext=(7.5, 7.8), arrowprops=dict(arrowstyle="->", lw=2.5, color='#2ca02c'))
    ax_tank.text(7.6, 8.1, f"Rebose (Clarificado)\nQₑ = {Qe:.1f} m³/h\nCₑ ≈ 0 kg/m³", fontsize=9, color='#2ca02c', fontweight='bold')

    # Salida inferior (Purga de lodos)
    ax_tank.annotate('', xy=(5, 0.5), xytext=(5, 2.0), arrowprops=dict(arrowstyle="->", lw=2.5, color='#8c564b'))
    ax_tank.text(5.3, 0.8, f"Purga de Lodos\nQᵤ = {Qu:.2f} m³/h\nCᵤ = {Cu:.1f} kg/m³", fontsize=9, color='#8c564b', fontweight='bold')

    # Etiquetas de zonas
    ax_tank.text(3.5, 6.8, "Zona de Clarificación", fontsize=8, color='#004085', style='italic')
    ax_tank.text(3.6, 3.2, "Zona de Espesamiento", fontsize=8, color='#004085', style='italic')

    st.pyplot(fig_tank)

# COLUMNA 2: GRÁFICA DE FLUJO DE SEDIMENTACIÓN Y RESULTADOS
with col2:
    st.subheader("2. Curva de Flujo de Sólidos (Método de Kynch)")
    
    if error_tangente:
        st.error("La concentración de lodos Cᵤ es demasiado baja respecto a los parámetros de sedimentación para trazar una tangente válida. Aumenta Cᵤ.")
    else:
        fig_flux, ax_flux = plt.subplots(figsize=(6, 4.2))
        
        # Curva de flujo G vs C
        ax_flux.plot(C_vals, G_vals, label="Curva de flujo: $G = C \cdot v_s$", color="#1f77b4", lw=2.5)
        
        # Recta de operación (tangente desde Cu hasta GL)
        C_line = np.array([0, Cu])
        G_line = np.array([GL, 0])
        ax_flux.plot(C_line, G_line, '--', color="#d62728", lw=2, label="Recta de operación (Tangente)")
        
        # Puntos clave
        ax_flux.scatter([0, C_lim, Cu], [GL, G_lim_point, 0], color="#d62728", zorder=5)
        ax_flux.annotate(f"$G_L$ = {GL:.2f}", xy=(0, GL), xytext=(1.5, GL * 1.03), fontweight='bold', color="#d62728")
        ax_flux.annotate(f"$C_L$ = {C_lim:.1f}", xy=(C_lim, G_lim_point), xytext=(C_lim + 1, G_lim_point + 1.5), fontsize=9)
        ax_flux.annotate(f"$C_u$ = {Cu:.1f}", xy=(Cu, 0), xytext=(Cu - 3, 2), fontweight='bold')

        ax_flux.set_title("Determinación del Flujo Límite ($G_L$)", fontsize=11)
        ax_flux.set_xlabel("Concentración de sólidos, C (kg/m³)")
        ax_flux.set_ylabel("Flujo de sedimentación, G (kg/m²·h)")
        ax_flux.set_xlim(0, Cu * 1.15)
        ax_flux.set_ylim(0, max(max(G_vals), GL) * 1.15)
        ax_flux.grid(True, linestyle=':', alpha=0.7)
        ax_flux.legend()
        
        st.pyplot(fig_flux)

        # Métricas destacadas de diseño
        st.markdown("### Resultados de Diseño")
        m1, m2, m3 = st.columns(3)
        m1.metric("Flujo Límite (Gₗ)", f"{GL:.2f} kg/m²·h")
        m2.metric("Área Mínima (Aₘᵢₙ)", f"{Area_min:.1f} m²")
        m3.metric("Diámetro Tanque (D)", f"{Diametro:.1f} m")
