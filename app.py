import streamlit as st
import pandas as pd
import plotly.express as px
from pyairtable import Table
import google.generativeai as genai
from PIL import Image
import json

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Contable IA v3", layout="wide")

# --- CARGA DE CREDENCIALES ---
try:
    AIRTABLE_KEY = st.secrets["AIRTABLE_API_KEY"]
    BASE_ID = st.secrets["BASE_ID"]
    TABLE_NAME = st.secrets["TABLE_NAME"]
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    
    genai.configure(api_key=GEMINI_KEY)
    
    # Probamos con el nombre más básico para evitar el 404
    model = genai.GenerativeModel('gemini-pro-vision') 
except Exception as e:
    st.error(f"Faltan Secrets: {e}")
    st.stop()

# --- BARRA LATERAL: CARGA IA ---
st.sidebar.title("📥 Carga de Facturas")
archivo = st.sidebar.file_uploader("Subí una imagen", type=["png", "jpg", "jpeg"])

if archivo:
    if st.sidebar.button("🤖 Procesar con IA"):
        with st.sidebar:
            with st.spinner("Analizando..."):
                try:
                    img = Image.open(archivo)
                    prompt = "Analiza esta factura y devuelve solo JSON con: Cliente, Activo, Fecha (YYYY-MM-DD), Monto, IVA."
                    
                    # Sistema de seguridad: intentamos con flash si pro-vision falla
                    try:
                        response = model.generate_content([prompt, img])
                    except:
                        alt_model = genai.GenerativeModel('gemini-1.5-flash-latest')
                        response = alt_model.generate_content([prompt, img])
                    
                    texto_limpio = response.text.replace('```json', '').replace('```', '').strip()
                    st.session_state['datos_ia'] = json.loads(texto_limpio)
                    st.success("✅ Datos extraídos.")
                except Exception as e:
                    st.error(f"Error técnico: {e}")
                    st.info("Revisá que la 'Generative Language API' esté activa en Google Cloud.")

# Formulario de revisión y guardado
if 'datos_ia' in st.session_state:
    d = st.session_state['datos_ia']
    with st.sidebar.form("revision"):
        st.write("### Confirmar Datos")
        c = st.text_input("Cliente", value=d.get("Cliente", ""))
        a = st.text_input("Activo", value=d.get("Activo", ""))
        f = st.text_input("Fecha", value=d.get("Fecha", ""))
        m = st.number_input("Monto", value=float(d.get("Monto", 0)))
        v = st.number_input("IVA", value=float(d.get("IVA", 0)))
        
        if st.form_submit_button("💾 Guardar en Airtable"):
            Table(AIRTABLE_KEY, BASE_ID, TABLE_NAME).create({
                "Cliente": c, "Activo": a, "Fecha_Compra": f, 
                "Valor_Origen": m, "IVA_Credito": v
            })
            st.success("¡Cargado!")
            del st.session_state['datos_ia']
            st.rerun()

# --- DASHBOARD ---
st.title("🏦 Panel Patrimonial")
try:
    df = pd.DataFrame([r['fields'] for r in Table(AIRTABLE_KEY, BASE_ID, TABLE_NAME).all()])
    if not df.empty:
        st.metric("Inversión Total", f"${df['Valor_Origen'].sum():,.2f}")
        st.plotly_chart(px.bar(df, x="Cliente", y="Valor_Origen", color="Activo"))
        st.dataframe(df)
except:
    st.info("Sin datos para mostrar.")
