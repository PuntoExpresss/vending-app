import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import date

# Configuración de página
st.set_page_config(
    page_title="Sistema de Vending",
    page_icon="🟢",
    layout="wide"
)

# Estilos personalizados
st.markdown("""
    <style>
    .main {
        background-color: #F5F5F5;
    }
    h1, h2, h3 {
        color: #007A5E;
    }
    .stButton>button {
        background-color: #007A5E;
        color: white;
        border: none;
        padding: 0.5em 1em;
        font-weight: bold;
    }
    .stSidebar {
        background-color: #FFFFFF;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar de navegación
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Green_circle_icon.svg/1024px-Green_circle_icon.svg.png", width=60)
st.sidebar.title("Menú")
opcion = st.sidebar.radio("Ir a:", ["Dashboard", "Ventas Semanales", "Historial", "Reportes"])

# Cabecera principal
st.title("📈 Sistema de Reposición de Máquinas Vending")
st.subheader("Control, visualización y eficiencia en tiempo real")

# Conexión a la base de datos
conn = sqlite3.connect("ventas.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS semanales (
    fecha TEXT,
    maquina1 INTEGER,
    maquina2 INTEGER,
    maquina3 INTEGER,
    maquina4 INTEGER,
    maquina5 INTEGER,
    maquina6 INTEGER,
    total INTEGER
)
""")
conn.commit()

# Simulación de datos para Dashboard
df = pd.DataFrame({
    "Fecha": pd.date_range("2025-09-01", periods=5),
    "Producto": ["Agua", "Galletas", "Jugo", "Café", "Barra"],
    "Cantidad": [20, 35, 15, 40, 25]
})

# Sección: Dashboard
if opcion == "Dashboard":
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### 📊 Reposición por producto")
        fig = px.bar(df, x="Producto", y="Cantidad", color="Producto", title="Reposiciones", color_discrete_sequence=["#007A5E"])
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("### 📦 Totales")
        st.metric("Total productos", df["Cantidad"].sum())
        st.metric("Productos únicos", df["Producto"].nunique())

# Sección: Ventas Semanales
elif opcion == "Ventas Semanales":
    st.markdown("## 🧮 Ingresar Ventas Semanales")
    col1, col2, col3 = st.columns(3)
    with col1:
        maquina1 = st.selectbox("Máquina #1", options=list(range(0, 101)), index=0)
        maquina4 = st.selectbox("Máquina #4", options=list(range(0, 101)), index=0)
    with col2:
        maquina2 = st.selectbox("Máquina #2", options=list(range(0, 101)), index=0)
        maquina5 = st.selectbox("Máquina #5", options=list(range(0, 101)), index=0)
    with col3:
        maquina3 = st.selectbox("Máquina #3", options=list(range(0, 101)), index=0)
        maquina6 = st.selectbox("Máquina #6", options=list(range(0, 101)), index=0)

    total_ventas = sum([maquina1, maquina2, maquina3, maquina4, maquina5, maquina6])
    st.metric("🧾 Total semanal", f"{total_ventas} unidades")

    if st.button("Guardar ventas"):
        hoy = str(date.today())
        cursor.execute("""
            INSERT INTO semanales (fecha, maquina1, maquina2, maquina3, maquina4, maquina5, maquina6, total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (hoy, maquina1, maquina2, maquina3, maquina4, maquina5, maquina6, total_ventas))
        conn.commit()
        st.success("✅ Ventas guardadas correctamente")

# Sección: Historial
elif opcion == "Historial":
    st.markdown("### 📋 Historial de ventas semanales")
    historial = pd.read_sql_query("SELECT * FROM semanales ORDER BY fecha DESC", conn)
    st.dataframe(historial)

# Sección: Reportes
elif opcion == "Reportes":
    st.markdown("### 📥 Descargar reporte")
    historial = pd.read_sql_query("SELECT * FROM semanales ORDER BY fecha DESC", conn)
    csv = historial.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar CSV",
        data=csv,
        file_name="ventas_semanales.csv",
        mime="text/csv",
        help="Descarga el historial en formato Excel"
    )
