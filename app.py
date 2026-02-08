import streamlit as st
import pandas as pd
import plotly.express as px
from pyairtable import Table
import google.generativeai as genai
from PIL import Image
import json

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Contable IA", layout="wide")

# --- 2. CARGA DE CREDENCIALES ---
try:
    # Estas llaves deben estar en Settings > Secrets de Streamlit
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    AIRTABLE_KEY = st.secrets["AIRTABLE_API_KEY"]
    BASE_ID = st.secrets["BASE_ID"]
    TABLE_NAME = st.secrets["TABLE_NAME"]
    
    # CONFIGURACIÓN PARA EVITAR ERROR 404:
    genai.configure(api_key=GEMINI_KEY)
    
    # Usamos el nombre del modelo sin el prefijo 'models/' para que la librería 
    # gestione la versión de la API (v1 en lugar de v1beta) automáticamente.
    model = genai.GenerativeModel('gemini-1.5-flash')
    
except Exception as e:
    st.error(f"Faltan Secrets o hay un error de configuración: {e}")
    st.stop()

# --- 3. BARRA LATERAL: CARGA DE COMPROBANTES ---
st.sidebar.title("📥 Procesador de Facturas")
archivo = st.sidebar.file_uploader("Subí tu comprobante (Imagen)", type=["png", "jpg", "jpeg"])

if archivo:
    if st.sidebar.button("🤖 Analizar con IA"):
        with st.sidebar:
            with st.spinner("Gemini analizando factura..."):
                try:
                    img = Image.open(archivo)
                    # Prompt optimizado para respuesta JSON limpia
                    prompt = """Analizá esta imagen de factura y extraé los siguientes datos:
                    1. Cliente (Comprador)
                    2. Activo (Bien o servicio comprado)
                    3. Fecha (Formato YYYY-MM-DD)
                    4. Monto (Valor neto sin IVA)
                    5. IVA (Monto del impuesto)
                    Devolvé únicamente un objeto JSON con estas llaves: Cliente, Activo, Fecha, Monto, IVA."""
                    
                    # Realizamos la petición
                    response = model.generate_content([prompt, img])
                    
                    # Limpiamos la respuesta de posibles etiquetas de markdown
                    texto_limpio = response.text.replace('```json', '').replace('```', '').strip()
                    st.session_state['datos_ia'] = json.loads(texto_limpio)
                    st.success("✅ ¡Datos extraídos con éxito!")
                except Exception as e:
                    st.error(f"Error de IA: {e}")
                    st.info("Asegurate de que la API Key en Secrets pertenezca al proyecto donde habilitaste la API.")

# Formulario de revisión y guardado
if 'datos_ia' in st.session_state:
    d = st.session_state['datos_ia']
    with st.sidebar.form("formulario_confirmacion"):
        st.write("### Revisión de Datos Extraídos")
        f_cliente = st.text_input("Cliente", value=d.get("Cliente", ""))
        f_activo = st.text_input("Activo", value=d.get("Activo", ""))
        f_fecha = st.text_input("Fecha", value=d.get("Fecha", ""))
        f_monto = st.number_input("Monto Neto", value=float(d.get("Monto", 0)))
        f_iva = st.number_input("IVA", value=float(d.get("IVA", 0)))
        
        if st.form_submit_button("✅ Guardar en Airtable"):
            try:
                table = Table(AIRTABLE_KEY, BASE_ID, TABLE_NAME)
                table.create({
                    "Cliente": f_cliente,
                    "Activo": f_activo,
                    "Fecha_Compra": f_fecha,
                    "Valor_Origen": f_monto,
                    "IVA_Credito": f_iva
                })
                st.success("¡Registro guardado!")
                del st.session_state['datos_ia']
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar en Airtable: {e}")

# --- 4. DASHBOARD PRINCIPAL ---
st.title("🏦 Portal de Activos - Gestión Contable")
# (Aquí va tu lógica de visualización que ya funciona)
