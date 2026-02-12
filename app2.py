import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO

st.set_page_config(layout="wide")

# ---------------------------
# ESTILOS
# ---------------------------
st.markdown("""
<style>
.titulo {
    text-align: center;
    font-size: 34px;
    font-weight: 800;
    color: #0A2A66;
    margin-bottom: 25px;
}

.buscador-box {
    background-color: #f2f4f8;
    padding: 25px;
    border-radius: 12px;
    margin-bottom: 30px;
}

.stTextInput > div > div > input {
    background-color: white;
    color: #0A2A66;
    font-weight: 600;
    border: 2px solid #0A2A66;
}

.stSelectbox > div > div {
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# TITULO
# ---------------------------
st.markdown('<div class="titulo">UNIFORME INVIERNO</div>', unsafe_allow_html=True)

# ---------------------------
# CARGA DE EXCEL
# ---------------------------
archivo = st.file_uploader("Subir archivo Excel", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)

    # Detectar columna POSICIÓN (con o sin tilde)
    if "Posición" in df.columns:
        col_posicion = "Posición"
    elif "Posicion" in df.columns:
        col_posicion = "Posicion"
    else:
        st.error("No se encontró columna Posición / Posicion")
        st.stop()

    # Validar columnas necesarias
    columnas_necesarias = [col_posicion, "CUIL", "Empleado"]
    for col in columnas_necesarias:
        if col not in df.columns:
            st.error(f"Falta la columna: {col}")
            st.stop()

    # ---------------------------
    # BUSCADOR EN RECUADRO GRANDE
    # ---------------------------
    st.markdown('<div class="buscador-box">', unsafe_allow_html=True)
    busqueda = st.text_input("Buscar empleado por nombre")
    st.markdown('</div>', unsafe_allow_html=True)

    if busqueda:
        df = df[df["Empleado"].str.contains(busqueda, case=False, na=False)]

    # ---------------------------
    # Sucursal
    # ---------------------------
    if "Sucursal" in df.columns:
        sucursal = df["Sucursal"].iloc[0]
        st.subheader(f"Sucursal: {sucursal}")

    # ---------------------------
    # TABLA
    # ---------------------------
    talles = ["👉 ELEGIR TALLE", "XS", "S", "M", "L", "XL", "XXL", "🚫 NO APLICA"]

    prendas = [
        "PANTALON",
        "CHOMBA M",
        "CAMPERA H",
        "CAMISA H",
        "CAMPERA M",
        "CAMISA M"
    ]

    for prenda in prendas:
        if prenda not in df.columns:
            df[prenda] = "🚫 NO APLICA"

    header = st.columns([2, 2, 3] + [2]*len(prendas))

    header[0].markdown(f"**{col_posicion}**")
    header[1].markdown("**CUIL**")
    header[2].markdown("**Empleado**")

    for i, prenda in enumerate(prendas):
        header[i+3].markdown(f"**{prenda}**")

    for index, row in df.iterrows():
        cols = st.columns([2, 2, 3] + [2]*len(prendas))

        cols[0].write(row[col_posicion])
        cols[1].write(row["CUIL"])
        cols[2].write(row["Empleado"])

        for i, prenda in enumerate(prendas):
            seleccion = cols[i+3].selectbox(
                "",
                talles,
                key=f"{index}_{prenda}"
            )
            df.loc[index, prenda] = seleccion

    # ---------------------------
    # EXPORTAR PDF
    # ---------------------------
    if st.button("Generar PDF"):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=10)
        pdf.add_page()
        pdf.set_font("Arial", size=8)

        pdf.cell(200, 10, txt="Uniforme Invierno", ln=True, align="C")
        pdf.ln(5)

        columnas_pdf = [col_posicion, "CUIL", "Empleado"] + prendas

        for col in columnas_pdf:
            pdf.cell(30, 8, col[:12], border=1)
        pdf.ln()

        for _, row in df.iterrows():
            for col in columnas_pdf:
                texto = str(row[col])[:12]
                pdf.cell(30, 8, texto, border=1)
            pdf.ln()

        buffer = BytesIO()
        pdf.output(buffer)
        buffer.seek(0)

        st.download_button(
            label="Descargar PDF",
            data=buffer,
            file_name="uniformes.pdf",
            mime="application/pdf"
        )
