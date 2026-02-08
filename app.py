import streamlit as st
import pandas as pd
import plotly.express as px
from pyairtable import Table

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Activos", layout="wide")

# Intentamos leer las llaves desde los Secrets de Streamlit
try:
    # Estas tres líneas buscan los datos que configuraste en el panel de Streamlit
    API_KEY = st.secrets["AIRTABLE_API_KEY"]
    BASE_ID = st.secrets["BASE_ID"]
    TABLE_NAME = st.secrets["TABLE_NAME"]
except Exception:
    st.error("Error: No se encontraron las credenciales en los 'Secrets' de Streamlit.")
    st.stop()

# --- FUNCIÓN DE CARGA ---
def cargar_datos():
    try:
        table = Table(API_KEY, BASE_ID, TABLE_NAME)
        records = table.all()
        return pd.DataFrame([r['fields'] for r in records]) if records else pd.DataFrame()
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🏦 Portal de Activos - Gestión Contable")
st.caption(f"Conectado a la base: {BASE_ID}")

df = cargar_datos()

if not df.empty:
    # Métricas
    c1, c2, c3 = st.columns(3)
    c1.metric("Inversión Total", f"${df['Valor_Origen'].sum():,.2f}")
    # Calculamos IVA si la columna existe, sino ponemos 0
    iva = df['IVA_Credito'].sum() if 'IVA_Credito' in df.columns else 0
    c2.metric("IVA Crédito Total", f"${iva:,.2f}")
    c3.metric("Activos", len(df))

    # Gráfico
    st.subheader("📊 Análisis Patrimonial")
    fig = px.bar(df, x="Cliente", y="Valor_Origen", color="Activo", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

    # Tabla
    st.subheader("📑 Detalle")
    st.dataframe(df, use_container_width=True)
else:
    st.info("No hay datos para mostrar.")
