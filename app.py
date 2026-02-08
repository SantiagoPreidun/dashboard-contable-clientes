import streamlit as st
import pandas as pd
from pyairtable import Table
from google import genai
from PIL import Image
import json
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Contable IA", layout="wide")

# --- 2. CARGA DE CREDENCIALES ---
try:
    # Estos nombres deben coincidir con tus Secrets en Streamlit Cloud
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    AIRTABLE_KEY = st.secrets["AIRTABLE_API_KEY"]
    BASE_ID = st.secrets["BASE_ID"]
    TABLE_NAME = st.secrets["TABLE_NAME"]
    
    # Inicialización del cliente moderno de Google GenAI
    client = genai.Client(api_key=GEMINI_KEY)
    
except Exception as e:
    st.error(f"Error en la configuración de Secrets: {e}")
    st.stop()

# --- 3. PROCESADOR DE FACTURAS (BARRA LATERAL) ---
st.sidebar.title("📥 Procesador de Facturas")
st.sidebar.markdown("Subí una imagen para extraer datos automáticamente.")

archivo_subido = st.sidebar.file_uploader("Subí una imagen (PNG/JPG)", type=["png", "jpg", "jpeg"])

if archivo_subido:
    if st.sidebar.button("🤖 Analizar con Gemini"):
        with st.sidebar:
            with st.spinner("IA analizando factura..."):
                try:
                    # Cargamos la imagen
                    imagen = Image.open(archivo_subido)
                    
                    # Llamada al modelo 2.0
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
                    
                    # Limpieza de la respuesta
                    texto_json = response.text.strip().replace('```json', '').replace('```', '')
                    st.session_state['datos_extraidos'] = json.loads(texto_json)
                    st.success("✅ ¡Datos extraídos!")
                    
                except Exception as e:
                    # MANEJO DEL ERROR DE CUOTA (429)
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        st.error("⏳ **Cuota agotada.** Google permite pocos intentos por minuto en la versión gratuita.")
                        st.info("Por favor, esperá **60 segundos** y volvé a intentarlo. Esto no es un error de código, es un límite de tu cuenta.")
                    else:
                        st.error(f"Error de la IA: {e}")

# Formulario de revisión y envío a Airtable
if 'datos_extraidos' in st.session_state:
    d = st.session_state['datos_extraidos']
    with st.sidebar.form("confirmar_guardado"):
        st.write("### Revisión de Datos")
        f_cliente = st.text_input("Cliente", value=d.get("Cliente", ""))
        f_activo = st.text_input("Activo", value=d.get("Activo", ""))
        f_fecha = st.text_input("Fecha", value=d.get("Fecha", ""))
        # Convertimos a float para evitar errores de tipo en Airtable
        f_monto = st.number_input("Monto Neto", value=float(d.get("Monto", 0)))
        f_iva = st.number_input("IVA", value=float(d.get("IVA", 0)))
        
        if st.form_submit_button("💾 Guardar en Airtable"):
            try:
                tabla = Table(AIRTABLE_KEY, BASE_ID, TABLE_NAME)
                tabla.create({
                    "Cliente": f_cliente,
                    "Activo": f_activo,
                    "Fecha_Compra": f_fecha,
                    "Valor_Origen": f_monto,
                    "IVA_Credito": f_iva
                })
                st.success("¡Registro guardado!")
                # Borramos el estado para permitir una nueva factura
                del st.session_state['datos_extraidos']
                time.sleep(1) # Pequeña pausa para que el usuario vea el éxito
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar en Airtable: {e}")

# --- 4. DASHBOARD PRINCIPAL ---
st.title("🏦 Portal de Activos - Dashboard")

def cargar_datos_dashboard():
    try:
        tabla = Table(AIRTABLE_KEY, BASE_ID, TABLE_NAME)
        registros = tabla.all()
        if registros:
            # Transformamos los registros en una lista limpia de diccionarios
            return pd.DataFrame([r['fields'] for r in registros])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al conectar con Airtable: {e}")
        return pd.DataFrame()

df = cargar_datos_dashboard()

if not df.empty:
    # Métricas principales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_inversion = df['Valor_Origen'].sum() if 'Valor_Origen' in df.columns else 0
        st.metric("Inversión Neta", f"${total_inversion:,.2f}")
    
    with col2:
        total_iva = df['IVA_Credito'].sum() if 'IVA_Credito' in df.columns else 0
        st.metric("IVA Crédito", f"${total_iva:,.2f}")
        
    with col3:
        st.metric("Total Bienes", len(df))

    st.divider()
    
    # Tabla interactiva
    st.write("### Detalle de Registros en Airtable")
    st.dataframe(df, use_container_width=True)
else:
    st.info("No hay datos cargados aún. Subí una factura en la barra lateral para empezar.")
