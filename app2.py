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

# Contraseña: nombre sucursal minúscula + 2026
pass_correcta = f"{sucursal_sel.lower().replace(' ', '')}2026"
password = st.sidebar.text_input("Contraseña", type="password")

if password == pass_correcta:
    st.success(f"Sesión iniciada: {sucursal_sel}")
    
    # Filtrar por sucursal
    df_sucursal = df[df["SUCURSAL"] == sucursal_sel].copy()

    # --- DEFINICIÓN DE OPCIONES ---
    t_num = [None] + [str(i) for i in range(36, 64, 2)]
    t_let = [None, "S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"]
    t_cam = [None] + [str(i) for i in range(38, 62, 2)]

    # --- LÓGICA DE BLOQUEO ---
    # Reemplazamos los que NO tienen "1" por un valor que indique que no pueden cargar
    prendas = ["PANTALON GRAFA", "CHOMBA MANGAS LARGAS", "CAMPERA HOMBRE", "CAMISA HOMBRE", "CAMPERA MUJER", "CAMISA MUJER"]
    
    for prenda in prendas:
        # Si la celda no tiene un 1 (o está vacía), la marcamos como "No habilitado"
        df_sucursal.loc[df_sucursal[prenda].astype(str) != "1", prenda] = "---"

    st.write(f"### Planilla de {sucursal_sel}")
    st.info("Solo se pueden completar los casilleros que estaban habilitados con un '1'.")

    # --- EDITOR DE TABLA ---
    edited_df = st.data_editor(
        df_sucursal[["APELLIDO Y NOMBRE"] + prendas],
        column_config={
            "APELLIDO Y NOMBRE": st.column_config.Column("Empleado", disabled=True),
            "PANTALON GRAFA": st.column_config.SelectboxColumn("PANTALÓN DE GRAFA", options=t_num),
            "CHOMBA MANGAS LARGAS": st.column_config.SelectboxColumn("CHOMBA MANGAS LARGAS", options=t_let),
            "CAMPERA HOMBRE": st.column_config.SelectboxColumn("CAMPERA HOMBRE", options=t_let),
            "CAMISA HOMBRE": st.column_config.SelectboxColumn("CAMISA HOMBRE", options=t_cam),
            "CAMPERA MUJER": st.column_config.SelectboxColumn("CAMPERA MUJER", options=t_let),
            "CAMISA MUJER": st.column_config.SelectboxColumn("CAMISA MUJER", options=t_cam),
        },
        hide_index=True,
    )

    if st.button("💾 GUARDAR CAMBIOS"):
        try:
            # Solo guardamos los valores que no son "---"
            for prenda in prendas:
                # Actualizamos en el DF original solo lo que cambió y es válido
                df.loc[df["SUCURSAL"] == sucursal_sel, prenda] = edited_df[prenda].values
            
            conn.update(data=df)
            st.balloons()
            st.success("¡Datos guardados! Los gerentes ya no pueden inventar pedidos.")
        except Exception as e:
            st.error(f"Error al guardar: {e}")
else:
    if password:
        st.error("Contraseña incorrecta")
