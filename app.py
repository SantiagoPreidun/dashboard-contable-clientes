import streamlit as st
import pandas as pd
import plotly.express as px
from pyairtable import Table
import google.generativeai as genai
from PIL import Image
import json

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión Contable IA", layout="wide")

try:
    # Leemos tus Secrets de Streamlit
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    AIRTABLE_KEY = st.secrets["AIRTABLE_API_KEY"]
    BASE_ID = st.secrets["BASE_ID"]
    TABLE_NAME = st.secrets["TABLE_NAME"]
    
    # CONFIGURACIÓN DE IA
    genai.configure(api_key=GEMINI_KEY)
    
    # CAMBIO CLAVE: Usamos gemini-1.5-flash sin el prefijo models/ 
    # para que la librería elija la ruta v1 (estable) y no la v1beta.
    model = genai.GenerativeModel('gemini-1.5-flash')
    
except Exception as e:
    st.error(f"Faltan Secrets o hay un error: {e}")
    st.stop()

# --- 2. BARRA LATERAL (PROCESAMIENTO) ---
st.sidebar.title("📥 Procesador de Facturas")
archivo = st.sidebar.file_uploader("Subí tu comprobante", type=["png", "jpg", "jpeg"])

if archivo:
    if st.sidebar.button("🤖 Analizar con IA"):
        with st.sidebar:
            with st.spinner("IA analizando factura..."):
                try:
                    img = Image.open(archivo)
                    prompt = """Analizá esta imagen y extraé: Cliente, Activo, Fecha (YYYY-MM-DD), Monto (neto), IVA. 
                    Respondé únicamente con un JSON puro, sin texto adicional."""
                    
                    response = model.generate_content([prompt, img])
                    
                    # Limpiamos el texto por si la IA agrega bloques de código
                    raw_text = response.text.strip().replace('```json', '').replace('```', '')
                    st.session_state['datos_ia'] = json.loads(raw_text)
                    st.success("✅ Datos extraídos.")
                except Exception as e:
                    # Si falla, te damos un diagnóstico real
                    st.error(f"Error técnico: {e}")

# Formulario de confirmación
if 'datos_ia' in st.session_state:
    d = st.session_state['datos_ia']
    with st.sidebar.form("confirmar_guardado"):
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

def cargar_datos():
    try:
        table = Table(AIRTABLE_KEY, BASE_ID, TABLE_NAME)
        records = table.all()
        return pd.DataFrame([r['fields'] for r in records]) if records else pd.DataFrame()
    except:
        return pd.DataFrame()

df = cargar_datos()

if not df.empty:
    m1, m2 = st.columns(2)
    m1.metric("Inversión Total", f"${df['Valor_Origen'].sum():,.2f}")
    m2.metric("IVA Acumulado", f"${df['IVA_Credito'].sum():,.2f}")
    st.plotly_chart(px.bar(df, x="Cliente", y="Valor_Origen", color="Activo"))
    st.dataframe(df, use_container_width=True)
else:
    st.info("No hay datos cargados. Usá la barra lateral para procesar una factura.")
