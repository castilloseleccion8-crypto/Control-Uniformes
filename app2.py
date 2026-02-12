import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from PIL import Image

st.set_page_config(page_title="Gestión de Uniformes", layout="wide")

# ===================== ESTILOS =====================
st.markdown("""
<style>

/* Fuente general */
html, body, [class*="css"]  {
    font-family: 'Segoe UI', sans-serif;
}

/* Fondo general con degradado */
.stApp {
    background: linear-gradient(
        135deg,
        #dcd2e8 0%,
        #e9e4f2 40%,
        #f4f5f7 100%
    );
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0f1f3d;
    width: 270px;
}

section[data-testid="stSidebar"] > div {
    padding-top: 30px;
}

label {
    color: white !important;
    font-weight: 600 !important;
}

/* Títulos */
.titulo {
    font-size: 42px;
    font-weight: 800;
    color: #0f1f3d;
    text-align: center;
    margin-top: 10px;
    margin-bottom: -10px;
}

.subtitulo {
    font-size: 34px;
    font-weight: 700;
    color: #0f1f3d;
    text-align: center;
    margin-bottom: 10px;
}

/* Card blanca */
.card {
    background-color: white;
    padding: 35px;
    border-radius: 18px;
    box-shadow: 0 10px 35px rgba(0,0,0,0.08);
    margin-top: 20px;
}

/* Botones */
div.stButton > button {
    background-color: #0f1f3d;
    color: white;
    border-radius: 10px;
    padding: 10px 30px;
    border: none;
    font-weight: 600;
}

div.stButton > button:hover {
    background-color: #1f2f5a;
}

/* Quitar espacio superior default */
.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
}

</style>
""", unsafe_allow_html=True)

# ===================== LOGO =====================
logo = Image.open("logo.png")

with st.sidebar:
    st.image(logo, use_column_width=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ===================== TITULOS =====================
st.markdown('<div class="titulo">CARGA DE TALLES</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">UNIFORME INVIERNO</div>', unsafe_allow_html=True)

# ===================== FUNCIÓN PDF =====================
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
    
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", "B", 8)
    for i, col in enumerate(cols):
        pdf.cell(widths[i], 7, col, border=1, fill=True, align="C")
    pdf.ln()
    
    pdf.set_font("Arial", "", 7)
    for row in datos_tabla:
        for i, val in enumerate(row):
            texto = str(val).replace("🚫 ", "").replace("👉 ", "")
            if texto in ["None", "nan", "1", "1.0"]:
                texto = ""
            pdf.cell(widths[i], 7, texto, border=1, align="C")
        pdf.ln()
    
    return bytes(pdf.output())

# ===================== CONEXIÓN =====================
conn = st.connection("gsheets", type=GSheetsConnection)

df = conn.read(worksheet="CASTILLO", ttl=0)
df.columns = [str(c).strip() for c in df.columns]

# ===================== LOGIN =====================
sucursales = sorted(df["SUCURSAL"].dropna().unique())

with st.sidebar:
    sucursal_sel = st.selectbox("SUCURSAL", sucursales)
    password = st.text_input("CONTRASEÑA", type="password")

if password == f"{sucursal_sel.lower().replace(' ', '')}2026":

    df_sucursal = df[df["SUCURSAL"] == sucursal_sel].copy()
    df_sucursal = df_sucursal.sort_values(by="POSICIÓN")

    prendas = [
        "PANTALON GRAFA",
        "CHOMBA MANGAS LARGAS",
        "CAMPERA HOMBRE",
        "CAMISA HOMBRE",
        "CAMPERA MUJER",
        "CAMISA MUJER"
    ]

    for prenda in prendas:
        df_sucursal[prenda] = df_sucursal[prenda].astype(str).str.strip().replace(
            {"nan": "", "None": "", "0": "", "0.0": ""}
        )

        def transformar(val):
            if val in ["1", "1.0"]:
                return "👉 ELEGIR TALLE"
            if val == "":
                return "🚫 NO APLICA"
            return val

        df_sucursal[prenda] = df_sucursal[prenda].apply(transformar)

    df_editor = df_sucursal[["POSICIÓN","CUIL","APELLIDO Y NOMBRE"] + prendas].copy()

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader(f"Sucursal: {sucursal_sel}")

    # 🔎 Buscador dentro del recuadro
    filtro = st.text_input("", placeholder="🔎 Buscar empleado por nombre")

    if filtro:
        df_editor = df_editor[
            df_editor["APELLIDO Y NOMBRE"].str.contains(filtro, case=False, na=False)
        ]

    t_num = ["👉 ELEGIR TALLE","36","38","40","42","44","46","48","50","52","54","56","58","60","62"]
    t_let = ["👉 ELEGIR TALLE","S","M","L","XL","XXL","XXXL","4XL","5XL"]
    t_cam = ["👉 ELEGIR TALLE","38","40","42","44","46","48","50","52","54","56","58","60"]

    column_config = {
        "POSICIÓN": st.column_config.Column("Posición", width="small", disabled=True),
        "CUIL": st.column_config.Column("CUIL", width="medium", disabled=True),
        "APELLIDO Y NOMBRE": st.column_config.Column("Empleado", width="large", disabled=True)
    }

    for p in prendas:
        opts = t_num if "PANTALON" in p else (t_cam if "CAMISA" in p else t_let)
        column_config[p] = st.column_config.SelectboxColumn(
            p,
            options=["🚫 NO APLICA"] + opts,
            width="small"
        )

    edited_df = st.data_editor(
        df_editor,
        column_config=column_config,
        hide_index=True,
        use_container_width=True
    )

    if st.button("GUARDAR Y REGISTRAR"):
        for p in prendas:
            def revertir(val):
                if val == "👉 ELEGIR TALLE":
                    return "1"
                if val == "🚫 NO APLICA":
                    return ""
                return val

            df.loc[df["SUCURSAL"] == sucursal_sel, p] = edited_df[p].apply(revertir).values

        conn.update(worksheet="CASTILLO", data=df)

        ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        pdf_bytes = generar_pdf(sucursal_sel, ahora, edited_df.values.tolist())

        st.success("Datos guardados correctamente.")
        st.download_button(
            "DESCARGAR ACUSE PDF",
            pdf_bytes,
            f"Acuse_{sucursal_sel}.pdf",
            "application/pdf"
        )

    st.markdown('</div>', unsafe_allow_html=True)

else:
    if password:
        st.error("Contraseña incorrecta.")
    else:
        st.info("Ingrese la contraseña para continuar.")
