import streamlit as st
import pandas as pd
import plotly.express as px
from pyairtable import Table
import google.generativeai as genai
from PIL import Image
import json

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Contable IA v2", layout="wide")

# --- 2. CARGA DE CREDENCIALES ---
try:
    AIRTABLE_KEY = st.secrets["AIRTABLE_API_KEY"]
    BASE_ID = st.secrets["BASE_ID"]
    TABLE_NAME = st.secrets["TABLE_NAME"]
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    
    # CONFIGURACIÓN CORREGIDA:
    genai.configure(api_key=GEMINI_KEY)
    # Usamos el nombre corto que la librería traduce automáticamente a la versión correcta
    model = genai.GenerativeModel('gemini-1.5-flash') 
except Exception as e:
    st.error(f"⚠️ Error en Secrets: {e}")
    st.stop()

# --- 3. FUNCIONES DE BASE DE DATOS ---
def cargar_datos():
    try:
        table = Table(AIRTABLE_KEY, BASE_ID, TABLE_NAME)
        records = table.all()
        return pd.DataFrame([r['fields'] for r in records]) if records else pd.DataFrame()
    except Exception as e:
        st.warning(f"Error al conectar con Airtable: {e}")
        return pd.DataFrame()

# --- 4. BARRA LATERAL: EXTRACCIÓN CON IA ---
st.sidebar.title("📥 Carga de Facturas")
archivo = st.sidebar.file_uploader("Subí el comprobante", type=["png", "jpg", "jpeg"])

if archivo:
    if st.sidebar.button("🤖 Procesar con Gemini"):
        with st.sidebar:
            with st.spinner("Analizando documento..."):
                try:
                    img = Image.open(archivo)
                    # Prompt para obtener JSON puro
                    prompt = "Analiza esta factura y devuelve solo un JSON con: Cliente, Activo, Fecha (YYYY-MM-DD), Monto (neto), IVA."
                    
                    response = model.generate_content([prompt, img])
                    
                    # Limpieza por si la IA agrega bloques de código markdown
                    res_text = response.text.replace('```json', '').replace('```', '').strip()
                    st.session_state['datos_ia'] = json.loads(res_text)
                    st.success("✅ Datos extraídos.")
                except Exception as e:
                    st.error(f"❌ Error de IA: {e}")
                    st.info("Tip: Verificá que la 'Generative Language API' esté activa en Google Cloud Console.")

# Formulario de revisión
if 'datos_ia' in st.session_state:
    d = st.session_state['datos_ia']
    with st.sidebar.form("confirmacion"):
        st.write("### Revisión Contable")
        c = st.text_input("Cliente", value=d.get("Cliente", ""))
        a = st.text_input("Activo", value=d.get("Activo", ""))
        f = st.text_input("Fecha", value=d.get("Fecha", ""))
        m = st.number_input("Monto Neto", value=float(d.get("Monto", 0)))
        v = st.number_input("IVA", value=float(d.get("IVA", 0)))
        
        if st.form_submit_button("✅ Guardar en Airtable"):
            try:
                Table(AIRTABLE_KEY, BASE_ID, TABLE_NAME).create({
                    "Cliente": c, "Activo": a, "Fecha_Compra": f,
                    "Valor_Origen": m, "IVA_Credito": v
                })
                st.success("¡Guardado!")
                del st.session_state['datos_ia']
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

# --- 5. DASHBOARD ---
st.title("🏦 Panel de Gestión de Activos")
df = cargar_datos()

if not df.empty:
    col1, col2 = st.columns(2)
    col1.metric("Inversión Total", f"${df['Valor_Origen'].sum():,.2f}")
    col2.metric("Bienes Registrados", len(df))
    
    st.plotly_chart(px.bar(df, x="Cliente", y="Valor_Origen", color="Activo"), use_container_width=True)
    st.dataframe(df, use_container_width=True)
else:
    st.info("Conexión establecida. La tabla está lista para recibir datos.")
