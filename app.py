import streamlit as st
import pandas as pd
import plotly.express as px
from pyairtable import Table

# --- CONFIGURACIÓN DE CONEXIÓN ---
# Reemplaza 'TU_TOKEN_PAT_AQUI' por el código que empieza con 'pat...' que generaste en Airtable
AIRTABLE_API_KEY = "patSRIW6PPjqCObmB"
BASE_ID = "appzSTRKpPq3xsCbF"
TABLE_NAME = "Activos" # Asegúrate de que la pestaña en Airtable se llame exactamente Activos

st.set_page_config(page_title="Dashboard Contable IA", layout="wide")

def cargar_datos():
    try:
        table = Table(AIRTABLE_API_KEY, BASE_ID, TABLE_NAME)
        records = table.all()
        if records:
            return pd.DataFrame([r['fields'] for r in records])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al conectar con Airtable: {e}")
        return pd.DataFrame()

# --- INTERFAZ DEL DASHBOARD ---
st.title("🏦 Portal de Activos - Gestión Contable")
st.markdown("---")

df = cargar_datos()

if not df.empty:
    # Métricas principales
    col1, col2, col3 = st.columns(3)
    
    # Intentamos sumar montos si las columnas existen
    total_inv = df['Valor_Origen'].sum() if 'Valor_Origen' in df.columns else 0
    total_iva = df['IVA_Credito'].sum() if 'IVA_Credito' in df.columns else 0
    
    col1.metric("Inversión Total", f"${total_inv:,.2f}")
    col2.metric("IVA Crédito Acumulado", f"${total_iva:,.2f}")
    col3.metric("Bienes Registrados", len(df))

    st.markdown("### 📈 Análisis de Inversiones por Cliente")
    
    # Gráfico interactivo
    if 'Cliente' in df.columns and 'Valor_Origen' in df.columns:
        fig = px.bar(df, x="Cliente", y="Valor_Origen", color="Activo", 
                     title="Distribución de Activos", barmode="group",
                     template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📑 Detalle de los Registros")
    st.dataframe(df, use_container_width=True)

else:
    st.info("Todavía no hay datos cargados en Airtable. En cuanto el Agente de IA procese una factura, aparecerán aquí.")
