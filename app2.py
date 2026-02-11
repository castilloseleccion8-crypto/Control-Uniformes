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
    # La primera opción es el texto instructivo
    t_num = ["👉 ELEGIR TALLE"] + [str(i) for i in range(36, 64, 2)]
    t_let = ["👉 ELEGIR TALLE", "S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"]
    t_cam = ["👉 ELEGIR TALLE"] + [str(i) for i in range(38, 62, 2)]

    prendas = ["PANTALON GRAFA", "CHOMBA MANGAS LARGAS", "CAMPERA HOMBRE", "CAMISA HOMBRE", "CAMPERA MUJER", "CAMISA MUJER"]

    # --- PREPARACIÓN DE VISTA (TEXTOS CLAROS) ---
    for prenda in prendas:
        # Convertimos a string para comparar
        df_sucursal[prenda] = df_sucursal[prenda].astype(str).replace({'nan': '', 'None': '', '0': ''})
        
        # Si es un "1", ponemos el mensaje de elegir
        df_sucursal.loc[df_sucursal[prenda] == "1", prenda] = "👉 ELEGIR TALLE"
        
        # Si está vacío, ponemos que no aplica
        df_sucursal.loc[df_sucursal[prenda] == "", prenda] = "🚫 NO APLICA"

    st.write(f"### Planilla de {sucursal_sel}")
    st.info("Solo debés cambiar las celdas que dicen **'👉 ELEGIR TALLE'**. Si dice **'🚫 NO APLICA'**, no toques nada.")

    # --- DATA EDITOR ---
    config_visual = {
        "APELLIDO Y NOMBRE": st.column_config.Column("Empleado", disabled=True),
    }

    for prenda in prendas:
        if "PANTALON" in prenda:
            opts = t_num
        elif "CAMISA" in prenda:
            opts = t_cam
        else:
            opts = t_let
            
        config_visual[prenda] = st.column_config.SelectboxColumn(
            prenda.replace("PANTALON GRAFA", "PANTALÓN DE GRAFA"), 
            options=opts,
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
                    # Obtenemos los valores del editor
                    nuevos_valores = edited_df[prenda].values
                    
                    # Limpiamos los textos de ayuda antes de mandar a Google Sheets
                    # '👉 ELEGIR TALLE' vuelve a ser '1' (para que no se borre el pedido)
                    # '🚫 NO APLICA' vuelve a ser vacio
                    final_save = []
                    for val in nuevos_valores:
                        if val == "👉 ELEGIR TALLE":
                            final_save.append("1")
                        elif val == "🚫 NO APLICA":
                            final_save.append("")
                        else:
                            final_save.append(val)
                    
                    df.loc[mask_sucursal, prenda] = final_save

                conn.update(data=df)
                st.balloons()
                st.success("✅ Guardado correctamente. Podés cerrar la página.")
            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")
else:
    if password: st.error("🔑 Contraseña incorrecta")
    else: st.info("Ingrese contraseña (ej: aguilares2026)")
    else:
        st.info("Introduzca la contraseña de sucursal para ver los colaboradores.")
