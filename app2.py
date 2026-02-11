import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="Gestión de Uniformes", layout="wide")

# --- FUNCIÓN PARA GENERAR PDF ---
def generar_pdf(sucursal, fecha, datos_tabla):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "ACUSE DE RECIBO - CARGA DE TALLES", ln=True, align="C")
    
    pdf.set_font("Arial", "", 10)
    pdf.ln(5)
    pdf.cell(190, 7, f"Sucursal: {sucursal}", ln=True)
    pdf.cell(190, 7, f"Fecha de Operación: {fecha}", ln=True)
    pdf.ln(10)
    
    # Encabezados
    pdf.set_fill_color(200, 200, 200)
    pdf.set_font("Arial", "B", 8)
    cols = ["Empleado", "Pantalon", "Chomba", "Camp.H", "Cam.H", "Camp.M", "Cam.M"]
    widths = [60, 22, 22, 22, 22, 22, 22]
    
    for i, col in enumerate(cols):
        pdf.cell(widths[i], 7, col, border=1, fill=True, align="C")
    pdf.ln()
    
    # Filas (Limpiando emojis para evitar el error)
    pdf.set_font("Arial", "", 7)
    for row in datos_tabla:
        for i, val in enumerate(row):
            # Limpiamos los emojis solo para el PDF
            texto = str(val)
            texto = texto.replace("🚫 ", "").replace("👉 ", "")
            
            if val == "🚫 NO APLICA":
                texto = "NO APLICA"
            elif val == "👉 ELEGIR TALLE":
                texto = "PENDIENTE"
                
            pdf.cell(widths[i], 7, texto, border=1, align="C")
        pdf.ln()
    
    pdf.ln(10)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(190, 10, "Este documento sirve como comprobante oficial de la carga realizada.", align="C")
    
    return pdf.output()
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

    prendas = ["PANTALON GRAFA", "CHOMBA MANGAS LARGAS", "CAMPERA HOMBRE", "CAMISA HOMBRE", "CAMPERA MUJER", "CAMISA MUJER"]
    
    # Limpieza inicial
    for prenda in prendas:
        df_sucursal[prenda] = df_sucursal[prenda].astype(str).str.strip().replace({"nan": "", "None": "", "0.0": "", "0": ""})

    # --- PREPARACIÓN VISUAL ---
    df_editor = df_sucursal[["APELLIDO Y NOMBRE"] + prendas].copy()
    no_aplica_mask = {}

    for prenda in prendas:
        no_aplica_mask[prenda] = df_editor[prenda] == ""
        df_editor.loc[df_editor[prenda] == "1", prenda] = "👉 ELEGIR TALLE"
        df_editor.loc[no_aplica_mask[prenda], prenda] = "🚫 NO APLICA"

    st.write(f"### Planilla de {sucursal_sel}")
    
    # Configuración de talles
    t_num = ["👉 ELEGIR TALLE", "36", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60", "62"]
    t_let = ["👉 ELEGIR TALLE", "S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"]
    t_cam = ["👉 ELEGIR TALLE", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60"]

    column_config = {"APELLIDO Y NOMBRE": st.column_config.Column("Empleado", disabled=True)}
    for prenda in prendas:
        opts = t_num if "PANTALON" in prenda else (t_cam if "CAMISA" in prenda else t_let)
        column_config[prenda] = st.column_config.SelectboxColumn(prenda.replace("PANTALON GRAFA", "PANTALÓN"), options=["🚫 NO APLICA"] + opts)

    edited_df = st.data_editor(df_editor, column_config=column_config, hide_index=True, use_container_width=True)

    # --- GUARDADO Y PDF ---
    if st.button("💾 GUARDAR Y GENERAR PDF"):
        with st.spinner("Guardando y preparando PDF..."):
            try:
                # Procesar datos para guardar en Excel
                for prenda in prendas:
                    nuevos_valores = edited_df[prenda].values
                    final_save = []
                    for i, val in enumerate(nuevos_valores):
                        if val == "🚫 NO APLICA": final_save.append("")
                        elif val == "👉 ELEGIR TALLE": final_save.append("1")
                        else: final_save.append(val)
                    df.loc[mask_sucursal, prenda] = final_save

                conn.update(data=df)
                
                # Preparar datos para la tabla del PDF
                filas_pdf = edited_df.values.tolist()
                ahora = datetime.now().strftime("%d-%m-%Y_%H-%M")
                
                pdf_bytes = generar_pdf(sucursal_sel, ahora.replace("_", " "), filas_pdf)
                
                st.balloons()
                st.success("✅ ¡Guardado! Descargá tu comprobante aquí abajo:")
                
                st.download_button(
                    label="📥 DESCARGAR ACUSE EN PDF",
                    data=pdf_bytes,
                    file_name=f"Acuse_{sucursal_sel}_{ahora}.pdf",
                    mime="application/pdf"
                )

            except Exception as e:
                st.error(f"❌ Error: {e}")
else:
    if password: st.error("🔑 Contraseña incorrecta")
    else: st.info(f"Ingrese clave de {sucursal_sel}")
