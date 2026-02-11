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

    # --- OPCIONES DE TALLES ---
    # Ponemos el texto de instrucción como primera opción
    t_num = ["👉 ELEGIR", "36", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60", "62"]
    t_let = ["👉 ELEGIR", "S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"]
    t_cam = ["👉 ELEGIR", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60"]

    prendas = ["PANTALON GRAFA", "CHOMBA MANGAS LARGAS", "CAMPERA HOMBRE", "CAMISA HOMBRE", "CAMPERA MUJER", "CAMISA MUJER"]

    # --- LÓGICA DE VISUALIZACIÓN (REFORZADA) ---
    for prenda in prendas:
        # Convertimos todo a string y limpiamos espacios
        df_sucursal[prenda] = df_sucursal[prenda].astype(str).str.strip().replace({'nan': '', 'None': '', '0.0': '', '0': ''})
        
        # Si la celda tiene un "1", "1.0" o está marcada como pedido, ponemos ELEGIR
        # Si ya tiene un talle (ej: "44"), dejamos el talle
        def transformar_vista(valor):
            if valor in ["1", "1.0"]:
                return "👉 ELEGIR"
            elif valor == "":
                return "🚫 NO APLICA"
            return valor # Si ya tiene un talle, lo mantiene

        df_sucursal[prenda] = df_sucursal[prenda].apply(transformar_vista)

    st.write(f"### Planilla de {sucursal_sel}")
    st.info("💡 Solo debés completar donde dice **'👉 ELEGIR'**. Si dice **'🚫 NO APLICA'**, ese empleado no requiere esa prenda.")

    # --- DATA EDITOR ---
    config_visual = {
        "APELLIDO Y NOMBRE": st.column_config.Column("Empleado", disabled=True),
    }

    for prenda in prendas:
        # Asignamos las opciones correctas según el tipo de prenda
        if "PANTALON" in prenda:
            opts = t_num
        elif "CAMISA" in prenda:
            opts = t_cam
        else:
            opts = t_let
            
        # Agregamos "🚫 NO APLICA" a las opciones por si quieren corregir
        config_visual[prenda] = st.column_config.SelectboxColumn(
            prenda.replace("PANTALON GRAFA", "PANTALÓN DE GRAFA"), 
            options=["🚫 NO APLICA"] + opts,
            width="medium"
        )

    edited_df = st.data_editor(
        df_sucursal[["APELLIDO Y NOMBRE"] + prendas],
        column_config=config_visual,
        hide_index=True,
        use_container_width=True
    )

    if st.button("💾 GUARDAR CAMBIOS"):
        with st.spinner("Actualizando Maestro..."):
            try:
                for prenda in prendas:
                    nuevos_valores = edited_df[prenda].values
                    final_save = []
                    for val in nuevos_valores:
                        if val == "👉 ELEGIR":
                            final_save.append("1") # Mantenemos el 1 si no eligieron talle
                        elif val == "🚫 NO APLICA":
                            final_save.append("") # Guardamos vacío en el Excel
                        else:
                            final_save.append(val) # Guardamos el talle elegido
                    
                    df.loc[mask_sucursal, prenda] = final_save

                conn.update(data=df)
                st.balloons()
                st.success("✅ ¡Guardado con éxito!")
            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")
else:
    if password:
        st.error("🔑 Contraseña incorrecta")
    else:
        st.info(f"Esperando contraseña de sucursal... (ej: {sucursal_sel.lower()}2026)")
