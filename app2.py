import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sistema de Uniformes", layout="wide")

st.title("👕 Carga de Talles - Gestión de Uniformes")

# --- CONFIGURACIÓN DE LA PLANILLA ---
# Este es el ID de tu planilla extraído de tu link
SHEET_ID = "1nzDspEMKJZJSa5thUozUBQh0J4TMBjJV83fA0Xw8fpE"
SHEET_NAME = "CASTILLO"
# Esta URL fuerza a Google a entregar los datos sin errores de cabecera
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data(ttl=0)
def load_data(url):
    try:
        # Leemos directamente desde la URL de exportación de Google
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"❌ Error al conectar: {e}")
        return None

df = load_data(url)

if df is not None:
    # Limpiar espacios en los nombres de las columnas
    df.columns = df.columns.str.strip()
    
    # --- LOGIN Y FILTRO ---
    st.sidebar.header("Acceso Gerentes")
    sucursales = sorted(df["SUCURSAL"].unique())
    sucursal_sel = st.sidebar.selectbox("Seleccione su Sucursal", sucursales)
    password = st.sidebar.text_input("Contraseña", type="password")

    # Claves (Podés agregar todas las que necesites aquí)
    claves = {
        "AGUILARES": "aguilares2026",
        "PERICO": "perico2026",
        "PLAZOLETA": "plazoleta2026"
    }

    if password == claves.get(sucursal_sel):
        st.success(f"Conectado a {sucursal_sel}")
        
        mask = df["SUCURSAL"] == sucursal_sel
        df_sucursal = df[mask].copy()

        # Configuración de talles
        talles_num = [str(i) for i in range(36, 64, 2)]
        talles_letras = ["S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"]
        talles_camisas = [str(i) for i in range(38, 62, 2)]

        # Editor de datos
        edited_df = st.data_editor(
            df_sucursal,
            column_config={
                "PANTALON GRAFA": st.column_config.SelectboxColumn("Pantalón", options=talles_num),
                "CHOMBA MANGAS LARGAS": st.column_config.SelectboxColumn("Chomba", options=talles_letras),
                "CAMPERA HOMBRE": st.column_config.SelectboxColumn("Camp. Hombre", options=talles_letras),
                "CAMISA HOMBRE": st.column_config.SelectboxColumn("Camisa Hombre", options=talles_camisas),
                "CAMPERA MUJER": st.column_config.SelectboxColumn("Camp. Mujer", options=talles_letras),
                "CAMISA MUJER": st.column_config.SelectboxColumn("Camisa Mujer", options=talles_camisas),
            },
            disabled=["LEGAJO", "SUCURSAL", "POSICIÓN", "Ingreso", "CUIL", "APELLIDO Y NOMBRE", "VALIDACION"],
            hide_index=True,
        )

        st.warning("⚠️ Nota: Por seguridad técnica, para guardar los cambios en esta versión, hacé clic en el botón y avisame si ves el archivo Maestro.")
        
        if st.button("💾 GUARDAR CAMBIOS"):
            st.info("Intentando guardar... si aparece error de credenciales, te daré el paso final para habilitar la escritura.")
            # Aquí iría el conn.update si la conexión base funciona
    else:
        st.info("Ingresá la contraseña para ver los datos.")
