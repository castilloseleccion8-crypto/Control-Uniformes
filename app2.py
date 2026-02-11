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

    # --- TALLES REALES (SIN ELEGIR NI NO APLICA) ---
    t_num = ["36", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60", "62"]
    t_let = ["S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"]
    t_cam = ["38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60"]

    prendas = [
        "PANTALON GRAFA",
        "CHOMBA MANGAS LARGAS",
        "CAMPERA HOMBRE",
        "CAMISA HOMBRE",
        "CAMPERA MUJER",
        "CAMISA MUJER"
    ]

    # --- LIMPIEZA DE DATOS ---
    for prenda in prendas:
        df_sucursal[prenda] = (
            df_sucursal[prenda]
            .astype(str)
            .str.strip()
            .replace({"nan": "", "None": "", "0.0": "", "0": ""})
        )

    # --- PREPARACIÓN PARA VISUALIZACIÓN ---
    df_editor = df_sucursal[["APELLIDO Y NOMBRE"] + prendas].copy()

    # Creamos máscara de NO APLICA (celdas vacías reales)
    no_aplica_mask = {}

    for prenda in prendas:
        no_aplica_mask[prenda] = df_editor[prenda] == ""
        
        # Si tiene "1" lo dejamos vacío para que puedan elegir talle
        df_editor.loc[df_editor[prenda] == "1", prenda] = None
        
        # Si está vacío real → lo mostramos como texto fijo
        df_editor.loc[no_aplica_mask[prenda], prenda] = "NO APLICA"

    st.write(f"### Planilla de {sucursal_sel}")
    st.info("💡 Solo completá las celdas vacías. Si dice 'NO APLICA', no requiere esa prenda.")

    # --- CONFIGURACIÓN DE COLUMNAS ---
    column_config = {
        "APELLIDO Y NOMBRE": st.column_config.Column("Empleado", disabled=True),
    }

    for prenda in prendas:
        if "PANTALON" in prenda:
            opts = t_num
        elif "CAMISA" in prenda:
            opts = t_cam
        else:
            opts = t_let

        column_config[prenda] = st.column_config.SelectboxColumn(
            prenda.replace("PANTALON GRAFA", "PANTALÓN DE GRAFA"),
            options=opts,
            required=False
        )

    edited_df = st.data_editor(
        df_editor,
        column_config=column_config,
        hide_index=True,
        use_container_width=True
    )

    # --- GUARDAR ---
    if st.button("💾 GUARDAR CAMBIOS"):
        with st.spinner("Actualizando Maestro..."):
            try:
                for prenda in prendas:
                    nuevos_valores = edited_df[prenda].values
                    final_save = []

                    for i, val in enumerate(nuevos_valores):
                        if no_aplica_mask[prenda].iloc[i]:
                            final_save.append("")  # Sigue siendo NO APLICA
                        elif pd.isna(val):
                            final_save.append("1")  # No eligió talle
                        else:
                            final_save.append(val)  # Talle elegido
                    
                    df.loc[mask_sucursal, prenda] = final_save

                conn.update(data=df)
                st.balloons()
                st.success("✅ ¡Guardado con éxito! Los datos ya están en tu Google Sheet.")

            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")

else:
    if password:
        st.error("🔑 Contraseña incorrecta")
    else:
        st.info(f"Esperando contraseña de sucursal... (ej: {sucursal_sel.lower()}2026)")
