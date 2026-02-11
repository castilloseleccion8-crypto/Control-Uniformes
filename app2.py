import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Gestión de Uniformes", layout="wide")

st.title("👕 Carga de Talles - Gestión de Uniformes")

# --- CONEXIÓN ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0)
    df.columns = [str(c).strip() for c in df.columns]
except Exception as e:
    st.error(f"❌ Error de conexión: {e}")
    st.stop()

# --- LOGIN AUTOMÁTICO ---
st.sidebar.header("Acceso Sucursales")
sucursales = sorted(df["SUCURSAL"].dropna().unique())
sucursal_sel = st.sidebar.selectbox("Seleccione su Sucursal", sucursales)

# La contraseña es el nombre en minúscula + 2026 (ej: aguilares2026)
pass_correcta = f"{sucursal_sel.lower().replace(' ', '')}2026"
password = st.sidebar.text_input("Contraseña", type="password")

if password == pass_correcta:
    st.success(f"Sesión iniciada: {sucursal_sel}")
    
    # Filtrar por sucursal
    df_sucursal = df[df["SUCURSAL"] == sucursal_sel].copy()

    # --- DEFINICIÓN DE TALLES ---
    t_num = [str(i) for i in range(36, 64, 2)] # 36 al 62
    t_let = ["S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"] #
    t_cam = [str(i) for i in range(38, 62, 2)] # 38 al 60

    # --- TABLA SIMPLIFICADA ---
    # Solo mostramos el Nombre y las prendas
    columnas_visibles = [
        "APELLIDO Y NOMBRE", "PANTALON GRAFA", "CHOMBA MANGAS LARGAS", 
        "CAMPERA HOMBRE", "CAMISA HOMBRE", "CAMPERA MUJER", "CAMISA MUJER"
    ]
    
    st.write(f"### Colaboradores de {sucursal_sel}")
    st.caption("Complete los talles en las celdas habilitadas.")

    edited_df = st.data_editor(
        df_sucursal[columnas_visibles], # Aquí hacemos que vea SOLO lo que pediste
        column_config={
            "APELLIDO Y NOMBRE": st.column_config.Column("Empleado", disabled=True),
            "PANTALON GRAFA": st.column_config.SelectboxColumn("Pantalón", options=t_num),
            "CHOMBA MANGAS LARGAS": st.column_config.SelectboxColumn("Chomba", options=t_let),
            "CAMPERA HOMBRE": st.column_config.SelectboxColumn("Camp. Hombre", options=t_let),
            "CAMISA HOMBRE": st.column_config.SelectboxColumn("Camisa Hombre", options=t_cam),
            "CAMPERA MUJER": st.column_config.SelectboxColumn("Camp. Mujer", options=t_let),
            "CAMISA MUJER": st.column_config.SelectboxColumn("Camisa Mujer", options=t_cam),
        },
        hide_index=True,
    )

    if st.button("💾 GUARDAR CAMBIOS"):
        try:
            # Sincronizamos los cambios de vuelta al archivo maestro
            for col in columnas_visibles:
                if col != "APELLIDO Y NOMBRE":
                    df.loc[df["SUCURSAL"] == sucursal_sel, col] = edited_df[col].values
            
            conn.update(data=df)
            st.balloons()
            st.success("¡Planilla actualizada!")
        except Exception as e:
            st.error(f"Error al guardar: {e}")
else:
    if password:
        st.error("Contraseña incorrecta")
    else:
        st.info(f" ")
