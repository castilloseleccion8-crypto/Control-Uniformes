import streamlit as st
import pandas as pd
from datetime import datetime
import os
from fpdf import FPDF

# =========================
# CONFIGURACIÓN
# =========================

st.set_page_config(layout="wide")

AZUL = "#162B3D"
AMARILLO = "#E1AD41"

# =========================
# ESTILOS PERSONALIZADOS
# =========================

st.markdown(f"""
<style>

section[data-testid="stSidebar"] {{
    background-color: {AZUL};
    color: white;
}}

section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stTextInput label {{
    color: white !important;
}}

div.stButton > button {{
    background-color: {AMARILLO};
    color: black;
    font-weight: bold;
    border-radius: 8px;
}}

.no-aplica {{
    font-weight: bold;
}}

</style>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR
# =========================

st.sidebar.title("Acceso Sucursales")

sucursal = st.sidebar.selectbox("Seleccione su Sucursal", ["AGUILARES"])
gerente = st.sidebar.text_input("Nombre del Gerente")

# =========================
# DATOS BASE (SIMULACIÓN)
# =========================

empleados = [
    "ZELARAYAN PABLO NERI",
    "MASS MELINA PATRICIA",
    "PAGANI DANIEL ALEJANDRO",
    "GORDILLO RICARDO JAVIER",
    "CISTERNA JULIO CESAR",
    "ARANDA RUBEN ALEJANDRO",
    "BURGOS ENZO NICOLAS",
    "MEDINA MIGUEL IGNACIO",
    "MORAN JUAN CARLOS",
    "VELIZ EDUARDO HERNAN"
]

columnas = [
    "PANTALON GRAFA",
    "CHOMBA MANGAS LARGAS",
    "CAMPERA HOMBRE",
    "CAMISA HOMBRE",
    "CAMPERA MUJER",
    "CAMISA MUJER"
]

st.title(f"Planilla de {sucursal}")

st.info("Complete únicamente las prendas necesarias.")

# =========================
# TABLA EDITABLE
# =========================

datos = []

for emp in empleados:
    fila = {"Empleado": emp}
    
    for col in columnas:
        opcion = st.selectbox(
            f"{emp} - {col}",
            ["ELEGIR", "NO APLICA", "XS", "S", "M", "L", "XL", "XXL"],
            key=f"{emp}_{col}"
        )
        fila[col] = opcion
    
    datos.append(fila)

df = pd.DataFrame(datos)

# =========================
# VALIDACIÓN
# =========================

incompletos = []

for index, row in df.iterrows():
    for col in columnas:
        if row[col] == "ELEGIR":
            incompletos.append(row["Empleado"])
            break

if incompletos:
    st.error(f"Hay empleados sin completar: {', '.join(incompletos)}")
else:
    st.success("Todos los empleados tienen sus talles completos.")

# =========================
# GENERAR ACUSE
# =========================

if st.button("GUARDAR CAMBIOS Y GENERAR ACUSE"):

    if incompletos:
        st.error("No se puede generar el acuse. Hay empleados sin completar.")
    else:

        if not gerente:
            st.error("Debe ingresar el nombre del gerente.")
        else:
            now = datetime.now()
            fecha_str = now.strftime("%Y%m%d_%H%M%S")
            
            os.makedirs("/mnt/data", exist_ok=True)
            filename = f"/mnt/data/ACUSE_{sucursal}_{fecha_str}.pdf"

            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Arial", size=10)

            pdf.cell(200, 10, txt="ACUSE DE CARGA DE UNIFORMES", ln=True, align='C')
            pdf.ln(5)

            pdf.cell(200, 8, txt=f"Sucursal: {sucursal}", ln=True)
            pdf.cell(200, 8, txt=f"Gerente: {gerente}", ln=True)
            pdf.cell(200, 8, txt=f"Fecha y Hora: {now.strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
            pdf.ln(5)

            for index, row in df.iterrows():
                pdf.cell(200, 8, txt=f"Empleado: {row['Empleado']}", ln=True)
                for col in columnas:
                    pdf.cell(200, 6, txt=f"   {col}: {row[col]}", ln=True)
                pdf.ln(3)

            pdf.output(filename)

            with open(filename, "rb") as file:
                st.download_button(
                    label="Descargar ACUSE",
                    data=file,
                    file_name=f"ACUSE_{sucursal}_{fecha_str}.pdf",
                    mime="application/pdf"
                )

            st.success("Acuse generado correctamente.")
