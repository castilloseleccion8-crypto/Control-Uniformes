import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Sistema de Uniformes", layout="wide")

st.title("👕 Carga de Talles - Gestión de Uniformes")

# --- CONEXIÓN ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Leemos la planilla. Si tu pestaña se llama CASTILLO, la busca automáticamente
    df = conn.read(ttl=0)
    # Limpieza de nombres de columnas
    df.columns = [str(c).strip() for c in df.columns]
except Exception as e:
    st.error("❌ Error de conexión con Google Sheets")
    st.info(f"Detalle: {e}")
    st.stop()

# --- VALIDACIÓN DE DATOS ---
if "SUCURSAL" not in df.columns:
    st.error(f"No encontré la columna 'SUCURSAL'. Columnas actuales: {list(df.columns)}")
    st.stop()

# --- LOGIN Y FILTRO ---
sucursales = sorted(df["SUCURSAL"].dropna().unique())
sucursal_sel = st.sidebar.selectbox("Seleccione su Sucursal", sucursales)
password = st.sidebar.text_input("Contraseña", type="password")

# Claves de acceso
claves = {
    "AGUILARES": "aguilares2026",
    "PERICO": "perico2026",
    "PLAZOLETA": "plazoleta2026"
}

if password == claves.get(sucursal_sel):
    st.success(f"Conectado a {sucursal_sel}")
    
    mask = df["SUCURSAL"] == sucursal_sel
    df_sucursal = df[mask].copy()

    # Opciones de talles según tus imágenes
    t_num = [str(i) for i in range(36, 64, 2)]
    t_let = ["S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"]
    t_cam = [str(i) for i in range(38, 62, 2)]

    st.write("### Planilla de Colaboradores")
    
    # Editor de tabla
    edited_df = st.data_editor(
        df_sucursal,
        column_config={
            "PANTALON GRAFA": st.column_config.SelectboxColumn("Pantalón", options=t_num),
            "CHOMBA MANGAS LARGAS": st.column_config.SelectboxColumn("Chomba", options=t_let),
            "CAMPERA HOMBRE": st.column_config.SelectboxColumn("Camp. Hombre", options=t_let),
            "CAMISA HOMBRE": st.column_config.SelectboxColumn("Camisa Hombre", options=t_cam),
            "CAMPERA MUJER": st.column_config.SelectboxColumn("Camp. Mujer", options=t_let),
            "CAMISA MUJER": st.column_config.SelectboxColumn("Camisa Mujer", options=t_cam),
        },
        disabled=["LEGAJO", "SUCURSAL", "POSICIÓN", "APELLIDO Y NOMBRE", "CUIL", "Ingreso"],
        hide_index=True,
    )

    if st.button("💾 GUARDAR CAMBIOS"):
        try:
            # Sincronizamos los cambios del editor al dataframe principal
            df.loc[mask, :] = edited_df
            # Enviamos de vuelta a Google Sheets
            conn.update(data=df)
            st.balloons()
            st.success("¡Datos guardados exitosamente!")
        except Exception as e:
            st.error(f"Error al guardar: {e}")
            st.info("Asegurate de que el permiso en Google Sheets esté como 'Editor'.")
else:
    if password:
        st.error("Contraseña incorrecta")
    else:
        st.info("Introduzca la contraseña en el panel de la izquierda.")
