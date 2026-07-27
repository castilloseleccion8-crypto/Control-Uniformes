import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from PIL import Image

st.set_page_config(page_title="Gestión de Uniformes", page_icon="🧥", layout="wide")

# ===================== ESTILOS CSS =====================
st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
.stApp { background: linear-gradient(180deg, #f4f6fb 0%, #eef1f7 100%); }
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1300px; }

section[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f1f3d 0%, #16264a 100%); width: 280px; }
section[data-testid="stSidebar"] > div { padding-top: 30px; }
section[data-testid="stSidebar"] label { color: #ffffff !important; font-weight: 600 !important; letter-spacing: .3px; }

.titulo {
    font-size: 38px; font-weight: 800; color: #0f1f3d; text-align: center;
    margin-top: 6px; margin-bottom: -6px; letter-spacing: .5px;
}
.subtitulo {
    font-size: 20px; font-weight: 600; color: #5b6b8c; text-align: center;
    margin-bottom: 20px; text-transform: uppercase; letter-spacing: 2px;
}

.card {
    background-color: white; padding: 32px 36px; border-radius: 20px;
    box-shadow: 0 10px 30px rgba(15,31,61,0.08); margin-top: 14px;
    border: 1px solid #eef0f5;
}

.badge-row { display:flex; gap:14px; margin-bottom: 18px; flex-wrap: wrap; }
.badge {
    background:#f4f6fb; border:1px solid #e3e7f1; border-radius:12px;
    padding:10px 18px; font-size:14px; color:#0f1f3d; font-weight:600;
}
.badge b { color:#1f7a3d; }

div[data-testid="stTextInput"] input {
    border: 2px solid #dbe0ea !important; background-color: #fbfbfd !important;
    border-radius: 10px !important; padding: 8px 12px !important;
}

div.stButton > button {
    background-color: #0f1f3d; color: white; border-radius: 12px;
    padding: 12px 30px; border: none; font-weight: 700; width: 100%;
    letter-spacing: .3px; transition: background-color .15s ease;
}
div.stButton > button:hover { background-color: #1f2f5a; }

div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
    border-radius: 14px; overflow: hidden; border: 1px solid #e6e9f0;
}
</style>
""", unsafe_allow_html=True)

PLACEHOLDER = "👉 ELEGIR TALLE"
BLOQUEADO = "🚫 NO APLICA"

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
            if val in ["None", "nan", "1", "1.0", "ELEGIR TALLE"]:
                val = ""
            if "NO APLICA" in val:
                val = "-"
            pdf.cell(widths[i], 7, val, border=1, align="C")
        pdf.ln()
    return bytes(pdf.output())

# ===================== LOGO =====================
try:
    logo = Image.open("logo.png")
    st.sidebar.image(logo, use_container_width=True)
except Exception:
    pass

st.markdown('<div class="titulo">CARGA DE TALLES</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Uniforme Invierno</div>', unsafe_allow_html=True)

# ===================== CONEXIÓN =====================
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_hoja():
    df = conn.read(worksheet="CASTILLO", ttl=30)
    df.columns = [str(c).strip() for c in df.columns]
    return df.astype(str)

try:
    df_global = leer_hoja()
except Exception as e:
    st.error(f"Error técnico al conectar con la base de datos: {e}")
    st.stop()

# ===================== LOGIN =====================
sucursales = sorted(df_global["SUCURSAL"].dropna().unique())
with st.sidebar:
    st.markdown("### 🧥 Panel de acceso")
    sucursal_sel = st.selectbox("SUCURSAL", sucursales)
    password = st.text_input("CONTRASEÑA", type="password")

if password == f"{sucursal_sel.lower().replace(' ', '')}2026":
    df_sucursal = df_global[df_global["SUCURSAL"] == sucursal_sel].copy()

    prendas = ["PANTALON GRAFA", "CHOMBA MANGAS LARGAS", "CAMPERA HOMBRE", "CAMISA HOMBRE", "CAMPERA MUJER", "CAMISA MUJER"]

    # --- LIMPIEZA CRÍTICA DE DATOS ---
    for prenda in prendas:
        df_sucursal[prenda] = df_sucursal[prenda].str.replace(".0", "", regex=False).str.strip()
        df_sucursal[prenda] = df_sucursal[prenda].replace({"nan": "", "None": "", "0": ""})

        def transformar(val):
            if val == "1":
                return PLACEHOLDER
            if val == "" or val == " ":
                return BLOQUEADO
            return val
        df_sucursal[prenda] = df_sucursal[prenda].apply(transformar)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader(f"Sucursal: {sucursal_sel}")

    # --- Indicadores rápidos ---
    total_pendientes = int((df_sucursal[prendas] == PLACEHOLDER).sum().sum())
    total_bloqueados = int((df_sucursal[prendas] == BLOQUEADO).sum().sum())
    st.markdown(f"""
    <div class="badge-row">
        <div class="badge">👥 Empleados: <b>{len(df_sucursal)}</b></div>
        <div class="badge">⏳ Talles pendientes: <b>{total_pendientes}</b></div>
        <div class="badge">🚫 Prendas no aplicables: <b>{total_bloqueados}</b></div>
    </div>
    """, unsafe_allow_html=True)

    filtro = st.text_input("", placeholder="🔎 Buscar empleado por nombre")

    df_mostrar = df_sucursal[["POSICIÓN", "CUIL", "APELLIDO Y NOMBRE"] + prendas].copy()
    if filtro:
        df_mostrar = df_mostrar[df_mostrar["APELLIDO Y NOMBRE"].str.contains(filtro, case=False, na=False)]

    # Opciones de talles como TEXTO
    t_num = [PLACEHOLDER, "36", "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60", "62"]
    t_let = [PLACEHOLDER, "S", "M", "L", "XL", "XXL", "XXXL", "4XL"]
    t_cam = [PLACEHOLDER, "38", "40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60"]

    column_config = {
        "POSICIÓN": st.column_config.Column("Posición", disabled=True),
        "CUIL": st.column_config.Column("CUIL", disabled=True),
        "APELLIDO Y NOMBRE": st.column_config.Column("Empleado", width="large", disabled=True),
    }
    for p in prendas:
        opts = t_num if "PANTALON" in p else (t_cam if "CAMISA" in p else t_let)
        # Nota: Streamlit no permite bloquear celdas individuales dentro de una
        # columna de tipo Selectbox. Por eso la regla real de "NO APLICA" se
        # refuerza al momento de GUARDAR (más abajo), no solo acá en la UI.
        column_config[p] = st.column_config.SelectboxColumn(p, options=[BLOQUEADO] + opts, width="small")

    edited_df = st.data_editor(df_mostrar, column_config=column_config, hide_index=True, use_container_width=True)

    st.caption("⚠️ Las prendas marcadas como 'NO APLICA' quedan bloqueadas automáticamente al guardar, aunque el desplegable las muestre editables.")

    if st.button("GUARDAR Y REGISTRAR"):
        # 1) VALIDACIÓN: no debe quedar ningún "ELEGIR TALLE" pendiente en una prenda que sí aplica
        pendientes = []
        for _, row in edited_df.iterrows():
            for p in prendas:
                if PLACEHOLDER in str(row[p]):
                    pendientes.append(f"• {row['APELLIDO Y NOMBRE']} — {p}")

        if pendientes:
            st.error(
                "No se puede guardar: faltan talles por elegir.\n\n" + "\n".join(pendientes)
            )
        else:
            try:
                with st.spinner("Sincronizando con la base de datos..."):
                    # 2) RE-LECTURA FRESCA justo antes de escribir, para no pisar
                    # cambios que otra sucursal haya guardado mientras esta
                    # persona tenía la página abierta.
                    df_fresh = leer_hoja()
                    df_update = df_fresh.copy()

                    for _, row in edited_df.iterrows():
                        cuil_empleado = str(row["CUIL"])
                        original_row = df_sucursal[df_sucursal["CUIL"] == cuil_empleado].iloc[0]

                        for p in prendas:
                            # 3) REFUERZO DE BLOQUEO: si originalmente era "NO APLICA",
                            # se ignora cualquier cambio hecho en la UI y se guarda vacío.
                            if BLOQUEADO in str(original_row[p]):
                                valor_db = ""
                            else:
                                nuevo_val = str(row[p])
                                if PLACEHOLDER in nuevo_val:
                                    valor_db = "1"
                                elif BLOQUEADO in nuevo_val:
                                    valor_db = ""
                                else:
                                    valor_db = nuevo_val

                            df_update.loc[df_update["CUIL"] == cuil_empleado, p] = valor_db

                    conn.update(worksheet="CASTILLO", data=df_update)

                    ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    pdf_bytes = generar_pdf(sucursal_sel, ahora, edited_df)

                    st.success("✅ ¡Talles guardados con éxito!")
                    st.download_button("📄 DESCARGAR ACUSE PDF", pdf_bytes, f"Acuse_{sucursal_sel}.pdf", "application/pdf")
                    st.balloons()
            except Exception:
                st.error("⚠️ **ERROR AL GUARDAR. ESPERA 2 MINUTOS Y REINTENTA. SI PERSISTE CONTACTA A RRHH.**")

    st.markdown('</div>', unsafe_allow_html=True)
else:
    if password:
        st.error("Contraseña incorrecta.")
    else:
        st.info("Ingrese la contraseña para continuar.")
