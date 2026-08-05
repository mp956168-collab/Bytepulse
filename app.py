import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os
import random
import re

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
            "telefono": "3000000000",
            "transacciones": [],
            "metas": []
        }
    }

def guardar_datos():
    with open(DB_FILE, "w") as f:
        json.dump(st.session_state.db_usuarios, f, indent=4)

def validar_telefono_colombia(telefono):
    # Valida formato celular colombiano: 10 dígitos iniciando por 3
    patron = r"^3\d{9}$"
    return bool(re.match(patron, telefono))

if 'db_usuarios' not in st.session_state:
    st.session_state.db_usuarios = cargar_datos()

if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None

def formato_cop(valor):
    if valor < 0:
        return f"-${abs(valor):,.0f}".replace(",", ".")
    return f"${valor:,.0f}".replace(",", ".")

# ==========================================
# 2. SISTEMA DE AUTENTICACIÓN Y RECUPERACIÓN
# ==========================================
if st.session_state.usuario_actual is None:
    st.title("Bytepulse 📈")
    st.caption("Gestión Financiera Multi-Usuario por **Quantumsoft**")
    st.divider()

    col_login, col_reg = st.columns(2)

    with col_login:
        st.subheader("🔑 Iniciar Sesión (Usuario Ya Existente)")
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

        st.write("")
        # RECUPERACIÓN DE CONTRASEÑA VÍA TELÉFONO COLOMBIANO
        with st.expander("📲 ¿Olvidaste tu contraseña? (Recuperar por Teléfono)"):
            with st.form("form_recuperar"):
                u_recuperar = st.text_input("Ingresa tu Usuario").strip().lower()
                tel_recuperar = st.text_input("Número de Teléfono Registrado", placeholder="Ej: 3001234567")
                btn_recuperar = st.form_submit_button("Enviar Contraseña por SMS")

                if btn_recuperar:
                    db = st.session_state.db_usuarios
                    if u_recuperar in db:
                        tel_guardado = db[u_recuperar].get("telefono", "")
                        if tel_recuperar == tel_guardado:
                            pass_encontrada = db[u_recuperar]["password"]
                            st.success(f"📲 **SMS Enviado a +57 {tel_recuperar}:** Tu contraseña para Bytepulse es: `{pass_encontrada}`")
                        else:
                            st.error("El número telefónico no coincide con el registrado para este usuario.")
                    else:
                        st.error("El usuario ingresado no existe.")

    with col_reg:
        st.subheader("📝 Registrar Nuevo Cliente")
        with st.form("form_registro"):
            user_reg = st.text_input("Nuevo Usuario").strip().lower()
            pass_reg = st.text_input("Nueva Contraseña", type="password")
            tel_reg = st.text_input("Número Telefónico (Colombia +57)", placeholder="Ej: 3101234567").strip()
            btn_reg = st.form_submit_button("Crear Cuenta")

            if btn_reg:
                if not user_reg or not pass_reg or not tel_reg:
                    st.warning("Por favor completa todos los campos requeridos.")
                elif user_reg in st.session_state.db_usuarios:
                    st.error("El usuario ya existe. Intenta con otro nombre.")
                elif not validar_telefono_colombia(tel_reg):
                    st.error("El número telefónico debe ser un celular colombiano válido de 10 dígitos (debe comenzar por 3, ej: 3001234567).")
                else:
                    st.session_state.db_usuarios[user_reg] = {
                        "password": pass_reg,
                        "telefono": tel_reg,
                        "transacciones": [],
                        "metas": []
                    }
                    guardar_datos()
                    st.success("Cuenta creada con éxito. Ya puedes iniciar sesión.")

    st.stop()

# ==========================================
# 3. PANEL PRINCIPAL Y PESTAÑAS DINÁMICAS
# ==========================================
user = st.session_state.usuario_actual
datos_user = st.session_state.db_usuarios[user]
es_admin = (user == "admin")

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

titulos_pestañas = ["📊 Dashboard General", "📝 Registrar Transacción", "🎯 Planes de Ahorro"]
if es_admin:
    titulos_pestañas.append("👑 Control de Administrador")

pestañas = st.tabs(titulos_pestañas)

tab_dashboard = pestañas[0]
tab_registro = pestañas[1]
tab_ahorro = pestañas[2]
tab_admin = pestañas[3] if es_admin else None

# ==========================================
# 4. DASHBOARD GENERAL
# ==========================================
df = pd.DataFrame(datos_user["transacciones"])

with tab_dashboard:
    if not df.empty:
        ingresos_totales = float(df[df['Tipo'] == 'Ingreso']['Monto'].sum())
        gastos_ordinarios = float(df[(df['Tipo'] == 'Gasto') & (~df['Categoría'].isin(['Gasto de Inversión / Retiro de Ahorro', 'Uso Fondo Meta']))]['Monto'].sum())
        deudas_totales = float(df[df['Tipo'] == 'Deuda']['Monto'].sum())
        ahorros_totales = float(df[df['Tipo'] == 'Ahorro / Inversión']['Monto'].sum())
        gastos_de_ahorros = float(df[df['Categoría'].isin(['Gasto de Inversión / Retiro de Ahorro', 'Uso Fondo Meta'])]['Monto'].sum())
        
        fondo_ahorro_neto = max(0.0, ahorros_totales - gastos_de_ahorros)
        gastos_totales_visibles = gastos_ordinarios + gastos_de_ahorros
    else:
        ingresos_totales, gastos_ordinarios, deudas_totales, ahorros_totales, gastos_de_ahorros, fondo_ahorro_neto, gastos_totales_visibles = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    egresos_corrientes = gastos_ordinarios + deudas_totales
    balance = ingresos_totales - egresos_corrientes - fondo_ahorro_neto
    
    if ingresos_totales > 0:
        porcentaje_gastado = (egresos_corrientes / ingresos_totales) * 100
        if porcentaje_gastado >= 100:
            st.error(f"🚨 **¡Límite Máximo Superado!** Has consumido el **{porcentaje_gastado:.1f}%** de tus ingresos libres.")
        elif porcentaje_gastado >= 80:
            st.warning(f"⚠️ **Aviso de Límite:** Consumiste el **{porcentaje_gastado:.1f}%** de tus ingresos. Saldo libre: **{formato_cop(balance)}**.")
        else:
            st.success(f"✅ **Presupuesto Saludable:** Has utilizado el **{porcentaje_gastado:.1f}%** de tus ingresos. Tienes libre **{formato_cop(balance)}**.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Balance Libre Disponible", formato_cop(balance))
    col2.metric("Ingresos Totales", formato_cop(ingresos_totales))
    col3.metric("Gastos Totales", formato_cop(gastos_totales_visibles), delta_color="inverse")
    col4.metric("Fondo Neto Ahorrado", formato_cop(fondo_ahorro_neto))
    
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
# 5. REGISTRO Y GESTIÓN DE TRANSACCIONES
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
            categoria = st.selectbox("Categoría", [
                "Gasto de Inversión / Retiro de Ahorro", 
                "Uso Fondo Meta", 
                "Ahorro Meta", 
                "Nómina", 
                "Alquiler", 
                "Alimentación", 
                "Servicios", 
                "Transporte", 
                "Tarjeta Crédito", 
                "Otros"
            ])
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
            
            if meta_destino != "Ninguna":
                for m in datos_user["metas"]:
                    if m["Meta"] == meta_destino:
                        saldo_previo = float(m.get("Actual", 0.0))
                        monto_objetivo = float(m.get("Objetivo", 1.0))
                        
                        if tipo in ["Ahorro / Inversión", "Ingreso"]:
                            m["Actual"] = saldo_previo + monto
                            st.info(f"🎉 ¡Abono de {formato_cop(monto)} registrado en '{meta_destino}'!")
                        
                        elif tipo in ["Gasto", "Deuda"]:
                            nuevo_saldo = saldo_previo - monto
                            m["Actual"] = nuevo_saldo
                            
                            porcentaje_retirado = (monto / saldo_previo * 100) if saldo_previo > 0 else 100.0
                            pct_perdidofondo = (monto / monto_objetivo * 100) if monto_objetivo > 0 else 0.0
                            
                            if nuevo_saldo < 0:
                                st.error(
                                    f"🚨 **¡ALERTA: META EN RIESGO!**\n\n"
                                    f"Has retirado **{formato_cop(monto)}** de **'{meta_destino}'**.\n\n"
                                    f"⚠️ Consumiste el **{porcentaje_retirado:.1f}%** del saldo acumulado "
                                    f"y perdiste un **{pct_perdidofondo:.1f}%** de la meta global.\n\n"
                                    f"📉 Déficit en la meta: **{formato_cop(nuevo_saldo)}**."
                                )
                            else:
                                st.warning(
                                    f"⚠️ **Aviso de Retiro:** Se retiraron **{formato_cop(monto)}** de **'{meta_destino}'** "
                                    f"(pérdida del **{pct_perdidofondo:.1f}%** del objetivo global). Quedan: **{formato_cop(nuevo_saldo)}**."
                                )

            elif tipo == "Ingreso":
                st.balloons()
                st.success(f"{random.choice(MENSAJES_MOTIVACIONALES)}\n\n💡 Saldo disponible estimado: **{formato_cop(balance + monto)}**.")
            
            guardar_datos()
            st.rerun()

    st.divider()
    
    col_hist_head, col_hist_export, col_hist_del = st.columns([2.5, 1.5, 1.5])
    with col_hist_head:
        st.subheader("Historial de Transacciones")
        
    with col_hist_export:
        if not df.empty:
            csv_data = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Descargar Reporte",
                data=csv_data,
                file_name=f"Reporte_Financiero_{user}.csv",
                mime="text/csv"
            )

    # BOTÓN PARA ELIMINAR TODAS LAS TRANSACCIONES
    with col_hist_del:
        if not df.empty:
            if st.button("🚨 Eliminar TODAS las Transacciones", type="primary"):
                datos_user["transacciones"] = []
                guardar_datos()
                st.success("Se han eliminado todas las transacciones.")
                st.rerun()

    if not datos_user["transacciones"]:
        st.info("No hay transacciones guardadas.")
    else:
        for idx, row in enumerate(datos_user["transacciones"]):
            c_fecha, c_tipo, c_cat, c_monto, c_meta, c_del = st.columns([1.5, 1.2, 1.8, 1.5, 2, 1])
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
# 6. PLANES DE AHORRO
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
            porcentaje_real = (monto_actual / monto_objetivo) * 100 if monto_objetivo > 0 else 0.0
            
            st.markdown(f"### 🎯 {meta['Meta']}")
            
            if monto_actual < 0:
                st.error(
                    f"🚨 **ESTADO: META EN RIESGO Y FONDOS EN DÉFICIT**\n\n"
                    f"**Saldo Actual:** `{formato_cop(monto_actual)}` de `{formato_cop(monto_objetivo)}` (**{porcentaje_real:.1f}%**)\n\n"
                    f"⚠️ Has sobrepasado el fondo de este plan. Repón los fondos para continuar."
                )
                st.progress(0.0)
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

# ==========================================
# 7. PANEL DE CONTROL DE ADMINISTRADOR
# ==========================================
if es_admin and tab_admin is not None:
    with tab_admin:
        st.subheader("👑 Panel de Control, Credenciales y Auditoría (Dueño)")
        st.caption("Visualización de claves de usuarios, teléfonos de contacto, métricas de rendimiento y borrado de cuentas.")
        
        db_global = st.session_state.db_usuarios
        lista_usuarios = list(db_global.keys())
        
        # MÉTRICAS GLOBALES
        total_usuarios = len(lista_usuarios)
        todas_las_tx = []
        
        for u, d in db_global.items():
            for tx in d.get("transacciones", []):
                tx_copy = tx.copy()
                tx_copy["Usuario"] = u
                todas_las_tx.append(tx_copy)

        df_global_tx = pd.DataFrame(todas_las_tx)
        
        total_ingresos_global = df_global_tx[df_global_tx['Tipo'] == 'Ingreso']['Monto'].sum() if not df_global_tx.empty else 0.0
        total_gastos_global = df_global_tx[df_global_tx['Tipo'] == 'Gasto']['Monto'].sum() if not df_global_tx.empty else 0.0
        
        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Clientes Registrados", total_usuarios)
        a2.metric("Movimientos Totales", len(todas_las_tx))
        a3.metric("Ingresos Globales", formato_cop(total_ingresos_global))
        a4.metric("Gastos Globales", formato_cop(total_gastos_global))
        
        st.divider()
        
        # TABLA DE CREDENCIALES DE USUARIOS (EL ADMIN PUEDE VER LAS CONTRASEÑAS Y TELÉFONOS)
        st.subheader("🔑 Directorio y Credenciales de Usuarios")
        
        datos_credenciales = []
        for u, d in db_global.items():
            datos_credenciales.append({
                "Usuario": u,
                "Contraseña": d.get("password", "N/A"),
                "Teléfono Colombia": f"+57 {d.get('telefono', 'Sin registro')}",
                "Total Transacciones": len(d.get("transacciones", [])),
                "Total Metas": len(d.get("metas", []))
            })
            
        df_credenciales = pd.DataFrame(datos_credenciales)
        st.dataframe(df_credenciales, use_container_width=True)
        
        st.divider()
        
        # INSPECCIÓN INDIVIDUAL Y ELIMINACIÓN DE USUARIOS
        st.subheader("🔍 Inspección y Borrado Individual de Usuarios")
        
        col_sel, col_del = st.columns([3, 2])
        
        with col_sel:
            usuario_seleccionado = st.selectbox("Selecciona un usuario para auditar:", lista_usuarios)
            
        with col_del:
            st.write("")
            st.write("")
            if usuario_seleccionado == "admin":
                st.info("🛡️ La cuenta `admin` no se puede eliminar.")
            else:
                if st.button(f"🗑️ Eliminar Usuario '{usuario_seleccionado}'", type="primary"):
                    del st.session_state.db_usuarios[usuario_seleccionado]
                    guardar_datos()
                    st.success(f"El usuario `{usuario_seleccionado}` ha sido eliminado.")
                    st.rerun()

        if usuario_seleccionado:
            datos_sel = db_global[usuario_seleccionado]
            df_sel = pd.DataFrame(datos_sel.get("transacciones", []))
            metas_sel = datos_sel.get("metas", [])
            
            # CÁLCULOS DE RENDIMIENTO
            if not df_sel.empty:
                u_ingresos = float(df_sel[df_sel['Tipo'] == 'Ingreso']['Monto'].sum())
                u_gastos = float(df_sel[(df_sel['Tipo'] == 'Gasto') & (~df_sel['Categoría'].isin(['Gasto de Inversión / Retiro de Ahorro', 'Uso Fondo Meta']))]['Monto'].sum())
                u_deudas = float(df_sel[df_sel['Tipo'] == 'Deuda']['Monto'].sum())
                u_ahorros = float(df_sel[df_sel['Tipo'] == 'Ahorro / Inversión']['Monto'].sum())
                u_gastos_ahorros = float(df_sel[df_sel['Categoría'].isin(['Gasto de Inversión / Retiro de Ahorro', 'Uso Fondo Meta'])]['Monto'].sum())
                
                u_fondo_ahorro = max(0.0, u_ahorros - u_gastos_ahorros)
                u_balance = u_ingresos - (u_gastos + u_deudas) - u_fondo_ahorro
            else:
                u_ingresos, u_gastos, u_deudas, u_fondo_ahorro, u_balance = 0.0, 0.0, 0.0, 0.0, 0.0

            st.markdown(f"#### 📊 Rendimiento Financiero de `{usuario_seleccionado}`")
            st.info(f"🔑 **Contraseña:** `{datos_sel.get('password')}` | 📞 **Teléfono:** `+57 {datos_sel.get('telefono', 'N/A')}`")
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Ingresos", formato_cop(u_ingresos))
            m2.metric("Gastos Corrientes", formato_cop(u_gastos + u_deudas))
            m3.metric("Fondo de Ahorro", formato_cop(u_fondo_ahorro))
            m4.metric("Balance Libre", formato_cop(u_balance))
            
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                st.markdown(f"**Transacciones Registradas ({len(df_sel)}):**")
                if not df_sel.empty:
                    st.dataframe(df_sel[['Fecha', 'Tipo', 'Categoría', 'Monto', 'Meta_Asociada']], use_container_width=True)
                else:
                    st.info("Sin transacciones.")
                    
            with col_u2:
                st.markdown(f"**Metas de Ahorro Activas ({len(metas_sel)}):**")
                if metas_sel:
                    df_m_sel = pd.DataFrame(metas_sel)
                    st.dataframe(df_m_sel[['Meta', 'Objetivo', 'Actual', 'Plazo_Meses']], use_container_width=True)
                else:
                    st.info("Sin metas registradas.")

        st.divider()
        
        # AUDITORÍA GENERAL DE TRANSACCIONES
        st.subheader("📋 Registro Global de Transacciones del Sistema")
        if not df_global_tx.empty:
            st.dataframe(df_global_tx[['Usuario', 'Fecha', 'Tipo', 'Categoría', 'Monto', 'Meta_Asociada', 'Descripción']], use_container_width=True)
        else:
            st.info("No hay transacciones registradas por ningún usuario.")
