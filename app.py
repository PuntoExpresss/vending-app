import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import date, timedelta
import io
from xhtml2pdf import pisa

# Configuración visual
st.set_page_config(page_title="Sistema de Vending", page_icon="🟢", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #F5F5F5; }
    h1, h2, h3 { color: #007A5E; }
    .stButton>button {
        background-color: #007A5E;
        color: white;
        border: none;
        padding: 0.5em 1em;
        font-weight: bold;
    }
    .stSidebar { background-color: #FFFFFF; }
    </style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Green_circle_icon.svg/1024px-Green_circle_icon.svg.png", width=60)
st.sidebar.title("Menú")
opcion = st.sidebar.radio("Ir a:", ["Dashboard", "Ventas Diarias", "Historial", "Reportes"])

# Conexión a base de datos
conn = sqlite3.connect("ventas_semanales.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS resumen_semanal (
    semana TEXT,
    maquina TEXT,
    dia TEXT,
    ventas INTEGER,
    egresos INTEGER
)
""")
conn.commit()

# Sección: Ventas Diarias
if opcion == "Ventas Diarias":
    st.markdown("## 📋 Registro Semanal por Máquina")
    fecha_lunes = st.date_input("Selecciona el lunes de la semana", help="Elige el lunes para registrar la semana")
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
    fechas_dia = [fecha_lunes + timedelta(days=i) for i in range(6)]

    maquinas = [
        "Motomall", "Unidad", "Norte", "Buses",
        "Paquetex", "Dekohouse", "Caldas", "Maquina 8"
    ]

    registros = []
    ventas_por_maquina = {m: 0 for m in maquinas}
    ventas_por_dia = {d: 0 for d in dias}

    for maquina in maquinas:
        st.markdown(f"### {maquina}")
        cols = st.columns(len(dias))
        for i, dia in enumerate(dias):
            with cols[i]:
                st.markdown(f"**{dia} ({fechas_dia[i]})**")
                venta = st.number_input(f"Ventas", min_value=0, step=1, key=f"{maquina}_{dia}_v")
                egreso = st.number_input(f"Egresos", min_value=0, step=1, key=f"{maquina}_{dia}_e")
                registros.append((str(fecha_lunes), maquina, dia, venta, egreso))
                st.write(f"Neto: ${venta - egreso}")
                st.write(f"Fondo: ${round((venta - egreso) * 0.05)}")
                ventas_por_maquina[maquina] += venta
                ventas_por_dia[dia] += venta

    if st.button("💾 Guardar semana"):
        cursor.executemany("INSERT INTO resumen_semanal VALUES (?, ?, ?, ?, ?)", registros)
        conn.commit()
        st.success("✅ Semana guardada correctamente")

    # Selector de semana registrada
    semanas_registradas = pd.read_sql_query("SELECT DISTINCT semana FROM resumen_semanal ORDER BY semana DESC", conn)
    if not semanas_registradas.empty:
        semana_seleccionada = st.selectbox("📅 Ver datos de semana registrada", semanas_registradas["semana"])
        df = pd.read_sql_query("SELECT * FROM resumen_semanal WHERE semana = ?", conn, params=(semana_seleccionada,))
        st.markdown(f"## 📊 Datos de la semana: {semana_seleccionada}")
        st.dataframe(df)

        # Gráfica por máquina
        df_maquinas = df.groupby("maquina")["ventas"].sum().reset_index()
        fig1 = px.bar(df_maquinas, x="maquina", y="ventas", title="Ventas totales por máquina", color="maquina", color_discrete_sequence=["#007A5E"])
        st.plotly_chart(fig1, use_container_width=True)

        # Gráfica por día
        df_dias = df.groupby("dia")["ventas"].sum().reset_index()
        fig2 = px.line(df_dias, x="dia", y="ventas", title="Días con más ventas en la semana", markers=True)
        st.plotly_chart(fig2, use_container_width=True)

        # Exportar a Excel
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Semana')
        st.download_button(
            label="📥 Exportar a Excel",
            data=excel_buffer.getvalue(),
            file_name=f"reporte_{semana_seleccionada}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Exportar a PDF
        html = f"<h1>Reporte Semana {semana_seleccionada}</h1>{df.to_html(index=False)}"
        pdf_buffer = io.BytesIO()
        pisa.CreatePDF(io.StringIO(html), dest=pdf_buffer)
        st.download_button(
            label="📄 Exportar a PDF",
            data=pdf_buffer.getvalue(),
            file_name=f"reporte_{semana_seleccionada}.pdf",
            mime="application/pdf"
        )

# Sección: Dashboard
elif opcion == "Dashboard":
    st.markdown("### 📊 Análisis semanal")
    df = pd.read_sql_query("SELECT * FROM resumen_semanal ORDER BY semana DESC", conn)
    if not df.empty:
        semana_actual = df["semana"].max()
        semana = df[df["semana"] == semana_actual]
        profit = (semana["ventas"] - semana["egresos"]).sum()
        fondo_emergencia = round(profit * 0.05)

        st.metric("💰 Profit semanal", f"${profit}")
        st.metric("🛟 Fondo de emergencia (5%)", f"${fondo_emergencia}")
        st.latex(r"\text{Fondo} = (\text{Ventas} - \text{Egresos}) \times 0.05")

        df_maquinas = semana.groupby("maquina")["ventas"].sum().reset_index()
        fig = px.bar(df_maquinas, x="maquina", y="ventas", title="Máquinas más vendidas esta semana", color="maquina", color_discrete_sequence=["#007A5E"])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos registrados aún.")

# Sección: Historial
elif opcion == "Historial":
    st.markdown("### 📋 Historial completo")
    df = pd.read_sql_query("SELECT * FROM resumen_semanal ORDER BY semana DESC", conn)
    st.dataframe(df)

# Sección: Reportes
elif opcion == "Reportes":
    st.markdown("### 📥 Descargar reporte")
    df = pd.read_sql_query("SELECT * FROM resumen_semanal ORDER BY semana DESC", conn)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar CSV",
        data=csv,
        file_name="resumen_semanal.csv",
        mime="text/csv",
        help="Descarga el historial en formato Excel"
    )
