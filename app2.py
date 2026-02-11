import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import pagesizes
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import inch
import os

st.set_page_config(page_title="Gestión de Uniformes", layout="wide")

# =========================
# 🎨 ESTILO CORPORATIVO
# =========================
st.markdown("""
<style>
.main {background-color: #F8F9FA;}

h1, h2, h3 {color: #162B3D;}

div.stButton > button {
    background-color: #E1AD41;
    color: #162B3D;
    font-weight: bold;
    border-radius: 8px;
    height: 45px;
}

div.stButton > button:hover {
    background-color: #c9972f;
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("Gestión de Uniformes")

# =========================
# CONEXIÓN
# =========================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0)
    df.columns = [str(c).strip() for c in df.columns]
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

# =========================
# LOGIN
# =========================
st.sidebar.header("Acceso Sucursales")
sucursales = sorted(df["SUCURSAL"].dropna().unique())
sucursal_sel = st.sidebar.selectbox("Seleccione su Sucursal", sucursales)

pass_correcta = f"{sucursal_sel.lower().replace(' ', '')}2026"
password = st.sidebar.text_input("Contraseña", type="password")

if password == pass_correcta:

    st.success(f"Sucursal: {sucursal_sel}")

    mask_sucursal = df["SUCURSAL"] == sucursal_sel
    df_sucursal = df[mask_sucursal].copy()

    # =========================
    # TALLES
    # =========================
    t_num = ["36","38","40","42","44","46","48","50","52","54","56","58","60","62"]
    t_let = ["S","M","L","XL","XXL","XXXL","4XL","5XL"]
    t_cam = ["38","40","42","44","46","48","50","52","54","56","58","60"]

    prendas = [
        "PANTALON GRAFA",
        "CHOMBA MANGAS LARGAS",
        "CAMPERA HOMBRE",
        "CAMISA HOMBRE",
        "CAMPERA MUJER",
        "CAMISA MUJER"
    ]

    # =========================
    # LIMPIEZA
    # =========================
    for prenda in prendas:
        df_sucursal[prenda] = (
            df_sucursal[prenda]
            .astype(str)
            .str.strip()
            .replace({"nan": "", "None": "", "0.0": "", "0": ""})
        )

    df_editor = df_sucursal[["APELLIDO Y NOMBRE"] + prendas].copy()

    no_aplica_mask = {}

    for prenda in prendas:
        no_aplica_mask[prenda] = df_editor[prenda] == ""
        df_editor.loc[df_editor[prenda] == "1", prenda] = None
        df_editor.loc[no_aplica_mask[prenda], prenda] = "NO APLICA"

    st.markdown(f"## Planilla de {sucursal_sel}")

    # =========================
    # COLUMNAS
    # =========================
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
            prenda,
            options=opts,
            required=False
        )

    edited_df = st.data_editor(
        df_editor,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        disabled=no_aplica_mask
    )

    # =========================
    # DETECTOR DE PENDIENTES
    # =========================
    pendientes = edited_df[prendas].isna().any(axis=1)
    empleados_pendientes = edited_df.loc[pendientes, "APELLIDO Y NOMBRE"]

    if len(empleados_pendientes) > 0:
        st.warning(f"Hay {len(empleados_pendientes)} empleados con talles pendientes.")
    else:
        st.success("Todos los empleados tienen sus talles completos.")

    # =========================
    # GUARDAR + ACUSE PDF
    # =========================
    if st.button("GUARDAR CAMBIOS Y GENERAR ACUSE"):

        with st.spinner("Actualizando y generando acuse..."):

            try:
                # Guardar en sheet
                for prenda in prendas:
                    nuevos = edited_df[prenda].values
                    final = []

                    for val in nuevos:
                        if val == "NO APLICA":
                            final.append("")
                        elif pd.isna(val):
                            final.append("1")
                        else:
                            final.append(val)

                    df.loc[mask_sucursal, prenda] = final

                conn.update(data=df)

                # =========================
                # GENERAR PDF ACUSE
                # =========================
                fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
                nombre_archivo = f"ACUSE_{sucursal_sel}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                ruta = f"/mnt/data/{nombre_archivo}"

                doc = SimpleDocTemplate(ruta, pagesize=pagesizes.A4)
                elements = []

                styles = getSampleStyleSheet()
                style_title = styles["Heading1"]
                style_normal = styles["Normal"]

                elements.append(Paragraph("ACUSE DE CARGA DE TALLES", style_title))
                elements.append(Spacer(1, 0.3 * inch))

                elements.append(Paragraph(f"Sucursal: {sucursal_sel}", style_normal))
                elements.append(Paragraph(f"Fecha y Hora: {fecha}", style_normal))
                elements.append(Spacer(1, 0.3 * inch))

                data_table = [["Empleado"] + prendas]

                for _, row in edited_df.iterrows():
                    fila = [row["APELLIDO Y NOMBRE"]]
                    for prenda in prendas:
                        fila.append(row[prenda] if pd.notna(row[prenda]) else "PENDIENTE")
                    data_table.append(fila)

                table = Table(data_table, repeatRows=1)
                table.setStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#162B3D")),
                    ('TEXTCOLOR',(0,0),(-1,0),colors.white),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
                ])

                elements.append(table)
                doc.build(elements)

                st.success("Datos actualizados correctamente.")

                with open(ruta, "rb") as f:
                    st.download_button(
                        label="Descargar ACUSE PDF",
                        data=f,
                        file_name=nombre_archivo,
                        mime="application/pdf"
                    )

            except Exception as e:
                st.error(f"Error: {e}")

else:
    if password:
        st.error("Contraseña incorrecta")
    else:
        st.error("Contraseña incorrecta")
