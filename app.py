import streamlit as st
import pandas as pd
import plotly.express as px
from pyairtable import Table
import google.generativeai as genai
from PIL import Image
import json

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Contable IA", layout="wide")

# --- 2. CARGA DE CREDENCIALES Y CONFIGURACIÓN DE IA ---
try:
    AIRTABLE_API_KEY = st.secrets["AIRTABLE_API_KEY"]
    BASE_ID = st.secrets["BASE_ID"]
    TABLE_NAME = st.secrets["TABLE_NAME"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    
    # CONFIGURACIÓN ROBUSTA: Forzamos el nombre completo del modelo estable
    genai.configure(api_key=GEMINI_API_KEY)
    # Usamos gemini-1.5-flash-latest que es la versión más aceptada globalmente
    model = genai.GenerativeModel('gemini-1.5-flash-latest') 
except Exception as e:
    st.error(f"⚠️ Error en configuración de Secrets: {e}")
    st.stop()

# --- 3. FUNCIONES DE APOYO ---
def guardar_en_airtable(datos):
    try:
        table = Table(AIRTABLE_API_KEY, BASE_ID, TABLE_NAME)
        table.create(datos)
        return True
    except Exception as e:
        st.error(f"❌ Error al guardar en Airtable: {e}")
        return False

def cargar_datos_dashboard():
    try:
        table = Table(AIRTABLE_API_KEY, BASE_ID, TABLE_NAME)
        records = table.all()
        return pd.DataFrame([r['fields'] for r in records]) if records else pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error al leer datos de Airtable: {e}")
        return pd.DataFrame()

# --- 4. BARRA LATERAL: CARGA CON IA ---
st.sidebar.title("📥 Extracción de Facturas")
st.sidebar.markdown("Subí una factura para que la IA extraiga los datos automáticamente.")

archivo_subido = st.sidebar.file_uploader("Subí PDF o Imagen", type=["png", "jpg", "jpeg"])

if archivo_subido:
    if st.sidebar.button("🤖 Procesar con Gemini"):
        with st.sidebar:
            with st.spinner("Leyendo comprobante..."):
                try:
                    # Convertir archivo para Gemini
                    image_data = Image.open(archivo_subido)
                    
                    prompt = """
                    Analiza esta imagen de factura y extrae los siguientes datos en formato JSON puro:
                    {
                      "Cliente": "Nombre del comprador",
                      "Activo": "Descripción del bien",
                      "Fecha": "YYYY-MM-DD",
                      "Monto": número neto sin IVA,
                      "IVA": número del IVA
                    }
                    Responde solo el JSON.
                    """
                    
                    # Llamada con manejo de errores específico
                    response = model.generate_content([prompt, image_data])
                    
                    # Limpieza de la respuesta
                    texto_limpio = response.text.replace('```json', '').replace('```', '').strip()
                    st.session_state['datos_ia'] = json.loads(texto_limpio)
                    st.success("✅ Datos extraídos.")
                except Exception as e:
                    st.error(f"❌ Error en la IA: {e}")
                    st.info("Tip: Verificá que tu GEMINI_API_KEY sea correcta en los Secrets.")

# Formulario de revisión
if 'datos_ia' in st.session_state:
    datos = st.session_state['datos_ia']
    with st.sidebar.form("formulario_revision"):
        st.write("### Revisión de Datos")
        f_cliente = st.text_input("Cliente", value=datos.get("Cliente", ""))
        f_activo = st.text_input("Activo", value=datos.get("Activo", ""))
        f_fecha = st.text_input("Fecha", value=datos.get("Fecha", ""))
        f_monto = st.number_input("Monto Neto", value=float(datos.get("Monto", 0)))
        f_iva = st.number_input("IVA", value=float(datos.get("IVA", 0)))
        
        if st.form_submit_button("🚀 Confirmar y Subir"):
            nueva_fila = {
                "Cliente": f_cliente,
                "Activo": f_activo,
                "Fecha_Compra": f_fecha,
                "Valor_Origen": f_monto,
                "IVA_Credito": f_iva,
                "Vida_Util": 5,
                "Estado": "Activo"
            }
            if guardar_en_airtable(nueva_fila):
                st.balloons()
                del st.session_state['datos_ia']
                st.rerun()

# --- 5. DASHBOARD PRINCIPAL ---
st.title("🏦 Panel de Control Patrimonial")

df = cargar_datos_dashboard()

if not df.empty:
    # Métricas
    c1, c2, c3 = st.columns(3)
    total_neto = df['Valor_Origen'].sum() if 'Valor_Origen' in df.columns else 0
    total_iva = df['IVA_Credito'].sum() if 'IVA_Credito' in df.columns else 0
    
    c1.metric("Inversión Neta Total", f"${total_neto:,.2f}")
    c2.metric("IVA Crédito Total", f"${total_iva:,.2f}")
    c3.metric("Bienes Registrados", len(df))

    # Gráfico
    st.markdown("### 📊 Inversión por Cliente")
    if 'Cliente' in df.columns and 'Valor_Origen' in df.columns:
        fig = px.bar(df, x="Cliente", y="Valor_Origen", color="Activo", 
                     title="Distribución de Activos", barmode="group")
        st.plotly_chart(fig, use_container_width=True)

    # Tabla Detallada
    st.markdown("### 📑 Listado Detallado")
    st.dataframe(df, use_container_width=True)
else:
    st.info("Aún no hay registros. Usá la barra lateral para subir tu primera factura.")
