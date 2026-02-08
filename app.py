import streamlit as st
import pandas as pd
import plotly.express as px
from pyairtable import Table

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Dashboard Contable - Gestión de Activos", layout="wide")

# --- CONEXIÓN CON AIRTABLE ---
# Usamos st.secrets para proteger tus llaves (se configuran en Streamlit Cloud)
try:
    AIRTABLE_API_KEY = st.secrets["AIRTABLE_API_KEY"]
    BASE_ID = st.secrets["BASE_ID"]
    TABLE_NAME = st.secrets["TABLE_NAME"]
except Exception:
    st.error("Faltan las credenciales en los Secrets de Streamlit. Por favor, configúralas.")
    st.stop()

def cargar_datos():
    try:
        table = Table(AIRTABLE_API_KEY, BASE_ID, TABLE_NAME)
        records = table.all()
        if records:
            # Extraemos los campos de cada registro
            data = [r['fields'] for r in records]
            return pd.DataFrame(data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al conectar con Airtable: {e}")
        return pd.DataFrame()

# --- CUERPO DE LA APP ---
st.title("🏦 Portal de Activos - Gestión Contable")
st.markdown(f"**Base de Datos conectada:** `{BASE_ID}`")
st.markdown("---")

df = cargar_datos()

if not df.empty:
    # 1. MÉTRICAS PRINCIPALES
    col1, col2, col3 = st.columns(3)
    
    # Verificamos que las columnas existan antes de operar
    total_inv = df['Valor_Origen'].sum() if 'Valor_Origen' in df.columns else 0
    total_iva = df['IVA_Credito'].sum() if 'IVA_Credito' in df.columns else 0
    cantidad = len(df)
    
    col1.metric("Inversión Total", f"${total_inv:,.2f}")
    col2.metric("IVA Crédito Total", f"${total_iva:,.2f}")
    col3.metric("Activos Registrados", cantidad)

    st.markdown("### 📈 Análisis Patrimonial")

    # 2. GRÁFICO DE BARRAS
    if 'Cliente' in df.columns and 'Valor_Origen' in df.columns:
        fig = px.bar(
            df, 
            x="Cliente", 
            y="Valor_Origen", 
            color="Activo", 
            title="Inversión por Cliente y Bien",
            text_auto='.2s',
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

    # 3. TABLA DE DATOS
    st.markdown("### 📑 Detalle de Registros")
    st.dataframe(df, use_container_width=True)

else:
    st.info("La conexión es exitosa, pero no hay datos en la tabla 'Activos'. ¡Carga una fila en Airtable para ver la magia!")

# --- FOOTER ---
st.sidebar.info("Sistema de Gestión Contable IA v1.0")
