import streamlit as st
import pandas as pd
from pyairtable import Table
from google import genai
from PIL import Image
import json

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Contable IA", layout="wide")

# --- 2. CARGA DE CREDENCIALES ---
try:
    # Estos nombres deben coincidir con tus Secrets en Streamlit
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    AIRTABLE_KEY = st.secrets["AIRTABLE_API_KEY"]
    BASE_ID = st.secrets["BASE_ID"]
    TABLE_NAME = st.secrets["TABLE_NAME"]
    
    # Inicialización del nuevo cliente de Google GenAI
    client = genai.Client(api_key=GEMINI_KEY)
    
except Exception as e:
    st.error(f"Error en la configuración de Secrets: {e}")
    st.stop()

# --- 3. PROCESADOR DE FACTURAS (BARRA LATERAL) ---
st.sidebar.title("📥 Procesador de Facturas")
archivo_subido = st.sidebar.file_uploader("Subí una imagen (PNG/JPG)", type=["png", "jpg", "jpeg"])

if archivo_subido:
    if st.sidebar.button("🤖 Analizar con Gemini"):
        with st.sidebar:
            with st.spinner("IA analizando factura..."):
                try:
                    # Cargamos la imagen
                    imagen = Image.open(archivo_subido)
                    
                    # Llamada al modelo usando el nuevo formato
                    # Nota: gemini-2.0-flash es la versión más estable y rápida
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=["""Analizá esta factura y extraé los siguientes datos en formato JSON:
                        - Cliente (Nombre de la empresa o persona)
                        - Activo (Bien o servicio adquirido)
                        - Fecha (En formato YYYY-MM-DD)
                        - Monto (Valor neto sin impuestos)
                        - IVA (Monto del impuesto)
                        Respondé SOLO el objeto JSON.""", imagen]
                    )
                    
                    # Limpieza de la respuesta por si incluye bloques de código markdown
                    texto_json = response.text.strip().replace('```json', '').replace('```', '')
                    st.session_state['datos_extraidos'] = json.loads(texto_json)
                    st.success("✅ ¡Datos extraídos con éxito!")
                    
                except Exception as e:
                    st.error(f"Error de la IA: {e}")

# Formulario de confirmación y envío a Airtable
if 'datos_extraidos' in st.session_state:
    d = st.session_state['datos_extraidos']
    with st.sidebar.form("confirmar_guardado"):
        st.write("### Revisión de Datos")
        f_cliente = st.text_input("Cliente", value=d.get("Cliente", ""))
        f_activo = st.text_input("Activo", value=d.get("Activo", ""))
        f_fecha = st.text_input("Fecha", value=d.get("Fecha", ""))
        f_monto = st.number_input("Monto Neto", value=float(d.get("Monto", 0)))
        f_iva = st.number_input("IVA", value=float(d.get("IVA", 0)))
        
        if st.form_submit_button("💾 Guardar en Airtable"):
            try:
                # Conexión y creación del registro
                tabla = Table(AIRTABLE_KEY, BASE_ID, TABLE_NAME)
                tabla.create({
                    "Cliente": f_cliente,
                    "Activo": f_activo,
                    "Fecha_Compra": f_fecha,
                    "Valor_Origen": f_monto,
                    "IVA_Credito": f_iva
                })
                st.success("¡Registro guardado correctamente!")
                # Limpiar datos para permitir nueva carga
                del st.session_state['datos_extraidos']
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar en Airtable: {e}")

# --- 4. DASHBOARD PRINCIPAL ---
st.title("🏦 Portal de Activos - Dashboard")

def cargar_datos_dashboard():
    try:
        tabla = Table(AIRTABLE_KEY, BASE_ID, TABLE_NAME)
        registros = tabla.all()
        return pd.DataFrame([r['fields'] for r in registros]) if registros else pd.DataFrame()
    except:
        return pd.DataFrame()

df = cargar_datos_dashboard()

if not df.empty:
    col1, col2 = st.columns(2)
    with col1:
        total_inversion = df['Valor_Origen'].sum() if 'Valor_Origen' in df.columns else 0
        st.metric("Inversión Neta Total", f"${total_inversion:,.2f}")
    with col2:
        total_iva = df['IVA_Credito'].sum() if 'IVA_Credito' in df.columns else 0
        st.metric("IVA Crédito Acumulado", f"${total_iva:,.2f}")
    
    st.write("### Listado de Activos")
    st.dataframe(df, use_container_width=True)
else:
    st.info("No hay datos cargados aún. Subí una factura para empezar.")
