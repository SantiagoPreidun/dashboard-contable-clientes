import streamlit as st
import pandas as pd
from pyairtable import Table
from google import genai
from PIL import Image
import json

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión Contable IA v3", layout="wide")

try:
    # Traemos los secretos
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    AIRTABLE_KEY = st.secrets["AIRTABLE_API_KEY"]
    BASE_ID = st.secrets["BASE_ID"]
    TABLE_NAME = st.secrets["TABLE_NAME"]
    
    # Nuevo Cliente de Gemini (SDK Moderno)
    client = genai.Client(api_key=GEMINI_KEY)
    
except Exception as e:
    st.error(f"Faltan Secrets o hay un error de carga: {e}")
    st.stop()

# --- 2. BARRA LATERAL: PROCESAMIENTO ---
st.sidebar.title("📥 Procesador de Facturas")
archivo = st.sidebar.file_uploader("Subí tu comprobante", type=["png", "jpg", "jpeg"])

if archivo:
    if st.sidebar.button("🤖 Analizar con IA"):
        with st.sidebar:
            with st.spinner("IA analizando factura..."):
                try:
                    # Abrir imagen para el nuevo SDK
                    img = Image.open(archivo)
                    
                    # Llamada con el nuevo formato de cliente
                    response = client.models.generate_content(
                        model="gemini-2.0-flash", # Usamos la versión estable más potente
                        contents=["Analiza esta factura y devuelve solo JSON con llaves: Cliente, Activo, Fecha, Monto, IVA.", img]
                    )
                    
                    # Limpieza y carga de datos
                    raw_text = response.text.strip().replace('```json', '').replace('```', '')
                    st.session_state['datos_ia'] = json.loads(raw_text)
                    st.success("✅ ¡Datos extraídos!")
                except Exception as e:
                    st.error(f"Error técnico de IA: {e}")

# Formulario de guardado (Airtable)
if 'datos_ia' in st.session_state:
    d = st.session_state['datos_ia']
    with st.sidebar.form("confirmar_datos"):
        st.write("### Revisión de Datos")
        f_cli = st.text_input("Cliente", value=d.get("Cliente", ""))
        f_act = st.text_input("Activo", value=d.get("Activo", ""))
        f_fec = st.text_input("Fecha", value=d.get("Fecha", ""))
        f_mon = st.number_input("Monto", value=float(d.get("Monto", 0)))
        f_iva = st.number_input("IVA", value=float(d.get("IVA", 0)))
        
        if st.form_submit_button("✅ Guardar en Airtable"):
            try:
                table = Table(AIRTABLE_KEY, BASE_ID, TABLE_NAME)
                table.create({
                    "Cliente": f_cli, "Activo": f_act, "Fecha_Compra": f_fec,
                    "Valor_Origen": f_mon, "IVA_Credito": f_iva
                })
                st.success("¡Guardado!")
                del st.session_state['datos_ia']
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

# --- 3. DASHBOARD PRINCIPAL ---
st.title("🏦 Portal de Activos - Gestión Contable")

try:
    recs = Table(AIRTABLE_KEY, BASE_ID, TABLE_NAME).all()
    if recs:
        df = pd.DataFrame([r['fields'] for r in recs])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No hay datos todavía.")
except:
    st.info("Conectando con Airtable...")
