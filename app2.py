import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from PIL import Image

st.set_page_config(page_title="Gestión de Uniformes", layout="wide")

# ===================== ESTILOS CSS REFORMADOS =====================
st.markdown("""
<style>
/* Fuente y Fondo General */
html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}
.stApp {
    background-color: #f4f5f7;
}

/* Sidebar Estilo Castillo */
section[data-testid="stSidebar"] {
    background-color: #0f1f3d !important;
    min-width: 300px !important;
}

/* Títulos con el color corporativo */
.titulo-container {
    text-align: center;
    padding: 10px 0 5px 0; /* Reducido para evitar espacios */
}
.titulo {
    font-size: 48px;
    font-weight: 800;
    color: #0f1f3d;
    margin-bottom: 0px;
}
.subtitulo {
    font-size: 42px;
    font-weight: 800;
    color: #0f1f3d;
    margin-top: -15px;
}

/* El "Recuadro Blanco" limpio - Sin bloques innecesarios arriba */
.bloque-blanco {
    background-color: white;
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    margin-top: 10px;
}

/* BUSCADOR CON COLORCITO */
div[data-testid="stTextInput"] input {
    border: 2px solid #f1b434 !important; /* Borde Dorado */
    background-color: #fffdf5 !important; /* Fondo crema suave */
    border-radius: 8px !important;
}

div[data-testid="stTextInput"] label {
    color: #0f1f3d !important;
    font-weight: bold !important;
}

/* Botones */
div.stButton > button {
    background-color: #f1b434 !important; 
    color: #0f1f3d !important;
    border-radius: 8px;
    padding: 12px 30px;
    border: none;
    font-weight: bold;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# ===================== LOGO Y SIDEBAR =====================
try:
    logo = Image.open("logo.png")
    st.sidebar.image(logo, use_container_width=True)
except:
    pass

# ===================== CONEXIÓN =====================
conn = st.connection("gsheets", type=GSheetsConnection)
try:
    df = conn.read(worksheet="CASTILLO", ttl=0)
    df.columns = [str(c).strip() for c in df.columns]
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

# ===================== LOGIN EN SIDEBAR =====================
sucursales = sorted(df["SUCURSAL"].dropna().unique())
with st.sidebar:
    st.markdown("<h3 style='color:white;'>ACCESO</h3>", unsafe_allow_html=True)
    sucursal_sel = st.selectbox("SUCURSAL", sucursales)
    password = st.text_input("CONTRASEÑA", type="password")

# ===================== TÍTULOS =====================
st.markdown('<div class="titulo-container"><div class="titulo">CARGA DE TALLES</div><div class="subtitulo">UNIFORME INVIERNO</div></div>', unsafe_allow_html=True)

if password == f"{sucursal_sel.lower().replace(' ', '')}2026":
    
    # Recuadro Blanco Principal
    st.markdown('<div class="bloque-blanco">', unsafe_allow_html=True)
    
    # Fila de Título y Buscador más compacto
    col_t, col_b = st.columns([2, 1])
    with col_t:
        st.markdown(f"### 📍 Sucursal: {sucursal_sel}")
    with col_b:
        filtro = st.text_input("Buscar empleado...", placeholder="Escriba nombre aquí...")

    mask_sucursal = df["SUCURSAL"] == sucursal_sel
    df_sucursal = df[mask_sucursal].copy()

    if filtro:
        df_sucursal = df_sucursal[df_sucursal["APELLIDO Y NOMBRE"].str.contains(filtro, case=False, na=False)]

    prendas = ["PANTALON GRAFA", "CHOMBA MANGAS LARGAS", "CAMPERA HOMBRE", "CAMISA HOMBRE", "CAMPERA MUJER", "CAMISA MUJER"]
    
    for prenda in prendas:
        df_sucursal[prenda] = df_sucursal[prenda].astype(str).str.strip().replace({"nan": "", "None": "", "0": "", "0.0": ""})
        df_sucursal[prenda] = df_sucursal[prenda].apply(lambda x: "👉 ELEGIR TALLE" if x in ["1", "1.0"] else ("🚫 NO APLICA" if x == "" else x))

    df_editor = df_sucursal[["POSICIÓN","CUIL","APELLIDO Y NOMBRE"] + prendas].sort_values("POSICIÓN")

    # Configuración Editor
    t_num = ["👉 ELEGIR TALLE", "36", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60", "62"]
    t_let = ["👉 ELEGIR TALLE", "S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"]
    t_cam = ["👉 ELEGIR TALLE", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60"]

    config = {
        "POSICIÓN": st.column_config.Column("Pos.", width="small", disabled=True),
        "CUIL": st.column_config.Column("CUIL", disabled=True),
        "APELLIDO Y NOMBRE": st.column_config.Column("Empleado", width="large", disabled=True)
    }
    for p in prendas:
        opts = t_num if "PANTALON" in p else (t_cam if "CAMISA" in p else t_let)
        config[p] = st.column_config.SelectboxColumn(p, options=["🚫 NO APLICA"] + opts)

    # Grilla
    edited_df = st.data_editor(df_editor, column_config=config, hide_index=True, use_container_width=True)

    # Botón Guardar
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("💾 GUARDAR CAMBIOS"):
            try:
                for p in prendas:
                    def revertir(v): return "1" if v == "👉 ELEGIR TALLE" else ("" if v == "🚫 NO APLICA" else v)
                    df.loc[df["SUCURSAL"] == sucursal_sel, p] = edited_df[p].apply(revertir).values
                conn.update(worksheet="CASTILLO", data=df)
                st.success("¡Datos guardados!")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown('<div class="bloque-blanco" style="text-align:center;">', unsafe_allow_html=True)
    if password:
        st.error("❌ Contraseña incorrecta")
    else:
        st.info("👋 Por favor, ingrese su contraseña en la barra lateral para ver la planilla.")
    st.markdown('</div>', unsafe_allow_html=True)
