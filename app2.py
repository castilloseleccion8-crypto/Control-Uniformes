import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Sistema de Uniformes", layout="wide")

st.title("👕 Carga de Talles - Gestión de Uniformes")

# --- CONEXIÓN ---
try:
    # ttl=0 evita que Streamlit guarde datos viejos en memoria
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="CASTILLO", ttl=0)
    
    # Limpiamos nombres de columnas por si hay espacios extra
    df.columns = df.columns.str.strip()
    
except Exception as e:
    st.error("❌ No se pudo conectar con la planilla.")
    st.info(f"Detalle técnico: {e}")
    st.markdown("""
    **Revisá lo siguiente:**
    1. Que en **Secrets** el link termine en `/edit`.
    2. Que la pestaña del Google Sheet se llame exactamente **CASTILLO**.
    3. Que el archivo esté compartido como **'Cualquier persona con el enlace'** en modo **'Editor'**.
    """)
    st.stop()

# --- LOGIN Y FILTRO ---
st.sidebar.header("Acceso Gerentes")
sucursales = sorted(df["SUCURSAL"].unique())
sucursal_sel = st.sidebar.selectbox("Seleccione su Sucursal", sucursales)

# Definí acá las contraseñas para cada sucursal (podés agregar más)
claves = {
    "PERICO": "perico2026",
    "PLAZOLETA": "plazoleta2026",
    "AGUILARES": "aguilares2026"
}

password = st.sidebar.text_input("Contraseña", type="password")

if password == claves.get(sucursal_sel):
    st.success(f"Conectado a Sucursal: {sucursal_sel}")
    
    # Filtrar datos de la sucursal
    mask = df["SUCURSAL"] == sucursal_sel
    df_sucursal = df[mask].copy()

    # --- DEFINICIÓN DE TALLES ---
    talles_num = [str(i) for i in range(36, 64, 2)] # 36 al 62
    talles_letras = ["S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"]
    talles_camisas = [str(i) for i in range(38, 62, 2)] # 38 al 60

    st.write("### Planilla de Carga")
    st.caption("Elegí el talle en las celdas habilitadas. Al terminar, dale al botón de Guardar abajo.")

    # --- EDITOR DE DATOS ---
    # Solo permitimos editar las columnas de uniformes
    columnas_editables = [
        "PANTALON GRAFA", "CHOMBA MANGAS LARGAS", "CAMPERA HOMBRE", 
        "CAMISA HOMBRE", "CAMPERA MUJER", "CAMISA MUJER"
    ]

    edited_df = st.data_editor(
        df_sucursal,
        column_config={
            "PANTALON GRAFA": st.column_config.SelectboxColumn("Pantalón Grafa", options=talles_num),
            "CHOMBA MANGAS LARGAS": st.column_config.SelectboxColumn("Chomba M.L.", options=talles_letras),
            "CAMPERA HOMBRE": st.column_config.SelectboxColumn("Campera Hombre", options=talles_letras),
            "CAMISA HOMBRE": st.column_config.SelectboxColumn("Camisa Hombre", options=talles_camisas),
            "CAMPERA MUJER": st.column_config.SelectboxColumn("Campera Mujer", options=talles_letras),
            "CAMISA MUJER": st.column_config.SelectboxColumn("Camisa Mujer", options=talles_camisas),
            "LEGAJO": st.column_config.Column(disabled=True),
            "SUCURSAL": st.column_config.Column(disabled=True),
            "APELLIDO Y NOMBRE": st.column_config.Column(disabled=True),
            "POSICIÓN": st.column_config.Column(disabled=True),
            "CUIL": st.column_config.Column(disabled=True),
            "Ingreso": st.column_config.Column(disabled=True),
        },
        hide_index=True,
    )

    # --- BOTÓN DE GUARDAR ---
    if st.button("💾 GUARDAR CAMBIOS EN MAESTRO"):
        try:
            # Actualizamos el dataframe original con los cambios realizados
            df.loc[mask, :] = edited_df
            conn.update(worksheet="CASTILLO", data=df)
            st.balloons()
            st.success("¡Datos guardados exitosamente en el Google Sheet!")
        except Exception as e:
            st.error(f"Error al guardar: {e}")
            st.info("Asegurate de que el permiso en Google Sheets esté como 'Editor'.")

else:
    if password:
        st.error("Contraseña incorrecta")
    else:
        st.info("Ingrese su contraseña en la barra lateral para ver los colaboradores.")
