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

# Estilos personalizados (paleta: negro, gris, blanco, verde)
st.markdown("""<style>
/* Sidebar background y texto */
[data-testid="stSidebar"] > div:first-child {
  background: linear-gradient(180deg, #000000 0%, #1f1f1f 100%) !important;
  color: #ffffff !important;
}

/* Título y subtítulo en sidebar (si hay clases diferentes, esto mantiene el color) */
[data-testid="stSidebar"] .css-1lcbmhc,
[data-testid="stSidebar"] .css-ng1t4o,
[data-testid="stSidebar"] .css-10trblm {
  color: #ffffff !important;
}

/* Texto de los items del menú */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .css-1d391kg,
[data-testid="stSidebar"] .css-1v3fvcr,
[data-testid="stSidebar"] .stRadio {
  color: #e6e6e6 !important;
}

/* Fondo del item seleccionado y hover (resalte verde) */
[data-testid="stSidebar"] .css-1v3fvcr:focus,
[data-testid="stSidebar"] .css-1v3fvcr:active,
[data-testid="stSidebar"] .css-1v3fvcr:hover,
[data-testid="stSidebar"] [role="radiogroup"] > div[aria-checked="true"] {
  background: linear-gradient(90deg, rgba(0,200,83,0.12), rgba(0,200,83,0.06)) !important;
  border-left: 4px solid #00c853 !important;
  color: #ffffff !important;
}

/* Links y botones verdes */
a, .stButton>button, .css-1v0mbdj button {
  color: #00c853 !important;
}

/* Ajustar color de iconos SVG en sidebar */
[data-testid="stSidebar"] svg { fill: #00c853 !important; }

/* Contenido principal: NO tocar (se mantiene por defecto) */
/* No aplicar cambios al contenedor principal para evitar fondo oscuro accidental */

/* Footer pequeño */
.footer-text { color: #bdbdbd; font-size:12px; }

/* Forzar contraste en textos y encabezados dentro del sidebar */
[data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
  color: #f5f5f5 !important;
}

/* Ajustes responsivos: mantener legibilidad en mobile */
@media (max-width: 600px) {
  [data-testid="stSidebar"] > div:first-child { padding-left: 12px !important; padding-right: 12px !important; }
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
conn = sqlite3.connect("ventas_semanales.db", check_same_thread=False)
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

# 🔧 Mejora: función para sincronizar egresos desde rotación
def sincronizar_egreso_en_ventas(maquina, fecha, monto):
    dia_semana = date.fromisoformat(fecha).strftime("%A")
    dia_map = {
        "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
        "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
    }
    dia = dia_map.get(dia_semana, dia_semana)
    semana_iso = date.fromisoformat(fecha).isocalendar()[1]
    semana_txt = f"Semana {semana_iso}"

    cursor.execute("""
        SELECT egresos FROM resumen_semanal
        WHERE maquina = ? AND fecha = ?
    """, (maquina, fecha))
    resultado = cursor.fetchone()

    if resultado:
        cursor.execute("""
            UPDATE resumen_semanal
            SET egresos = egresos + ?
            WHERE maquina = ? AND fecha = ?
        """, (monto, maquina, fecha))
    else:
        cursor.execute("""
            INSERT INTO resumen_semanal (semana, fecha, maquina, dia, ventas, egresos)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (semana_txt, fecha, maquina, dia, 0, monto))
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
import re
import pandas as pd
import plotly.express as px

def limpiar_unicode(texto):
    return re.sub(r'[^\x00-\x7F]+', '', texto)

if opcion == "Dashboard":
    st.header("📊 Dashboard")
    df = pd.read_sql_query("SELECT * FROM resumen_semanal ORDER BY fecha DESC", conn)

    if not df.empty:
        df["semana_num"] = df["semana"].str.extract(r'(\d+)').astype(int)
        semana_actual = df["semana_num"].max()
        semana_anterior = semana_actual - 1

        df_sem = df[df["semana_num"] == semana_actual].copy()
        df_sem["neto"] = df_sem["ventas"] - df_sem["egresos"]
        profit = df_sem["neto"].sum()
        fondo = round(profit * 0.05)

        df_prev = df[df["semana_num"] == semana_anterior].copy()
        ventas_actual = df_sem["ventas"].sum()
        ventas_prev = df_prev["ventas"].sum()
        variacion = round(((ventas_actual - ventas_prev) / ventas_prev) * 100, 2) if ventas_prev else 0

        st.metric("💰 Profit semanal", f"${profit}")
        st.metric("🛟 Fondo emergencia (5%)", f"${fondo}")
        st.metric("📈 Ventas vs semana anterior", f"${ventas_actual:,.0f}", f"{variacion:+.2f}%")

        df_maq = df_sem.groupby("maquina")["ventas"].sum().reset_index()
        fig = px.bar(df_maq, x="maquina", y="ventas", title=f"Máquinas más vendidas - Semana {semana_actual}", color="maquina")
        st.plotly_chart(fig, use_container_width=True)

        df_comp = df[df["semana_num"].isin([semana_anterior, semana_actual])]
        df_comp_sum = df_comp.groupby(["semana_num", "maquina"])["ventas"].sum().reset_index()
        fig2 = px.bar(df_comp_sum, x="maquina", y="ventas", color="semana_num", barmode="group", title="📊 Comparativa por máquina (2 semanas)")
        st.plotly_chart(fig2, use_container_width=True)

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

        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.markdown("### 📄 Exportación PDF")
        st.download_button(
            label="📄 Exportar resumen en PDF",
            data=pdf_bytes,
            file_name=f"resumen_semana_{semana_actual}.pdf",
            mime="application/pdf"
        )

        # 📊 Panel de métricas semanales por mes
        st.markdown("### 📊 Panel de métricas semanales por mes")

        df_mensual = pd.read_sql_query("SELECT semana, fecha, ventas FROM resumen_semanal", conn)
        df_mensual["fecha"] = pd.to_datetime(df_mensual["fecha"])
        df_mensual["mes"] = df_mensual["fecha"].dt.strftime("%B")
        df_mensual["semana_num"] = df_mensual["fecha"].dt.isocalendar().week

        df_semanal = df_mensual.groupby(["mes", "semana_num"])["ventas"].sum().reset_index()
        df_semanal = df_semanal.sort_values(by="semana_num").reset_index(drop=True)

        df_semanal["variacion"] = df_semanal["ventas"].pct_change().fillna(0) * 100
        df_semanal["color"] = df_semanal["variacion"].apply(lambda x: "🟢" if x > 0 else ("🔴" if x < 0 else "⚪"))

        for mes in df_semanal["mes"].unique():
            st.markdown(f"#### 📅 {mes}")
            semanas_mes = df_semanal[df_semanal["mes"] == mes]
            cols = st.columns(len(semanas_mes))
            for i, row in semanas_mes.iterrows():
                with cols[i % len(cols)]:
                    st.metric(
                        label=f"Semana {int(row['semana_num'])}",
                        value=f"${row['ventas']:,.0f}",
                        delta=f"{row['color']} {row['variacion']:+.1f}%",
                        delta_color="normal"
                    )

    else:
        st.info("No hay datos registrados aún.")

#
# Control Ventas
# 
from datetime import date, timedelta
import io

if opcion == "Control Ventas":
    st.title("📆 Informe Semanal Editable")

    # Semana actual por defecto
    semana_actual = date.today().isocalendar()[1]
    año_actual = date.today().year

    # Selección de semana
    col1, col2 = st.columns(2)
    with col1:
        semana_num = st.number_input("Número de semana", 1, 52, semana_actual)
    with col2:
        año = st.number_input("Año", 2020, 2030, año_actual)

    lunes = date.fromisocalendar(año, semana_num, 1)
    fechas = [lunes + timedelta(days=i) for i in range(6)]  # lunes a sábado
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
    st.subheader(f"📅 Semana {semana_num}: {fechas[0]} a {fechas[-1]}")

    # Crear tabla si no existe
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
            "INSERT INTO resumen_semanal (semana, fecha, maquina, dia, ventas, egresos) VALUES (?, ?, ?, ?, ?, ?)",
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

        # 🟠 Alerta corregida: días sin ventas reales
        ventas_por_dia = df_actualizada.groupby("fecha")["ventas"].sum()
        dias_sin_ventas = (ventas_por_dia == 0).sum()
        if dias_sin_ventas > 0:
            st.warning(f"🟠 Alerta: hay {dias_sin_ventas} días sin ventas esta semana.")

        # 🟢 Nota si todas las máquinas registraron ventas
        maquinas_con_ventas = df_actualizada[df_actualizada["ventas"] > 0]["maquina"].unique()
        if set(maquinas_con_ventas) == set(maquinas):
            st.success("🟢 Todas las máquinas registraron ventas esta semana. ¡Buen desempeño!")

        # Gráficos
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

    # 📊 Resumen mensual por semana
    df_mensual = pd.read_sql_query("SELECT semana, fecha, ventas FROM resumen_semanal", conn)
    df_mensual["fecha"] = pd.to_datetime(df_mensual["fecha"])
    df_mensual["mes"] = df_mensual["fecha"].dt.strftime("%B")
    df_mensual["semana_num"] = df_mensual["fecha"].dt.isocalendar().week

    resumen_semanal = df_mensual.groupby(["mes", "semana_num"])["ventas"].sum().reset_index()
    resumen_semanal = resumen_semanal.sort_values(by=["semana_num"])

    st.markdown("### 📅 Totales por semana agrupados por mes")
    st.dataframe(resumen_semanal.rename(columns={
        "mes": "Mes",
        "semana_num": "Semana",
        "ventas": "Total Ventas"
    }), use_container_width=True)

    # ⚠️ Alerta por semanas con ventas bajas
    semanas_bajas = resumen_semanal[resumen_semanal["ventas"] < 10000]
    if not semanas_bajas.empty:
        st.warning(f"⚠️ Atención: {len(semanas_bajas)} semana(s) con ventas menores a $10,000.")


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
elif opcion == "Rotación":
    st.title("🔁 Rotación por Máquina")

    # --- Migración local y aseguramiento de tablas mínimas (solo dentro de esta sección) ---
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rotacion_producto'")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE rotacion_producto (
                semana TEXT,
                fecha TEXT,
                maquina TEXT,
                producto TEXT,
                cantidad INTEGER,
                precio_unitario REAL,
                costo_compra REAL,
                unidad_compra TEXT,
                unidades_por_paquete INTEGER
            )
        """)
        conn.commit()
    else:
        cursor.execute("PRAGMA table_info(rotacion_producto)")
        cols = [r[1] for r in cursor.fetchall()]
        if "unidades_por_paquete" not in cols:
            cursor.execute("ALTER TABLE rotacion_producto ADD COLUMN unidades_por_paquete INTEGER")
            conn.commit()
        if "precio_unitario" not in cols:
            cursor.execute("ALTER TABLE rotacion_producto ADD COLUMN precio_unitario REAL")
            conn.commit()
            rows = cursor.execute("SELECT rowid, costo_compra, unidad_compra, unidades_por_paquete FROM rotacion_producto").fetchall()
            for row in rows:
                rowid, costo_compra, unidad_compra, unidades_por_paquete = row
                try:
                    c = float(costo_compra) if costo_compra is not None else 0.0
                except:
                    c = 0.0
                up = int(unidades_por_paquete) if unidades_por_paquete not in (None, 0) else 6
                if unidad_compra == "unidad" or unidad_compra is None:
                    precio = c
                elif unidad_compra == "docena":
                    precio = c / 12.0
                elif unidad_compra == "paquete":
                    precio = c / up
                else:
                    precio = c
                cursor.execute("UPDATE rotacion_producto SET precio_unitario = ?, unidades_por_paquete = ? WHERE rowid = ?", (precio, up, rowid))
            conn.commit()

    # Asegurar egreso_auto en resumen_semanal si existe la tabla
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='resumen_semanal'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(resumen_semanal)")
        cols_rs = [r[1] for r in cursor.fetchall()]
        if "egreso_auto" not in cols_rs:
            cursor.execute("ALTER TABLE resumen_semanal ADD COLUMN egreso_auto INTEGER DEFAULT 0")
            conn.commit()

    # Crear catálogo de productos si no existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='producto_catalog'")
    if not cursor.fetchone():
        cursor.execute("CREATE TABLE producto_catalog (producto TEXT PRIMARY KEY)")
        conn.commit()

    # Asegurar tabla maquina mínima
    cursor.execute("""CREATE TABLE IF NOT EXISTS maquina (nombre_maquina TEXT PRIMARY KEY)""")
    conn.commit()

    # Popular máquinas si están vacías
    cursor.execute("SELECT COUNT(*) FROM maquina")
    if cursor.fetchone()[0] == 0:
        maquinas_sim = ["Motomall", "Unidad", "Norte", "Buses", "Paquetex", "Dekohouse", "Caldas", "Maquina 8"]
        for nombre in maquinas_sim:
            cursor.execute("INSERT OR IGNORE INTO maquina (nombre_maquina) VALUES (?)", (nombre,))
        conn.commit()

    cursor.execute("SELECT nombre_maquina FROM maquina")
    maquinas_disponibles = sorted(set(row[0] for row in cursor.fetchall() if row[0]))

    # Selectores
    maquina_sel = st.selectbox("Selecciona la máquina", maquinas_disponibles)
    fecha_sel = st.date_input("Selecciona una fecha", value=date.today())
    semana_sel = st.number_input("Semana ISO", min_value=1, max_value=52, value=fecha_sel.isocalendar()[1], key=f"sem_iso_{maquina_sel}_{str(fecha_sel)}")

    # Funciones de cálculo
    def calcular_precio_unitario(costo_compra, unidad_compra, unidades_por_paquete=6):
        try:
            costo = float(costo_compra)
        except:
            return 0.0
        if unidad_compra == "unidad":
            return costo
        if unidad_compra == "docena":
            return costo / 12.0
        if unidad_compra == "paquete":
            return costo / unidades_por_paquete
        return costo

    def calcular_gasto(costo_compra, unidad_compra, cantidad_vendida, unidades_por_paquete=6):
        precio_unit = calcular_precio_unitario(costo_compra, unidad_compra, unidades_por_paquete)
        try:
            return precio_unit * float(cantidad_vendida)
        except:
            return 0.0

    # --- Registrar producto vendido (con catálogo que guarda nombre tal cual) ---
    with st.expander("➕ Registrar producto vendido"):
        cursor.execute("SELECT producto FROM producto_catalog ORDER BY producto COLLATE NOCASE")
        productos_guardados = [r[0] for r in cursor.fetchall()]

        producto_seleccionado = st.selectbox("Elegir producto (o escribe uno nuevo abajo)", ["-- Nuevo producto --"] + productos_guardados, key=f"select_prod_new_{maquina_sel}_{str(fecha_sel)}")
        producto_nuevo_text = st.text_input("Producto (nuevo o igual al seleccionado)", value=(producto_seleccionado if producto_seleccionado != "-- Nuevo producto --" else ""), key=f"prod_text_new_{maquina_sel}_{str(fecha_sel)}")
        producto_nuevo = producto_nuevo_text.strip()

        cantidad_nueva = st.number_input("Cantidad vendida", min_value=1, value=1, step=1, key=f"cantidad_nuevo_{maquina_sel}_{str(fecha_sel)}")
        costo_compra = st.number_input("Costo total de compra", min_value=0.0, value=1200.0, step=100.0, format="%.2f", key=f"costo_nuevo_{maquina_sel}_{str(fecha_sel)}")
        unidad_compra = st.selectbox("Unidad de compra", ["unidad", "docena", "paquete"], key=f"unidad_nuevo_{maquina_sel}_{str(fecha_sel)}")
        unidades_por_paquete = st.number_input("Unidades por paquete", min_value=1, value=6, key=f"up_nuevo_{maquina_sel}_{str(fecha_sel)}") if unidad_compra == "paquete" else 6

        precio_unitario_preview = calcular_precio_unitario(costo_compra, unidad_compra, unidades_por_paquete)
        st.info(f"💡 Precio unitario calculado: ${precio_unitario_preview:,.2f}")

        if st.button("📌 Guardar producto", key=f"guardar_nuevo_{maquina_sel}_{str(fecha_sel)}"):
            if not producto_nuevo:
                st.error("El nombre del producto no puede estar vacío.")
            elif cantidad_nueva <= 0 or costo_compra <= 0:
                st.error("Cantidad y costo deben ser mayores a cero.")
            else:
                try:
                    cursor.execute("INSERT OR IGNORE INTO producto_catalog (producto) VALUES (?)", (producto_nuevo,))
                    conn.commit()
                except Exception as e:
                    st.error(f"Error guardando en catálogo: {e}")

                cursor.execute("""
                    SELECT COUNT(*) FROM rotacion_producto
                    WHERE fecha = ? AND maquina = ? AND producto = ?
                """, (str(fecha_sel), maquina_sel, producto_nuevo))
                if cursor.fetchone()[0] > 0:
                    st.warning("Ya existe un registro para ese producto en esta máquina y fecha. Si necesitas registrar otra venta, ajusta cantidades manualmente.")
                else:
                    cursor.execute("""
                        INSERT INTO rotacion_producto (semana, fecha, maquina, producto, cantidad, precio_unitario, costo_compra, unidad_compra, unidades_por_paquete)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(semana_sel), str(fecha_sel), maquina_sel, producto_nuevo,
                        int(cantidad_nueva), float(precio_unitario_preview), float(costo_compra), unidad_compra, int(unidades_por_paquete)
                    ))
                    conn.commit()
                    try:
                        sincronizar_egreso_en_ventas(maquina_sel, str(fecha_sel), float(costo_compra))
                    except Exception:
                        pass
                    st.success("Producto registrado correctamente y egreso sincronizado (si aplica).")

    # --- Editar registros por fila directamente en la tabla (sin selector global) ---
    with st.expander("✏️ Editar registros (edita por fila)"):
        df_todos = pd.read_sql_query(
            "SELECT rowid, * FROM rotacion_producto WHERE semana = ? AND maquina = ? ORDER BY fecha, producto",
            conn, params=(str(semana_sel), maquina_sel)
        )

        if df_todos.empty:
            st.info("No hay productos registrados para esta máquina en esta semana.")
        else:
            # Mostrar tabla resumida
            df_mostrar = df_todos[["rowid", "fecha", "producto", "cantidad", "costo_compra", "unidad_compra"]].copy()
            df_mostrar.columns = ["rowid", "Fecha", "Producto", "Cantidad", "Costo compra", "Unidad"]
            st.dataframe(df_mostrar.reset_index(drop=True), use_container_width=True)

            st.markdown("**Acciones por fila**")
            for _, fila in df_todos.iterrows():
                rowid = int(fila["rowid"])
                cols = st.columns([2, 3, 2, 2, 2, 1])
                cols[0].write(fila["fecha"])
                cols[1].write(fila["producto"])
                cols[2].write(int(fila["cantidad"]))
                cols[3].write(f"${float(fila['costo_compra'] or 0):,.0f}")
                cols[4].write(fila["unidad_compra"])
                if cols[5].button("Editar", key=f"editar_row_{rowid}"):
                    # Abrir mini-formulario de edición exclusivo para esta fila
                    with st.form(key=f"form_edit_{rowid}", clear_on_submit=False):
                        st.markdown(f"### Editando registro: {fila['producto']} — {fila['fecha']}")
                        cursor.execute("SELECT producto FROM producto_catalog ORDER BY producto COLLATE NOCASE")
                        productos_guardados = [r[0] for r in cursor.fetchall()]
                        producto_text = st.text_input("Producto", value=fila["producto"], key=f"prod_row_{rowid}")
                        cantidad_val = st.number_input("Cantidad vendida", min_value=1, value=int(fila["cantidad"]), step=1, key=f"cant_row_{rowid}")
                        costo_val = st.number_input("Costo total de compra", min_value=0.0, value=float(fila["costo_compra"] or 0.0), step=100.0, format="%.2f", key=f"cost_row_{rowid}")
                        unidad_options = ["unidad", "docena", "paquete"]
                        unidad_index = unidad_options.index(fila["unidad_compra"]) if fila["unidad_compra"] in unidad_options else 0
                        unidad_val = st.selectbox("Unidad de compra", unidad_options, index=unidad_index, key=f"unidad_row_{rowid}")
                        up_val = st.number_input("Unidades por paquete (si aplica)", min_value=1, value=int(fila.get("unidades_por_paquete") or 6), key=f"up_row_{rowid}") if unidad_val == "paquete" else 6

                        submitted = st.form_submit_button("Guardar cambios", use_container_width=True, key=f"submit_row_{rowid}")
                        if submitted:
                            if not producto_text.strip():
                                st.error("El nombre del producto no puede quedar vacío.")
                            elif cantidad_val <= 0 or costo_val < 0:
                                st.error("Cantidad debe ser >=1 y costo no negativo.")
                            else:
                                # Guardar nombre en catálogo si es nuevo
                                try:
                                    cursor.execute("INSERT OR IGNORE INTO producto_catalog (producto) VALUES (?)", (producto_text.strip(),))
                                except:
                                    pass
                                # Actualizar registro
                                precio_unit = calcular_precio_unitario(costo_val, unidad_val, up_val)
                                cursor.execute("""
                                    UPDATE rotacion_producto
                                    SET producto = ?, cantidad = ?, costo_compra = ?, unidad_compra = ?, unidades_por_paquete = ?, precio_unitario = ?
                                    WHERE rowid = ?
                                """, (producto_text.strip(), int(cantidad_val), float(costo_val), unidad_val, int(up_val), float(precio_unit), rowid))
                                conn.commit()

                                # Ajuste de egreso según diferencia
                                costo_ant = float(fila["costo_compra"] or 0.0)
                                diferencia = float(costo_val) - costo_ant
                                if diferencia != 0:
                                    cursor.execute("SELECT egresos, egreso_auto FROM resumen_semanal WHERE maquina = ? AND fecha = ?", (fila["maquina"], fila["fecha"]))
                                    res = cursor.fetchone()
                                    if res:
                                        egresos_act = float(res[0] or 0.0)
                                        nuevo_egreso = max(0.0, egresos_act + diferencia)
                                        egreso_auto_flag = res[1] if len(res) > 1 else 0
                                        cursor.execute("UPDATE resumen_semanal SET egresos = ?, egreso_auto = ? WHERE maquina = ? AND fecha = ?", (nuevo_egreso, egreso_auto_flag, fila["maquina"], fila["fecha"]))
                                        conn.commit()
                                    else:
                                        if diferencia > 0:
                                            dia_semana = date.fromisoformat(fila["fecha"]).strftime("%A")
                                            dia_map = {"Monday":"Lunes","Tuesday":"Martes","Wednesday":"Miércoles","Thursday":"Jueves","Friday":"Viernes","Saturday":"Sábado","Sunday":"Domingo"}
                                            dia = dia_map.get(dia_semana, dia_semana)
                                            semana_iso = date.fromisoformat(fila["fecha"]).isocalendar()[1]
                                            semana_txt = f"Semana {semana_iso}"
                                            cursor.execute("INSERT INTO resumen_semanal (semana, fecha, maquina, dia, ventas, egresos, egreso_auto) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                                           (semana_txt, fila["fecha"], fila["maquina"], dia, 0, diferencia, 1))
                                            conn.commit()
                                # Intentar log y re-sincronizar si corresponde
                                try:
                                    log_accion("UPDATE", fila["maquina"], fila["fecha"], producto_text.strip(), float(costo_val), f"Edición inline rowid={rowid}")
                                except:
                                    pass
                                try:
                                    if diferencia > 0:
                                        sincronizar_egreso_en_ventas(fila["maquina"], fila["fecha"], diferencia)
                                except:
                                    pass

                                st.success("Registro actualizado correctamente.")
                                st.experimental_rerun()

    # --- Cargar y mostrar datos de rotación para la máquina y semana ---
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
        if "valor_unitario" not in df_rotacion.columns:
            df_rotacion["valor_unitario"] = 0.0
        df_rotacion["margen_unitario"] = df_rotacion["valor_unitario"] - df_rotacion["precio_unitario"]

        margen_total = df_rotacion["valor_unitario"].sum() - df_rotacion["gasto_total"].sum()
        if margen_total < 0:
            st.error("⚠️ Margen negativo: estás gastando más de lo que vendes en esta máquina.")

        st.subheader("📋 Resumen financiero semanal")
        df_resumen_gasto = df_rotacion.groupby(["producto", "unidad_compra"], as_index=False).agg({"costo_compra":"sum"})
        total_inversion_semana = df_resumen_gasto["costo_compra"].sum()
        st.success(f"🔔 Total invertido en compras esta semana: ${total_inversion_semana:,.0f}")
        df_resumen_gasto["porcentaje_inversion"] = (df_resumen_gasto["costo_compra"] / total_inversion_semana * 100) if total_inversion_semana > 0 else 0.0
        st.markdown("### 💸 Inversión por producto (según unidad de compra)")
        st.dataframe(df_resumen_gasto.sort_values("costo_compra", ascending=False), use_container_width=True)

        # Gráfica de inversión total por producto
        st.markdown("### 📈 Gráfica: Inversión total por producto (esta semana)")
        try:
            fig_inversion = px.bar(
                df_resumen_gasto.sort_values("costo_compra", ascending=False),
                x="producto",
                y="costo_compra",
                color="producto",
                text="costo_compra",
                labels={"costo_compra": "Inversión (COP)", "producto": "Producto"},
                title="Inversión total por producto"
            )
            fig_inversion.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
            fig_inversion.update_layout(template="plotly_dark", showlegend=False, xaxis_title="", yaxis_title="Inversión")
            st.plotly_chart(fig_inversion, use_container_width=True)
        except Exception:
            st.info("No se pudo generar la gráfica de inversión.")

        # Tabla de productos más vendidos
        st.subheader("🏆 Productos más vendidos esta semana")
        df_productos_vendidos = df_rotacion.groupby(["producto", "unidad_compra"], as_index=False).agg({
            "cantidad": "sum",
            "precio_unitario": "mean"
        })
        df_productos_vendidos["cantidad"] = df_productos_vendidos["cantidad"].astype(int)
        df_productos_vendidos = df_productos_vendidos.sort_values("cantidad", ascending=False)
        df_productos_vendidos = df_productos_vendidos[["producto", "unidad_compra", "cantidad", "precio_unitario"]]
        st.dataframe(df_productos_vendidos.reset_index(drop=True), use_container_width=True)

        # Exportar a Excel
        buf_rotacion = io.BytesIO()
        with pd.ExcelWriter(buf_rotacion, engine="openpyxl") as writer:
            df_rotacion.to_excel(writer, index=False, sheet_name=f"Rotación_{maquina_sel}")
            df_resumen_gasto.to_excel(writer, index=False, sheet_name="Inversión_por_Producto")
            df_productos_vendidos.to_excel(writer, index=False, sheet_name="Productos_Vendidos")
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