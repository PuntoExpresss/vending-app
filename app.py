import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import date, timedelta
import io

# Festivos Colombia 2025
festivos_2025 = {
    "2025-01-01", "2025-01-06", "2025-03-24", "2025-04-17", "2025-04-18",
    "2025-05-01", "2025-06-02", "2025-06-23", "2025-06-30", "2025-07-20",
    "2025-08-07", "2025-08-18", "2025-10-13", "2025-11-03", "2025-11-17",
    "2025-12-08", "2025-12-25"
}

# Configuración visual
st.set_page_config(page_title="Sistema de Vending", page_icon="🟢", layout="wide")
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Green_circle_icon.svg/1024px-Green_circle_icon.svg.png",
    width=60
)
st.sidebar.title("Menú")
opcion = st.sidebar.radio("Ir a:", ["Dashboard", "Ventas Semanales", "Historial", "Reportes"])

# Conexión a base de datos
conn = sqlite3.connect("ventas_semanales.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS resumen_semanal (
    semana TEXT,
    fecha TEXT,
    maquina TEXT,
    dia TEXT,
    ventas INTEGER,
    egresos INTEGER
)
""")
conn.commit()

#
# Sección: Ventas Semanales (Editable + Export)
#
if opcion == "Ventas Semanales":
    st.title("📆 Informe Semanal Editable")

    # 1. Selección de semana y año
    col1, col2 = st.columns(2)
    with col1:
        semana_num = st.number_input("Número de semana", min_value=1, max_value=52, value=38)
    with col2:
        año = st.number_input("Año", min_value=2020, max_value=2030, value=2025)

    # 2. Generación automática de fechas (lunes a viernes)
    lunes = date.fromisocalendar(año, semana_num, 1)
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    fechas = [lunes + timedelta(days=i) for i in range(5)]
    rango = f"{fechas[0]} a {fechas[-1]}"
    st.subheader(f"📅 Semana {semana_num} ({rango})")

    # 3. Leer datos existentes
    df_existente = pd.read_sql_query(
        "SELECT * FROM resumen_semanal WHERE fecha BETWEEN ? AND ? ORDER BY maquina, fecha",
        conn, params=(str(fechas[0]), str(fechas[-1]))
    )

    maquinas = [
        "Motomall", "Unidad", "Norte", "Buses",
        "Paquetex", "Dekohouse", "Caldas", "Maquina 8"
    ]
    registros = []

    st.info("✏️ Edita los valores y haz clic en Guardar para actualizar esta semana.")

    # 4. Formulario editable con valores precargados
    for maquina in maquinas:
        st.markdown(f"### {maquina}")
        cols = st.columns(5)
        for i, fecha in enumerate(fechas):
            dia = dias_semana[i]
            fecha_str = str(fecha)

            # obtener valores previos si existen
            fila = df_existente[
                (df_existente["maquina"] == maquina) &
                (df_existente["fecha"] == fecha_str)
            ]
            venta_valor = int(fila["ventas"].values[0]) if not fila.empty else 0
            egreso_valor = int(fila["egresos"].values[0]) if not fila.empty else 0

            with cols[i]:
                venta = st.number_input(
                    f"{dia} Ventas",
                    min_value=0, step=1, value=venta_valor,
                    key=f"{maquina}_{dia}_v"
                )
                egreso = st.number_input(
                    f"{dia} Egresos",
                    min_value=0, step=1, value=egreso_valor,
                    key=f"{maquina}_{dia}_e"
                )
                registros.append((
                    f"Semana {semana_num}", fecha_str, maquina, dia, venta, egreso
                ))

    # 5. Guardar cambios
    if st.button("💾 Guardar semana"):
        # eliminar registros anteriores de la semana
        cursor.execute(
            "DELETE FROM resumen_semanal WHERE fecha BETWEEN ? AND ?",
            (str(fechas[0]), str(fechas[-1]))
        )
        conn.commit()

        # insertar nuevos registros
        cursor.executemany(
            "INSERT INTO resumen_semanal VALUES (?, ?, ?, ?, ?, ?)",
            registros
        )
        conn.commit()
        st.success("✅ Semana actualizada correctamente")

        # recargar datos para métricas y export
        df_existente = pd.read_sql_query(
            "SELECT * FROM resumen_semanal WHERE fecha BETWEEN ? AND ? ORDER BY maquina, fecha",
            conn, params=(str(fechas[0]), str(fechas[-1]))
        )

    # 6. Si hay datos, mostrar métricas, gráficas y exportar
    if not df_existente.empty:
        df_existente["neto"] = df_existente["ventas"] - df_existente["egresos"]
        df_existente["fondo"] = df_existente["neto"] * 0.05

        total_ventas = df_existente["ventas"].sum()
        total_egresos = df_existente["egresos"].sum()
        total_neto = df_existente["neto"].sum()
        fondo_total = round(total_neto * 0.05)
        dias_con_ventas = df_existente[df_existente["ventas"] > 0]["fecha"].nunique()
        promedio_diario = round(total_ventas / dias_con_ventas, 2) if dias_con_ventas else 0

        st.markdown("### 📊 Totales Semanales")
        c1, c2, c3 = st.columns(3)
        c1.metric("🔢 Total ventas", f"${total_ventas}")
        c2.metric("📉 Total egresos", f"${total_egresos}")
        c3.metric("💰 Profit semanal", f"${total_neto}")

        c4, c5 = st.columns(2)
        c4.metric("📈 Promedio diario", f"${promedio_diario}")
        c5.metric("🛟 Fondo emergencia (5%)", f"${fondo_total}")

        # gráfica: días con más ventas
        df_dias = df_existente.groupby("dia")["ventas"].sum().reset_index()
        fig1 = px.bar(
            df_dias, x="dia", y="ventas",
            title="📅 Días con más ventas",
            color="dia"
        )
        st.plotly_chart(fig1, use_container_width=True)

        # gráfica: totales por máquina
        df_maquinas = df_existente.groupby("maquina")["ventas"].sum().reset_index()
        fig2 = px.bar(
            df_maquinas, x="maquina", y="ventas",
            title="🏭 Ventas por máquina",
            color="maquina"
        )
        st.plotly_chart(fig2, use_container_width=True)

        # exportar a Excel
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df_existente.to_excel(
                writer, index=False,
                sheet_name=f"Semana_{semana_num}"
            )
        st.download_button(
            label="📥 Exportar informe semanal a Excel",
            data=excel_buffer.getvalue(),
            file_name=f"informe_semanal_{semana_num}_{año}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

#
# Sección: Dashboard
#
elif opcion == "Dashboard":
    st.markdown("### 📊 Análisis Semanal Actual")
    df = pd.read_sql_query("SELECT * FROM resumen_semanal ORDER BY fecha DESC", conn)
    if not df.empty:
        semana_actual = df["semana"].max()
        semana = df[df["semana"] == semana_actual].copy()
        semana["neto"] = semana["ventas"] - semana["egresos"]
        fondo_emergencia = round(semana["neto"].sum() * 0.05)

        st.metric("💰 Profit semanal", f"${semana['neto'].sum()}")
        st.metric("🛟 Fondo emergencia (5%)", f"${fondo_emergencia}")

        df_maquinas = semana.groupby("maquina")["ventas"].sum().reset_index()
        fig = px.bar(
            df_maquinas, x="maquina", y="ventas",
            title="Máquinas más vendidas esta semana",
            color="maquina"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos registrados aún.")

#
# Sección: Historial
#
elif opcion == "Historial":
    st.markdown("### 📋 Historial Completo")
    df = pd.read_sql_query("SELECT * FROM resumen_semanal ORDER BY fecha DESC", conn)
    st.dataframe(df)

#
# Sección: Reportes
#
elif opcion == "Reportes":
    st.markdown("### 📥 Descargar Historial")
    df = pd.read_sql_query("SELECT * FROM resumen_semanal ORDER BY fecha DESC", conn)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📄 Descargar CSV",
        data=csv,
        file_name="resumen_semanal.csv",
        mime="text/csv"
    )
