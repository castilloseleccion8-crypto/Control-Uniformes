import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Sistema de Uniformes", layout="wide")

st.title("👕 Carga de Talles - Gestión de Uniformes")

# --- CONEXIÓN MODIFICADA ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Quitamos el parámetro 'worksheet' de aquí para probar la conexión base primero
    full_df = conn.read(ttl=0) 
    
    # Intentamos filtrar la pestaña CASTILLO manualmente
    df = conn.read(worksheet="CASTILLO", ttl=0)
    
    df.columns = df.columns.str.strip()
    st.sidebar.success("✅ Conexión establecida")
    
except Exception as e:
    st.error("❌ Error de comunicación con Google Sheets")
    st.info(f"Detalle: {e}")
    st.stop()

# --- EL RESTO DEL CÓDIGO SIGUE IGUAL ---
sucursales = sorted(df["SUCURSAL"].unique())
sucursal_sel = st.sidebar.selectbox("Seleccione su Sucursal", sucursales)

claves = {
    "AGUILARES": "aguilares2026",
    "PERICO": "perico2026",
    "PLAZOLETA": "plazoleta2026"
}

password = st.sidebar.text_input("Contraseña", type="password")

if password == claves.get(sucursal_sel):
    st.success(f"Sucursal: {sucursal_sel}")
    mask = df["SUCURSAL"] == sucursal_sel
    df_sucursal = df[mask].copy()

    talles_num = [str(i) for i in range(36, 64, 2)]
    talles_letras = ["S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"]
    talles_camisas = [str(i) for i in range(38, 62, 2)]

    edited_df = st.data_editor(
        df_sucursal,
        column_config={
            "PANTALON GRAFA": st.column_config.SelectboxColumn("Pantalón", options=talles_num),
            "CHOMBA MANGAS LARGAS": st.column_config.SelectboxColumn("Chomba", options=talles_letras),
            "CAMPERA HOMBRE": st.column_config.SelectboxColumn("Camp. Hombre", options=talles_letras),
            "CAMISA HOMBRE": st.column_config.SelectboxColumn("Camisa Hombre", options=talles_camisas),
            "CAMPERA MUJER": st.column_config.SelectboxColumn("Camp. Mujer", options=talles_letras),
            "CAMISA MUJER": st.column_config.SelectboxColumn("Camisa Mujer", options=talles_camisas),
        },
        disabled=["LEGAJO", "SUCURSAL", "POSICIÓN", "Ingreso", "CUIL", "APELLIDO Y NOMBRE", "VALIDACION"],
        hide_index=True,
    )

    if st.button("💾 GUARDAR CAMBIOS"):
        df.loc[mask, :] = edited_df
        conn.update(worksheet="CASTILLO", data=df)
        st.success("Guardado correctamente")
else:
    st.info("Esperando contraseña...")
    if password:
        st.error("Contraseña incorrecta")
    else:
        st.info("Ingrese su contraseña en la barra lateral para ver los colaboradores.")
