import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Gestión de Uniformes", layout="wide")

st.title("Carga de Talles - Gestión de Uniformes")

# --- CONEXIÓN ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Leemos la planilla (usa la Service Account de tus Secrets)
    df = conn.read(ttl=0)
    # Limpieza de nombres de columnas por si hay espacios
    df.columns = [str(c).strip() for c in df.columns]
except Exception as e:
    st.error(f"❌ Error de conexión: {e}")
    st.stop()

# --- LOGIN AUTOMÁTICO ---
st.sidebar.header("Acceso Sucursales")
if "SUCURSAL" in df.columns:
    sucursales = sorted(df["SUCURSAL"].dropna().unique())
    sucursal_sel = st.sidebar.selectbox("Seleccione su Sucursal", sucursales)
else:
    st.error("No se encontró la columna 'SUCURSAL' en la planilla.")
    st.stop()

# La contraseña es el nombre de la sucursal en minúscula + 2026
pass_correcta = f"{sucursal_sel.lower().replace(' ', '')}2026"
password = st.sidebar.text_input("Contraseña", type="password")

if password == pass_correcta:
    st.success(f"Sesión iniciada: {sucursal_sel}")
    
    # Filtrar datos de la sucursal elegida
    mask_sucursal = df["SUCURSAL"] == sucursal_sel
    df_sucursal = df[mask_sucursal].copy()

    # --- DEFINICIÓN DE OPCIONES DE TALLES ---
    # Agregamos None al principio para que puedan dejar en blanco si se equivocan
    t_num = [None] + [str(i) for i in range(36, 64, 2)]
    t_let = [None, "S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"]
    t_cam = [None] + [str(i) for i in range(38, 62, 2)]

    # Prendas a gestionar
    prendas = [
        "PANTALON GRAFA", "CHOMBA MANGAS LARGAS", "CAMPERA HOMBRE", 
        "CAMISA HOMBRE", "CAMPERA MUJER", "CAMISA MUJER"
    ]

    # --- LÓGICA DE BLOQUEO DINÁMICO ---
    # Si la celda no tiene un "1", la convertimos en un valor fijo que no se pueda editar con talle
    for prenda in prendas:
        # Solo permitimos editar si el valor original es "1" o ya tiene un talle cargado
        # Si está vacío o tiene otro valor, se bloquea con "---"
        df_sucursal.loc[df_sucursal[prenda].astype(str).isin(['', 'nan', 'None', '0']), prenda] = "---"

    st.write(f"### Planilla de {sucursal_sel}")

    # --- DATA EDITOR MEJORADO ---
    # Configuramos los nombres visuales y los selectores
    config_visual = {
        "APELLIDO Y NOMBRE": st.column_config.Column("Empleado", disabled=True),
        "PANTALON GRAFA": st.column_config.SelectboxColumn("PANTALÓN DE GRAFA", options=t_num),
        "CHOMBA MANGAS LARGAS": st.column_config.SelectboxColumn("CHOMBA MANGAS LARGAS", options=t_let),
        "CAMPERA HOMBRE": st.column_config.SelectboxColumn("CAMPERA HOMBRE", options=t_let),
        "CAMISA HOMBRE": st.column_config.SelectboxColumn("CAMISA HOMBRE", options=t_cam),
        "CAMPERA MUJER": st.column_config.SelectboxColumn("CAMPERA MUJER", options=t_let),
        "CAMISA MUJER": st.column_config.SelectboxColumn("CAMISA MUJER", options=t_cam),
    }

    # El editor solo muestra el nombre y las prendas
    columnas_a_mostrar = ["APELLIDO Y NOMBRE"] + prendas
    
    edited_df = st.data_editor(
        df_sucursal[columnas_a_mostrar],
        column_config=config_visual,
        hide_index=True,
        use_container_width=True
    )

    # --- BOTÓN GUARDAR ---
    if st.button("💾 GUARDAR CAMBIOS"):
        with st.spinner("Guardando en Google Sheets..."):
            try:
                # Volcamos los cambios del editor al dataframe original 'df'
                for prenda in prendas:
                    # Solo actualizamos las filas de la sucursal actual
                    df.loc[mask_sucursal, prenda] = edited_df[prenda].values
                
                # Limpiamos los "---" antes de guardar para que el Excel quede prolijo
                for prenda in prendas:
                    df[prenda] = df[prenda].replace("---", "")

                # Enviamos la actualización
                conn.update(data=df)
                st.balloons()
                st.success("✅ ¡Cambios guardados con éxito en el Maestro!")
            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")
                st.info("Revisá que hayas compartido el Excel con el mail del 'Service Account' como Editor.")

else:
    if password:
        st.error("🔑 Contraseña incorrecta")
    else:
        st.info("Introduzca la contraseña de sucursal para ver los colaboradores.")
