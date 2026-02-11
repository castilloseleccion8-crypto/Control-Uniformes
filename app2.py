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
    
    cols = ["Empleado", "Pantalon", "Chomba", "Camp.H", "Cam.H", "Camp.M", "Cam.M"]
    widths = [60, 22, 22, 22, 22, 22, 22]
    
    pdf.set_fill_color(200, 200, 200)
    pdf.set_font("Arial", "B", 8)
    for i, col in enumerate(cols):
        pdf.cell(widths[i], 7, col, border=1, fill=True, align="C")
    pdf.ln()
    
    pdf.set_font("Arial", "", 7)
    for row in datos_tabla:
        for val in row:
            texto = str(val).replace("🚫 ", "").replace("👉 ", "")
            if texto in ["None", "nan", "1"]: texto = ""
            pdf.cell(22 if row.index(val) > 0 else 60, 7, texto, border=1, align="C")
        pdf.ln()
    
    return bytes(pdf.output())

st.title("👕 Carga de Talles - Gestión de Uniformes")

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Leemos la pestaña principal
    df = conn.read(worksheet="Sheet1", ttl=0) # Ajustar nombre de pestaña si es necesario
    df.columns = [str(c).strip() for c in df.columns]
except Exception as e:
    st.error(f"Error al conectar: {e}")
    st.stop()

# --- LOGIN ---
sucursales = sorted(df["SUCURSAL"].dropna().unique())
sucursal_sel = st.sidebar.selectbox("Seleccione su Sucursal", sucursales)
password = st.sidebar.text_input("Contraseña", type="password")

if password == f"{sucursal_sel.lower().replace(' ', '')}2026":
    mask_sucursal = df["SUCURSAL"] == sucursal_sel
    df_sucursal = df[mask_sucursal].copy()

    prendas = ["PANTALON GRAFA", "CHOMBA MANGAS LARGAS", "CAMPERA HOMBRE", "CAMISA HOMBRE", "CAMPERA MUJER", "CAMISA MUJER"]
    
    # --- PROCESAMIENTO PARA EL EDITOR (Preselección de "Elegir Talle") ---
    for prenda in prendas:
        df_sucursal[prenda] = df_sucursal[prenda].astype(str).str.strip()
        df_sucursal[prenda] = df_sucursal[prenda].replace({"nan": "", "None": "", "0": "", "0.0": ""})
        
        # Si el valor es "1", forzamos visualmente el texto "👉 ELEGIR TALLE"
        df_sucursal.loc[df_sucursal[prenda] == "1", prenda] = "👉 ELEGIR TALLE"
        # Si está vacío, "NO APLICA"
        df_sucursal.loc[df_sucursal[prenda] == "", prenda] = "🚫 NO APLICA"

    df_editor = df_sucursal[["APELLIDO Y NOMBRE"] + prendas].copy()

    # Configuración de columnas
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
        with st.spinner("Procesando..."):
            # 1. Preparar datos para actualizar Sheet1
            for p in prendas:
                valores = edited_df[p].apply(lambda x: "1" if x == "👉 ELEGIR TALLE" else ("" if x == "🚫 NO APLICA" else x))
                df.loc[mask_sucursal, p] = valores.values

            # 2. Guardar en Sheet1
            conn.update(worksheet="Sheet1", data=df)

            # 3. REGISTRO EN OTRA PESTAÑA (Constancia en el Sheets)
            ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            try:
                # Intentamos leer el historial existente
                historial_df = conn.read(worksheet="HISTORIAL_ACUSES")
            except:
                # Si no existe, creamos la estructura
                historial_df = pd.DataFrame(columns=["FECHA", "SUCURSAL", "DETALLE_CARGA"])
            
            # Resumimos la carga en un texto para la celda
            detalle = str(edited_df.to_dict(orient='records'))
            nueva_fila = pd.DataFrame([{"FECHA": ahora, "SUCURSAL": sucursal_sel, "DETALLE_CARGA": detalle}])
            historial_df = pd.concat([historial_df, nueva_fila], ignore_index=True)
            
            # Actualizamos la pestaña de historial
            conn.update(worksheet="HISTORIAL_ACUSES", data=historial_df)

            # 4. Generar PDF para el usuario
            pdf_bytes = generar_pdf(sucursal_sel, ahora, edited_df.values.tolist())
            
            st.success(f"✅ Datos guardados y registrados en 'HISTORIAL_ACUSES'.")
            st.download_button("📥 DESCARGAR COMPROBANTE PDF", pdf_bytes, f"Acuse_{sucursal_sel}.pdf", "application/pdf")
            st.balloons()

else:
    st.info("Por favor, ingrese la contraseña de su sucursal.")
