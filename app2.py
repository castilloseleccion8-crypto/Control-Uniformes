import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from PIL import Image

st.set_page_config(page_title="Gestión de Uniformes", layout="wide")

# ===================== ESTILOS CSS =====================
st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
.stApp { background-color: #f4f5f7; }
.block-container { padding-top: 1rem; padding-bottom: 2rem; }
section[data-testid="stSidebar"] { background-color: #0f1f3d; width: 270px; }
section[data-testid="stSidebar"] > div { padding-top: 30px; }
label { color: white !important; font-weight: 600 !important; }
.titulo { font-size: 40px; font-weight: 800; color: #0f1f3d; text-align: center; margin-top: 10px; margin-bottom: -10px; }
.subtitulo { font-size: 32px; font-weight: 700; color: #0f1f3d; text-align: center; margin-bottom: 15px; }
.card { background-color: white; padding: 35px; border-radius: 18px; box-shadow: 0 8px 25px rgba(0,0,0,0.08); margin-top: 10px; }
div[data-testid="stTextInput"] input { border: 2px solid #bdc3c7 !important; background-color: #f9f9f9 !important; border-radius: 8px !important; }
div.stButton > button { background-color: #0f1f3d; color: white; border-radius: 10px; padding: 10px 30px; border: none; font-weight: 600; width: 100%;}
div.stButton > button:hover { background-color: #1f2f5a; }
</style>
""", unsafe_allow_html=True)

# ===================== FUNCIÓN PDF =====================
def generar_pdf(sucursal, fecha, df_para_pdf):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "ACUSE DE RECIBO - CARGA DE TALLES", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.ln(5)
    pdf.cell(190, 7, f"Sucursal: {sucursal}", ln=True)
    pdf.cell(190, 7, f"Fecha de Operación: {fecha}", ln=True)
    pdf.ln(10)
    
    cols_display = ["Empleado", "Pantalon", "Chomba", "Camp.H", "Cam.H", "Camp.M", "Cam.M"]
    cols_reales = ["APELLIDO Y NOMBRE", "PANTALON GRAFA", "CHOMBA MANGAS LARGAS", "CAMPERA HOMBRE", "CAMISA HOMBRE", "CAMPERA MUJER", "CAMISA MUJER"]
    widths = [60, 22, 22, 22, 22, 22, 22]
    
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", "B", 8)
    for i, col in enumerate(cols_display):
        pdf.cell(widths[i], 7, col, border=1, fill=True, align="C")
    pdf.ln()
    
    pdf.set_font("Arial", "", 7)
    for _, row in df_para_pdf.iterrows():
        for i, col_name in enumerate(cols_reales):
            val = str(row[col_name]).replace("🚫 ", "").replace("👉 ", "")
            if val in ["None", "nan", "1", "1.0", "ELEGIR TALLE", "1.0"]: val = ""
            if "NO APLICA" in val: val = "-"
            pdf.cell(widths[i], 7, val, border=1, align="C")
        pdf.ln()
    return bytes(pdf.output())

# ===================== LOGO =====================
try:
    logo = Image.open("logo.png")
    st.sidebar.image(logo, use_column_width=True)
except:
    pass

st.markdown('<div class="titulo">CARGA DE TALLES</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">UNIFORME INVIERNO</div>', unsafe_allow_html=True)

# ===================== CONEXIÓN =====================
conn = st.connection("gsheets", type=GSheetsConnection)
try:
    df_global = conn.read(worksheet="CASTILLO", ttl=0)
    df_global.columns = [str(c).strip() for c in df_global.columns]
    # FORZAR TODO A TEXTO PARA EVITAR ERRORES CON NÚMEROS
    df_global = df_global.astype(str)
except Exception:
    st.error("⚠️ **ESPERA 2M, RECARGA LA PAGINA Y VOLVE A INTENTARLO. SI EL ERROR PERSISTE COMUNICARSE CON RRHH**")
    st.stop()

# ===================== LOGIN =====================
sucursales = sorted(df_global["SUCURSAL"].dropna().unique())
with st.sidebar:
    sucursal_sel = st.selectbox("SUCURSAL", sucursales)
    password = st.text_input("CONTRASEÑA", type="password")

if password == f"{sucursal_sel.lower().replace(' ', '')}2026":
    df_sucursal = df_global[df_global["SUCURSAL"] == sucursal_sel].copy()
    
    prendas = ["PANTALON GRAFA", "CHOMBA MANGAS LARGAS", "CAMPERA HOMBRE", "CAMISA HOMBRE", "CAMPERA MUJER", "CAMISA MUJER"]

    # --- LIMPIEZA CRÍTICA DE DATOS ---
    for prenda in prendas:
        # Convertimos todo a string y limpiamos decimales feos como .0
        df_sucursal[prenda] = df_sucursal[prenda].str.replace(".0", "", regex=False).str.strip()
        df_sucursal[prenda] = df_sucursal[prenda].replace({"nan": "", "None": "", "0": ""})
        
        def transformar(val):
            if val == "1": return "👉 ELEGIR TALLE"
            if val == "" or val == " ": return "🚫 NO APLICA"
            return val
        df_sucursal[prenda] = df_sucursal[prenda].apply(transformar)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader(f"Sucursal: {sucursal_sel}")

    filtro = st.text_input("", placeholder="🔎 Buscar empleado por nombre")
    
    df_mostrar = df_sucursal[["POSICIÓN","CUIL","APELLIDO Y NOMBRE"] + prendas].copy()
    if filtro:
        df_mostrar = df_mostrar[df_mostrar["APELLIDO Y NOMBRE"].str.contains(filtro, case=False, na=False)]

    # Opciones de talles como TEXTO
    t_num = ["👉 ELEGIR TALLE","36","38","40","42","44","46","48","50","52","54","56","58","60","62"]
    t_let = ["👉 ELEGIR TALLE","S","M","L","XL","XXL","XXXL","4XL"]
    t_cam = ["👉 ELEGIR TALLE","38","40","42","44","46","48","50","52","54","56","58","60"]

    column_config = {
        "POSICIÓN": st.column_config.Column("Posición", disabled=True),
        "CUIL": st.column_config.Column("CUIL", disabled=True),
        "APELLIDO Y NOMBRE": st.column_config.Column("Empleado", width="large", disabled=True)
    }
    for p in prendas:
        opts = t_num if "PANTALON" in p else (t_cam if "CAMISA" in p else t_let)
        column_config[p] = st.column_config.SelectboxColumn(p, options=["🚫 NO APLICA"] + opts, width="small")

    edited_df = st.data_editor(df_mostrar, column_config=column_config, hide_index=True, use_container_width=True)

    if st.button("GUARDAR Y REGISTRAR"):
        try:
            with st.spinner("Sincronizando con la base de datos..."):
                df_update = df_global.copy()
                
                for index, row in edited_df.iterrows():
                    cuil_empleado = str(row["CUIL"])
                    for p in prendas:
                        nuevo_val = str(row[p])
                        if "ELEGIR TALLE" in nuevo_val: valor_db = "1"
                        elif "NO APLICA" in nuevo_val: valor_db = ""
                        else: valor_db = nuevo_val
                        
                        df_update.loc[df_update["CUIL"] == cuil_empleado, p] = valor_db

                conn.update(worksheet="CASTILLO", data=df_update)

                ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                pdf_bytes = generar_pdf(sucursal_sel, ahora, edited_df)
                
                st.success("✅ ¡Talles guardados con éxito!")
                st.download_button("DESCARGAR ACUSE PDF", pdf_bytes, f"Acuse_{sucursal_sel}.pdf", "application/pdf")
                st.balloons()
        except Exception:
            st.error("⚠️ **ERROR AL GUARDAR. ESPERA 2M Y REINTENTA. SI PERSISTE CONTACTA A RRHH.**")

    st.markdown('</div>', unsafe_allow_html=True)
else:
    if password: st.error("Contraseña incorrecta.")
    else: st.info("Ingrese la contraseña para continuar.")
