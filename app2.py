import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

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

    t_num = ["36", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60", "62"]
    t_let = ["S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"]
    t_cam = ["38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60"]

    prendas = ["PANTALON GRAFA", "CHOMBA MANGAS LARGAS", "CAMPERA HOMBRE", "CAMISA HOMBRE", "CAMPERA MUJER", "CAMISA MUJER"]

    # --- LIMPIEZA Y PREPARACIÓN ---
    for prenda in prendas:
        df_sucursal[prenda] = df_sucursal[prenda].astype(str).str.strip().replace({"nan": "", "None": "", "0.0": "", "0": ""})

    df_editor = df_sucursal[["APELLIDO Y NOMBRE"] + prendas].copy()
    no_aplica_mask = {}

    for prenda in prendas:
        no_aplica_mask[prenda] = df_editor[prenda] == ""
        df_editor.loc[df_editor[prenda] == "1", prenda] = None
        df_editor.loc[no_aplica_mask[prenda], prenda] = "NO APLICA"

    st.write(f"### Planilla de {sucursal_sel}")
    
    column_config = {"APELLIDO Y NOMBRE": st.column_config.Column("Empleado", disabled=True)}
    for prenda in prendas:
        opts = t_num if "PANTALON" in prenda else (t_cam if "CAMISA" in prenda else t_let)
        column_config[prenda] = st.column_config.SelectboxColumn(prenda.replace("PANTALON GRAFA", "PANTALÓN DE GRAFA"), options=opts)

    edited_df = st.data_editor(df_editor, column_config=column_config, hide_index=True, use_container_width=True)

    # --- GUARDAR CON ACUSE ---
    if st.button("💾 GUARDAR CAMBIOS Y GENERAR ACUSE"):
        with st.spinner("Procesando y registrando evidencia..."):
            try:
                cambios_realizados = []
                for prenda in prendas:
                    nuevos_valores = edited_df[prenda].values
                    final_save = []

                    for i, val in enumerate(nuevos_valores):
                        empleado = edited_df.iloc[i]["APELLIDO Y NOMBRE"]
                        
                        if no_aplica_mask[prenda].iloc[i]:
                            final_save.append("")
                        elif pd.isna(val):
                            final_save.append("1")
                        else:
                            final_save.append(val)
                            # Si es un talle real, lo anotamos para el acuse
                            cambios_realizados.append(f"{empleado}: {prenda} -> {val}")
                    
                    df.loc[mask_sucursal, prenda] = final_save

                # 1. Actualizar Maestro
                conn.update(data=df)

                # 2. Generar Acuse Visual
                ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                st.balloons()
                st.success(f"✅ ¡Datos guardados exitosamente!")
                
                # --- DISEÑO DEL TICKET ---
                st.markdown(f"""
                <div style="border: 2px solid #000; padding: 20px; border-radius: 10px; background-color: #f9f9f9; color: #000">
                    <h2 style="text-align: center;">📄 ACUSE DE RECIBO - UNIFORMES</h2>
                    <p><strong>Sucursal:</strong> {sucursal_sel}</p>
                    <p><strong>Fecha y Hora:</strong> {ahora}</p>
                    <hr>
                    <p><strong>Detalle de carga:</strong></p>
                    <ul>
                        {"".join([f"<li>{item}</li>" for item in cambios_realizados if "->" in item])}
                    </ul>
                    <hr>
                    <p style="font-size: 0.8em; text-align: center;">Este documento sirve como comprobante de carga. <br> 
                    ID de Transacción: {hash(ahora)}</p>
                </div>
                """, unsafe_allow_html=True)

                st.info("⬆️ **Tomá una captura de pantalla de este recuadro como comprobante.**")

            except Exception as e:
                st.error(f"❌ Error: {e}")

else:
    if password: st.error("🔑 Contraseña incorrecta")
    else: st.info(f"Esperando contraseña de {sucursal_sel}...")
