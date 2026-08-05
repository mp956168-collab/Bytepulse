import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os
import random

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y PERSISTENCIA
# ==========================================
st.set_page_config(
    page_title="Bytepulse - Quantumsoft",
    page_icon="📈",
    layout="wide"
)

DB_FILE = "usuarios_data.json"

MENSAJES_MOTIVACIONALES = [
    "¡Excelente trabajo! Cada ingreso te acerca un paso más a tus metas financieras. 🚀",
    "¡Gran movimiento! La disciplina financiera de hoy es tu tranquilidad de mañana. 💡",
    "¡Tu capital sigue creciendo! Recuerda destinar una parte a tus planes de ahorro. 🎯",
    "¡Paso firme! Mantén la consistencia y verás cómo tus metas se cumplen más rápido. ⭐"
]

def cargar_datos():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {
        "admin": {
            "password": "123",
            "transacciones": [
                {"Fecha": "2026-08-01", "Tipo": "Ingreso", "Categoría": "Nómina", "Monto": 3500000.0, "Descripción": "Sueldo mensual", "Meta_Asociada": "Ninguna"},
                {"Fecha": "2026-08-02", "Tipo": "Gasto", "Categoría": "Alquiler", "Monto": 1200000.0, "Descripción": "Pago de arriendo", "Meta_Asociada": "Ninguna"}
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
    if valor < 0:
        return f"-${abs(valor):,.0f}".replace(",", ".")
    return f"${valor:,.0f}".replace(",", ".")

# ==========================================
# 2. SISTEMA DE AUTENTICACIÓN
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
# 3. PANEL PRINCIPAL
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
        ingresos_totales = float(df[df['Tipo'] == 'Ingreso']['Monto'].sum())
        gastos_totales = float(df[df['Tipo'] == 'Gasto']['Monto'].sum())
        deudas_totales = float(df[df['Tipo'] == 'Deuda']['Monto'].sum())
        ahorros_totales = float(df[df['Tipo'] == 'Ahorro / Inversión']['Monto'].sum())
    else:
        ingresos_totales, gastos_totales, deudas_totales, ahorros_totales = 0.0, 0.0, 0.0, 0.0
        
    egresos_totales = gastos_totales + deudas_totales
    balance = ingresos_totales - egresos_totales - ahorros_totales
    
    # ALERTAS DE PRESUPUESTO
    if ingresos_totales > 0:
        porcentaje_gastado = (egresos_totales / ingresos_totales) * 100
        if porcentaje_gastado >= 100:
            st.error(f"🚨 **¡Límite Máximo Superado!** Has consumido el **{porcentaje_gastado:.1f}%** de tus ingresos ({formato_cop(egresos_totales)} de {formato_cop(ingresos_totales)}). Procura congelar gastos superfluos.")
        elif porcentaje_gastado >= 80:
            st.warning(f"⚠️ **Aviso de Límite:** Consumiste el **{porcentaje_gastado:.1f}%** de tus ingresos. Te quedan **{formato_cop(balance)}** libres.")
        else:
            st.success(f"✅ **Presupuesto Saludable:** Has utilizado el **{porcentaje_gastado:.1f}%** de tus ingresos. Tienes libre **{formato_cop(balance)}**.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Balance Libre Disponible", formato_cop(balance))
    col2.metric("Ingresos Totales", formato_cop(ingresos_totales))
    col3.metric("Gastos Totales", formato_cop(gastos_totales), delta_color="inverse")
    col4.metric("Fondo de Ahorros / Metas", formato_cop(ahorros_totales))
    
    st.divider()
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Distribución Financiera")
        df_gastos = df[df['Tipo'].isin(['Gasto', 'Deuda', 'Ahorro / Inversión'])] if not df.empty else pd.DataFrame()
        if not df_gastos.empty:
            fig_pie = px.pie(df_gastos, values='Monto', names='Categoría', hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No hay datos de gastos ni ahorros registrados.")
            
    with c2:
        st.subheader("Flujo de Movimientos")
        if not df.empty:
            fig_bar = px.bar(df, x='Fecha', y='Monto', color='Tipo', barmode='group',
                             color_discrete_map={'Ingreso': '#2ecc71', 'Gasto': '#e74c3c', 'Deuda': '#f39c12', 'Ahorro / Inversión': '#3498db'})
            st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# 5. REGISTRO DE TRANSACCIONES Y ALERTA DE RIESGO
# ==========================================
with tab_registro:
    st.subheader("Nuevo Registro Financiero")
    
    nombres_metas = [m["Meta"] for m in datos_user["metas"]]
    
    with st.form("form_transaccion", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        
        with col_a:
            tipo = st.selectbox("Tipo de Movimiento", ["Gasto", "Ahorro / Inversión", "Ingreso", "Deuda"])
            monto = st.number_input("Monto (COP $)", min_value=1000.0, step=50000.0, format="%.0f")
            fecha = st.date_input("Fecha de la Transacción", datetime.now())
            
        with col_b:
            categoria = st.selectbox("Categoría", ["Uso Fondo Meta", "Ahorro Meta", "Nómina", "Alquiler", "Alimentación", "Servicios", "Transporte", "Tarjeta Crédito", "Otros"])
            meta_destino = st.selectbox("Asociar a Meta (Opcional)", ["Ninguna"] + nombres_metas)
            descripcion = st.text_input("Descripción (Opcional)")
            
        guardar = st.form_submit_button("Guardar Transacción")
        
        if guardar:
            nueva_tx = {
                "Fecha": str(fecha),
                "Tipo": tipo,
                "Categoría": categoria,
                "Monto": monto,
                "Descripción": descripcion,
                "Meta_Asociada": meta_destino
            }
            datos_user["transacciones"].append(nueva_tx)
            
            # ACTUALIZACIÓN EN TIEMPO REAL CON ALERTA DE METAS EN RIESGO
            if meta_destino != "Ninguna":
                for m in datos_user["metas"]:
                    if m["Meta"] == meta_destino:
                        saldo_previo = float(m.get("Actual", 0.0))
                        
                        if tipo in ["Ahorro / Inversión", "Ingreso"]:
                            m["Actual"] = saldo_previo + monto
                            st.info(f"🎉 ¡Abono de {formato_cop(monto)} registrado en la meta '{meta_destino}'!")
                        elif tipo in ["Gasto", "Deuda"]:
                            # Permite valores negativos si se gasta más de lo acumulado
                            m["Actual"] = saldo_previo - monto
                            
                            # Si se sobrepasa el acumulado, se activa la alerta de riesgo
                            if m["Actual"] < 0:
                                st.error(
                                    f"🚨 **¡ALERTA: META EN RIESGO!**\n\n"
                                    f"Has registrado un gasto de **{formato_cop(monto)}** asociado a la meta **'{meta_destino}'** "
                                    f"que supera su fondo acumulado previo (**{formato_cop(saldo_previo)}**).\n\n"
                                    f"⚠️ La meta ha entrado en un **déficit negativo de {formato_cop(m['Actual'])}**."
                                )
                            else:
                                st.warning(f"🔻 Se retiran {formato_cop(monto)} de la meta '{meta_destino}'. Saldo restante: {formato_cop(m['Actual'])}.")

            # NOTIFICACIONES GENERALES
            elif tipo == "Ingreso":
                st.balloons()
                st.success(f"{random.choice(MENSAJES_MOTIVACIONALES)}\n\n💡 Saldo disponible estimado: **{formato_cop(balance + monto)}**.")
            elif tipo in ["Gasto", "Deuda"] and (egresos_totales + monto > ingresos_totales):
                st.warning("⚠️ Este gasto sobrepasa tus ingresos acumulados.")

            guardar_datos()
            st.rerun()

    st.divider()
    
    col_hist_head, col_hist_export = st.columns([3, 2])
    with col_hist_head:
        st.subheader("Historial de Transacciones")
        
    with col_hist_export:
        if not df.empty:
            csv_data = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Descargar Reporte (Excel / CSV)",
                data=csv_data,
                file_name=f"Reporte_Financiero_{user}.csv",
                mime="text/csv"
            )

    if not datos_user["transacciones"]:
        st.info("No hay transacciones guardadas.")
    else:
        for idx, row in enumerate(datos_user["transacciones"]):
            c_fecha, c_tipo, c_cat, c_monto, c_meta, c_del = st.columns([1.5, 1.2, 1.5, 1.5, 2, 1])
            c_fecha.write(row['Fecha'])
            c_tipo.write(f"**{row['Tipo']}**")
            c_cat.write(row['Categoría'])
            c_monto.write(formato_cop(row['Monto']))
            c_meta.write(f"🎯 {row.get('Meta_Asociada', 'Ninguna')}")
            
            if c_del.button("🗑️", key=f"del_tx_{idx}"):
                tx_eliminada = datos_user["transacciones"].pop(idx)
                if tx_eliminada.get("Meta_Asociada") != "Ninguna":
                    for m in datos_user["metas"]:
                        if m["Meta"] == tx_eliminada["Meta_Asociada"]:
                            if tx_eliminada.get("Tipo") in ["Ahorro / Inversión", "Ingreso"]:
                                m["Actual"] = float(m.get("Actual", 0.0)) - tx_eliminada["Monto"]
                            elif tx_eliminada.get("Tipo") in ["Gasto", "Deuda"]:
                                m["Actual"] = float(m.get("Actual", 0.0)) + tx_eliminada["Monto"]
                guardar_datos()
                st.rerun()

# ==========================================
# 6. PLANES DE AHORRO CON METAS EN RIESGO
# ==========================================
with tab_ahorro:
    st.subheader("Planes de Ahorro e Inteligencia Financiera")
    
    capacidad_ahorro = max(0.0, balance)
    cuota_sugerida = capacidad_ahorro * 0.20
    
    st.info(f"💡 **Recomendación Bytepulse:** Tu dinero libre disponible para ahorro/inversión es de **{formato_cop(capacidad_ahorro)}**. Te sugerimos abonar al menos **{formato_cop(cuota_sugerida)}** al mes a tus metas.")

    st.subheader("➕ Crear Nueva Meta de Ahorro")
    with st.form("form_nueva_meta", clear_on_submit=True):
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            nombre_meta = st.text_input("Nombre de la Meta", value="Viaje / Inversión")
            monto_meta = st.number_input("Monto Objetivo (COP $)", min_value=100000.0, step=100000.0, format="%.0f")
        with col_m2:
            plazo_meses = st.number_input("Plazo estimado (Meses)", min_value=1, value=6)
            monto_inicial = st.number_input("Ahorro Inicial (COP $)", min_value=0.0, step=50000.0, format="%.0f")
        
        btn_crear_meta = st.form_submit_button("Guardar Meta de Ahorro")
        
        if btn_crear_meta:
            datos_user["metas"].append({
                "Meta": nombre_meta, 
                "Objetivo": float(monto_meta), 
                "Actual": float(monto_inicial), 
                "Plazo_Meses": int(plazo_meses)
            })
            
            if monto_inicial > 0:
                datos_user["transacciones"].append({
                    "Fecha": str(datetime.now().date()),
                    "Tipo": "Ahorro / Inversión",
                    "Categoría": "Ahorro Meta",
                    "Monto": float(monto_inicial),
                    "Descripción": f"Ahorro inicial para {nombre_meta}",
                    "Meta_Asociada": nombre_meta
                })

            guardar_datos()
            cuota_mes = max(0.0, monto_meta - monto_inicial) / plazo_meses
            st.success(f"¡Meta creada! Debes abonar **{formato_cop(cuota_mes)}/mes** durante {plazo_meses} meses.")
            st.rerun()

    st.divider()
    
    st.subheader("Tus Metas Activas")
    if not datos_user["metas"]:
        st.info("No tienes metas registradas actualmente.")
    else:
        for idx, meta in enumerate(datos_user["metas"]):
            monto_objetivo = float(meta.get("Objetivo", 1.0))
            monto_actual = float(meta.get("Actual", 0.0))
            plazo_m = int(meta.get("Plazo_Meses", 1))
            
            monto_faltante = max(0.0, monto_objetivo - monto_actual)
            cuota_mensual = monto_faltante / plazo_m if plazo_m > 0 else 0
            
            # Cálculo del porcentaje de cumplimiento (permite valores negativos)
            porcentaje_real = (monto_actual / monto_objetivo) * 100 if monto_objetivo > 0 else 0.0
            
            st.markdown(f"### 🎯 {meta['Meta']}")
            
            # CONTROL VISUAL DE METAS EN RIESGO / NÚMEROS NEGATIVOS
            if monto_actual < 0:
                st.error(
                    f"⚠️ **ESTADO: META EN RIESGO Y FONDOS EN NEGATIVO**\n\n"
                    f"**Acumulado Actual:** `{formato_cop(monto_actual)}` de `{formato_cop(monto_objetivo)}` (**{porcentaje_real:.1f}%**)\n\n"
                    f"🚨 Has retirado más dinero del disponible en este plan. Cubre el saldo negativo para retomar el avance."
                )
                st.progress(0.0) # Barra en cero para reflejar el déficit
            else:
                porcentaje_bar = min(max(monto_actual / monto_objetivo, 0.0), 1.0)
                st.write(f"**Progreso:** {formato_cop(monto_actual)} de {formato_cop(monto_objetivo)} (**{porcentaje_real:.1f}%**)")
                st.progress(porcentaje_bar)
            
            col_m_details1, col_m_details2, col_m_btn = st.columns([3, 3, 1])
            col_m_details1.caption(f"📅 **Plazo estimado:** {plazo_m} meses")
            col_m_details2.caption(f"📌 **Cuota Mensual Requerida:** {formato_cop(cuota_mensual)} / mes")
            
            if col_m_btn.button("🗑️ Eliminar", key=f"btn_del_meta_{idx}"):
                datos_user["metas"].pop(idx)
                guardar_datos()
                st.rerun()
                
            st.divider()
