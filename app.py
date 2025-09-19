import streamlit as st
from openpyxl import Workbook
import sqlite3
import matplotlib.pyplot as plt

st.set_page_config(page_title="Sistema de Reabastecimiento", layout="centered")

st.title("📦 Sistema de Reabastecimiento Inteligente")
st.subheader("Ingresar Ventas Semanales")

# Entradas de ventas
ventas = []
for i in range(8):
    venta = st.number_input(f"Máquina #{i+1}", min_value=0, step=100, key=f"maq{i}")
    ventas.append(venta)

# Función para evaluar frecuencia y estado
def evaluar(venta):
    if venta > 1600:
        return "Alta", "Crítica"
    elif venta > 1300:
        return "Media", "Normal"
    else:
        return "Baja", "Estable"

# Botón para calcular
if st.button("Calcular Ranking y Programación"):
    maquinas = [f"Máquina #{i+1}" for i in range(len(ventas))]
    ranking = sorted(zip(maquinas, ventas), key=lambda x: x[1], reverse=True)

    st.markdown("### 📊 Ranking Semanal")
    for i, (maq, ven) in enumerate(ranking, start=1):
        freq, estado = evaluar(ven)
        st.write(f"{i}. {maq} - Ventas: {ven} - Frecuencia: {freq} - Estado: {estado}")

    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
    programacion = {dia: [] for dia in dias}
    for i, (maq, _) in enumerate(ranking):
        dia = dias[i % len(dias)]
        programacion[dia].append(maq)

    st.markdown("### 📅 Programación Semanal")
    for dia in dias:
        maquinas_dia = ", ".join(programacion[dia])
        st.write(f"{dia}: {maquinas_dia}")

    # Gráfico de ventas
    st.markdown("### 📈 Gráfico de Ventas por Máquina")
    fig, ax = plt.subplots()
    maquinas_grafico = [maq for maq, _ in ranking]
    ventas_grafico = [ven for _, ven in ranking]
    ax.bar(maquinas_grafico, ventas_grafico, color='skyblue')
    ax.set_ylabel("Ventas Semanales")
    ax.set_xlabel("Máquinas")
    ax.set_title("Ranking de Ventas")
    st.pyplot(fig)

    # Exportar a Excel
    if st.button("Exportar a Excel"):
        wb = Workbook()
        ws1 = wb.active
        ws1.title = "Ranking Semanal"
        ws1.append(["Posición", "Máquina", "Ventas", "Frecuencia", "Estado"])
        for i, (maq, ven) in enumerate(ranking, start=1):
            freq, estado = evaluar(ven)
            ws1.append([i, maq, ven, freq, estado])
        ws2 = wb.create_sheet("Programación Semanal")
        for dia, maquinas in programacion.items():
            ws2.append([dia] + maquinas)
        wb.save("reabastecimiento.xlsx")
        st.success("Archivo Excel guardado como 'reabastecimiento.xlsx'")

    # Guardar en base de datos
    if st.button("Guardar en Base de Datos"):
        conn = sqlite3.connect("reabastecimiento.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ranking (
                posicion INTEGER,
                maquina TEXT,
                ventas INTEGER,
                frecuencia TEXT,
                estado TEXT
            )
        """)
        cursor.execute("DELETE FROM ranking")
        for i, (maq, ven) in enumerate(ranking, start=1):
            freq, estado = evaluar(ven)
            cursor.execute("INSERT INTO ranking VALUES (?, ?, ?, ?, ?)", (i, maq, ven, freq, estado))
        conn.commit()
        conn.close()
        st.success("Datos almacenados en la base de datos.")
