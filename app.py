import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Bytepulse - Quantumsoft",
    page_icon="📈",
    layout="wide"
)

# Estructura de datos en sesión (Formato en Pesos Colombianos - COP)
if 'transacciones' not in st.session_state:
    st.session_state.transacciones = pd.DataFrame([
        {"Fecha": "2026-08-01", "Tipo": "Ingreso", "Categoría": "Nómina", "Monto": 3500000.0, "Descripción": "Sueldo mensual"},
        {"Fecha": "2026-08-02", "Tipo": "Gasto", "Categoría": "Alquiler", "Monto": 1200000.0, "Descripción": "Pago de arriendo"},
        {"Fecha": "2026-08-03", "Tipo": "Gasto", "Categoría": "Alimentación", "Monto": 450000.0, "Descripción": "Mercado del mes"},
        {"Fecha": "2026-08-04", "Tipo": "Deuda", "Categoría": "Tarjeta Crédito", "Monto": 300000.0, "Descripción": "Cuota del mes"}
    ])

if 'metas' not in st.session_state:
    st.session_state.metas = [
        {"Meta": "Fondo de Emergencia", "Objetivo": 5000000.0, "Actual": 1500000.0, "Plazo_Meses": 6}
    ]

def formato_cop(valor):
    return f"${valor:,.0f}".replace(",", ".")

# ==========================================
# 2. ENCABEZADO PRINCIPAL
# ==========================================
st.title("Bytepulse 📈")
st.caption("Solución Tecnológica de Gestión Financiera por **Quantumsoft** (Valores en COP)")
st.divider()

# Navegación por Pestañas
tab_dashboard, tab_registro, tab_ahorro = st.tabs([
    "📊 Dashboard General", 
    "📝 Registrar Transacción", 
    "🎯 Planes de Ahorro"
])

# ==========================================
# 3. PESTAÑA 1: DASHBOARD GENERAL
# ==========================================
with tab_dashboard:
    df = st.session_state.transacciones
    
    ingresos_totales = df[df['Tipo'] == 'Ingreso']['Monto'].sum()
    gastos_totales = df[df['Tipo'] == 'Gasto']['Monto'].sum()
    deudas_totales = df[df['Tipo'] == 'Deuda']['Monto'].sum()
    balance = ingresos_totales - gastos_totales - deudas_totales
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Balance Disponible", formato_cop(balance))
    col2.metric("Ingresos Totales", formato_cop(ingresos_totales))
    col3.metric("Gastos Totales", formato_cop(gastos_totales), delta_color="inverse")
    col4.metric("Deudas Acumuladas", formato_cop(deudas_totales), delta_color="inverse")
    
    st.divider()
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Distribución de Gastos y Deudas")
        df_gastos = df[df['Tipo'].isin(['Gasto', 'Deuda'])]
        if not df_gastos.empty:
            fig_pie = px.pie(df_gastos, values='Monto', names='Categoría', hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No hay datos de gastos registrados.")
            
    with c2:
        st.subheader("Flujo Financiero")
        if not df.empty:
            fig_bar = px.bar(df, x='Fecha', y='Monto', color='Tipo', barmode='group',
                             color_discrete_map={'Ingreso': '#2ecc71', 'Gasto': '#e74c3c', 'Deuda': '#f39c12'})
            st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# 4. PESTAÑA 2: REGISTRO DE TRANSACCIONES
# ==========================================
with tab_registro:
    st.subheader("Nuevo Registro Financiero")
    
    with st.form("form_transaccion", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        
        with col_a:
            tipo = st.selectbox("Tipo de Movimiento", ["Ingreso", "Gasto", "Deuda", "Inversión"])
            monto = st.number_input("Monto (COP $)", min_value=1000.0, step=50000.0, format="%.0f")
            fecha = st.date_input("Fecha de la Transacción", datetime.now())
            
        with col_b:
            categoria = st.selectbox("Categoría", ["Nómina", "Alquiler", "Alimentación", "Servicios", "Transporte", "Tarjeta Crédito", "Otros"])
            descripcion = st.text_input("Descripción (Opcional)")
            
        guardar = st.form_submit_button("Guardar Transacción")
        
        if guardar:
            nueva_transaccion = {
                "Fecha": str(fecha),
                "Tipo": tipo,
                "Categoría": categoria,
                "Monto": monto,
                "Descripción": descripcion
            }
            st.session_state.transacciones = pd.concat(
                [st.session_state.transacciones, pd.DataFrame([nueva_transaccion])], 
                ignore_index=True
            )
            st.success("Transacción registrada exitosamente.")
            st.rerun()

    st.subheader("Historial de Transacciones")
    st.dataframe(st.session_state.transacciones, use_container_width=True)

# ==========================================
# 5. PESTAÑA 3: PLANES DE AHORRO (CORREGIDO)
# ==========================================
with tab_ahorro:
    st.subheader("Planes de Ahorro y Recomendaciones Inteligentes")
    
    capacidad_ahorro = balance
    cuota_sugerida = capacidad_ahorro * 0.20 if capacidad_ahorro > 0 else 0
    
    st.info(f"💡 **Recomendación Bytepulse:** Tu capacidad actual de ahorro libre es de **{formato_cop(capacidad_ahorro)}**. Te sugerimos destinar al menos **{formato_cop(cuota_sugerida)}** mensuales a tus metas.")

    # Formulario con st.form para solucionar la persistencia del botón
    st.subheader("➕ Crear Nueva Meta de Ahorro")
    with st.form("form_nueva_meta", clear_on_submit=True):
        nombre_meta = st.text_input("Nombre de la Meta", value="Viaje / Inversión")
        monto_meta = st.number_input("Monto Objetivo (COP $)", min_value=100000.0, step=100000.0, format="%.0f")
        plazo_meses = st.number_input("Plazo estimado (Meses)", min_value=1, value=6)
        
        btn_crear_meta = st.form_submit_button("Guardar Meta de Ahorro")
        
        if btn_crear_meta:
            cuota_requerida = monto_meta / plazo_meses
            st.session_state.metas.append({
                "Meta": nombre_meta, 
                "Objetivo": monto_meta, 
                "Actual": 0.0, 
                "Plazo_Meses": plazo_meses
            })
            st.success(f"¡Meta '{nombre_meta}' creada exitosamente!")
            st.rerun()

    st.divider()
    # Despliegue de Metas Activas
    st.subheader("Tus Metas Activas")
    for idx, meta in enumerate(st.session_state.metas):
        porcentaje = min(meta["Actual"] / meta["Objetivo"], 1.0)
        st.write(f"**{meta['Meta']}** - Ahorrado: {formato_cop(meta['Actual'])} de {formato_cop(meta['Objetivo'])} ({porcentaje*100:.1f}%)")
        st.progress(porcentaje)
