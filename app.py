import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y PERSISTENCIA
# ==========================================
st.set_page_config(
    page_title="Bytepulse - Quantumsoft",
    page_icon="📈",
    layout="wide"
)

DB_FILE = "usuarios_data.json"

def cargar_datos():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {
        "admin": {
            "password": "123",
            "transacciones": [
                {"Fecha": "2026-08-01", "Tipo": "Ingreso", "Categoría": "Nómina", "Monto": 3500000.0, "Descripción": "Sueldo mensual"},
                {"Fecha": "2026-08-02", "Tipo": "Gasto", "Categoría": "Alquiler", "Monto": 1200000.0, "Descripción": "Pago de arriendo"}
            ],
            "metas": [
                {"Meta": "Fondo de Emergencia", "Objetivo": 5000000.0, "Actual": 1500000.0, "Plazo_Meses": 6}
            ]
        }
    }

def guardar_datos():
    with open(DB_FILE, "w") as f:
        json.dump(st.session_state.db_usuarios, f, indent=4)

if 'db_usuarios' not in st.session_state:
    st.session_state.db_usuarios = cargar_datos()

if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None

def formato_cop(valor):
    return f"${valor:,.0f}".replace(",", ".")

# ==========================================
# 2. SISTEMA DE AUTENTICACIÓN (LOGIN/REGISTRO)
# ==========================================
if st.session_state.usuario_actual is None:
    st.title("Bytepulse 📈")
    st.caption("Gestión Financiera Multi-Usuario por **Quantumsoft**")
    st.divider()

    col_login, col_reg = st.columns(2)

    with col_login:
        st.subheader("🔑 Iniciar Sesión")
        with st.form("form_login"):
            user_login = st.text_input("Usuario").strip().lower()
            pass_login = st.text_input("Contraseña", type="password")
            btn_login = st.form_submit_button("Entrar")

            if btn_login:
                db = st.session_state.db_usuarios
                if user_login in db and db[user_login]["password"] == pass_login:
                    st.session_state.usuario_actual = user_login
                    st.success(f"¡Bienvenido {user_login}!")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")

    with col_reg:
        st.subheader("📝 Registrar Nuevo Cliente")
        with st.form("form_registro"):
            user_reg = st.text_input("Nuevo Usuario").strip().lower()
            pass_reg = st.text_input("Nueva Contraseña", type="password")
            btn_reg = st.form_submit_button("Crear Cuenta")

            if btn_reg:
                if not user_reg or not pass_reg:
                    st.warning("Completa todos los campos.")
                elif user_reg in st.session_state.db_usuarios:
                    st.error("El usuario ya existe.")
                else:
                    st.session_state.db_usuarios[user_reg] = {
                        "password": pass_reg,
                        "transacciones": [],
                        "metas": []
                    }
                    guardar_datos()
                    st.success("Cuenta creada con éxito. Ya puedes iniciar sesión.")

    st.stop()

# ==========================================
# 3. PANEL PRINCIPAL (USUARIO AUTENTICADO)
# ==========================================
user = st.session_state.usuario_actual
datos_user = st.session_state.db_usuarios[user]

col_header, col_logout = st.columns([5, 1])
with col_header:
    st.title(f"Bytepulse 📈 - Hola, {user.capitalize()}")
    st.caption("Solución Tecnológica de Gestión Financiera por **Quantumsoft** (Valores en COP)")
with col_logout:
    st.write("")
    if st.button("🔒 Cerrar Sesión"):
        st.session_state.usuario_actual = None
        st.rerun()

st.divider()

tab_dashboard, tab_registro, tab_ahorro = st.tabs([
    "📊 Dashboard General", 
    "📝 Registrar Transacción", 
    "🎯 Planes de Ahorro"
])

# ==========================================
# 4. DASHBOARD GENERAL
# ==========================================
df = pd.DataFrame(datos_user["transacciones"])

with tab_dashboard:
    if not df.empty:
        ingresos_totales = df[df['Tipo'] == 'Ingreso']['Monto'].sum()
        gastos_totales = df[df['Tipo'] == 'Gasto']['Monto'].sum()
        deudas_totales = df[df['Tipo'] == 'Deuda']['Monto'].sum()
    else:
        ingresos_totales, gastos_totales, deudas_totales = 0.0, 0.0, 0.0
        
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
        df_gastos = df[df['Tipo'].isin(['Gasto', 'Deuda'])] if not df.empty else pd.DataFrame()
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
# 5. REGISTRO DE TRANSACCIONES
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
            nueva_tx = {
                "Fecha": str(fecha),
                "Tipo": tipo,
                "Categoría": categoria,
                "Monto": monto,
                "Descripción": descripcion
            }
            datos_user["transacciones"].append(nueva_tx)
            guardar_datos()
            st.success("Transacción registrada exitosamente.")
            st.rerun()

    st.divider()
    st.subheader("Historial de Transacciones")
    
    if not datos_user["transacciones"]:
        st.info("No hay transacciones en el historial.")
    else:
        col_hist_header, col_hist_btn = st.columns([4, 1])
        with col_hist_btn:
            if st.button("🚨 Vaciar Todo el Historial"):
                datos_user["transacciones"] = []
                guardar_datos()
                st.rerun()

        for idx, row in enumerate(datos_user["transacciones"]):
            c_fecha, c_tipo, c_cat, c_monto, c_desc, c_del = st.columns([1.5, 1.2, 1.5, 1.8, 2.5, 1])
            c_fecha.write(row['Fecha'])
            c_tipo.write(f"**{row['Tipo']}**")
            c_cat.write(row['Categoría'])
            c_monto.write(formato_cop(row['Monto']))
            c_desc.write(row['Descripción'] if row['Descripción'] else "-")
            
            if c_del.button("🗑️", key=f"del_tx_{idx}"):
                datos_user["transacciones"].pop(idx)
                guardar_datos()
                st.rerun()

# ==========================================
# 6. PLANES DE AHORRO
# ==========================================
with tab_ahorro:
    st.subheader("Planes de Ahorro y Recomendaciones Inteligentes")
    
    capacidad_ahorro = balance
    cuota_sugerida = capacidad_ahorro * 0.20 if capacidad_ahorro > 0 else 0
    
    st.info(f"💡 **Recomendación Bytepulse:** Tu capacidad actual de ahorro libre es de **{formato_cop(capacidad_ahorro)}**. Te sugerimos destinar al menos **{formato_cop(cuota_sugerida)}** mensuales a tus metas.")

    st.subheader("➕ Crear Nueva Meta de Ahorro")
    with st.form("form_nueva_meta", clear_on_submit=True):
        nombre_meta = st.text_input("Nombre de la Meta", value="Viaje / Inversión")
        monto_meta = st.number_input("Monto Objetivo (COP $)", min_value=100000.0, step=100000.0, format="%.0f")
        plazo_meses = st.number_input("Plazo estimado (Meses)", min_value=1, value=6)
        
        btn_crear_meta = st.form_submit_button("Guardar Meta de Ahorro")
        
        if btn_crear_meta:
            datos_user["metas"].append({
                "Meta": nombre_meta, 
                "Objetivo": monto_meta, 
                "Actual": 0.0, 
                "Plazo_Meses": plazo_meses
            })
            guardar_datos()
            st.success(f"¡Meta '{nombre_meta}' creada exitosamente!")
            st.rerun()

    st.divider()
    
    st.subheader("Tus Metas Activas")
    if not datos_user["metas"]:
        st.info("No tienes metas registradas actualmente.")
    else:
        for idx, meta in enumerate(datos_user["metas"]):
            col_info, col_btn = st.columns([5, 1])
            porcentaje = min(meta["Actual"] / meta["Objetivo"], 1.0) if meta["Objetivo"] > 0 else 0
            
            with col_info:
                st.write(f"**{meta['Meta']}** - Ahorrado: {formato_cop(meta['Actual'])} de {formato_cop(meta['Objetivo'])} ({porcentaje*100:.1f}%)")
                st.progress(porcentaje)
                
            with col_btn:
                if st.button("🗑️ Eliminar", key=f"btn_del_meta_{idx}"):
                    datos_user["metas"].pop(idx)
                    guardar_datos()
                    st.rerun()
