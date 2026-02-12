import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from PIL import Image

st.set_page_config(page_title="Gestión de Uniformes", layout="wide")

# ===================== ESTILOS CORPORATIVOS =====================
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}

.stApp {
    background-color: #f4f5f7;
}

section[data-testid="stSidebar"] {
    background-color: #0f1f3d;
    width: 270px;
}

section[data-testid="stSidebar"] > div {
    padding-top: 40px;
}

label {
    color: white !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px;
}

input {
    border-radius: 6px !important;
    border: none !important;
}

.main > div {
    background: linear-gradient(
        to right,
        #dcd2e8 0px,
        #dcd2e8 420px,
        #f4f5f7 420px
    );
}

.titulo {
    font-size: 44px;
    font-weight: 800;
    color: #0f1f3d;
    text-align: center;
    margin-top: 70px;
}

.subtitulo {
    font-size: 40px;
    font-weight: 800;
    color: #0f1f3d;
    text-align: center;
    margin-top: -15px;
}

.card {
    background-color: white;
    padding: 30px;
    border-radius: 16px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.08);
    margin-top: 40px;
}

div.stButton > button {
    background-color: #0f1f3d;
    color: white;
    border-radius: 8px;
    padding: 10px 25px;
    border: none;
    font-weight: 600;
}

div.stButton > button:hover {
    background-color: #1f2f5a;
}

[data-testid="stDataEditor"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #e6e6e6;
}
</style>
""", unsafe_allow_html=True)

# ===================== LOGO =====================
logo = Image.open("logo.png")

with st.sidebar:
    st.image(logo, use_column_width=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ===================== TÍTULO =====================
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

try:
    df = conn.read(worksheet="CASTILLO", ttl=0)
    df.columns = [str(c).strip() for c in df.columns]
except Exception as e:
    st.error(f"Error al conectar con la hoja CASTILLO: {e}")
    st.stop()

# ===================== LOGIN =====================
sucursales = sorted(df["SUCURSAL"].dropna().unique())

with st.sidebar:
    sucursal_sel = st.selectbox("SUCURSAL", sucursales)
    password = st.text_input("CONTRASEÑA", type="password")

if password == f"{sucursal_sel.lower().replace(' ', '')}2026":

    mask_sucursal = df["SUCURSAL"] == sucursal_sel
    df_sucursal = df[mask_sucursal].copy()

    prendas = [
        "PANTALON GRAFA",
        "CHOMBA MANGAS LARGAS",
        "CAMPERA HOMBRE",
        "CAMISA HOMBRE",
        "CAMPERA MUJER",
        "CAMISA MUJER"
    ]

    # 🔹 Volvemos a usar lógica con emojis
    for prenda in prendas:
        df_sucursal[prenda] = df_sucursal[prenda].astype(str).str.strip().replace(
            {"nan": "", "None": "", "0": "", "0.0": ""}
        )

        def transformar_vista(val):
            if val in ["1", "1.0"]:
                return "👉 ELEGIR TALLE"
            if val == "":
                return "🚫 NO APLICA"
            return val

        df_sucursal[prenda] = df_sucursal[prenda].apply(transformar_vista)

    df_editor = df_sucursal[["APELLIDO Y NOMBRE"] + prendas].copy()

    t_num = ["👉 ELEGIR TALLE","36","38","40","42","44","46","48","50","52","54","56","58","60","62"]
    t_let = ["👉 ELEGIR TALLE","S","M","L","XL","XXL","XXXL","4XL","5XL"]
    t_cam = ["👉 ELEGIR TALLE","38","40","42","44","46","48","50","52","54","56","58","60"]

    column_config = {"APELLIDO Y NOMBRE": st.column_config.Column("Empleado", disabled=True)}

    for p in prendas:
        opts = t_num if "PANTALON" in p else (t_cam if "CAMISA" in p else t_let)
        column_config[p] = st.column_config.SelectboxColumn(
            p,
            options=["🚫 NO APLICA"] + opts
        )

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader(f"Sucursal: {sucursal_sel}")

    edited_df = st.data_editor(
        df_editor,
        column_config=column_config,
        hide_index=True,
        use_container_width=True
    )

    if st.button("GUARDAR Y REGISTRAR"):
        with st.spinner("Procesando..."):
            try:
                for p in prendas:
                    def revertir(val):
                        if val == "👉 ELEGIR TALLE":
                            return "1"
                        if val == "🚫 NO APLICA":
                            return ""
                        return val
                    df.loc[mask_sucursal, p] = edited_df[p].apply(revertir).values

                conn.update(worksheet="CASTILLO", data=df)

                ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

                try:
                    historial_df = conn.read(worksheet="HISTORIAL_ACUSES", ttl=0)
                except:
                    historial_df = pd.DataFrame(columns=["FECHA","SUCURSAL","ACCION"])

                nueva_fila = pd.DataFrame([{
                    "FECHA": ahora,
                    "SUCURSAL": sucursal_sel,
                    "ACCION": "Carga confirmada"
                }])

                historial_df = pd.concat([historial_df, nueva_fila], ignore_index=True)
                conn.update(worksheet="HISTORIAL_ACUSES", data=historial_df)

                pdf_bytes = generar_pdf(sucursal_sel, ahora, edited_df.values.tolist())

                st.success("Datos guardados correctamente.")
                st.download_button(
                    "DESCARGAR ACUSE PDF",
                    pdf_bytes,
                    f"Acuse_{sucursal_sel}.pdf",
                    "application/pdf"
                )

            except Exception as e:
                st.error(f"Error al procesar: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

else:
    if password:
        st.error("Contraseña incorrecta.")
    else:
        st.info("Ingrese la contraseña para continuar.")
