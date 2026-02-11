import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="Gestión de Uniformes", layout="wide")

# --- FUNCIÓN PARA GENERAR PDF CORREGIDA ---
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
    
    # Filas (Limpiando emojis para el PDF)
    pdf.set_font("Arial", "", 7)
    for row in datos_tabla:
        for i, val in enumerate(row):
            texto = str(val)
            # Quitamos emojis para que no de error la fuente del PDF
            texto = texto.replace("🚫 ", "").replace("👉 ", "")
            if texto == "None" or texto == "nan": texto = ""
            pdf.cell(widths[i], 7, texto, border=1, align="C")
        pdf.ln()
    
    pdf.ln(10)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(190, 10, "Este documento sirve como comprobante oficial de la carga realizada.", align="C")
    
    # Retornamos como bytes (soluciona el error de bytearray)
    return bytes(pdf.output())

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
    
    # --- PREPARACIÓN VISUAL (Para que aparezca preseleccionado) ---
    for prenda in prendas:
        # Limpieza de datos
        df_sucursal[prenda] = df_sucursal[prenda].astype(str).str.strip().replace({"nan": "", "None": "", "0.0": "", "0": ""})
        
        # Lógica de preselección:
        # 1. Si está vacío -> NO APLICA
        # 2. Si tiene un "1" -> 👉 ELEGIR TALLE
        # 3. Si tiene cualquier otra cosa -> Mantiene el talle que ya tenía
        def transformar(x):
            if x == "" or x == "nan": return "🚫 NO APLICA"
            if x == "1": return "👉 ELEGIR TALLE"
            return x
        
        df_sucursal[prenda] = df_sucursal[prenda].apply(transformar)

    df_editor = df_sucursal[["APELLIDO Y NOMBRE"] + prendas].copy()

    # --- CONFIGURACIÓN DE TALLES ---
    t_num = ["👉 ELEGIR TALLE", "36", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60", "62"]
    t_let = ["👉 ELEGIR TALLE", "S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"]
    t_cam = ["👉 ELEGIR TALLE", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60"]

    column_config = {"APELLIDO Y NOMBRE": st.column_config.Column("Empleado", disabled=True)}
    for prenda in prendas:
        if "PANTALON" in prenda: opts = t_num
        elif "CAMISA" in prenda: opts = t_cam
        else: opts = t_let
        
        # Agregamos NO APLICA a las opciones para que sea compatible
        column_config[prenda] = st.column_config.SelectboxColumn(
            prenda.replace("PANTALON GRAFA", "PANTALÓN"), 
            options=["🚫 NO APLICA"] + opts
        )

    st.write(f"### Planilla de {sucursal_sel}")
    edited_df = st.data_editor(df_editor, column_config=column_config, hide_index=True, use_container_width=True)

    # --- GUARDADO Y PDF ---
    if st.button("💾 GUARDAR Y GENERAR PDF"):
        with st.spinner("Guardando y preparando PDF..."):
            try:
                for prenda in prendas:
                    nuevos_valores = edited_df[prenda].values
                    final_save = []
                    for val in nuevos_valores:
                        if val == "🚫 NO APLICA": final_save.append("")
                        elif val == "👉 ELEGIR TALLE": final_save.append("1")
                        else: final_save.append(val)
                    df.loc[mask_sucursal, prenda] = final_save

                conn.update(data=df)
                
                # Generar PDF
                filas_pdf = edited_df.values.tolist()
                ahora = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                pdf_bytes = generar_pdf(sucursal_sel, ahora, filas_pdf)
                
                st.balloons()
                st.success("✅ ¡Guardado con éxito!")
                
                st.download_button(
                    label="📥 DESCARGAR ACUSE EN PDF",
                    data=pdf_bytes,
                    file_name=f"Acuse_{sucursal_sel}_{ahora.replace(':','-')}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"❌ Error: {e}")
else:
    if password: st.error("🔑 Contraseña incorrecta")
    else: st.info(f"Ingrese clave de {sucursal_sel}")
