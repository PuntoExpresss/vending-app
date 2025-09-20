01 import streamlit as st
02 import pandas as pd
03 import sqlite3
04 import holidays
05 from datetime import date, timedelta
06 
07 conn = sqlite3.connect("vending.db")
08 cursor = conn.cursor()
09 
10 st.set_page_config(page_title="Punto Express", layout="wide")
11 
12 st.sidebar.image("logo.png", width=150)
13 opcion = st.sidebar.radio(
14     "📋 Navegación:",
15     ["Dashboard", "Ventas Semanales", "Reabastecimiento", "Historial", "Reportes"]
16 )
17 
18 festivos_col = holidays.Colombia()
19 hoy = date.today()
20 mañana = hoy + timedelta(days=1)
21 if mañana in festivos_col:
22     nombre_festivo = festivos_col[mañana]
23     st.sidebar.warning(f"🎉 Mañana es festivo: {nombre_festivo}. ¡Carga completa recomendada hoy!")
24 
25 # 📊 DASHBOARD
26 if opcion == "Dashboard":
27     st.header("📊 Resumen Semanal")
28     df_resumen = pd.read_sql_query("SELECT * FROM resumen_semanal ORDER BY fecha DESC LIMIT 7", conn)
29     df_resumen.index = df_resumen.index + 1
30     st.dataframe(df_resumen)
31 
32     st.subheader("🏪 Ventas por máquina")
33     maquinas = [col for col in df_resumen.columns if col.startswith("maquina_")]
34     df_maquinas = df_resumen[maquinas].sum().reset_index()
35     df_maquinas.columns = ["Máquina", "Ventas"]
36     st.bar_chart(df_maquinas.set_index("Máquina"))
37 
38     st.subheader("📅 Tendencia de ventas diarias")
39     df_tendencia = df_resumen[["fecha", "total_ventas"]].sort_values("fecha")
40     df_tendencia["fecha"] = pd.to_datetime(df_tendencia["fecha"])
41     st.line_chart(df_tendencia.set_index("fecha"))
42 
43     st.subheader("📌 Indicadores clave")
44     total_semanal = df_resumen["total_ventas"].sum()
45     promedio_diario = df_resumen["total_ventas"].mean()
46     dia_mayor = df_resumen.loc[df_resumen["total_ventas"].idxmax(), "fecha"]
47     st.metric(label="💰 Total semanal", value=f"${total_semanal:,.0f}")
48     st.metric(label="📈 Promedio diario", value=f"${promedio_diario:,.0f}")
49     st.metric(label="🔥 Día más fuerte", value=str(dia_mayor))
50 
51 # 📈 VENTAS SEMANALES
52 elif opcion == "Ventas Semanales":
53     st.header("📅 Ventas por Semana")
54     df_ventas = pd.read_sql_query("SELECT * FROM ventas_semanales ORDER BY semana DESC", conn)
55     df_ventas.index = df_ventas.index + 1
56     st.dataframe(df_ventas)
57 
58     st.subheader("📊 Comparativa por máquina")
59     maquinas = [col for col in df_ventas.columns if col.startswith("maquina_")]
60     df_maquinas = df_ventas[maquinas].sum().reset_index()
61     df_maquinas.columns = ["Máquina", "Ventas"]
62     st.bar_chart(df_maquinas.set_index("Máquina"))
63 
64 # 🔄 REABASTECIMIENTO
65 elif opcion == "Reabastecimiento":
66     st.header("🔄 Reabastecimiento de Máquinas")
67     df_stock = pd.read_sql_query("SELECT * FROM stock_actual ORDER BY maquina, producto", conn)
68     df_stock.index = df_stock.index + 1
69     st.dataframe(df_stock)
70 
71     st.subheader("⚠️ Alertas de Reabastecimiento")
72     for i, row in df_stock.iterrows():
73         if row["cantidad"] < 10:
74             st.warning(f"🟠 Producto '{row['producto']}' en máquina {row['maquina']} tiene solo {row['cantidad']} unidades. ¡Reabastecer pronto!")
75 
76     if mañana in festivos_col:
77         nombre_festivo = festivos_col[mañana]
78         st.info(f"🎉 Mañana es festivo: {nombre_festivo}. Se recomienda carga completa hoy en todas las máquinas.")
79 
80     if st.button("📦 Simular carga completa"):
81         for i, row in df_stock.iterrows():
82             cursor.execute(
83                 "UPDATE stock_actual SET cantidad = ? WHERE maquina = ? AND producto = ?",
84                 (50, row["maquina"], row["producto"])
85             )
86         conn.commit()
87         st.success("✅ Simulación de carga completa realizada")
88 
89         df_stock = pd.read_sql_query("SELECT * FROM stock_actual ORDER BY maquina, producto", conn)
90         df_stock.index = df_stock.index + 1
91         st.dataframe(df_stock)
92 
93 # 📚 HISTORIAL
94 elif opcion == "Historial":
95     st.header("📚 Historial de Transacciones")
96     df_historial = pd.read_sql_query("SELECT * FROM historial ORDER BY fecha DESC", conn)
97     df_historial.index = df_historial.index + 1
98     st.dataframe(df_historial)
99 
100     st.subheader("🔍 Filtro por máquina")
101     maquinas = df_historial["maquina"].unique()
102     seleccion = st.selectbox("Selecciona una máquina", maquinas)
103     filtrado = df_historial[df_historial["maquina"] == seleccion]
104     st.dataframe(filtrado)
105 
106 # 📥 REPORTES
107 elif opcion == "Reportes":
108     st.header("📥 Gestionar Reportes")
109 
110     if st.button("🗑️ Borrar simulación Semana 38"):
111         cursor.execute("DELETE FROM resumen_semanal WHERE semana = ?", ("Semana 38",))
112         conn.commit()
113         st.success("✅ Datos de simulación eliminados")
114 
115     df_r = pd.read_sql_query("SELECT * FROM resumen_semanal ORDER BY fecha DESC", conn)
116     df_r.index = df_r.index + 1
117     st.dataframe(df_r)
118 
119     csv = df_r.to_csv(index=False).encode("utf-8")
120     st.download_button(
121         label="📥 Descargar CSV",
122         data=csv,
123         file_name="resumen_semanal.csv",
124         mime="text/csv"
125     )

