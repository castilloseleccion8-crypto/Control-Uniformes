# ===================== FUNCIÓN PDF CORREGIDA =====================
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
    
    # Encabezados del PDF
    cols_display = ["Empleado", "Pantalon", "Chomba", "Camp.H", "Cam.H", "Camp.M", "Cam.M"]
    # Mapeo exacto a las columnas del DataFrame
    cols_reales = ["APELLIDO Y NOMBRE", "PANTALON GRAFA", "CHOMBA MANGAS LARGAS", 
                   "CAMPERA HOMBRE", "CAMISA HOMBRE", "CAMPERA MUJER", "CAMISA MUJER"]
    
    widths = [60, 22, 22, 22, 22, 22, 22]
    
    # Dibujar Cabecera
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", "B", 8)
    for i, col in enumerate(cols_display):
        pdf.cell(widths[i], 7, col, border=1, fill=True, align="C")
    pdf.ln()
    
    # Dibujar Filas
    pdf.set_font("Arial", "", 7)
    for _, row in df_para_pdf.iterrows():
        for i, col_name in enumerate(cols_reales):
            val = str(row[col_name]).replace("🚫 ", "").replace("👉 ", "")
            if val in ["None", "nan", "1", "1.0", "ELEGIR TALLE", "NO APLICA"]:
                val = ""
            # Si el valor es "NO APLICA" en el original, lo dejamos vacío o con un guión
            if "NO APLICA" in str(row[col_name]):
                val = "-"
                
            pdf.cell(widths[i], 7, val, border=1, align="C")
        pdf.ln()
    
    return bytes(pdf.output())

# ... (resto de tu código de conexión y login) ...

# ===================== DENTRO DEL BOTÓN GUARDAR =====================
# Cuando llames a la función, pasale el 'edited_df' completo:
if st.button("GUARDAR Y REGISTRAR"):
    try:
        # (Aquí va tu lógica de guardado en GSheets que ya tienes)
        
        ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # CAMBIO AQUÍ: Pasamos el DataFrame directamente, no una lista
        pdf_bytes = generar_pdf(sucursal_sel, ahora, edited_df) 
        
        st.success("✅ Datos guardados correctamente.")
        st.download_button(
            "DESCARGAR ACUSE PDF",
            pdf_bytes,
            f"Acuse_{sucursal_sel}.pdf",
            "application/pdf"
        )
        st.balloons()
    except Exception as e:
        st.error("⚠️ ERROR AL GUARDAR. INTENTE NUEVAMENTE.")
