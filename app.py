import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Gestión de Uniformes", layout="wide")

st.title("👕 Carga de Talles por Sucursal")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Leer los datos (ajusta el nombre de tu hoja)
df = conn.read(worksheet="Hoja1")

# 1. Login simple
sucursales = df["SUCURSAL"].unique()
sucursal_sel = st.sidebar.selectbox("Seleccione su Sucursal", sucursales)
password = st.sidebar.text_input("Contraseña de Sucursal", type="password")

# Diccionario simple de claves (puedes ampliarlo)
claves = {"AGUILARES": "aguilares2026", "PERICO": "perico2026"}

if password == claves.get(sucursal_sel):
    st.success(f"Acceso concedido a sucursal: {sucursal_sel}")
    
    # Filtrar solo los colaboradores de esa sucursal
    df_filtrado = df[df["SUCURSAL"] == sucursal_sel].copy()
    
    # Definir opciones de talles
    talles_num = [str(i) for i in range(36, 64, 2)] # 36 al 62
    talles_letras = ["S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"]
    camisas_num = [str(i) for i in range(38, 62, 2)] # 38 al 60

    st.write("### Complete los talles donde corresponda:")
    st.info("Solo se permite editar las celdas habilitadas con talles.")

    # Configurar el editor de tabla
    # Hacemos que solo las columnas de prendas sean editables con sus talles específicos
    edited_df = st.data_editor(
        df_filtrado,
        column_config={
            "PANTALON GRAFA": st.column_config.SelectboxColumn("Pantalón", options=talles_num),
            "CHOMBA MANGAS LARGAS": st.column_config.SelectboxColumn("Chomba", options=talles_letras),
            "CAMPERA HOMBRE": st.column_config.SelectboxColumn("Camp. Hombre", options=talles_letras),
            "CAMISA HOMBRE": st.column_config.SelectboxColumn("Camisa Hombre", options=camisas_num),
            "CAMPERA MUJER": st.column_config.SelectboxColumn("Camp. Mujer", options=talles_letras),
            "CAMISA MUJER": st.column_config.SelectboxColumn("Camisa Mujer", options=camisas_num),
            "LEGAJO": st.column_config.Column(disabled=True),
            "APELLIDO Y NOMBRE": st.column_config.Column(disabled=True),
            "SUCURSAL": st.column_config.Column(disabled=True),
        },
        disabled=["LEGAJO", "SUCURSAL", "POSICIÓN", "Ingreso", "CUIL", "APELLIDO Y NOMBRE"],
        hide_index=True,
    )

    if st.button("💾 Guardar Cambios en Maestro"):
        # Aquí actualizamos el DataFrame original con los datos editados
        df.update(edited_df)
        conn.update(worksheet="Hoja1", data=df)
        st.balloons()
        st.success("¡Datos actualizados correctamente en el archivo maestro!")

else:
    st.warning("Por favor, ingrese la sucursal y contraseña correcta.")
