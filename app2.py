import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Sistema de Uniformes", layout="wide")

st.title("👕 Carga de Talles - Gestión de Uniformes")

# --- CONEXIÓN ---
try:
    # Usamos la conexión oficial pero con manejo de errores manual
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Intentamos leer la planilla. Si no ponemos 'worksheet', lee la primera.
    df = conn.read(ttl=0)
    
    # Limpiamos los nombres de las columnas (sacamos espacios locos)
    df.columns = [str(c).strip() for c in df.columns]
    
except Exception as e:
    st.error("❌ Google Sheets rechazó la conexión.")
    st.info(f"Detalle del error: {e}")
    st.warning("REVISÁ ESTO: ¿El archivo está compartido como 'Cualquier persona con el enlace' y 'Editor'?")
    st.stop()

# --- VERIFICACIÓN DE COLUMNA ---
if "SUCURSAL" not in df.columns:
    st.error(f"❌ No encontré la columna 'SUCURSAL'. Columnas detectadas: {list(df.columns)}")
    st.stop()

# --- LOGIN Y FILTRO ---
sucursales = sorted(df["SUCURSAL"].dropna().unique())
sucursal_sel = st.sidebar.selectbox("Seleccione su Sucursal", sucursales)
password = st.sidebar.text_input("Contraseña", type="password")

# Diccionario de claves
claves = {
    "AGUILARES": "aguilares2026",
    "PERICO": "perico2026",
    "PLAZOLETA": "plazoleta2026"
}

if password == claves.get(sucursal_sel):
    st.success(f"Conectado a {sucursal_sel}")
    
    mask = df["SUCURSAL"] == sucursal_sel
    df_sucursal = df[mask].copy()

    # Configuración de talles
    t_num = [str(i) for i in range(36, 64, 2)]
    t_let = ["S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"]
    t_cam = [str(i) for i in range(38, 62, 2)]

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
        disabled=["LEGAJO", "SUCURSAL", "POSICIÓN", "APELLIDO Y NOMBRE"],
        hide_index=True,
    )

    if st.button("💾 GUARDAR CAMBIOS"):
        try:
            df.loc[mask, :] = edited_df
            conn.update(data=df)
            st.balloons()
            st.success("¡Guardado correctamente en el Maestro!")
        except Exception as e:
            st.error(f"Error al guardar: {e}")
else:
    st.info("Por favor, ingrese la contraseña en la barra lateral.")
            st.info("Intentando guardar... si aparece error de credenciales, te daré el paso final para habilitar la escritura.")
            # Aquí iría el conn.update si la conexión base funciona
    else:
        st.info("Ingresá la contraseña para ver los datos.")
