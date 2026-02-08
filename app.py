import streamlit as st
import pandas as pd
import plotly.express as px
from pyairtable import Table
import google.generativeai as genai
from PIL import Image
import json

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Contable IA", layout="wide")

# --- 2. VALIDACIÓN DE CONEXIÓN (SECRETS) ---
def inicializar_conexiones():
    try:
        # Intentamos leer los secretos
        creds = {
            "airtable_key": st.secrets["AIRTABLE_API_KEY"],
            "base_id": st.secrets["BASE_ID"],
            "table_name": st.secrets["TABLE_NAME"],
            "gemini_key": st.secrets["GEMINI_API_KEY"]
        }
        
        # Configurar Gemini
        genai.configure(api_key=creds["gemini_key"])
        # Usamos el nombre de modelo más estándar
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        return creds, model
    except Exception as e:
        st.error(f"❌ Error en los Secrets de Streamlit: {e}")
        st.info("Asegúrate de que las llaves en 'Settings > Secrets' coincidan exactamente con los nombres en el código.")
        st.stop()

creds, model_ia = inicializar_conexiones()

# --- 3. FUNCIONES DE BASE DE DATOS ---
def cargar_datos():
    try:
        table = Table(creds["airtable_key"], creds["base_id"], creds["table_name"])
        records = table.all()
        if records:
            return pd.DataFrame([r['fields'] for r in records])
        return pd.DataFrame()
    except Exception as e:
        st.warning(f"⚠️ Conectado a Airtable pero no se pudieron leer datos: {e}")
        return pd.DataFrame()

# --- 4. BARRA LATERAL: PROCESAMIENTO CON IA ---
st.sidebar.title("📥 Carga de Comprobantes")
archivo = st.sidebar.file_uploader("Subí una imagen de la factura", type=["png", "jpg", "jpeg"])

if archivo:
    if st.sidebar.button("🤖 Procesar con IA"):
        with st.sidebar:
            with st.spinner("Gemini analizando factura..."):
                try:
                    img = Image.open(archivo)
                    prompt = """Analiza esta factura y extrae: Cliente, Activo, Fecha (YYYY-MM-DD), Monto (neto), IVA. 
                    Responde únicamente con un JSON puro."""
                    response = model_ia.generate_content([prompt, img])
                    
                    # Limpieza y carga de JSON
                    raw_json = response.text.replace('```json', '').replace('```', '').strip()
                    st.session_state['datos_factura'] = json.loads(raw_json)
                    st.success("✅ ¡Datos extraídos!")
                except Exception as e:
                    st.error(f"❌ Error de IA: {e}")

# Formulario para confirmar y guardar
if 'datos_factura' in st.session_state:
    d = st.session_state['datos_factura']
    with st.sidebar.form("confirmar_datos"):
        st.write("### Revisar y Guardar")
        f_cli = st.text_input("Cliente", value=d.get("Cliente", ""))
        f_act = st.text_input("Activo", value=d.get("Activo", ""))
        f_fec = st.text_input("Fecha", value=d.get("Fecha", ""))
        f_mon = st.number_input("Monto Neto", value=float(d.get("Monto", 0)))
        f_iva = st.number_input("IVA", value=float(d.get("IVA", 0)))
        
        if st.form_submit_button("💾 Guardar en Airtable"):
            try:
                table = Table(creds["airtable_key"], creds["base_id"], creds["table_name"])
                table.create({
                    "Cliente": f_cli,
                    "Activo": f_act,
                    "Fecha_Compra": f_fec,
                    "Valor_Origen": f_mon,
                    "IVA_Credito": f_iva
                })
                st.success("¡Guardado correctamente!")
                del st.session_state['datos_factura']
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

# --- 5. DASHBOARD PRINCIPAL ---
st.title("🏦 Panel Patrimonial - Gestión Contable")
df = cargar_datos()

if not df.empty:
    m1, m2, m3 = st.columns(3)
    m1.metric("Inversión Total", f"${df['Valor_Origen'].sum():,.2f}")
    m2.metric("IVA Acumulado", f"${df['IVA_Credito'].sum():,.2f}")
    m3.metric("Bienes", len(df))
    
    st.markdown("### 📊 Análisis por Cliente")
    fig = px.bar(df, x="Cliente", y="Valor_Origen", color="Activo", barmode="group", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(df, use_container_width=True)
else:
    st.info("La conexión es correcta, pero la tabla está vacía. Subí una factura para empezar.")
