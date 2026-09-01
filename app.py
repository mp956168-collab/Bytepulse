import streamlit as st
import streamlit.components.v1 as components
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

def limpiar_valor_corrupto(val):
    """Evita valores numéricos absurdos o concatenados por error."""
    try:
        num = float(val)
        if num > 1e11: # Si supera los 100 mil millones por error de concatenación
            return 0.0
        return num
    except:
        return 0.0

def cargar_datos():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Sanitizar datos corruptos automáticamente
                for u, info in data.items():
                    for tx in info.get("transacciones", []):
                        tx["Monto"] = limpiar_valor_corrupto(tx.get("Monto", 0))
                    for m in info.get("metas", []):
                        m["Objetivo"] = limpiar_valor_corrupto(m.get("Objetivo", 0))
                        m["Actual"] = limpiar_valor_corrupto(m.get("Actual", 0))
                return data
        except:
            pass
    return {
        "admin": {
            "password": "123",
            "telefono": "3000000000",
            "transacciones": [],
            "metas": []
        }
    }

def guardar_datos():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.db_usuarios, f, indent=4, ensure_ascii=False)

def validar_telefono_colombia(telefono):
    patron = r"^3\d{9}$"
    return bool(re.match(patron, telefono))

if 'db_usuarios' not in st.session_state:
    st.session_state.db_usuarios = cargar_datos()

if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None

if 'mostrar_registro' not in st.session_state:
    st.session_state.mostrar_registro = False

def formato_cop(valor):
    try:
        val_float = float(valor)
    except (ValueError, TypeError):
        val_float = 0.0
    if val_float < 0:
        return f"-${abs(val_float):,.0f}".replace(",", ".")
    return f"${val_float:,.0f}".replace(",", ".")

def parsear_monto(texto_monto):
    if not texto_monto:
        return 0.0
    limpio = re.sub(r"[^\d]", "", str(texto_monto))
    if not limpio:
        return 0.0
    val = float(limpio)
    return val if val < 1e11 else 0.0

# ==========================================
# COMPONENTE CON MÁSCARA TECLA A TECLA SEGURO
# ==========================================
def input_moneda_tiempo_real(label, key_name, valor_defecto=0):
    monto_inicial_fmt = f"{int(valor_defecto):,}".replace(',', '.') if valor_defecto > 0 else ""
    
    html_code = f"""
    <div style="font-family: Source Sans Pro, sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto; margin-bottom: 0px;">
        <label style="font-size: 14px; color: #ffffff; display: block; margin-bottom: 6px; font-weight: 400;">{label}</label>
        <input type="text" id="{key_name}" value="{monto_inicial_fmt}" 
               placeholder="0" 
               style="width: 100%; padding: 8px 12px; font-size: 16px; border: 1px solid rgba(250, 250, 250, 0.2); border-radius: 8px; outline: none; box-sizing: border-box; background-color: #262730; color: #ffffff; transition: border-color 0.2s, background-color 0.2s;">
    </div>
    <script>
        const input = document.getElementById("{key_name}");
        
        input.addEventListener("focus", function() {{
            this.style.backgroundColor = "#262730";
            this.style.borderColor = "#ff4b4b";
        }});
        
        input.addEventListener("blur", function() {{
            this.style.backgroundColor = "#262730";
            this.style.borderColor = "rgba(250, 250, 250, 0.2)";
        }});

        function formatear(val) {{
            let num = val.replace(/\\D/g, "");
            if(!num) return "";
            return new Intl.NumberFormat('es-CO').format(num);
        }}

        function enviarValor() {{
            let numLimpio = input.value.replace(/\\D/g, "");
            window.parent.postMessage({{
                type: 'streamlit:setComponentValue',
                value: numLimpio ? numLimpio : "0"
            }}, '*');
        }}

        input.addEventListener("input", function(e) {{
            let val = e.target.value;
            e.target.value = formatear(val);
            enviarValor();
        }});

        enviarValor();
    </script>
    """
    val_string = components.html(html_code, height=75)
    return parsear_monto(val_string)

# --- EXPORTACIONES NATIVAS ---
def generar_excel_nativo(dataframe):
    return dataframe.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')

def generar_pdf_nativo(dataframe, titulo="Reporte Financiero"):
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #111; color: #fff; }}
            h2 {{ color: #ffffff; text-align: center; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #444; text-align: left; padding: 8px; font-size: 12px; }}
            th {{ background-color: #262730; color: white; }}
            tr:nth-child(even) {{ background-color: #1e1e1e; }}
        </style>
    </head>
    <body onload="window.print()">
        <h2>{titulo}</h2>
        {dataframe.to_html(index=False, classes='table')}
    </body>
    </html>
    """
    return html_content.encode('utf-8')

# ==========================================
# 2. AUTENTICACIÓN Y REGISTRO
# ==========================================
if st.session_state.usuario_actual is None:
    st.title("Bytepulse 📈")
    st.caption("Gestión Financiera Multi-Usuario por **Quantumsoft**")
    st.divider()

    col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
    
    with col_c2:
        if not st.session_state.mostrar_registro:
            st.subheader("🔑 Iniciar Sesión")
            with st.form("form_login"):
                user_login = st.text_input("Usuario").strip().lower()
                pass_login = st.text_input("Contraseña", type="password")
                btn_login = st.form_submit_button("Entrar", use_container_width=True)

                if btn_login:
                    db = st.session_state.db_usuarios
                    if user_login in db and db[user_login]["password"] == pass_login:
                        st.session_state.usuario_actual = user_login
                        st.success(f"¡Bienvenido {user_login}!")
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")

            st.write("")
            col_b1, col_b2 = st.columns([1, 1])
            with col_b1:
                if st.button("📝 ¿No tienes cuenta? Regístrate aquí"):
                    st.session_state.mostrar_registro = True
                    st.rerun()
                    
            with st.expander("📲 ¿Olvidaste tu contraseña? (Recuperar por Teléfono)"):
                with st.form("form_recuperar"):
                    u_recuperar = st.text_input("Ingresa tu Usuario").strip().lower()
                    tel_recuperar = st.text_input("Número de Teléfono Registrado (Colombia)", placeholder="Ej: 3001234567").strip()
                    btn_recuperar = st.form_submit_button("Enviar Contraseña al Número")

                    if btn_recuperar:
                        db = st.session_state.db_usuarios
                        if u_recuperar in db:
                            tel_guardado = db[u_recuperar].get("telefono", "")
                            if tel_recuperar == tel_guardado:
                                pass_encontrada = db[u_recuperar]["password"]
                                st.success(f"📲 **SMS Enviado a +57 {tel_recuperar}:** Tu contraseña actual es: `{pass_encontrada}`")
                            else:
                                st.error("El número telefónico no coincide con el registrado.")
                        else:
                            st.error("El usuario ingresado no existe.")
        else:
            st.subheader("📝 Crear Nueva Cuenta")
            with st.form("form_registro"):
                user_reg = st.text_input("Nuevo Usuario").strip().lower()
                pass_reg = st.text_input("Nueva Contraseña", type="password")
                tel_reg = st.text_input("Número Telefónico (Colombia +57)", placeholder="Ej: 3101234567").strip()
                btn_reg = st.form_submit_button("Registrarse", use_container_width=True)

                if btn_reg:
                    if not user_reg or not pass_reg or not tel_reg:
                        st.warning("Por favor completa todos los campos requeridos.")
                    elif user_reg in st.session_state.db_usuarios:
                        st.error("El usuario ya existe. Intenta con otro nombre.")
                    elif not validar_telefono_colombia(tel_reg):
                        st.error("El número telefónico debe ser un celular colombiano de 10 dígitos que empiece por 3.")
                    else:
                        st.session_state.db_usuarios[user_reg] = {
                            "password": pass_reg,
                            "telefono": tel_reg,
                            "transacciones": [],
                            "metas": []
                        }
                        guardar_datos()
                        st.success("Cuenta creada exitosamente. Ya puedes iniciar sesión.")
                        st.session_state.mostrar_registro = False
                        st.rerun()

            if st.button("⬅️ Volver al Inicio de Sesión"):
                st.session_state.mostrar_registro = False
                st.rerun()

    st.stop()

# ==========================================
# 3. PANEL PRINCIPAL Y PESTAÑAS
# ==========================================
user = st.session_state.usuario_actual
datos_user = st.session_state.db_usuarios[user]
es_admin = (user == "admin")

col_header, col_logout = st.columns([5, 1])
with col_header:
    st.title(f"Bytepulse 📈 - Hola, {user.capitalize()}")
    st.caption("Solución Tecnológica de Gestión Financiera por **Quantumsoft**")
with col_logout:
    st.write("")
    if st.button("🔒 Cerrar Sesión"):
        st.session_state.usuario_actual = None
        st.rerun()

st.divider()

titulos_pestañas = ["📊 Dashboard General", "📝 Registrar Transacción", "🎯 Planes de Ahorro", "⚙️ Configuración Cuenta"]
if es_admin:
    titulos_pestañas.append("👑 Control de Administrador")

pestañas = st.tabs(titulos_pestañas)

tab_dashboard = pestañas[0]
tab_registro = pestañas[1]
tab_ahorro = pestañas[2]
tab_config = pestañas[3]
tab_admin = pestañas[4] if es_admin else None

# ==========================================
# 4. DASHBOARD GENERAL
# ==========================================
df = pd.DataFrame(datos_user["transacciones"])

with tab_dashboard:
    if not df.empty:
        ingresos_totales = float(df[df['Tipo'] == 'Ingreso']['Monto'].sum())
        gastos_ordinarios = float(df[(df['Tipo'] == 'Gasto') & (df['Categoría'] != 'Uso Fondo Meta')]['Monto'].sum())
        deudas_totales = float(df[df['Tipo'] == 'Deuda']['Monto'].sum())
        ahorros_totales = float(df[df['Tipo'] == 'Ahorro / Inversión']['Monto'].sum())
        gastos_de_ahorros = float(df[df['Categoría'] == 'Uso Fondo Meta']['Monto'].sum())
        
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
            fig_pie = px.pie(df_gastos, values='Monto', names='Categoría', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
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
# 5. REGISTRO Y HISTORIAL DE TRANSACCIONES
# ==========================================
with tab_registro:
    st.subheader("Nuevo Registro Financiero")
    
    nombres_metas = [m["Meta"] for m in datos_user.get("metas", [])]

    col_a, col_b = st.columns(2)
    with col_a:
        tipo = st.selectbox("Tipo de Movimiento", ["Gasto", "Ahorro / Inversión", "Ingreso", "Deuda"])
        monto = input_moneda_tiempo_real("Monto (COP $)", "monto_tx_live", valor_defecto=50000)
        fecha = st.date_input("Fecha de la Transacción", datetime.now().date())
        
    with col_b:
        categoria = st.selectbox("Categoría", [
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
        
    guardar = st.button("Guardar Transacción", use_container_width=True, type="primary")
    
    if guardar:
        if monto <= 0:
            st.warning("Ingresa un monto válido mayor a $0.")
        else:
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
    
    col_hist_head, col_hist_excel, col_hist_pdf, col_hist_del = st.columns([2, 1.2, 1.2, 1.6])
    with col_hist_head:
        st.subheader("Historial de Transacciones")
        
    with col_hist_excel:
        if not df.empty:
            bytes_excel = generar_excel_nativo(df)
            st.download_button(
                label="📊 Exportar Excel",
                data=bytes_excel,
                file_name=f"Reporte_Financiero_{user}.csv",
                mime="text/csv"
            )

    with col_hist_pdf:
        if not df.empty:
            bytes_pdf = generar_pdf_nativo(df, titulo=f"Reporte Financiero - Usuario: {user.capitalize()}")
            st.download_button(
                label="📄 Imprimir/PDF",
                data=bytes_pdf,
                file_name=f"Reporte_Financiero_{user}.html",
                mime="text/html"
            )

    with col_hist_del:
        if not df.empty:
            if st.button("🚨 Eliminar TODAS las Transacciones", type="primary"):
                datos_user["transacciones"] = []
                guardar_datos()
                st.success("Se borraron todas tus transacciones.")
                st.rerun()

    if not datos_user["transacciones"]:
        st.info("No tienes transacciones guardadas.")
    else:
        index_to_delete = None
        for idx, row in enumerate(datos_user["transacciones"]):
            c_fecha, c_tipo, c_cat, c_monto, c_meta, c_del = st.columns([1.5, 1.2, 1.8, 1.5, 2, 1])
            c_fecha.write(row['Fecha'])
            c_tipo.write(f"**{row['Tipo']}**")
            c_cat.write(row['Categoría'])
            c_monto.write(formato_cop(row['Monto']))
            c_meta.write(f"🎯 {row.get('Meta_Asociada', 'Ninguna')}")
            
            if c_del.button("🗑️", key=f"del_tx_{idx}"):
                index_to_delete = idx
        
        if index_to_delete is not None:
            tx_eliminada = datos_user["transacciones"].pop(index_to_delete)
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
    
    st.info(f"💡 **Recomendación Bytepulse:** Tu dinero libre disponible es **{formato_cop(capacidad_ahorro)}**. Te sugerimos abonar al menos **{formato_cop(cuota_sugerida)}** al mes a tus metas.")

    st.subheader("➕ Crear Nueva Meta de Ahorro")

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        nombre_meta = st.text_input("Nombre de la Meta", value="Viaje / Inversión")
        monto_meta = input_moneda_tiempo_real("Monto Objetivo (COP $)", "monto_meta_live", valor_defecto=1000000)
        monto_inicial = input_moneda_tiempo_real("Ahorro Inicial (COP $)", "monto_inic_live", valor_defecto=0)
        
    with col_m2:
        plazo_meses = st.number_input("Plazo estimado (Meses)", min_value=1, value=6)
        st.caption("⏱️ **Frecuencia de Meta Deseada:**")
        
        meta_diaria_manual = input_moneda_tiempo_real("Meta Diaria Sugerida (COP $)", "meta_d_live", valor_defecto=0)
        meta_semanal_manual = input_moneda_tiempo_real("Meta Semanal Sugerida (COP $)", "meta_s_live", valor_defecto=0)

    btn_crear_meta = st.button("Guardar Meta de Ahorro", use_container_width=True, type="primary")
    
    if btn_crear_meta:
        if monto_meta <= 0:
            st.warning("El monto objetivo debe ser mayor a $0.")
        else:
            datos_user["metas"].append({
                "Meta": nombre_meta, 
                "Objetivo": float(monto_meta), 
                "Actual": float(monto_inicial), 
                "Plazo_Meses": int(plazo_meses),
                "Meta_Diaria_Manual": float(meta_diaria_manual),
                "Meta_Semanal_Manual": float(meta_semanal_manual)
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
            st.success(f"¡Meta creada! Debes abonar aproximadamente **{formato_cop(cuota_mes)}/mes** durante {plazo_meses} meses.")
            st.rerun()

    st.divider()
    
    col_reset_meta, _ = st.columns([2, 2])
    with col_reset_meta:
        if st.button("🧹 Limpiar / Reiniciar Metas Corregidas"):
            for m in datos_user.get("metas", []):
                m["Actual"] = 0.0
                m["Objetivo"] = min(m["Objetivo"], 1e9)
            guardar_datos()
            st.success("Se han saneado los saldos de tus metas para corregir valores erróneos.")
            st.rerun()

    st.subheader("Tus Metas Activas")
    if not datos_user["metas"]:
        st.info("No tienes metas registradas actualmente.")
    else:
        meta_to_delete = None
        for idx, meta in enumerate(datos_user["metas"]):
            monto_objetivo = float(meta.get("Objetivo", 1.0))
            monto_actual = float(meta.get("Actual", 0.0))
            plazo_m = int(meta.get("Plazo_Meses", 1))
            
            monto_faltante = max(0.0, monto_objetivo - monto_actual)
            
            cuota_mensual = monto_faltante / plazo_m if plazo_m > 0 else 0
            cuota_semanal = cuota_mensual / 4.33 if cuota_mensual > 0 else 0
            cuota_diaria = cuota_mensual / 30.0 if cuota_mensual > 0 else 0
            
            meta_d_display = meta.get("Meta_Diaria_Manual", 0.0) if meta.get("Meta_Diaria_Manual", 0.0) > 0 else cuota_diaria
            meta_s_display = meta.get("Meta_Semanal_Manual", 0.0) if meta.get("Meta_Semanal_Manual", 0.0) > 0 else cuota_semanal
            
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
            
            mc1, mc2, mc3, mc4 = st.columns([2, 2, 2, 1])
            mc1.metric("📅 Meta Diaria", formato_cop(meta_d_display))
            mc2.metric("🗓️ Meta Semanal", formato_cop(meta_s_display))
            mc3.metric("📆 Meta Mensual", formato_cop(cuota_mensual))
            
            if mc4.button("🗑️ Eliminar", key=f"btn_del_meta_{idx}"):
                meta_to_delete = idx
                
            st.divider()

        if meta_to_delete is not None:
            datos_user["metas"].pop(meta_to_delete)
            guardar_datos()
            st.rerun()

# ==========================================
# 7. CONFIGURACIÓN Y CAMBIO DE CONTRASEÑA
# ==========================================
with tab_config:
    st.subheader("🔒 Seguridad y Configuración de Cuenta")
    st.write(f"**Usuario Actual:** `{user}`")
    st.write(f"**Teléfono Registrado:** `+57 {datos_user.get('telefono', 'Sin registro')}`")
    st.divider()
    
    st.subheader("🔑 Cambiar Contraseña")
    with st.form("form_cambiar_pass"):
        old_pass = st.text_input("Contraseña Anterior", type="password")
        new_pass = st.text_input("Nueva Contraseña", type="password")
        confirm_pass = st.text_input("Confirmar Nueva Contraseña", type="password")
        btn_cambiar = st.form_submit_button("Actualizar Contraseña")
        
        if btn_cambiar:
            if not old_pass or not new_pass or not confirm_pass:
                st.warning("Por favor completa todos los campos de contraseña.")
            elif old_pass != datos_user["password"]:
                st.error("La contraseña anterior introducida es incorrecta.")
            elif new_pass != confirm_pass:
                st.error("La nueva contraseña y su confirmación no coinciden.")
            elif new_pass == old_pass:
                st.warning("La nueva contraseña debe ser distinta a la contraseña actual.")
            else:
                datos_user["password"] = new_pass
                guardar_datos()
                st.success("¡Tu contraseña ha sido actualizada correctamente!")

# ==========================================
# 8. PANEL DE ADMINISTRADOR
# ==========================================
if es_admin and tab_admin is not None:
    with tab_admin:
        st.subheader("👑 Panel de Control de Administrador")
        st.caption("Inspección de contraseñas, métricas globales, actualización de datos y eliminación de cuentas.")
        
        db_global = st.session_state.db_usuarios
        lista_usuarios = list(db_global.keys())
        
        st.subheader("📱 Teléfono de la Cuenta Admin")
        tel_admin_actual = db_global["admin"].get("telefono", "")
        
        with st.form("form_tel_admin"):
            nuevo_tel_admin = st.text_input("Número Telefónico del Admin (Colombia)", value=tel_admin_actual, placeholder="Ej: 3001234567").strip()
            btn_guardar_tel_admin = st.form_submit_button("Guardar Teléfono Admin")
            
            if btn_guardar_tel_admin:
                if not validar_telefono_colombia(nuevo_tel_admin):
                    st.error("El teléfono debe ser un celular colombiano de 10 dígitos que empiece por 3.")
                else:
                    db_global["admin"]["telefono"] = nuevo_tel_admin
                    guardar_datos()
                    st.success(f"¡Teléfono del administrador actualizado a +57 {nuevo_tel_admin}!")
                    st.rerun()

        st.divider()

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
        
        col_cred_head, col_cred_excel, col_cred_pdf = st.columns([3, 1, 1])
        with col_cred_head:
            st.subheader("🔑 Directorio de Cuentas y Credenciales")
        
        datos_credenciales = []
        for u, d in db_global.items():
            datos_credenciales.append({
                "Usuario": u,
                "Contraseña Actual": d.get("password", "N/A"),
                "Teléfono Colombia": f"+57 {d.get('telefono', 'Sin registro')}",
                "Transacciones": len(d.get("transacciones", [])),
                "Metas": len(d.get("metas", []))
            })
            
        df_credenciales = pd.DataFrame(datos_credenciales)
        
        with col_cred_excel:
            if not df_credenciales.empty:
                b_excel_admin = generar_excel_nativo(df_credenciales)
                st.download_button(
                    label="📊 Excel Usuarios",
                    data=b_excel_admin,
                    file_name="Directorio_Usuarios.csv",
                    mime="text/csv"
                )
                
        with col_cred_pdf:
            if not df_credenciales.empty:
                b_pdf_admin = generar_pdf_nativo(df_credenciales, titulo="Directorio de Usuarios")
                st.download_button(
                    label="📄 Imprimir/PDF",
                    data=b_pdf_admin,
                    file_name="Directorio_Usuarios.html",
                    mime="text/html"
                )

        st.dataframe(df_credenciales, use_container_width=True)
        
        st.divider()
        
        st.subheader("🗑️ Gestión y Borrado de Cuentas")
        col_sel, col_del = st.columns([3, 2])
        
        with col_sel:
            usuario_seleccionado = st.selectbox("Selecciona un usuario para auditar/eliminar:", lista_usuarios)
            
        with col_del:
            st.write("")
            st.write("")
            if usuario_seleccionado == "admin":
                st.info("🛡️ Por seguridad, la cuenta `admin` no se puede eliminar.")
            else:
                if st.button(f"🚨 Eliminar Cuenta de '{usuario_seleccionado}'", type="primary"):
                    del st.session_state.db_usuarios[usuario_seleccionado]
                    guardar_datos()
                    st.success(f"La cuenta del usuario `{usuario_seleccionado}` ha sido eliminada permanentemente.")
                    st.rerun()

        if usuario_seleccionado:
            datos_sel = db_global[usuario_seleccionado]
            df_sel = pd.DataFrame(datos_sel.get("transacciones", []))
            metas_sel = datos_sel.get("metas", [])
            
            st.markdown(f"#### 🔍 Auditoría en vivo del usuario: `{usuario_seleccionado}`")
            if not df_sel.empty:
                u_ingresos = float(df_sel[df_sel['Tipo'] == 'Ingreso']['Monto'].sum())
                u_gastos = float(df_sel[(df_sel['Tipo'] == 'Gasto')]['Monto'].sum())
                u_deudas = float(df_sel[df_sel['Tipo'] == 'Deuda']['Monto'].sum())
                
                aud1, aud2, aud3, aud4 = st.columns(4)
                aud1.metric("Ingresos", formato_cop(u_ingresos))
                aud2.metric("Gastos", formato_cop(u_gastos))
                aud3.metric("Deudas", formato_cop(u_deudas))
                aud4.metric("Metas Registradas", len(metas_sel))
                
                st.dataframe(df_sel, use_container_width=True)
            else:
                st.info("Este usuario no tiene transacciones registradas.")
