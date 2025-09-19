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

# Sección: Ventas Diarias
if opcion == "Ventas Diarias":
    st.markdown("## 🧮 Ingresar Ventas del Día")
    fecha = st.date_input("Fecha", value=date.today())

    col1, col2, col3 = st.columns(3)
    with col1:
        agua = st.number_input("Máquina Agua", min_value=0, step=1)
        galletas = st.number_input("Máquina Galletas", min_value=0, step=1)
    with col2:
        cafe = st.number_input("Máquina Café", min_value=0, step=1)
        barra = st.number_input("Máquina Barras", min_value=0, step=1)
    with col3:
        jugo = st.number_input("Máquina Jugo", min_value=0, step=1)
        energizante = st.number_input("Máquina Energizante", min_value=0, step=1)

    egresos = st.number_input("💸 Egresos del día", min_value=0, step=1)
    total = agua + cafe + jugo + galletas + barra + energizante

    st.metric("🧾 Total ventas", f"{total} unidades")

    cursor.execute("SELECT fecha FROM ventas_diarias WHERE fecha = ?", (str(fecha),))
    existe = cursor.fetchone()

    if existe:
        st.warning("⚠️ Ya hay ventas registradas para esta fecha.")
    elif st.button("Guardar ventas"):
        cursor.execute("""
            INSERT INTO ventas_diarias (
                fecha, maquina_agua, maquina_cafe, maquina_jugo,
                maquina_galletas, maquina_barra, maquina_energizante,
                egresos, total
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(fecha), agua, cafe, jugo, galletas, barra, energizante, egresos, total))
        conn.commit()
        st.success("✅ Ventas guardadas correctamente")

# Sección: Dashboard semanal
elif opcion == "Dashboard":
    st.markdown("### 📊 Análisis semanal")
    df = pd.read_sql_query("SELECT * FROM ventas_diarias ORDER BY fecha DESC", conn)

    if not df.empty:
        semana = df.tail(6)  # Últimos 6 días (lunes a sábado)
        profit = semana["total"].sum() - semana["egresos"].sum()
        fondo_emergencia = round(profit * 0.05)

        st.metric("💰 Profit semanal", f"${profit}")
        st.metric("🛟 Fondo de emergencia (5%)", f"${fondo_emergencia}")

        # Máquina más vendida
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
