import streamlit as st
import pandas as pd
from pyairtable import Table
import google.generativeai as genai
from PIL import Image
import json

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión Contable IA", layout="wide")

try:
    # Traemos las llaves de los Secrets de Streamlit
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    AIRTABLE_KEY = st.secrets["AIRTABLE_API_KEY"]
    BASE_ID = st.secrets["BASE_ID"]
    TABLE_NAME = st.secrets["TABLE_NAME"]
    
    # Configuramos Gemini
    genai.configure(api_key=GEMINI_KEY)
    # gemini-1.5-flash es el modelo más rápido y estable para este tipo de tareas
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Faltan Secrets o hay un error: {e}")
    st.stop()

# --- 2. CARGA DE FACTURAS (BARRA LATERAL) ---
st.sidebar.title("📥 Procesador de Facturas")
archivo = st.sidebar.file_uploader("Subí tu comprobante (Imagen)", type=["png", "jpg", "jpeg"])

if archivo:
    if st.sidebar.button("🤖 Analizar con IA"):
        try:
            img = Image.open(archivo)
            prompt = "Analizá esta factura y extraé: Cliente, Activo, Fecha (YYYY-MM-DD), Monto (neto), IVA. Respondé solo JSON puro."
            
            response = model.generate_content([prompt, img])
            
            # Limpiamos posibles formatos de markdown de la respuesta
            raw_text = response.text.strip().replace('```json', '').replace('```', '')
            st.session_state['datos_ia'] = json.loads(raw_text)
            st.sidebar.success("¡Datos extraídos con éxito!")
        except Exception as e:
            st.sidebar.error(f"Error de IA: {e}")

# Formulario para confirmar y guardar en Airtable
if 'datos_ia' in st.session_state:
    d = st.session_state['datos_ia']
    with st.sidebar.form("confirmar_registro"):
        st.write("### Confirmar Registro")
        c = st.text_input("Cliente", value=d.get("Cliente", ""))
        a = st.text_input("Activo", value=d.get("Activo", ""))
        f = st.text_input("Fecha", value=d.get("Fecha", ""))
        m = st.number_input("Monto", value=float(d.get("Monto", 0)))
        v = st.number_input("IVA", value=float(d.get("IVA", 0)))
        
        if st.form_submit_button("✅ Guardar en Airtable"):
            try:
                Table(AIRTABLE_KEY, BASE_ID, TABLE_NAME).create({
                    "Cliente": c, "Activo": a, "Fecha_Compra": f, 
                    "Valor_Origen": m, "IVA_Credito": v
                })
                st.success("¡Guardado en Airtable!")
                del st.session_state['datos_ia']
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

# --- 3. DASHBOARD PRINCIPAL ---
st.title("🏦 Portal de Activos - Gestión Contable")
# (Aquí sigue tu lógica de gráficos que ya vimos que funciona)
