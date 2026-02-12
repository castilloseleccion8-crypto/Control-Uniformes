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
    
    # Encabezados de tabla
    cols = ["Empleado", "Pantalon", "Chomba", "Camp.H", "Cam.H", "Camp.M", "Cam.M"]
    widths = [60, 22, 22, 22, 22, 22, 22]
    
    pdf.set_fill_color(200, 200, 200)
    pdf.set_font("Arial", "B", 8)
    for i, col in enumerate(cols):
        pdf.cell(widths[i], 7, col, border=1, fill=True, align="C")
    pdf.ln()
    
    # Filas de la tabla (sin emojis)
    pdf.set_font("Arial", "", 7)
    for row in datos_tabla:
        for i, val in enumerate(row):
            texto = str(val).replace("🚫 ", "").replace("👉 ", "")
            if texto in ["None", "nan", "1", "1.0"]: texto = ""
            pdf.cell(widths[i], 7, texto, border=1, align="C")
        pdf.ln()
    
    return bytes(pdf.output())

st.title("👕 Carga de Talles - Gestión de Uniformes")

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Usamos el nombre exacto de tu pestaña maestra
    df = conn.read(worksheet="CASTILLO", ttl=0) 
    df.columns = [str(c).strip() for c in df.columns]
except Exception as e:
    st.error(f"❌ Error al conectar con la pestaña 'CASTILLO': {e}")
    st.stop()

# --- LOGIN ---
sucursales = sorted(df["SUCURSAL"].dropna().unique())
sucursal_sel = st.sidebar.selectbox("Seleccione su Sucursal", sucursales)
password = st.sidebar.text_input("Contraseña", type="password")

# Contraseña: nombre de sucursal en minúsculas + 2026
if password == f"{sucursal_sel.lower().replace(' ', '')}2026":
    st.success(f"Sesión iniciada: {sucursal_sel}")
    
    mask_sucursal = df["SUCURSAL"] == sucursal_sel
    df_sucursal = df[mask_sucursal].copy()

    prendas = ["PANTALON GRAFA", "CHOMBA MANGAS LARGAS", "CAMPERA HOMBRE", "CAMISA HOMBRE", "CAMPERA MUJER", "CAMISA MUJER"]
    
    # --- PROCESAMIENTO REFORZADO PARA PRESELECCIÓN ---
    for prenda in prendas:
        # Limpieza de datos (convierte todo a texto limpio)
        df_sucursal[prenda] = df_sucursal[prenda].astype(str).str.strip().replace({"nan": "", "None": "", "0": "", "0.0": ""})
        
        # Si tiene un "1", forzamos visualmente el texto "👉 ELEGIR TALLE"
        # Si está vacío, ponemos "🚫 NO APLICA"
        def transformar_vista(val):
            if val in ["1", "1.0"]: return "👉 ELEGIR TALLE"
            if val == "": return "🚫 NO APLICA"
            return val

        df_sucursal[prenda] = df_sucursal[prenda].apply(transformar_vista)

    df_editor = df_sucursal[["APELLIDO Y NOMBRE"] + prendas].copy()

    # --- CONFIGURACIÓN DE COLUMNAS ---
    t_num = ["👉 ELEGIR TALLE", "36", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60", "62"]
    t_let = ["👉 ELEGIR TALLE", "S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"]
    t_cam = ["👉 ELEGIR TALLE", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60"]

    column_config = {"APELLIDO Y NOMBRE": st.column_config.Column("Empleado", disabled=True)}
    for p in prendas:
        opts = t_num if "PANTALON" in p else (t_cam if "CAMISA" in p else t_let)
        column_config[p] = st.column_config.SelectboxColumn(p, options=["🚫 NO APLICA"] + opts)

    st.write(f"### Planilla de {sucursal_sel}")
    edited_df = st.data_editor(df_editor, column_config=column_config, hide_index=True, use_container_width=True)

    if st.button("💾 GUARDAR Y REGISTRAR"):
        with st.spinner("Guardando en la nube..."):
            try:
                # 1. Preparar datos para actualizar CASTILLO
                for p in prendas:
                    def revertir(val):
                        if val == "👉 ELEGIR TALLE": return "1"
                        if val == "🚫 NO APLICA": return ""
                        return val
                    df.loc[mask_sucursal, p] = edited_df[p].apply(revertir).values

                conn.update(worksheet="CASTILLO", data=df)

                # 2. Registrar en HISTORIAL_ACUSES
                ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                try:
                    historial_df = conn.read(worksheet="HISTORIAL_ACUSES", ttl=0)
                except:
                    historial_df = pd.DataFrame(columns=["FECHA", "SUCURSAL", "ACCION"])
                
                nueva_fila = pd.DataFrame([{"FECHA": ahora, "SUCURSAL": sucursal_sel, "ACCION": "Carga confirmada"}])
                historial_df = pd.concat([historial_df, nueva_fila], ignore_index=True)
                conn.update(worksheet="HISTORIAL_ACUSES", data=historial_df)

                # 3. Generar PDF
                pdf_bytes = generar_pdf(sucursal_sel, ahora, edited_df.values.tolist())
                
                st.success(f"✅ ¡Guardado! Datos registrados en 'HISTORIAL_ACUSES'.")
                st.download_button("📥 DESCARGAR ACUSE PDF", pdf_bytes, f"Acuse_{sucursal_sel}.pdf", "application/pdf")
                st.balloons()

            except Exception as e:
                st.error(f"❌ Error al procesar el guardado: {e}")
else:
    if password: st.error("🔑 Contraseña incorrecta")
    else: st.info(f"Esperando contraseña para {sucursal_sel}...")
