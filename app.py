import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import date

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

# Cabecera
st.title("📈 Sistema de Reposición de Máquinas Vending")
st.subheader("Control, visualización y eficiencia en tiempo real")

# Conexión a base de datos
conn = sqlite3.connect("ventas.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS ventas_diarias (
    fecha TEXT PRIMARY KEY,
    maquina_agua INTEGER,
    maquina_cafe INTEGER,
    maquina_jugo INTEGER,
    maquina_galletas INTEGER,
    maquina_barra INTEGER,
    maquina_energizante INTEGER,
    egresos INTEGER,
    total INTEGER
)
""")
conn.commit()

# Sección: Ventas Diarias (nuevo diseño tipo tabla)
if opcion == "Ventas Diarias":
    st.markdown("## 📋 Registro Semanal por Máquina")
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    maquinas = [
        "Máquina 1 - Norte", "Máquina 2", "Máquina 3", "Máquina 4",
        "Máquina 5", "Máquina 6", "Máquina 7", "Máquina 8"
    ]

    for maquina in maquinas:
        st.markdown(f"### {maquina}")
        ventas = []
        egresos = []
        netos = []

        cols = st.columns(len(dias))
        for i, dia in enumerate(dias):
            with cols[i]:
                st.markdown(f"**{dia}**")
                venta = st.number_input(f"Ventas", min_value=0, step=1, key=f"{maquina}_{dia}_v")
                egreso = st.number_input(f"Egresos", min_value=0, step=1, key=f"{maquina}_{dia}_e")
                neto = venta - egreso
                st.write(f"Neto: ${neto}")
                ventas.append(venta)
                egresos.append(egreso)
                netos.append(neto)

        total_ventas = sum(ventas)
        total_egresos = sum(egresos)
        profit_semanal = sum(netos)
        dias_activos = sum(1 for v in ventas if v > 0)
        promedio_dia = round(total_ventas / dias_activos, 2) if dias_activos else 0
        fondo_emergencia = round(profit_semanal * 0.05)

        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🔢 Total Semana", f"${total_ventas}")
        col2.metric("💰 Profit Semanal", f"${profit_semanal}")
        col3.metric("📈 Promedio/Día", f"${promedio_dia}")
        col4.metric("🛟 Fondo Emergencia (5%)", f"${fondo_emergencia}")

# Sección: Dashboard semanal
elif opcion == "Dashboard":
    st.markdown("### 📊 Análisis semanal")
    df = pd.read_sql_query("SELECT * FROM ventas_diarias ORDER BY fecha DESC", conn)

    if not df.empty:
        semana = df.tail(6)
        profit = semana["total"].sum() - semana["egresos"].sum()
        fondo_emergencia = round(profit * 0.05)

        st.metric("💰 Profit semanal", f"${profit}")
        st.metric("🛟 Fondo de emergencia (5%)", f"${fondo_emergencia}")
        st.markdown("**Fórmula del fondo de emergencia:**")
        st.latex(r"\text{Fondo} = (\text{Ventas} - \text{Egresos}) \times 0.05")

        maquinas = ["maquina_agua", "maquina_cafe", "maquina_jugo", "maquina_galletas", "maquina_barra", "maquina_energizante"]
        totales = {m: semana[m].sum() for m in maquinas}
        df_maquinas = pd.DataFrame(list(totales.items()), columns=["Máquina", "Ventas"])
        df_maquinas["Máquina"] = df_maquinas["Máquina"].str.replace("maquina_", "").str.capitalize()

        fig = px.bar(df_maquinas, x="Máquina", y="Ventas", color="Máquina", title="Máquinas más vendidas esta semana", color_discrete_sequence=["#007A5E"])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos registrados aún.")

# Sección: Historial
elif opcion == "Historial":
    st.markdown("### 📋 Historial completo")
    df = pd.read_sql_query("SELECT * FROM ventas_diarias ORDER BY fecha DESC", conn)
    st.dataframe(df)

# Sección: Reportes
elif opcion == "Reportes":
    st.markdown("### 📥 Descargar reporte")
    df = pd.read_sql_query("SELECT * FROM ventas_diarias ORDER BY fecha DESC", conn)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar CSV",
        data=csv,
        file_name="ventas_diarias.csv",
        mime="text/csv",
        help="Descarga el historial en formato Excel"
    )
