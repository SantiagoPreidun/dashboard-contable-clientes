import streamlit as st
import pandas as pd
import plotly.express as px
from pyairtable import Table
import google.generativeai as genai
from PIL import Image
import json

# --- 1. CONFIGURACIÓN Y SEGURIDAD ---
st.set_page_config(page_title="Gestión Contable IA", layout="wide")

try:
    # Traemos todas las llaves desde los Secrets de Streamlit
    AIRTABLE_API_KEY = st.secrets["AIRTABLE_API_KEY"]
    BASE_ID = st.secrets["BASE_ID"]
    TABLE_NAME = st.secrets["TABLE_NAME"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    
    # Configuramos Gemini
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Faltan configuraciones en los Secrets: {e}")
    st.stop()

# --- 2. FUNCIÓN PARA CARGAR A AIRTABLE ---
def guardar_en_airtable(datos):
    try:
        table = Table(AIRTABLE_API_KEY, BASE_ID, TABLE_NAME)
        table.create(datos)
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# --- 3. INTERFAZ: BARRA LATERAL (CARGA CON IA) ---
st.sidebar.title("📥 Carga de Comprobantes")
archivo = st.sidebar.file_uploader("Subí una factura", type=["png", "jpg", "jpeg", "pdf"])

if archivo:
    if st.sidebar.button("🤖 Procesar con IA"):
        with st.sidebar:
            with st.spinner("Gemini leyendo factura..."):
                img = Image.open(archivo)
                prompt = """Extrae de esta factura: Cliente, Activo (bien comprado), Fecha (YYYY-MM-DD), Monto (Neto sin IVA), IVA. 
                Responde únicamente en formato JSON puro."""
                response = model.generate_content([prompt, img])
                # Limpiamos la respuesta para que sea un JSON válido
                json_data = response.text.replace('```json', '').replace('```', '').strip()
                st.session_state['datos_ia'] = json.loads(json_data)

# Formulario de confirmación si la IA ya leyó el archivo
if 'datos_ia' in st.session_state:
    datos = st.session_state['datos_ia']
    with st.sidebar.form("confirmar_carga"):
        st.write("### Confirmar datos")
        cliente = st.text_input("Cliente", value=datos.get("Cliente", ""))
        activo = st.text_input("Activo", value=datos.get("Activo", ""))
        fecha = st.text_input("Fecha", value=datos.get("Fecha", ""))
        monto = st.number_input("Monto Neto", value=float(datos.get("Monto", 0)))
        iva = st.number_input("IVA", value=float(datos.get("IVA", 0)))
        
        if st.form_submit_button("✅ Guardar en Base de Datos"):
            exito = guardar_en_airtable({
                "Cliente": cliente,
                "Activo": activo,
                "Fecha_Compra": fecha,
                "Valor_Origen": monto,
                "IVA_Credito": iva,
                "Vida_Util": 5,
                "Estado": "Activo"
            })
            if exito:
                st.success("¡Cargado!")
                del st.session_state['datos_ia'] # Limpiamos para la próxima carga
                st.rerun()

# --- 4. INTERFAZ: DASHBOARD PRINCIPAL ---
st.title("🏦 Panel de Control Patrimonial")
# ... (Aquí sigue tu código de gráficos que ya funcionaba)
