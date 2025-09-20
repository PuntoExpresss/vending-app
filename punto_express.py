import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import date, timedelta
import io
import random

# Festivos Colombia 2025
festivos_2025 = {
    "2025-01-01", "2025-01-06", "2025-03-24", "2025-04-17", "2025-04-18",
    "2025-05-01", "2025-06-02", "2025-06-23", "2025-06-30", "2025-07-20",
    "2025-08-07", "2025-08-18", "2025-10-13", "2025-11-03", "2025-11-17",
    "2025-12-08", "2025-12-25"
}

# Configuración visual
st.set_page_config(
    page_title="Punto Express | Sistema de Vending",
    page_icon="🟢",
    layout="wide"
)

# Estilos personalizados
st.markdown("""
    <style>
    /* Fondo oscuro del menú lateral */
    [data-testid="stSidebar"] {
        background-color: #1e1e1e;
        padding: 20px;
    }

    /* Forzar color blanco en todo el texto del sidebar */
    [data-testid="stSidebar"] * {
        color: white !important;
    }

    /* Título principal */
    .main-title {
        font-size: 36px;
        font-weight: 700;
        color: #00c853;
        margin-bottom: 0.5rem;
    }

    /* Ocultar footer de Streamlit */
    footer {visibility: hidden;}

    /* Texto flotante en el pie de página */
    .footer-text {
        position: fixed;
        bottom: 10px;
        right: 20px;
        font-size: 12px;
        color: #888;
    }
    </style>
""", unsafe_allow_html=True)

# Título corporativo
st.markdown(
    '<div class="main-title">🟢 Punto Express - Sistema de Vending</div>',
    unsafe_allow_html=True
)
st.markdown("---")

# Conexión a la base de datos
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

# Simulación de ventas (Semana 38) – solo si no existen registros
semana_sim = "Semana 38"
cursor.execute("SELECT COUNT(*) FROM resumen_semanal WHERE semana = ?", (semana_sim,))
existe = cursor.fetchone()[0]

if existe == 0:
    año_sim = 2025
    lunes_sim = date.fromisocalendar(año_sim, 38, 1)
    fechas_sim = [lunes_sim + timedelta(days=i) for i in range(6)]
    maquinas_sim = [
        "Motomall", "Unidad", "Norte", "Buses",
        "Paquetex", "Dekohouse", "Caldas", "Maquina 8"
    ]
    registros_sim = []
    for maquina in maquinas_sim:
        for i, fecha in enumerate(fechas_sim):
            dia = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"][i]
            ventas = random.randint(10000, 30000)
            egresos = random.randint(2000, 8000)
            registros_sim.append((semana_sim, str(fecha), maquina, dia, ventas, egresos))
    cursor.executemany(
        "INSERT INTO resumen_semanal VALUES (?, ?, ?, ?, ?, ?)",
        registros_sim
    )
    conn.commit()

# Menú lateral
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Green_check_icon.svg/1024px-Green_check_icon.svg.png",
    width=60
)
st.sidebar.markdown("## 🟢 Punto Express")
st.sidebar.markdown("### Sistema de Vending")
opcion = st.sidebar.radio(
    "📋 Navegación:",
    ["Dashboard", "Ventas Semanales", "Reabastecimiento", "Historial", "Reportes"]
)
st.markdown(
    '<div class="footer-text">© Punto Express | Última actualización: Septiembre 2025</div>',
    unsafe_allow_html=True
)

#
# Dashboard
#
from fpdf import FPDF
import io
from datetime import date
import re  # Para limpiar emojis del PDF

def limpiar_unicode(texto):
    return re.sub(r'[^\x00-\x7F]+', '', texto)

if opcion == "Dashboard":
    st.header("📊 Dashboard")
    df = pd.read_sql_query("SELECT * FROM resumen_semanal ORDER BY fecha DESC", conn)

    if not df.empty:
        # 🔢 Preparar semanas
        df["semana_num"] = df["semana"].str.extract(r'(\d+)').astype(int)
        semana_actual = df["semana_num"].max()
        semana_anterior = semana_actual - 1

        # 📊 Datos semana actual
        df_sem = df[df["semana_num"] == semana_actual].copy()
        df_sem["neto"] = df_sem["ventas"] - df_sem["egresos"]
        profit = df_sem["neto"].sum()
        fondo = round(profit * 0.05)

        # 📊 Datos semana anterior
        df_prev = df[df["semana_num"] == semana_anterior].copy()
        ventas_actual = df_sem["ventas"].sum()
        ventas_prev = df_prev["ventas"].sum()
        variacion = round(((ventas_actual - ventas_prev) / ventas_prev) * 100, 2) if ventas_prev else 0

        # 📈 Métricas principales
        st.metric("💰 Profit semanal", f"${profit}")
        st.metric("🛟 Fondo emergencia (5%)", f"${fondo}")
        st.metric("📈 Ventas vs semana anterior", f"${ventas_actual:,.0f}", f"{variacion:+.2f}%")

        # 📊 Gráfico por máquina
        df_maq = df_sem.groupby("maquina")["ventas"].sum().reset_index()
        fig = px.bar(df_maq, x="maquina", y="ventas", title=f"Máquinas más vendidas - Semana {semana_actual}", color="maquina")
        st.plotly_chart(fig, use_container_width=True)

        # 📊 Comparativa entre semanas
        df_comp = df[df["semana_num"].isin([semana_anterior, semana_actual])]
        df_comp_sum = df_comp.groupby(["semana_num", "maquina"])["ventas"].sum().reset_index()
        fig2 = px.bar(df_comp_sum, x="maquina", y="ventas", color="semana_num", barmode="group", title="📊 Comparativa por máquina (2 semanas)")
        st.plotly_chart(fig2, use_container_width=True)

        # 🚨 Alertas inteligentes
        lista_alertas = []
        ventas_actual_por_maquina = df_sem.groupby("maquina")["ventas"].sum()
        ventas_prev_por_maquina = df_prev.groupby("maquina")["ventas"].sum()

        for maquina in ventas_actual_por_maquina.index:
            actual = ventas_actual_por_maquina[maquina]
            anterior = ventas_prev_por_maquina.get(maquina, 0)
            if anterior > 0:
                cambio = ((actual - anterior) / anterior) * 100
                if cambio <= -30:
                    lista_alertas.append(f"🔴 {maquina} cayó {abs(round(cambio))}% respecto a la semana anterior.")
                elif cambio >= 20:
                    lista_alertas.append(f"🟢 {maquina} subió {round(cambio)}% respecto a la semana anterior.")
            elif actual > 0:
                lista_alertas.append(f"🟢 {maquina} tuvo ventas esta semana pero estaba en cero la anterior.")

        if profit < 0:
            lista_alertas.append("⚠️ Profit negativo esta semana. Revisa egresos y márgenes.")
        if fondo < 50000:
            lista_alertas.append(f"⚠️ Fondo de emergencia bajo: solo ${fondo:,.0f}")

        if lista_alertas:
            with st.expander("🚨 Alertas inteligentes"):
                for alerta in lista_alertas:
                    st.warning(alerta)

        # 📋 Construir resumen para PDF
        resumen = pd.DataFrame({
            "Métrica": [
                "Total Ventas", "Total Egresos", "Profit Neto",
                "Fondo Emergencia (5%)", "Variación semanal"
            ],
            "Valor": [
                f"${ventas_actual:,.0f}",
                f"${df_sem['egresos'].sum():,.0f}",
                f"${profit:,.0f}",
                f"${fondo:,.0f}",
                f"{variacion:+.2f}%"
            ]
        })

        # 🧾 Clase PDF personalizada
        class PDF(FPDF):
            def header(self):
                self.set_font("Arial", "B", 16)
                self.set_text_color(40, 40, 40)
                self.cell(0, 10, "Puntoexpress - Resumen Ejecutivo", ln=True, align="C")
                self.set_font("Arial", "", 12)
                self.cell(0, 10, f"Semana {semana_actual}", ln=True, align="C")
                self.ln(10)

            def footer(self):
                self.set_y(-15)
                self.set_font("Arial", "I", 8)
                self.set_text_color(100)
                self.cell(0, 10, f"Generado el {date.today()}", align="C")

        # 📄 Generar PDF
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=11)

        for _, row in resumen.iterrows():
            pdf.cell(60, 10, row["Métrica"], border=1)
            pdf.cell(120, 10, str(row["Valor"]), border=1, ln=True)

        if lista_alertas:
            pdf.ln(10)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Observaciones:", ln=True)
            pdf.set_font("Arial", size=11)
            for alerta in lista_alertas:
                texto_limpio = limpiar_unicode(alerta)
                pdf.multi_cell(0, 10, f"- {texto_limpio}")

        # 📥 Botón de descarga
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.markdown("### 📄 Exportación PDF")
        st.download_button(
            label="📄 Exportar resumen en PDF",
            data=pdf_bytes,
            file_name=f"resumen_semana_{semana_actual}.pdf",
            mime="application/pdf"
        )

    else:
        st.info("No hay datos registrados aún.")
#
# ventas Semanales
# 
from datetime import date, timedelta
import io

if opcion == "Ventas Semanales":
    st.title("📆 Informe Semanal Editable")

    # Selección de semana
    col1, col2 = st.columns(2)
    with col1:
        semana_num = st.number_input("Número de semana", 1, 52, 38)
    with col2:
        año = st.number_input("Año", 2020, 2030, 2025)

    lunes = date.fromisocalendar(año, semana_num, 1)
    fechas = [lunes + timedelta(days=i) for i in range(6)]  # lunes a sábado
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
    st.subheader(f"📅 Semana {semana_num}: {fechas[0]} a {fechas[-1]}")

    # Cargar datos existentes
    df_exist = pd.read_sql_query(
        "SELECT * FROM resumen_semanal WHERE fecha BETWEEN ? AND ? ORDER BY maquina, fecha",
        conn, params=(str(fechas[0]), str(fechas[-1]))
    )

    maquinas = [
        "Motomall", "Unidad", "Norte", "Buses",
        "Paquetex", "Dekohouse", "Caldas", "Maquina 8"
    ]
    registros = []

    for maquina in maquinas:
        st.markdown(f"### {maquina}")
        cols = st.columns(6)
        for i, fecha in enumerate(fechas):
            dia = dias_semana[i]
            fecha_str = str(fecha)
            fila = df_exist[
                (df_exist["maquina"] == maquina) &
                (df_exist["fecha"] == fecha_str)
            ]
            venta_val = int(fila["ventas"].values[0]) if not fila.empty else 0
            egreso_val = int(fila["egresos"].values[0]) if not fila.empty else 0
            with cols[i]:
                venta = st.number_input(
                    f"{dia} Ventas", value=venta_val,
                    key=f"{maquina}_{dia}_v"
                )
                egreso = st.number_input(
                    f"{dia} Egresos", value=egreso_val,
                    key=f"{maquina}_{dia}_e"
                )
            registros.append((
                f"Semana {semana_num}", fecha_str, maquina,
                dia, venta, egreso
            ))

    # Guardar datos
    if st.button("💾 Guardar semana"):
        cursor.execute(
            "DELETE FROM resumen_semanal WHERE fecha BETWEEN ? AND ?",
            (str(fechas[0]), str(fechas[-1]))
        )
        conn.commit()
        cursor.executemany(
            "INSERT INTO resumen_semanal VALUES (?, ?, ?, ?, ?, ?)",
            registros
        )
        conn.commit()
        st.success("✅ Semana actualizada")

    # Mostrar totales y gráficos
    df_actualizada = pd.read_sql_query(
        "SELECT * FROM resumen_semanal WHERE fecha BETWEEN ? AND ?",
        conn, params=(str(fechas[0]), str(fechas[-1]))
    )

    if not df_actualizada.empty:
        df_actualizada["neto"] = df_actualizada["ventas"] - df_actualizada["egresos"]
        tv = df_actualizada["ventas"].sum()
        te = df_actualizada["egresos"].sum()
        tn = df_actualizada["neto"].sum()
        dv = df_actualizada[df_actualizada["ventas"] > 0]["fecha"].nunique()
        pdia = round(tv / dv, 2) if dv else 0
        ft = round(tn * 0.05)

        st.markdown("### 📊 Totales Semanales")
        c1, c2, c3 = st.columns(3)
        c1.metric("🔢 Ventas", f"${tv}")
        c2.metric("📉 Egresos", f"${te}")
        c3.metric("💰 Profit", f"${tn}")
        c4, c5 = st.columns(2)
        c4.metric("📈 Promedio diario", f"${pdia}")
        c5.metric("🛟 Fondo 5%", f"${ft}")

        df_d = df_actualizada.groupby("dia")["ventas"].sum().reset_index()
        fig1 = px.bar(df_d, x="dia", y="ventas", title="📅 Días con más ventas", color="dia")
        st.plotly_chart(fig1, use_container_width=True)

        df_m = df_actualizada.groupby("maquina")["ventas"].sum().reset_index()
        fig2 = px.bar(df_m, x="maquina", y="ventas", title="🏭 Ventas por máquina", color="maquina")
        st.plotly_chart(fig2, use_container_width=True)

        # 🏆 Métricas destacadas
        dia_top = df_actualizada.groupby("dia")["ventas"].sum().sort_values(ascending=False).index[0]
        maquinas_top = df_actualizada.groupby("maquina")["ventas"].sum().sort_values(ascending=False).head(4)

        resumen = pd.DataFrame({
            "Métrica": [
                "Total Ventas", "Total Egresos", "Profit Neto",
                "Promedio Diario", "Fondo Emergencia (5%)",
                "Día con más ventas", "Top 4 máquinas"
            ],
            "Valor": [
                f"${tv:,.0f}", f"${te:,.0f}", f"${tn:,.0f}",
                f"${pdia:,.0f}", f"${ft:,.0f}",
                dia_top,
                ", ".join(maquinas_top.index)
            ]
        })

        st.markdown("### 📋 Resumen Ejecutivo")
        st.dataframe(resumen, use_container_width=True)

        # 📥 Exportar datos completos
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df_actualizada.to_excel(writer, index=False, sheet_name=f"Semana_{semana_num}")
        st.download_button(
            "📥 Exportar Excel",
            data=buf.getvalue(),
            file_name=f"ventas_semana_{semana_num}_{año}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # 📥 Exportar resumen ejecutivo
        buf_resumen = io.BytesIO()
        with pd.ExcelWriter(buf_resumen, engine="openpyxl") as writer:
            resumen.to_excel(writer, index=False, sheet_name="Resumen")
        st.download_button(
            "📥 Exportar resumen",
            data=buf_resumen.getvalue(),
            file_name=f"resumen_semana_{semana_num}_{año}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# 🧭 Nueva sección: Reabastecimiento Inteligente
if opcion == "Reabastecimiento":
    st.title("🚚 Reabastecimiento Inteligente")

    col1, col2 = st.columns(2)
    with col1:
        semana_prog = st.number_input("Semana de programación", 2, 52, 39)
    with col2:
        año_prog = st.number_input("Año de programación", 2020, 2030, 2025)

    # Ventas de la semana anterior
    sem_venta = semana_prog - 1
    lunes_v = date.fromisocalendar(año_prog, sem_venta, 1)
    fechas_v = [lunes_v + timedelta(days=i) for i in range(6)]
    df_v = pd.read_sql_query(
        "SELECT * FROM resumen_semanal WHERE fecha BETWEEN ? AND ?",
        conn, params=(str(fechas_v[0]), str(fechas_v[-1]))
    )

    df_rank = df_v.groupby("maquina")["ventas"].sum().reset_index().sort_values("ventas", ascending=False)
    top4 = df_rank.head(4)["maquina"].tolist()

    # Calendario de programación
    lunes_p = date.fromisocalendar(año_prog, semana_prog, 1)
    sched_days = [lunes_p + timedelta(days=i) for i in range(6)]
    dias_nombre = {0:"Lunes",1:"Martes",2:"Miércoles",3:"Jueves",4:"Viernes",5:"Sábado"}
    mapping = {
        "Lunes":   [top4[0], top4[1]],
        "Martes":  [top4[0], top4[2]],
        "Miércoles":[top4[0], top4[1]],
        "Jueves":  [top4[0], top4[3]],
        "Viernes": [top4[0], top4[1]],
        "Sábado":  [top4[2]]
    }

    schedule = {}
    workdays = [d for d in sched_days if str(d) not in festivos_2025]
    holidays = [d for d in sched_days if str(d) in festivos_2025]

    for d in workdays:
        name = dias_nombre[d.weekday()]
        schedule[d] = mapping.get(name, [])

    for h in holidays:
        prev = h - timedelta(days=1)
        if prev in schedule:
            schedule[prev] = top4.copy()

    sat = [d for d in workdays if d.weekday() == 5]
    sat_day = sat[0] if sat else None
    counts = {m: sum(m in v for v in schedule.values()) for m in top4}
    emergent = df_rank["maquina"].tolist()[4] if len(df_rank) > 4 else None
    least = min(counts, key=counts.get)

    opcion_libre = st.radio(
        "¿Cómo asignar espacio libre del sábado?",
        ("Opción A: máquina menos abastecida", "Opción B: máquina emergente")
    )
    flex = least if opcion_libre.startswith("Opción A") else emergent
    if sat_day and flex:
        schedule[sat_day].append(flex)

    st.markdown("### 🏆 Ranking Semanal")
    st.table(df_rank.head(8).reset_index(drop=True))

    data = []
    for d in sorted(schedule):
        data.append({
            "fecha": str(d),
            "día": dias_nombre[d.weekday()],
            "máquinas": ", ".join(schedule[d])
        })
    sched_df = pd.DataFrame(data)
    st.markdown("### 📅 Calendario de Reabastecimiento")
    st.table(sched_df)

    buf2 = io.BytesIO()
    with pd.ExcelWriter(buf2, engine="openpyxl") as writer:
        sched_df.to_excel(writer, index=False, sheet_name=f"Reab_{semana_prog}")
    st.download_button(
        "📥 Exportar Reabastecimiento a Excel",
        data=buf2.getvalue(),
        file_name=f"reabastecimiento_semana_{semana_prog}_{año_prog}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
#
# Historial
#
elif opcion == "Historial":
    st.markdown("### 📋 Historial Completo de Ventas")
    df_h = pd.read_sql_query("SELECT * FROM resumen_semanal ORDER BY fecha DESC", conn)
    st.dataframe(df_h)

#
# Reportes
#
elif opcion == "Reportes":
    st.markdown("### 📥 Gestionar Reportes")
    if st.button("🔄 Borrar simulación Semana 38"):
        cursor.execute("DELETE FROM resumen_semanal WHERE semana = ?", ("Semana 38",))
        conn.commit()
        st.success("✅ Datos de simulación eliminados")

    df_r = pd.read_sql_query("SELECT * FROM resumen_semanal ORDER BY fecha DESC", conn)
    csv = df_r.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📄 Descargar CSV",
        data=csv,
        file_name="resumen_semanal.csv",
        mime="text/csv"
    )
