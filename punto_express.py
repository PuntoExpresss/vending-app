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
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados
st.markdown("""<style>
/* Fondo oscuro del menú lateral */
[data-testid="stSidebar"] {
    background-color: #121212;
    padding: 25px 20px;
    border-right: 1px solid #333;
}

/* Texto blanco y tipografía profesional */
[data-testid="stSidebar"] * {
    color: #ffffff !important;
    font-family: 'Segoe UI', sans-serif;
}

/* Hover en opciones del menú */
[data-testid="stSidebar"] a:hover {
    background-color: #2e2e2e;
    border-radius: 5px;
    padding: 4px 8px;
    text-decoration: none;
}

/* Ocultar íconos rotos o imágenes vacías */
[data-testid="stSidebar"] img {
    display: none !important;
}

/* Título principal */
.main-title {
    font-size: 36px;
    font-weight: 700;
    color: #00c853;
    margin-bottom: 0.5rem;
    font-family: 'Segoe UI', sans-serif;
}
/* Ocultar tooltips automáticos como "key" sin bloquear clic */
[data-testid="collapsedControl"] [title],
[data-testid="collapsedControl"] [aria-label] {
    display: none !important;
}

/* Ocultar texto residual "key" */
[data-testid="collapsedControl"] span {
    visibility: hidden !important;
}

/* Reemplazar con ícono personalizado tipo hamburguesa */
[data-testid="collapsedControl"] span::after {
    content: "☰";
    font-size: 20px;
    color: #00c853;
    font-weight: bold;
    position: absolute;
    top: 0;
    left: 0;
}

/* Pie de página flotante */
.footer-text {
    position: fixed;
    bottom: 10px;
    right: 20px;
    font-size: 12px;
    color: #888;
    font-family: 'Segoe UI', sans-serif;
}
</style>""", unsafe_allow_html=True)

# Título corporativo en el cuerpo principal
st.markdown('<div class="main-title">🟢 Punto Express - Sistema de Vending</div>', unsafe_allow_html=True)
st.markdown("---")

# Nombre de empresa en el menú lateral
st.sidebar.markdown("""
    <div style='font-size:24px; font-weight:bold; color:#00c853; font-family:Segoe UI, sans-serif;'>
        🟢 Punto Express
    </div>
    <div style='font-size:16px; color:#ccc; font-family:Segoe UI, sans-serif;'>
        Sistema de Vending
    </div>
""", unsafe_allow_html=True)

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

# Simulación de datos si no existen
semana_sim = "Semana 38"
cursor.execute("SELECT COUNT(*) FROM resumen_semanal WHERE semana = ?", (semana_sim,))
if cursor.fetchone()[0] == 0:
    año_sim = 2025
    lunes_sim = date.fromisocalendar(año_sim, 38, 1)
    fechas_sim = [lunes_sim + timedelta(days=i) for i in range(6)]
    maquinas_sim = ["Motomall", "Unidad", "Norte", "Buses", "Paquetex", "Dekohouse", "Caldas", "Maquina 8"]
    registros_sim = []
    for maquina in maquinas_sim:
        for i, fecha in enumerate(fechas_sim):
            dia = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"][i]
            ventas = random.randint(10000, 30000)
            egresos = random.randint(2000, 8000)
            registros_sim.append((semana_sim, str(fecha), maquina, dia, ventas, egresos))
    cursor.executemany("INSERT INTO resumen_semanal VALUES (?, ?, ?, ?, ?, ?)", registros_sim)
    conn.commit()

def grafico_tendencia_semanal(df, festivos):
    df["fecha"] = pd.to_datetime(df["fecha"])
    df_agrupado = df.groupby("fecha")["ventas"].sum().reset_index()
    df_agrupado["promedio_movil"] = df_agrupado["ventas"].rolling(window=3).mean()

    fig = px.line(df_agrupado, x="fecha", y="ventas", title="Tendencia semanal de ventas",
                  markers=True, labels={"fecha": "Fecha", "ventas": "Ventas ($)"})
    fig.add_scatter(x=df_agrupado["fecha"], y=df_agrupado["promedio_movil"],
                    mode="lines", name="Promedio móvil (3 días)",
                    line=dict(dash="dash", color="#00c853"))
    festivos_dt = pd.to_datetime(list(festivos))
    for f in festivos_dt:
        if f in df_agrupado["fecha"].values:
            fig.add_vline(x=f, line_width=1, line_dash="dot", line_color="red",
                          annotation_text="Festivo", annotation_position="top left")
    fig.update_layout(template="plotly_dark", xaxis_title="Día", yaxis_title="Ventas ($)")
    return fig

def exportar_grafico(fig):
    buffer = io.BytesIO()
    fig.write_image(buffer, format="png")
    buffer.seek(0)
    st.download_button(
        label="📥 Descargar gráfica",
        data=buffer,
        file_name="tendencia_semanal.png",
        mime="image/png"
    )

# Menú de navegación
opcion = st.sidebar.radio("📋 Navegación:", [
    "Dashboard",
    "Control Ventas",
    "Reabastecimiento",
    "Rotación",
    "Mantenimiento",
    "Reportes"
], key="menu_navegacion")

# Pie de página flotante
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
# Rotación
#
elif opcion == "Rotación":
    st.title("🔁 Rotación por Máquina")

    # Crear tabla 'maquina' si no existe
    cursor.execute("""CREATE TABLE IF NOT EXISTS maquina (nombre_maquina TEXT PRIMARY KEY)""")
    conn.commit()

    # Poblar tabla 'maquina' si está vacía
    cursor.execute("SELECT COUNT(*) FROM maquina")
    if cursor.fetchone()[0] == 0:
        maquinas_sim = ["Motomall", "Unidad", "Norte", "Buses", "Paquetex", "Dekohouse", "Caldas", "Maquina 8"]
        for nombre in maquinas_sim:
            cursor.execute("INSERT OR IGNORE INTO maquina (nombre_maquina) VALUES (?)", (nombre,))
        conn.commit()

    # Obtener máquinas desde la tabla 'maquina'
    cursor.execute("SELECT nombre_maquina FROM maquina")
    maquinas_disponibles = sorted(set(row[0] for row in cursor.fetchall() if row[0]))

    # Selectores
    maquina_sel = st.selectbox("Selecciona la máquina", maquinas_disponibles)
    fecha_sel = st.date_input("Selecciona una fecha", value=date.today())
    semana_sel = st.number_input("Semana ISO", min_value=1, max_value=52, value=fecha_sel.isocalendar()[1])

    # Funciones de cálculo
    def calcular_precio_unitario(costo_compra, unidad_compra, unidades_por_paquete=6):
        if unidad_compra == "unidad":
            return costo_compra
        elif unidad_compra == "docena":
            return costo_compra / 12
        elif unidad_compra == "paquete":
            return costo_compra / unidades_por_paquete
        else:
            return costo_compra

    def calcular_gasto(costo_compra, unidad_compra, cantidad_vendida, unidades_por_paquete=6):
        precio_unitario = calcular_precio_unitario(costo_compra, unidad_compra, unidades_por_paquete)
        return precio_unitario * cantidad_vendida

    # Registro manual de producto vendido
    with st.expander("➕ Registrar producto vendido"):
        producto_nuevo = st.text_input("Producto")
        cantidad_nueva = st.number_input("Cantidad vendida", min_value=1, value=1)
        costo_compra = st.number_input("Costo total de compra", min_value=0, value=1200)
        unidad_compra = st.selectbox("Unidad de compra", ["unidad", "docena", "paquete"])
        unidades_por_paquete = st.number_input("Unidades por paquete", min_value=1, value=6) if unidad_compra == "paquete" else 6

        precio_unitario_preview = calcular_precio_unitario(costo_compra, unidad_compra, unidades_por_paquete)
        st.info(f"💡 Precio unitario calculado: ${precio_unitario_preview:,.0f}")

        if st.button("📌 Guardar producto"):
            cursor.execute("INSERT INTO rotacion_producto VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
                str(semana_sel), str(fecha_sel), maquina_sel, producto_nuevo,
                cantidad_nueva, precio_unitario_preview, costo_compra, unidad_compra
            ))
            conn.commit()
            st.success("Producto registrado correctamente.")

    # Cargar y filtrar datos
    df_rotacion = pd.read_sql_query(
        "SELECT * FROM rotacion_producto WHERE semana = ? AND maquina = ?",
        conn, params=(str(semana_sel), maquina_sel)
    )

    if df_rotacion.empty:
        st.warning("No hay datos de rotación para esta máquina en la semana seleccionada.")
    else:
        df_rotacion["unidades_por_paquete"] = df_rotacion["unidad_compra"].apply(lambda u: 6 if u == "paquete" else None)
        df_rotacion["precio_unitario"] = df_rotacion.apply(
            lambda row: calcular_precio_unitario(row["costo_compra"], row["unidad_compra"],
                                                 row["unidades_por_paquete"] if row["unidad_compra"] == "paquete" else 6),
            axis=1
        )
        df_rotacion["gasto_total"] = df_rotacion.apply(
            lambda row: calcular_gasto(row["costo_compra"], row["unidad_compra"], row["cantidad"],
                                       row["unidades_por_paquete"] if row["unidad_compra"] == "paquete" else 6),
            axis=1
        )
        df_rotacion["margen_unitario"] = df_rotacion["valor_unitario"] - df_rotacion["precio_unitario"]

        # 🔔 Alertas inteligentes
        alertas = []
        margen_total = df_rotacion["valor_unitario"].sum() - df_rotacion["gasto_total"].sum()
        if margen_total < 0:
            st.error("⚠️ Margen negativo: estás gastando más de lo que vendes en esta máquina.")
            alertas.append(["Margen negativo", "El gasto total supera el ingreso por ventas."])

        # 📋 Resumen financiero
        st.subheader("📋 Resumen financiero semanal")
        df_resumen_gasto = df_rotacion.groupby(["producto", "unidad_compra"]).agg({
            "costo_compra": "sum"
        }).reset_index()
        total_inversion_semana = df_resumen_gasto["costo_compra"].sum()
        st.success(f"🔔 Total invertido en compras esta semana: ${total_inversion_semana:,.0f}")
        df_resumen_gasto["porcentaje_inversion"] = (
            df_resumen_gasto["costo_compra"] / total_inversion_semana
        ) * 100
        st.markdown("### 💸 Inversión por producto (según unidad de compra)")
        st.dataframe(df_resumen_gasto.sort_values("costo_compra", ascending=False), use_container_width=True)

        # Resumen general para exportación
        resumen_general = pd.DataFrame({
            "Indicador": ["💰 Total vendido", "📦 Total gastado", "📈 Margen operativo"],
            "Valor": [f"${df_rotacion['valor_unitario'].sum():,.0f}",
                      f"${df_rotacion['gasto_total'].sum():,.0f}",
                      f"${margen_total:,.0f}"]
        })
        # 📊 Resumen detallado por producto
        st.subheader("📦 Productos más vendidos esta semana")
        df_resumen = df_rotacion.groupby(["producto", "unidad_compra"]).agg({
            "cantidad": "sum",
            "precio_unitario": "mean",
            "gasto_total": "sum",
            "valor_unitario": "sum"
        }).reset_index()
        df_resumen["margen_total"] = df_resumen["valor_unitario"] - df_resumen["gasto_total"]

        st.dataframe(df_resumen.sort_values("cantidad", ascending=False), use_container_width=True)

        # 🏆 Ranking de productos más vendidos
        fig_cantidad = px.bar(
            df_resumen.sort_values("cantidad", ascending=False),
            x="producto", y="cantidad", color="unidad_compra",
            title="Productos más vendidos por cantidad",
            text="cantidad"
        )
        fig_cantidad.update_layout(template="plotly_dark")
        st.plotly_chart(fig_cantidad, use_container_width=True)

        # 💸 Ranking de inversión por producto (compra real)
        fig_inversion_real = px.bar(
            df_resumen_gasto.sort_values("costo_compra", ascending=False),
            x="producto", y="costo_compra", color="unidad_compra",
            title="Inversión total por producto (según unidad de compra)",
            text="costo_compra",
            labels={"costo_compra": "Costo total de compra", "producto": "Producto"}
        )
        fig_inversion_real.update_layout(template="plotly_dark")
        st.plotly_chart(fig_inversion_real, use_container_width=True)

        # 📈 Ranking de margen operativo (con color rojo si negativo)
        df_resumen["color_margen"] = df_resumen["margen_total"].apply(
            lambda x: "red" if x < 0 else "#00c853"
        )
        fig_margen = px.bar(
            df_resumen.sort_values("margen_total", ascending=False),
            x="producto", y="margen_total", color="color_margen",
            title="Margen operativo semanal por producto",
            text="margen_total",
            color_discrete_map="identity"
        )
        fig_margen.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig_margen, use_container_width=True)

        # 📥 Exportar a Excel
        buf_rotacion = io.BytesIO()
        with pd.ExcelWriter(buf_rotacion, engine="openpyxl") as writer:
            df_rotacion.to_excel(writer, index=False, sheet_name=f"Rotación_{maquina_sel}")
            resumen_general.to_excel(writer, index=False, sheet_name="Resumen_Financiero")
            df_resumen_gasto.to_excel(writer, index=False, sheet_name="Inversión_por_Producto")
            df_resumen.to_excel(writer, index=False, sheet_name="Ranking_Productos")
        st.download_button(
            "📥 Exportar rotación a Excel",
            data=buf_rotacion.getvalue(),
            file_name=f"rotacion_{maquina_sel}_semana_{semana_sel}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
#
# Mantenimiento
#
elif opcion == "Mantenimiento":
    st.title("🛠️ Mantenimiento por Máquina")

    # Asegurar que la tabla 'maquina' existe
    cursor.execute("""CREATE TABLE IF NOT EXISTS maquina (nombre_maquina TEXT PRIMARY KEY)""")
    conn.commit()

    # Obtener máquinas disponibles
    cursor.execute("SELECT nombre_maquina FROM maquina")
    maquinas_disponibles = sorted(set(row[0] for row in cursor.fetchall() if row[0]))

    # Detectar cambio de máquina y reiniciar campos
    if "maquina_anterior_mant" not in st.session_state:
        st.session_state.maquina_anterior_mant = None

    maquina_sel = st.selectbox("Selecciona la máquina", maquinas_disponibles)
    fecha_mant = st.date_input("Fecha del mantenimiento", value=date.today())
    semana_mant = st.number_input("Semana ISO", min_value=1, max_value=52, value=fecha_mant.isocalendar()[1])

    if st.session_state.maquina_anterior_mant != maquina_sel:
        st.session_state.maquina_anterior_mant = maquina_sel
        st.session_state.tipo_mant = "Preventivo"
        st.session_state.descripcion_mant = ""
        st.session_state.costo_mant = 0.0

    # Crear tabla de mantenimiento si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mantenimiento (
            fecha TEXT,
            semana TEXT,
            maquina TEXT,
            tipo TEXT,
            descripcion TEXT,
            costo REAL
        )
    """)
    conn.commit()

    # Verificar si la columna 'semana' existe y agregarla si no
    try:
        cursor.execute("SELECT semana FROM mantenimiento LIMIT 1")
    except:
        cursor.execute("ALTER TABLE mantenimiento ADD COLUMN semana TEXT")
        conn.commit()

    # Registro de mantenimiento
    with st.expander("➕ Registrar mantenimiento"):
        tipo_mant = st.selectbox("Tipo de mantenimiento", ["Preventivo", "Correctivo", "Otro"], key="tipo_mant")
        descripcion = st.text_area("Descripción del trabajo realizado", key="descripcion_mant")
        costo_mant = st.number_input("Costo total", min_value=0.0, value=st.session_state.costo_mant, key="costo_mant")

        if st.button("📌 Guardar mantenimiento"):
            cursor.execute("""
                INSERT INTO mantenimiento (fecha, semana, maquina, tipo, descripcion, costo)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(fecha_mant), str(semana_mant), maquina_sel, tipo_mant, descripcion, costo_mant
            ))
            conn.commit()
            st.success("Mantenimiento registrado correctamente.")

    # Historial de mantenimientos por semana
    st.subheader("📋 Historial de mantenimientos")
    df_mantenimiento = pd.read_sql_query(
        "SELECT * FROM mantenimiento WHERE maquina = ? AND semana = ? ORDER BY fecha DESC",
        conn, params=(maquina_sel, str(semana_mant))
    )

    if df_mantenimiento.empty:
        st.warning("No hay mantenimientos registrados para esta máquina en la semana seleccionada.")
    else:
        st.dataframe(df_mantenimiento, use_container_width=True)

        # Total invertido y cantidad de mantenimientos
        total_mantenimiento = df_mantenimiento["costo"].sum()
        cantidad_mantenimientos = len(df_mantenimiento)

        st.info(f"🔧 Total invertido esta semana: ${total_mantenimiento:,.0f}")
        st.success(f"🧮 Número de mantenimientos realizados: {cantidad_mantenimientos}")

    # 🟠 Alerta por frecuencia excesiva
    if cantidad_mantenimientos > 3:
        st.warning("🟠 Alerta: esta máquina ha recibido más de 3 mantenimientos esta semana. Revisa si hay fallas recurrentes.")

    # 🟢 Nota positiva si no hubo mantenimiento
    if cantidad_mantenimientos == 0:
        st.info("🟢 Esta máquina no ha requerido mantenimiento esta semana. ¡Buen desempeño!")

        # Exportar historial
        buf_mant = io.BytesIO()
        with pd.ExcelWriter(buf_mant, engine="openpyxl") as writer:
            df_mantenimiento.to_excel(writer, index=False, sheet_name=f"Mantenimiento_{maquina_sel}")
        st.download_button(
            "📥 Exportar historial a Excel",
            data=buf_mant.getvalue(),
            file_name=f"mantenimiento_{maquina_sel}_semana_{semana_mant}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
#   
# Reportes
#
if opcion == "Reportes":
    st.title("📊 Reportes Semanales")

    cursor.execute("SELECT fecha, ventas FROM resumen_semanal WHERE semana = ?", (semana_sim,))
    df_ventas = pd.DataFrame(cursor.fetchall(), columns=["fecha", "ventas"])

    cursor.execute("""
        SELECT fecha, dia, maquina, ventas, egresos
        FROM resumen_semanal
        WHERE semana = ?
    """, (semana_sim,))
    df_detalle = pd.DataFrame(cursor.fetchall(), columns=["fecha", "dia", "maquina", "ventas", "egresos"])
    df_detalle["neto"] = df_detalle["ventas"] - df_detalle["egresos"]

    tv = df_detalle["ventas"].sum()
    te = df_detalle["egresos"].sum()
    tn = df_detalle["neto"].sum()
    dv = df_detalle[df_detalle["ventas"] > 0]["fecha"].nunique()
    pdia = round(tv / dv, 2) if dv else 0
    ft = round(tn * 0.05)
    dia_top = df_detalle.groupby("dia")["neto"].sum().sort_values(ascending=False).index[0]

    st.subheader("📈 Tendencia de ventas semanales")
    fig1 = grafico_tendencia_semanal(df_ventas, festivos_2025)
    st.plotly_chart(fig1, use_container_width=True)
    exportar_grafico(fig1)

    st.subheader("🏭 Comparativa por máquina")
    df_m = df_detalle.groupby("maquina")["ventas"].sum().reset_index()
    fig2 = px.bar(df_m, x="maquina", y="ventas", title="Ventas por máquina", color="maquina")
    fig2.update_layout(template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📋 Resumen ejecutivo")
    resumen = pd.DataFrame({
        "Indicador": [
            "🔢 Total Ventas", "📉 Total Egresos", "💰 Profit Neto",
            "📈 Promedio Diario", "🛟 Fondo Emergencia (5%)",
            "📆 Día más rentable"
        ],
        "Valor": [
            f"${tv:,}", f"${te:,}", f"${tn:,}",
            f"${pdia:,}", f"${ft:,}", dia_top
        ]
    })
    st.dataframe(resumen, use_container_width=True)

    buf_reportes = io.BytesIO()
    with pd.ExcelWriter(buf_reportes, engine="openpyxl") as writer:
        df_ventas.to_excel(writer, index=False, sheet_name="Tendencia")
        df_m.to_excel(writer, index=False, sheet_name="Por Máquina")
        df_detalle.to_excel(writer, index=False, sheet_name="Detalle")
        resumen.to_excel(writer, index=False, sheet_name="Resumen")
    st.download_button(
        "📥 Exportar Reporte a Excel",
        data=buf_reportes.getvalue(),
        file_name=f"reporte_semanal_{semana_sim}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Pie de página flotante
st.markdown("""
    <div class="footer-text">
        © Punto Express | Última actualización: Septiembre 2025
    </div>
""", unsafe_allow_html=True)
