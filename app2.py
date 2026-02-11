import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Gestión de Uniformes", layout="wide")

st.title("Carga de Talles - Gestión de Uniformes")

# --- CONEXIÓN ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0)
    df.columns = [str(c).strip() for c in df.columns]
except Exception as e:
    st.error(f"❌ Error de conexión: {e}")
    st.stop()

# --- LOGIN ---
st.sidebar.header("Acceso Sucursales")
sucursales = sorted(df["SUCURSAL"].dropna().unique())
sucursal_sel = st.sidebar.selectbox("Seleccione su Sucursal", sucursales)

pass_correcta = f"{sucursal_sel.lower().replace(' ', '')}2026"
password = st.sidebar.text_input("Contraseña", type="password")

if password == pass_correcta:
    st.success(f"Sesión iniciada: {sucursal_sel}")
    
    mask_sucursal = df["SUCURSAL"] == sucursal_sel
    df_sucursal = df[mask_sucursal].copy()

    # --- LISTAS DE TALLES ---
    t_num = [str(i) for i in range(36, 64, 2)]
    t_let = ["S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"]
    t_cam = [str(i) for i in range(38, 62, 2)]

    prendas = ["PANTALON GRAFA", "CHOMBA MANGAS LARGAS", "CAMPERA HOMBRE", "CAMISA HOMBRE", "CAMPERA MUJER", "CAMISA MUJER"]

    # --- PROCESAMIENTO DE DATOS ---
    for prenda in prendas:
        # Limpiamos los datos
        df_sucursal[prenda] = df_sucursal[prenda].astype(str).str.strip().replace({'nan': '', 'None': '', '0.0': '', '0': ''})
        
        # Si NO es un pedido (celda vacía), le ponemos el texto fijo
        df_sucursal.loc[df_sucursal[prenda] == "", prenda] = "🚫 NO APLICA"
        # Si ES un pedido (valor 1), lo dejamos vacío para que elijan
        df_sucursal.loc[df_sucursal[prenda] == "1", prenda] = None

    st.write(f"### Planilla de {sucursal_sel}")
    st.info("💡 Solo podés elegir talles en las celdas que NO dicen '🚫 NO APLICA'.")

    # --- CONFIGURACIÓN DEL EDITOR ---
    config_visual = {
        "APELLIDO Y NOMBRE": st.column_config.Column("Empleado", disabled=True),
    }

    for prenda in prendas:
        # Definir qué lista de talles usar
        if "PANTALON" in prenda: opts = t_num
        elif "CAMISA" in prenda: opts = t_cam
        else: opts = t_let
        
        # Agregamos "🚫 NO APLICA" como una opción válida para evitar el TypeError
        # pero el gerente sabrá que no debe tocarla.
        config_visual[prenda] = st.column_config.SelectboxColumn(
            prenda.replace("PANTALON GRAFA", "PANTALÓN DE GRAFA"),
            options=["🚫 NO APLICA"] + opts,
            width="medium"
        )

    # El editor muestra el nombre y las prendas
    edited_df = st.data_editor(
        df_sucursal[["APELLIDO Y NOMBRE"] + prendas],
        column_config=config_visual,
        hide_index=True,
        use_container_width=True
    )

    # --- BOTÓN GUARDAR ---
    if st.button("💾 GUARDAR CAMBIOS"):
        with st.spinner("Actualizando Maestro..."):
            try:
                for prenda in prendas:
                    nuevos_valores = edited_df[prenda].values
                    final_save = []
                    
                    for i, val in enumerate(nuevos_valores):
                        # Si quedó en None (era un pedido y no eligieron talle)
                        if pd.isna(val) or val == "None" or val == "":
                            final_save.append("1")
                        # Si dice No Aplica, guardamos vacío
                        elif val == "🚫 NO APLICA":
                            final_save.append("")
                        # Si eligieron un talle real, lo guardamos
                        else:
                            final_save.append(val)
                    
                    df.loc[mask_sucursal, prenda] = final_save

                conn.update(data=df)
                st.balloons()
                st.success("✅ Datos guardados correctamente en Google Sheets.")
            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")
else:
    if password: st.error("🔑 Contraseña incorrecta")
    else: st.info("Introduzca la contraseña de la sucursal.")
