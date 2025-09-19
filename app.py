import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import date, timedelta

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

# Sección: Ventas Diarias (nuevo diseño semanal)
if opcion == "Ventas Diarias":
    st.markdown("## 📋 Registro Semanal por Máquina")
    fecha_lunes = st.date_input("Selecciona el lunes de la semana", help="Elige el lunes para registrar la semana")
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
    fechas_dia = [fecha_lunes + timedelta(days=i) for i in range(6)]

    maquinas = [
        "Motomall", "Unidad", "Norte", "Buses",
        "Paquetex", "Dekohouse", "Caldas", "Maquina 8"
    ]

    ventas_por_maquina = {m: 0 for m in maquinas}
    ventas_por_dia = {d: 0 for d in dias}

    for maquina in maquinas:
        st.markdown(f"### {maquina}")
        ventas = []
        egresos = []
        netos = []

        cols = st.columns(len(dias))
        for i, dia in enumerate(dias):
            with cols[i]:
                st.markdown(f"**{dia} ({fechas_dia[i]})**")
                venta = st.number_input(f"Ventas", min_value=0, step=1, key=f"{maquina}_{dia}_v")
                egreso = st.number_input(f"Egresos", min_value=0, step=1, key=f"{maquina}_{dia}_e")
                neto = venta - egreso
                fondo = round(neto * 0.05)
                st.write(f"Neto: ${neto}")
                st.write(f"Fondo: ${fondo}")
                ventas.append(venta)
                egresos.append(egreso)
                netos.append(neto)
                ventas_por_maquina[maquina] += venta
                ventas_por_dia[dia] += venta

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

    # Gráfica: Ventas por máquina
    st.markdown("## 📊 Ventas totales por máquina en la semana")
    df_maquinas = pd.DataFrame({
        "Máquina": list(ventas_por_maquina.keys()),
        "Ventas": list(ventas_por_maquina.values())
    })
    st.bar_chart(df_maquinas.set_index("Máquina"))

    # Gráfica: Días con más ventas
    st.markdown("## 📈 Días con más ventas en la semana")
    df_dias = pd.DataFrame({
        "Día": list(ventas_por_dia.keys()),
        "Ventas": list(ventas_por_dia.values())
    })
    st.line_chart(df_dias.set_index("Día"))

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
        df_maquinas = pd.DataFrame(list(totales.items()),