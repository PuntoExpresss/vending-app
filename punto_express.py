import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import date, timedelta
import io
import random
import re    

# import seguro de FPDF (debe ir una sola vez, al inicio del archivo)
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except Exception:
    FPDF_AVAILABLE = False
def limpiar_unicode(texto):
    """Elimina caracteres no ASCII para evitar errores al generar PDF."""
    return re.sub(r'[^\x00-\x7F]+', '', str(texto))



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
st.header("📊 Dashboard")

# Leer datos crudos
df = pd.read_sql_query("SELECT * FROM resumen_semanal ORDER BY fecha DESC", conn)

if df.empty:
    st.info("No hay datos registrados aún.")
else:
    # Normalizaciones y tipos
    df["semana"] = df.get("semana", "").fillna("")
    df["fecha"] = pd.to_datetime(df.get("fecha", None), errors="coerce")
    df["ventas"] = pd.to_numeric(df.get("ventas", 0), errors="coerce").fillna(0.0).astype(float)
    df["egresos"] = pd.to_numeric(df.get("egresos", 0), errors="coerce").fillna(0.0).astype(float)

    # Extraer semana/año desde etiqueta "Semana N-AAAA" o "Semana N"
    m = df["semana"].str.extract(r"Semana\s*(\d{1,2})(?:-(\d{4}))?")
    df["semana_tag_num"] = pd.to_numeric(m[0], errors="coerce")
    df["semana_tag_year"] = pd.to_numeric(m[1], errors="coerce")

    # Semana/año desde fecha (compatibilidad con distintas versiones de pandas)
    sem_info = df["fecha"].dt.isocalendar()
    if hasattr(sem_info, "columns") and {"week", "year"}.issubset(sem_info.columns):
        df["semana_date_num"] = sem_info["week"].astype("Int64")
        df["semana_date_year"] = sem_info["year"].astype("Int64")
    else:
        df["semana_date_num"] = df["fecha"].dt.week.astype("Int64")
        df["semana_date_year"] = df["fecha"].dt.year.astype("Int64")

    # Preferir etiqueta si existe, sino usar fecha
    df["semana_num"] = df["semana_tag_num"].fillna(df["semana_date_num"]).astype(int)
    df["semana_year"] = df["semana_tag_year"].fillna(df["semana_date_year"]).astype(int)

    # Determinar la semana más reciente por (año, semana)
    df_valid = df.dropna(subset=["semana_num", "semana_year"])
    if df_valid.empty:
        st.info("No hay semanas reconocibles en los registros.")
        st.stop()

    max_pair = df_valid[["semana_year", "semana_num"]].drop_duplicates().sort_values(["semana_year", "semana_num"]).iloc[-1]
    semana_actual = int(max_pair["semana_num"])
    año_actual = int(max_pair["semana_year"])
    semana_text = f"Semana {semana_actual}-{año_actual}"
    semana_text_simple = f"Semana {semana_actual}"

    # -------------------------------------------------------
    # Totales autoritativos (usar lo que guardó Control Ventas)
    # -------------------------------------------------------
    cursor = conn.cursor()
    tot_ventas_db = tot_egresos_db = 0.0
    note_fallback = False

    def leer_totales_por_etiqueta(etiqueta):
        try:
            cursor.execute(
                "SELECT COALESCE(SUM(CAST(ventas AS REAL)),0), COALESCE(SUM(CAST(egresos AS REAL)),0) FROM resumen_semanal WHERE semana = ?",
                (etiqueta,)
            )
            r = cursor.fetchone()
            if r:
                return float(r[0] or 0.0), float(r[1] or 0.0)
        except Exception:
            pass
        return 0.0, 0.0

    # 1) intentar etiqueta con año
    tot_ventas_db, tot_egresos_db = leer_totales_por_etiqueta(semana_text)

    # 2) fallback etiqueta simple
    if tot_ventas_db == 0 and tot_egresos_db == 0:
        tot_ventas_db, tot_egresos_db = leer_totales_por_etiqueta(semana_text_simple)

    # 3) fallback por rango de fecha (lunes a sábado)
    if tot_ventas_db == 0 and tot_egresos_db == 0:
        try:
            lunes = date.fromisocalendar(int(año_actual), int(semana_actual), 1)
            fecha_ini = str(lunes)
            fecha_fin = str(lunes + timedelta(days=5))
            cursor.execute(
                "SELECT COALESCE(SUM(CAST(ventas AS REAL)),0), COALESCE(SUM(CAST(egresos AS REAL)),0) FROM resumen_semanal WHERE fecha BETWEEN ? AND ?",
                (fecha_ini, fecha_fin)
            )
            r = cursor.fetchone()
            if r:
                tot_ventas_db, tot_egresos_db = float(r[0] or 0.0), float(r[1] or 0.0)
                note_fallback = True
        except Exception:
            tot_ventas_db, tot_egresos_db = 0.0, 0.0

    ventas_actual = float(tot_ventas_db)
    egresos_actual = float(tot_egresos_db)
    margen_actual = ventas_actual - egresos_actual

    # -------------------------------------------------------
    # Construir df_sem desde la misma fuente autoritativa
    # -------------------------------------------------------
    try:
        if not note_fallback:
            df_sem = pd.read_sql_query(
                "SELECT * FROM resumen_semanal WHERE semana = ? ORDER BY fecha, maquina",
                conn, params=(semana_text,)
            )
            if df_sem.empty:
                df_sem = pd.read_sql_query(
                    "SELECT * FROM resumen_semanal WHERE semana = ? ORDER BY fecha, maquina",
                    conn, params=(semana_text_simple,)
                )
        else:
            df_sem = pd.read_sql_query(
                "SELECT * FROM resumen_semanal WHERE fecha BETWEEN ? AND ? ORDER BY fecha, maquina",
                conn, params=(fecha_ini, fecha_fin)
            )
    except Exception:
        df_sem = pd.DataFrame(columns=["semana","fecha","maquina","dia","ventas","egresos"])

    # Normalizar df_sem
    if not df_sem.empty:
        df_sem["fecha"] = pd.to_datetime(df_sem["fecha"], errors="coerce")
        df_sem["ventas"] = pd.to_numeric(df_sem.get("ventas", 0), errors="coerce").fillna(0.0).astype(float)
        df_sem["egresos"] = pd.to_numeric(df_sem.get("egresos", 0), errors="coerce").fillna(0.0).astype(float)
        df_sem["neto"] = df_sem["ventas"] - df_sem["egresos"]
    else:
        df_sem = pd.DataFrame(columns=["semana","fecha","maquina","dia","ventas","egresos","neto"])

    # -----------------------
    # Métricas principales y adicionales
    # -----------------------
    # Promedio diario (Lun-Sáb)
    try:
        if not df_sem.empty:
            dias_unicos = df_sem["fecha"].dt.date.nunique()
            dias_unicos = dias_unicos if dias_unicos > 0 else 6
            avg_daily = ventas_actual / dias_unicos
        else:
            avg_daily = ventas_actual / 6 if ventas_actual else 0.0
    except Exception:
        avg_daily = 0.0

    # Top máquina y su porcentaje de contribución
    top_machine_pct = 0.0
    top_machine = None
    try:
        if not df_sem.empty:
            df_by_machine = df_sem.groupby("maquina", sort=False)["ventas"].sum().reset_index().sort_values("ventas", ascending=False)
            if not df_by_machine.empty and ventas_actual > 0:
                top_machine = df_by_machine.iloc[0]["maquina"]
                top_machine_pct = float(df_by_machine.iloc[0]["ventas"]) / ventas_actual * 100
    except Exception:
        top_machine_pct = 0.0
        top_machine = None

    # Mostrar métricas (origen: Control Ventas)
    st.metric("💰 Ventas (semana - Control Ventas)", f"${ventas_actual:,.0f}")
    st.metric("💸 Egresos (semana - Control Ventas)", f"${egresos_actual:,.0f}")
    st.metric("📊 Margen (semana)", f"${margen_actual:,.0f}")

    # métricas adicionales
    st.metric("📅 Promedio diario (Lun-Sáb)", f"${avg_daily:,.0f}")
    if top_machine:
        st.metric("🏆 Top máquina (% ventas)", f"{top_machine}: {top_machine_pct:.1f}%")
    else:
        st.metric("🏆 Top máquina (% ventas)", "Sin datos")

    if note_fallback:
        st.warning("Se usó fallback por rango de fechas; verifica que Control Ventas guardó la etiqueta 'Semana N-AAAA'.")

    # -----------------------
    # Gráfica por máquina
    # -----------------------
    df_maq = df_sem.groupby("maquina", sort=False)["ventas"].sum().reset_index()
    if not df_maq.empty:
        fig = px.bar(df_maq, x="maquina", y="ventas", title=f"Máquinas más vendidas - Semana {semana_actual}-{año_actual}", color="maquina")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay ventas por máquina para la semana seleccionada.")

    # -----------------------
    # Comparativa 2 semanas
    # -----------------------
    semana_anterior = semana_actual - 1
    año_anterior = año_actual
    if semana_anterior < 1:
        semana_anterior = 52
        año_anterior = año_actual - 1

    df_comp = df[df[["semana_num", "semana_year"]].apply(tuple, axis=1).isin([(semana_actual, año_actual), (semana_anterior, año_anterior)])]
    if df_comp.empty:
        try:
            lunes = date.fromisocalendar(año_actual, semana_actual, 1)
            fecha_ini = str(lunes)
            fecha_fin = str(lunes + timedelta(days=5))
            lunes_prev = date.fromisocalendar(año_anterior, semana_anterior, 1)
            fecha_ini_prev = str(lunes_prev)
            fecha_fin_prev = str(lunes_prev + timedelta(days=5))
            df_comp = df[df["fecha"].astype(str).between(fecha_ini_prev, fecha_fin) & df["fecha"].notna()]
        except Exception:
            df_comp = pd.DataFrame(columns=df.columns)

    if not df_comp.empty:
        df_comp_sum = df_comp.groupby(["semana_num", "maquina"], sort=False)["ventas"].sum().reset_index()
        fig2 = px.bar(df_comp_sum, x="maquina", y="ventas", color="semana_num", barmode="group", title="📊 Comparativa por máquina (2 semanas)")
        st.plotly_chart(fig2, use_container_width=True)

    # -----------------------
    # Alertas inteligentes
    # -----------------------
    lista_alertas = []
    ventas_actual_por_maquina = df_sem.groupby("maquina")["ventas"].sum()
    # Construir df_prev (priorizar etiqueta)
    semana_text_prev = f"Semana {semana_anterior}-{año_anterior}"
    semana_text_prev_simple = f"Semana {semana_anterior}"

    cursor.execute("SELECT COALESCE(COUNT(*),0) FROM resumen_semanal WHERE semana = ?", (semana_text_prev,))
    try:
        count_prev_exact = int(cursor.fetchone()[0] or 0)
    except Exception:
        count_prev_exact = 0
    if count_prev_exact == 0:
        cursor.execute("SELECT COALESCE(COUNT(*),0) FROM resumen_semanal WHERE semana = ?", (semana_text_prev_simple,))
        try:
            count_prev_simple = int(cursor.fetchone()[0] or 0)
        except Exception:
            count_prev_simple = 0
    else:
        count_prev_simple = 0

    if count_prev_exact > 0:
        df_prev = pd.read_sql_query("SELECT * FROM resumen_semanal WHERE semana = ? ORDER BY fecha, maquina", conn, params=(semana_text_prev,))
    elif count_prev_simple > 0:
        df_prev = pd.read_sql_query("SELECT * FROM resumen_semanal WHERE semana = ? ORDER BY fecha, maquina", conn, params=(semana_text_prev_simple,))
    else:
        try:
            lunes_prev = date.fromisocalendar(año_anterior, semana_anterior, 1)
            fecha_ini_prev = str(lunes_prev)
            fecha_fin_prev = str(lunes_prev + timedelta(days=5))
            df_prev = pd.read_sql_query("SELECT * FROM resumen_semanal WHERE fecha BETWEEN ? AND ? ORDER BY fecha, maquina", conn, params=(fecha_ini_prev, fecha_fin_prev))
        except Exception:
            df_prev = pd.DataFrame(columns=df.columns)

    ventas_prev_por_maquina = df_prev.groupby("maquina")["ventas"].sum() if not df_prev.empty else pd.Series(dtype=float)

    for maquina in ventas_actual_por_maquina.index:
        actual = float(ventas_actual_por_maquina.get(maquina, 0.0))
        anterior = float(ventas_prev_por_maquina.get(maquina, 0.0)) if not ventas_prev_por_maquina.empty else 0.0
        if anterior > 0:
            cambio = ((actual - anterior) / anterior) * 100
            if cambio <= -30:
                lista_alertas.append(f"🔴 {maquina} cayó {abs(round(cambio))}% respecto a la semana anterior.")
            elif cambio >= 20:
                lista_alertas.append(f"🟢 {maquina} subió {round(cambio)}% respecto a la semana anterior.")
        elif actual > 0:
            lista_alertas.append(f"🟢 {maquina} tuvo ventas esta semana pero estaba en cero la anterior.")

    if float(df_sem["neto"].sum()) < 0:
        lista_alertas.append("⚠️ Profit negativo esta semana. Revisa egresos y márgenes.")
    if round(max(0.0, float(df_sem["neto"].sum())) * 0.05) < 50000:
        lista_alertas.append(f"⚠️ Fondo de emergencia bajo: solo ${round(max(0.0, float(df_sem['neto'].sum())) * 0.05):,.0f}")

    if lista_alertas:
        with st.expander("🚨 Alertas inteligentes"):
            for alerta in lista_alertas:
                try:
                    texto_limpio = limpiar_unicode(alerta)
                except Exception:
                    texto_limpio = str(alerta)
                st.warning(texto_limpio)

    # -----------------------
    # Resumen y exportación PDF (opcional)
    # -----------------------
    resumen = pd.DataFrame({
        "Métrica": [
            "Total Ventas", "Total Egresos", "Profit Neto",
            "Fondo Emergencia (5%)", "Variación semanal"
        ],
        "Valor": [
            f"${ventas_actual:,.0f}",
            f"${df_sem['egresos'].sum():,.0f}",
            f"${df_sem['neto'].sum():,.0f}",
            f"${round(max(0.0, df_sem['neto'].sum()) * 0.05):,.0f}",
            f"{(round(((ventas_actual - (ventas_prev if 'ventas_prev' in locals() else 0)) / (ventas_prev if 'ventas_prev' in locals() and ventas_prev else 1)) * 100, 2) if 'ventas_prev' in locals() and ventas_prev else 0):+.2f}%"
        ]
    })

    if 'FPDF_AVAILABLE' in globals() and FPDF_AVAILABLE:
        try:
            class PDF(FPDF):
                def header(self):
                    self.set_font("Arial", "B", 16)
                    self.set_text_color(40, 40, 40)
                    self.cell(0, 10, "Puntoexpress - Resumen Ejecutivo", ln=True, align="C")
                    self.set_font("Arial", "", 12)
                    self.cell(0, 10, f"Semana {semana_actual}-{año_actual}", ln=True, align="C")
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
                    try:
                        texto_limpio = limpiar_unicode(alerta)
                    except Exception:
                        texto_limpio = str(alerta)
                    pdf.multi_cell(0, 10, f"- {texto_limpio}")

            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.markdown("### 📄 Exportación PDF")
            st.download_button(
                label="📄 Exportar resumen en PDF",
                data=pdf_bytes,
                file_name=f"resumen_semana_{semana_actual}_{año_actual}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.info(f"No se pudo generar PDF: {e}")
    else:
        st.info("La librería FPDF no está disponible; instala 'fpdf' si quieres generar PDF desde el dashboard.")

    # -----------------------
    # Panel de métricas semanales por mes (forzar semana actual a usar ventas_actual)
    # -----------------------
    df_mensual = pd.read_sql_query("SELECT semana, fecha, COALESCE(ventas,0) AS ventas FROM resumen_semanal", conn)
    df_mensual["fecha"] = pd.to_datetime(df_mensual["fecha"], errors="coerce")
    df_mensual = df_mensual.dropna(subset=["fecha"]).copy()

    if df_mensual.empty:
        st.info("No hay datos históricos para mostrar métricas por mes.")
    else:
        # obtener semana y año ISO (compatible)
        sem_info = df_mensual["fecha"].dt.isocalendar()
        if hasattr(sem_info, "columns") and {"week", "year"}.issubset(sem_info.columns):
            df_mensual["semana_num"] = sem_info["week"].astype(int)
            df_mensual["semana_year"] = sem_info["year"].astype(int)
        else:
            df_mensual["semana_num"] = df_mensual["fecha"].dt.week.astype(int)
            df_mensual["semana_year"] = df_mensual["fecha"].dt.year.astype(int)

        # calcular el lunes de la semana y asignar mes por ese lunes
        df_mensual["lunes_week"] = df_mensual["fecha"].apply(lambda d: (d - pd.Timedelta(days=d.weekday())).date())
        df_mensual["mes_asignado"] = df_mensual["lunes_week"].apply(lambda d: pd.to_datetime(d).strftime("%B %Y"))

        # etiqueta de semana unívoca
        df_mensual["sem_label"] = df_mensual.apply(lambda r: f"{int(r['semana_num'])}-{int(r['semana_year'])}", axis=1)

        # agrupar ventas por mes_asignado y sem_label
        df_semanal = df_mensual.groupby(["mes_asignado", "sem_label"], sort=False)["ventas"].sum().reset_index()

        # extraer componentes para ordenar
        df_semanal[["sem_num_only", "sem_year_only"]] = df_semanal["sem_label"].str.split("-", expand=True).astype(int)
        df_semanal = df_semanal.sort_values(by=["mes_asignado", "sem_year_only", "sem_num_only"]).reset_index(drop=True)

        # Si falta la semana actual en df_semanal, insertarla con ventas_actual
        current_label = f"{int(semana_actual)}-{int(año_actual)}"
        if current_label not in df_semanal["sem_label"].values:
            # intentar determinar mes_asignado para el lunes de la semana actual
            try:
                monday_current = date.fromisocalendar(int(año_actual), int(semana_actual), 1)
                mes_asignado_current = pd.to_datetime(monday_current).strftime("%B %Y")
            except Exception:
                mes_asignado_current = df_semanal["mes_asignado"].iloc[0] if not df_semanal.empty else pd.to_datetime(date.today()).strftime("%B %Y")
            # insertar fila
            df_semanal = pd.concat([
                df_semanal,
                pd.DataFrame([{
                    "mes_asignado": mes_asignado_current,
                    "sem_label": current_label,
                    "ventas": float(ventas_actual),
                    "sem_num_only": int(semana_actual),
                    "sem_year_only": int(año_actual)
                }])
            ], ignore_index=True)

        # Reemplazar si existe para forzar el valor autoritativo
        df_semanal.loc[df_semanal["sem_label"] == current_label, "ventas"] = float(ventas_actual)

        # recalcular variaciones y color después del ajuste
        df_semanal["variacion"] = df_semanal.groupby("mes_asignado")["ventas"].pct_change().fillna(0) * 100
        df_semanal["color"] = df_semanal["variacion"].apply(lambda x: "🟢" if x > 0 else ("🔴" if x < 0 else "⚪"))

        # mostrar panel (paginado si hay muchas semanas)
        st.markdown("### 📊 Panel de métricas semanales por mes")
        MAX_COLS = 6
        for mes in df_semanal["mes_asignado"].unique():
            st.markdown(f"#### 📅 {mes}")
            semanas_mes = df_semanal[df_semanal["mes_asignado"] == mes].reset_index(drop=True)
            if semanas_mes.empty:
                st.info("No hay datos para este mes.")
                continue

            n = len(semanas_mes)
            for start in range(0, n, MAX_COLS):
                chunk = semanas_mes.iloc[start:start + MAX_COLS].reset_index(drop=True)
                cols = st.columns(len(chunk))
                for i, row in chunk.iterrows():
                    sem_display = row["sem_label"].replace("-", " / ")
                    label = f"Semana {sem_display}"
                    if row["sem_label"] == current_label:
                        label += " (actual)"
                    with cols[i]:
                        st.metric(
                            label=label,
                            value=f"${row['ventas']:,.0f}",
                            delta=f"{row['color']} {row['variacion']:+.1f}%",
                            delta_color="normal"
                        )
#
# Control Ventas
# 
    from datetime import date, timedelta
if opcion == "Control Ventas":
    st.title("📆 Informe Semanal Editable")

    # Semana actual por defecto
    semana_actual = date.today().isocalendar()[1]
    año_actual = date.today().year

    # Selección de semana y año (keys únicas para evitar conflicto entre dispositivos/vistas)
    col1, col2 = st.columns(2)
    with col1:
        semana_num = st.number_input(
            "Número de semana", min_value=1, max_value=53,
            value=semana_actual, key=f"cv_semana_{semana_actual}_{año_actual}"
        )
    with col2:
        año = st.number_input(
            "Año", min_value=2020, max_value=2035,
            value=año_actual, key=f"cv_año_{semana_actual}_{año_actual}"
        )

    # Validar y calcular rango de fechas (lunes a sábado)
    try:
        lunes = date.fromisocalendar(int(año), int(semana_num), 1)
    except Exception:
        st.error("Semana o año inválidos. Ajusta los valores.")
        st.stop()

    fechas = [lunes + timedelta(days=i) for i in range(6)]  # lunes a sábado
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
    st.subheader(f"📅 Semana {semana_num}: {fechas[0]} a {fechas[-1]}")

    # Etiqueta única de semana que incluye año para evitar colisiones
    semana_text = f"Semana {int(semana_num)}-{int(año)}"

    # Asegurar existencia de tabla con tipos numéricos apropiados
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumen_semanal (
            semana TEXT,
            fecha TEXT,
            maquina TEXT,
            dia TEXT,
            ventas REAL,
            egresos REAL,
            egreso_auto INTEGER DEFAULT 0
        )
    """)
    conn.commit()

    # Cargar datos existentes para el rango: preferimos registros con la etiqueta semana_text,
    # además incluimos aquellas filas sin etiqueta pero dentro del rango (compatibilidad con datos antiguos)
    df_exist = pd.read_sql_query(
        "SELECT semana, fecha, maquina, dia, COALESCE(ventas,0) AS ventas, COALESCE(egresos,0) AS egresos "
        "FROM resumen_semanal WHERE semana = ? OR fecha BETWEEN ? AND ? ORDER BY maquina, fecha",
        conn, params=(semana_text, str(fechas[0]), str(fechas[-1]))
    )

    # Lista de máquinas (mantener consistente en toda la app)
    maquinas = [
        "Motomall", "Unidad", "Norte", "Buses",
        "Paquetex", "Dekohouse", "Caldas", "Maquina 8"
    ]

    st.markdown("#### Ingresa ventas y egresos por día y máquina")

    # Mostrar inputs por máquina y día, usar keys únicas basadas en máquina/fecha/semana/año
    for maquina in maquinas:
        st.markdown(f"### {maquina}")
        cols = st.columns(6)
        for i, fecha in enumerate(fechas):
            dia = dias_semana[i]
            fecha_str = str(fecha)
            # Recuperar valores existentes en df_exist (si hay múltiples, preferir fila con semana_text)
            filas_m = df_exist[(df_exist["maquina"] == maquina) & (df_exist["fecha"] == fecha_str)]
            if not filas_m.empty:
                fila_preferida = filas_m[filas_m["semana"] == semana_text]
                if fila_preferida.empty:
                    fila_preferida = filas_m.iloc[[0]]
                else:
                    fila_preferida = fila_preferida.iloc[[0]]
                venta_val = float(fila_preferida["ventas"].values[0])
                egreso_val = float(fila_preferida["egresos"].values[0])
            else:
                venta_val = 0.0
                egreso_val = 0.0

            # Keys únicas por input (incluyen semana y año)
            key_v = f"cv_{maquina}_{fecha_str}_v_sem{semana_num}_y{año}"
            key_e = f"cv_{maquina}_{fecha_str}_e_sem{semana_num}_y{año}"

            with cols[i]:
                venta = st.number_input(
                    f"{dia} Ventas", min_value=0.0, value=venta_val,
                    step=100.0, format="%.2f", key=key_v
                )
                egreso = st.number_input(
                    f"{dia} Egresos", min_value=0.0, value=egreso_val,
                    step=50.0, format="%.2f", key=key_e
                )

    # Botón para guardar: leer desde session_state para garantizar consistencia entre dispositivos
    if st.button("💾 Guardar semana", key=f"guardar_semana_cv_{semana_num}_{año}"):
        registros_a_insertar = []
        for maquina in maquinas:
            for i, fecha in enumerate(fechas):
                dia = dias_semana[i]
                fecha_str = str(fecha)
                key_v = f"cv_{maquina}_{fecha_str}_v_sem{semana_num}_y{año}"
                key_e = f"cv_{maquina}_{fecha_str}_e_sem{semana_num}_y{año}"

                # Obtener valores desde session_state con fallback
                venta_val = float(st.session_state.get(key_v, 0.0))
                egreso_val = float(st.session_state.get(key_e, 0.0))

                registros_a_insertar.append((
                    semana_text, fecha_str, maquina, dia, venta_val, egreso_val
                ))

        # Operación atómica: borrar por etiqueta de semana y limpiar filas antiguas sin etiqueta dentro del rango
        try:
            # Borrar registros con la etiqueta exacta (seguro)
            cursor.execute("DELETE FROM resumen_semanal WHERE semana = ?", (semana_text,))
            # Borrar registros sin etiqueta (NULL o '') dentro el rango para evitar colisiones previas
            cursor.execute("DELETE FROM resumen_semanal WHERE (semana IS NULL OR semana = '') AND fecha BETWEEN ? AND ?", (str(fechas[0]), str(fechas[-1])))
            if registros_a_insertar:
                cursor.executemany(
                    "INSERT INTO resumen_semanal (semana, fecha, maquina, dia, ventas, egresos, egreso_auto) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [(r[0], r[1], r[2], r[3], r[4], r[5], 1) for r in registros_a_insertar]
                )
            conn.commit()
            st.success("✅ Semana actualizada correctamente.")
        except Exception as e:
            conn.rollback()
            st.error(f"Error guardando la semana: {e}")

    # --- Mostrar totales y gráficos (usar solamente registros con la etiqueta exacta de semana) ---
    df_actualizada = pd.read_sql_query(
        "SELECT semana, fecha, maquina, dia, COALESCE(ventas,0) AS ventas, COALESCE(egresos,0) AS egresos FROM resumen_semanal WHERE semana = ? ORDER BY maquina, fecha",
        conn, params=(semana_text,)
    )

    if df_actualizada.empty:
        st.info("No se encontraron registros guardados con la etiqueta de semana. Asegúrate de haber guardado la semana (botón Guardar semana).")
    else:
        # asegurar tipos numéricos y rellenar NA
        df_actualizada["ventas"] = pd.to_numeric(df_actualizada["ventas"], errors="coerce").fillna(0.0).astype(float)
        df_actualizada["egresos"] = pd.to_numeric(df_actualizada["egresos"], errors="coerce").fillna(0.0).astype(float)

        # Totales por SQL (robusto frente a duplicados)
        cursor.execute("SELECT COALESCE(SUM(CAST(ventas AS REAL)),0), COALESCE(SUM(CAST(egresos AS REAL)),0) FROM resumen_semanal WHERE semana = ?", (semana_text,))
        tot_ventas_sql, tot_egresos_sql = cursor.fetchone() or (0.0, 0.0)
        tv = float(tot_ventas_sql)
        te = float(tot_egresos_sql)

        # neto y resto de métricas desde el dataframe confiable
        df_actualizada["neto"] = df_actualizada["ventas"] - df_actualizada["egresos"]
        tn = float(df_actualizada["neto"].sum())

        # días con ventas > 0 para promedio diario
        ventas_por_dia = df_actualizada.groupby("fecha", sort=False)["ventas"].sum()
        dv = int((ventas_por_dia > 0).sum())
        pdia = round(tv / dv, 2) if dv else 0.0

        ft = round(max(0.0, tn) * 0.05)

        st.markdown("### 📊 Totales Semanales (calculado desde registros con etiqueta exacta)")
        c1, c2, c3 = st.columns(3)
        c1.metric("🔢 Ventas", f"${tv:,.0f}")
        c2.metric("📉 Egresos", f"${te:,.0f}")
        c3.metric("💰 Profit", f"${tn:,.0f}")
        c4, c5 = st.columns(2)
        c4.metric("📈 Promedio diario (días con ventas)", f"${pdia:,.2f}")
        c5.metric("🛟 Fondo 5%", f"${ft:,.0f}")

        # Alerta: días sin ventas reales
        dias_sin_ventas = int((ventas_por_dia == 0).sum())
        if dias_sin_ventas > 0:
            st.warning(f"🟠 Alerta: hay {dias_sin_ventas} día(s) sin ventas esta semana.")

        # Nota si todas las máquinas registraron ventas
        maquinas_con_ventas = sorted(df_actualizada[df_actualizada["ventas"] > 0]["maquina"].unique().tolist())
        maquinas_ref = maquinas  # lista definida arriba
        if set(maquinas_con_ventas) == set(maquinas_ref) and len(maquinas_ref) > 0:
            st.success("🟢 Todas las máquinas registraron ventas esta semana. ¡Buen desempeño!")

        # Gráficos: días y máquinas (mantener orden de dias_semana)
        order_dias = dias_semana
        df_d = df_actualizada.groupby("dia", sort=False)["ventas"].sum().reindex(order_dias).fillna(0).reset_index()
        fig1 = px.bar(df_d, x="dia", y="ventas", title="📅 Días con más ventas", color="dia", labels={"ventas": "Ventas", "dia": "Día"})
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

        df_m = df_actualizada.groupby("maquina")["ventas"].sum().reset_index().sort_values("ventas", ascending=False)
        fig2 = px.bar(df_m, x="maquina", y="ventas", title="🏭 Ventas por máquina", color="maquina", labels={"ventas": "Ventas", "maquina": "Máquina"})
        fig2.update_layout(xaxis_tickangle=-45, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

        # Métricas destacadas protegidas
        if df_actualizada["ventas"].sum() > 0:
            dia_top = df_actualizada.groupby("dia")["ventas"].sum().sort_values(ascending=False).index[0]
            maquinas_top_list = df_actualizada.groupby("maquina")["ventas"].sum().sort_values(ascending=False).head(4).index.to_list()
            maquinas_top_str = ", ".join(maquinas_top_list)
        else:
            dia_top = "N/A"
            maquinas_top_str = "N/A"

        resumen = pd.DataFrame({
            "Métrica": [
                "Total Ventas", "Total Egresos", "Profit Neto",
                "Promedio Diario", "Fondo Emergencia (5%)",
                "Día con más ventas", "Top 4 máquinas"
            ],
            "Valor": [
                f"${tv:,.0f}", f"${te:,.0f}", f"${tn:,.0f}",
                f"${pdia:,.2f}", f"${ft:,.0f}",
                dia_top,
                maquinas_top_str
            ]
        })

        st.markdown("### 📋 Resumen Ejecutivo")
        st.dataframe(resumen, use_container_width=True)

        # 📥 Exportar datos completos (ventas de la semana)
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

    # --- Resumen mensual por semana (sujeto a existencia de datos) ---
    df_mensual = pd.read_sql_query("SELECT semana, fecha, COALESCE(ventas,0) AS ventas FROM resumen_semanal", conn)
    if not df_mensual.empty:
        df_mensual["fecha"] = pd.to_datetime(df_mensual["fecha"])
        df_mensual["mes"] = df_mensual["fecha"].dt.strftime("%B")
        df_mensual["semana_num"] = df_mensual["fecha"].dt.isocalendar().week

        resumen_semanal = df_mensual.groupby(["mes", "semana_num"])["ventas"].sum().reset_index()
        resumen_semanal = resumen_semanal.sort_values(by=["mes", "semana_num"])

        st.markdown("### 📅 Totales por semana agrupados por mes")
        st.dataframe(resumen_semanal.rename(columns={
            "mes": "Mes",
            "semana_num": "Semana",
            "ventas": "Total Ventas"
        }), use_container_width=True)

        # Alerta por semanas con ventas bajas
        semanas_bajas = resumen_semanal[resumen_semanal["ventas"] < 10000]
        if not semanas_bajas.empty:
            st.warning(f"⚠️ Atención: {len(semanas_bajas)} semana(s) con ventas menores a $10,000.")
    else:
        st.info("No hay datos históricos para mostrar el resumen mensual.")


    # 🧭 Nueva sección: Reabastecimiento Inteligente
if opcion == "Reabastecimiento":
    st.title("🚚 Reabastecimiento Inteligente")

    # Parámetros de entrada
    col1, col2 = st.columns(2)
    with col1:
        semana_prog = st.number_input("Semana de programación", min_value=1, max_value=53, value=date.today().isocalendar()[1], key="rb_sem_prog")
    with col2:
        año_prog = st.number_input("Año de programación", min_value=2020, max_value=2100, value=date.today().year, key="rb_año_prog")

    # Helpers: festivos (asegúrate de definir o cargar festivos_2025 en tu entorno)
    try:
        festivos = festivos_2025  # variable que ya tenías en tu app
    except Exception:
        # Si no existe, prevenir que falle: lista vacía
        festivos = []

    # --- Ventas de la semana anterior (segura) ---
    sem_venta = semana_prog - 1
    if sem_venta < 1:
        # manejar cambio de año simple: retroceder al año anterior última semana (simplificación)
        sem_venta = 52
        año_venta = año_prog - 1
    else:
        año_venta = año_prog

    try:
        lunes_v = date.fromisocalendar(int(año_venta), int(sem_venta), 1)
    except Exception:
        st.error("Semana/anio inválidos para la consulta de ventas anteriores.")
        st.stop()

    fechas_v = [lunes_v + timedelta(days=i) for i in range(6)]
    # Leer solo columnas necesarias y proteger la consulta
    try:
        df_v = pd.read_sql_query(
            "SELECT semana, fecha, maquina, COALESCE(ventas,0) AS ventas FROM resumen_semanal WHERE fecha BETWEEN ? AND ?",
            conn, params=(str(fechas_v[0]), str(fechas_v[-1]))
        )
    except Exception:
        df_v = pd.DataFrame(columns=["semana", "fecha", "maquina", "ventas"])

    # Si no hay datos, evitar errores posteriores
    if df_v.empty:
        st.info("No se encontraron registros de ventas para la semana anterior; la programación será conservadora.")
        # crear df_rank vacío con columna maquina para no romper el flujo
        df_rank = pd.DataFrame(columns=["maquina", "ventas"])
    else:
        df_rank = df_v.groupby("maquina", sort=False)["ventas"].sum().reset_index().sort_values("ventas", ascending=False)

    # Top4 robusto (si hay menos de 4 máquinas, tomar las disponibles)
    top4 = df_rank.head(4)["maquina"].tolist()
    # si top4 vacío, usar lista de máquinas desde BD o una lista por defecto
    if not top4:
        try:
            cursor.execute("SELECT nombre_maquina FROM maquina")
            top4 = [r[0] for r in cursor.fetchall() if r[0]]
        except Exception:
            top4 = []
    # Si aún vacío, usar un placeholder para evitar crash
    if not top4:
        st.warning("No hay máquinas disponibles para programar reabastecimiento.")
        top4 = []

    # --- Calendario de programación (semana objetivo) ---
    try:
        lunes_p = date.fromisocalendar(int(año_prog), int(semana_prog), 1)
    except Exception:
        st.error("Semana/anio inválidos para la programación.")
        st.stop()

    sched_days = [lunes_p + timedelta(days=i) for i in range(6)]
    dias_nombre = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado"}

    # mapping defensivo: si top4 tiene menos elementos, usar lo que exista
    mapping = {
        "Lunes":   top4[0:2] if len(top4) >= 2 else top4[:],
        "Martes":  [top4[0]] + ([top4[2]] if len(top4) > 2 else []),
        "Miércoles": top4[0:2] if len(top4) >= 2 else top4[:],
        "Jueves":  [top4[0]] + ([top4[3]] if len(top4) > 3 else []),
        "Viernes": top4[0:2] if len(top4) >= 2 else top4[:],
        "Sábado":  [top4[2]] if len(top4) > 2 else (top4[:] if top4 else [])
    }

    # construir schedule evitando claves duplicadas y asegurando listas
    schedule = {}
    workdays = [d for d in sched_days if str(d) not in [str(x) for x in festivos]]
    holidays = [d for d in sched_days if str(d) in [str(x) for x in festivos]]

    for d in workdays:
        name = dias_nombre.get(d.weekday(), str(d.weekday()))
        assigned = mapping.get(name, []).copy()
        # garantizar elementos únicos
        schedule[d] = list(dict.fromkeys(assigned))

    # si hay feriados, trasladar programación al día anterior si existe en schedule
    for h in holidays:
        prev = h - timedelta(days=1)
        if prev in schedule:
            # reemplazar por top4 completo (si existe) o dejar como estaba
            schedule[prev] = list(dict.fromkeys(top4 + schedule.get(prev, [])))

    # Sábado: asignar espacio libre según opción de usuario
    sat = [d for d in workdays if d.weekday() == 5]
    sat_day = sat[0] if sat else None
    # counts seguros (si top4 vacío, counts vacíos)
    counts = {m: sum(m in v for v in schedule.values()) for m in top4} if top4 else {}
    emergent = None
    if not df_rank.empty and len(df_rank) > 4:
        emergent = df_rank.iloc[4]["maquina"]
    # elegir la menos abastecida de top4 si existen
    least = None
    if counts:
        least = min(counts, key=counts.get)

    opcion_libre = st.radio(
        "¿Cómo asignar espacio libre del sábado?",
        ("Opción A: máquina menos abastecida", "Opción B: máquina emergente")
    )
    # decidir flex de forma robusta
    flex = None
    if opcion_libre.startswith("Opción A") and least:
        flex = least
    elif opcion_libre.startswith("Opción B") and emergent:
        flex = emergent
    # si no hay flex disponible, no asignar
    if sat_day and flex:
        if flex not in schedule.get(sat_day, []):
            schedule.setdefault(sat_day, []).append(flex)

    # Mostrar ranking (protecciones)
    st.markdown("### 🏆 Ranking Semanal")
    if df_rank.empty:
        st.info("No hay datos de ventas para generar ranking.")
    else:
        st.table(df_rank.head(8).reset_index(drop=True))

    # Construir DataFrame de calendario (ordenado)
    data = []
    for d in sorted(schedule.keys()):
        maquinas_str = ", ".join(schedule[d]) if schedule[d] else "(sin asignar)"
        data.append({
            "fecha": str(d),
            "día": dias_nombre.get(d.weekday(), ""),
            "máquinas": maquinas_str
        })
    if data:
        sched_df = pd.DataFrame(data)
    else:
        sched_df = pd.DataFrame(columns=["fecha", "día", "máquinas"])

    st.markdown("### 📅 Calendario de Reabastecimiento")
    if sched_df.empty:
        st.info("No hay programación generada para la semana seleccionada.")
    else:
        st.table(sched_df)

    # Exportar Excel (seguro)
    try:
        buf2 = io.BytesIO()
        with pd.ExcelWriter(buf2, engine="openpyxl") as writer:
            sched_df.to_excel(writer, index=False, sheet_name=f"Reab_{semana_prog}")
        st.download_button(
            "📥 Exportar Reabastecimiento a Excel",
            data=buf2.getvalue(),
            file_name=f"reabastecimiento_semana_{semana_prog}_{año_prog}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"No se pudo generar el archivo de exportación: {e}")
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