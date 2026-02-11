import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Gestión de Uniformes", layout="wide")

st.title("Carga de Talles - Gestión de Uniformes")

# --- CONEXIÓN ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0)
    df.columns = [str(c).strip() for c in df.columns]
except Exception as e:
    st.error(f"❌ Error de conexión: {e}")
    st.stop()

# --- LOGIN ---
st.sidebar.header("Acceso Sucursales")
sucursales = sorted(df["SUCURSAL"].dropna().unique())
sucursal_sel = st.sidebar.selectbox("Seleccione su Sucursal", sucursales)

pass_correcta = f"{sucursal_sel.lower().replace(' ', '')}2026"
password = st.sidebar.text_input("Contraseña", type="password")

if password == pass_correcta:
    st.success(f"Sesión iniciada: {sucursal_sel}")
    
    mask_sucursal = df["SUCURSAL"] == sucursal_sel
    df_sucursal = df[mask_sucursal].copy()

    # --- LISTAS DE TALLES PURAS (Sin textos de ayuda) ---
    t_num = [str(i) for i in range(36, 64, 2)]
    t_let = ["S", "M", "L", "XL", "XXL", "XXXL", "4XL", "5XL"]
    t_cam = [str(i) for i in range(38, 62, 2)]

    prendas = ["PANTALON GRAFA", "CHOMBA MANGAS LARGAS", "CAMPERA HOMBRE", "CAMISA HOMBRE", "CAMPERA MUJER", "CAMISA MUJER"]

    # --- PROCESAMIENTO DE DATOS ---
    for prenda in prendas:
        df_sucursal[prenda] = df_sucursal[prenda].astype(str).str.strip().replace({'nan': '', 'None': '', '0.0': '', '0': ''})
        # Marcamos internamente las que son "1" para saber que son editables
        # Pero en la vista las dejamos vacías para que el placeholder actúe
        df_sucursal.loc[df_sucursal[prenda] == "1", prenda] = None 

    st.write(f"### Planilla de {sucursal_sel}")
    st.info("💡 Solo podés editar las celdas donde aparece 'Seleccionar...'. Las celdas grises están bloqueadas.")

    # --- CONFIGURACIÓN DEL EDITOR ---
    config_visual = {
        "APELLIDO Y NOMBRE": st.column_config.Column("Empleado", disabled=True),
    }

    for prenda in prendas:
        # Definir opciones
        if "PANTALON" in prenda: opts = t_num
        elif "CAMISA" in prenda: opts = t_cam
        else: opts = t_let
        
        # Lógica: Si el empleado NO tiene un pedido (celda vacía), desactivamos la columna para esa fila
        # Como Streamlit no permite desactivar 'celdas' individuales fácil, usamos el Placeholder
        config_visual[prenda] = st.column_config.SelectboxColumn(
            prenda.replace("PANTALON GRAFA", "PANTALÓN DE GRAFA"),
            options=opts,
            placeholder="🚫 NO APLICA", # Este texto aparece en gris y no es seleccionable
            width="medium"
        )

    # Creamos un DF limpio para editar
    # Las celdas que eran "" (No aplica) se mantienen vacías y mostrarán el placeholder gris
    edited_df = st.data_editor(
        df_sucursal[["APELLIDO Y NOMBRE"] + prendas],
        column_config=config_visual,
        hide_index=True,
        use_container_width=True
    )

    if st.button("💾 GUARDAR CAMBIOS"):
        with st.spinner("Actualizando Maestro..."):
            try:
                for prenda in prendas:
                    nuevos_valores = edited_df[prenda].values
                    final_save = []
                    
                    # Recuperamos los valores originales para comparar
                    originales = df_sucursal[prenda].values
                    
                    for i, val in enumerate(nuevos_valores):
                        # Si el valor es None (no tocaron la celda)
                        if pd.isna(val) or val == "" or val == "None":
                            # Si originalmente era un pedido (None en nuestra transformación), devolvemos el 1
                            if pd.isna(df_sucursal.iloc[i][prenda]):
                                final_save.append("1")
                            else:
                                final_save.append("")
                        else:
                            final_save.append(val)
                    
                    df.loc[mask_sucursal, prenda] = final_save

                conn.update(data=df)
                st.balloons()
                st.success("✅ Datos guardados correctamente.")
            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")
else:
    if password: st.error("🔑 Contraseña incorrecta")
    else: st.info("Ingrese contraseña para continuar.")
