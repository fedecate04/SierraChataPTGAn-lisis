import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
from datetime import datetime
import os
from io import BytesIO
from PIL import Image
import re

# Configuración
st.set_page_config(page_title="LTS Lab Analyzer", layout="wide")
LOGO_PATH = "logopetrogas.png"
MANUAL_PATH = "manual_operador_LTS.pdf"
HISTORIAL_PATH = "historial.csv"

# Estilo gris oscuro
st.markdown("""
    <style>
        .stApp {
            background-color: #2d2d2d;
            color: #f0f0f0;
        }
        .stButton>button {
            background-color: #0d6efd;
            color: white;
            border: none;
        }
        input, textarea, .stTextInput, .stTextArea {
            background-color: #3a3a3a !important;
            color: white !important;
        }
        .stSelectbox div, .stDownloadButton, .stNumberInput {
            background-color: #3a3a3a !important;
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

# Funciones auxiliares
def limpiar_texto(texto):
    texto = str(texto)
    texto = texto.replace("–", "-").replace("—", "-").replace("“", '"').replace("”", '"')
    texto = texto.replace("√", "sqrt")
    texto = re.sub(r'[^\x00-\xFF]', '', texto)
    return texto

class PDF(FPDF):
    def header(self):
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, 10, 8, 33)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'INFORME DE ANÁLISIS DE LABORATORIO', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 10, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, 'R')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Confidencial - Uso interno Petrobras LTS', 0, 0, 'C')

    def add_operator(self, operador):
        self.set_font('Arial', '', 10)
        self.cell(0, 10, f"Operador: {limpiar_texto(operador)}", 0, 1)
        self.ln(2)

    def add_explanation(self, texto):
        self.set_font('Arial', 'I', 9)
        self.multi_cell(0, 6, limpiar_texto(texto))
        self.ln(2)
        self.set_font('Arial', '', 9)
        self.multi_cell(0, 6, "Fórmulas utilizadas:\nW = HHV / sqrt(densidad relativa)\n(Ver GPA 2145 / ISO 6976)")
        self.ln(3)

    def add_results(self, resultados):
        self.set_font('Arial', '', 10)
        for k, v in resultados.items():
            self.cell(0, 8, f"{limpiar_texto(k)}: {limpiar_texto(v)}", 0, 1)
        self.ln(4)

    def add_observaciones(self, texto="Sin observaciones."):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 8, f"Observaciones: {limpiar_texto(texto)}")
        self.ln(3)
# Validación de parámetros
def validar_parametro(valor, minimo, maximo):
    if valor is None:
        return "—"
    return "✅ Cumple" if minimo <= valor <= maximo else "❌ No cumple"

def mostrar_resultados_validacion(parametros):
    filas = []
    for nombre, val, unidad, minimo, maximo in parametros:
        estado = validar_parametro(val, minimo, maximo)
        label = f"Parámetro: {nombre}\nValor: {val} {unidad}\nRango esperado: {minimo} - {maximo} {unidad}\nResultado: {estado}"
        filas.append((nombre, label))
    return dict(filas)

# Generar informe PDF y guardar historial
def generar_pdf(nombre_archivo, operador, explicacion, resultados, obs, carpeta):
    pdf = PDF()
    pdf.add_page()
    pdf.add_operator(operador)
    pdf.add_explanation(explicacion)
    pdf.add_results(resultados)
    pdf.add_observaciones(obs)
    ruta = os.path.join(f"informes/{carpeta}", nombre_archivo)
    pdf_bytes = pdf.output(dest="S").encode("latin-1", errors="replace")
    with open(ruta, "wb") as f:
        f.write(pdf_bytes)

    hist = pd.DataFrame([[datetime.now(), operador, carpeta, nombre_archivo]],
                        columns=["Fecha", "Operador", "Análisis", "Archivo"])
    if os.path.exists(HISTORIAL_PATH):
        hist_old = pd.read_csv(HISTORIAL_PATH)
        hist = pd.concat([hist_old, hist], ignore_index=True)
    hist.to_csv(HISTORIAL_PATH, index=False)

    st.download_button("⬇️ Descargar informe PDF", BytesIO(pdf_bytes), nombre_archivo, mime="application/pdf")

# Formulario común
def formulario_analisis(nombre_modulo, parametros, descripcion):
    st.subheader(f"🔬 Análisis de {nombre_modulo}")
    with st.expander("ℹ️ Más información sobre este análisis"):
        st.markdown(descripcion)
    valores = []
    for param in parametros:
        label = param["nombre"]
        unidad_sel = param["unidad"]
        valor = st.number_input(f"{label} ({unidad_sel})", step=0.1, key=f"valor_{label}_{nombre_modulo}")
        valores.append((label, valor, unidad_sel, param["min"], param["max"]))
    operador = st.text_input("👤 Operador", key=f"operador_{nombre_modulo}")
    obs = st.text_area("Observaciones", key=f"obs_{nombre_modulo}")
    if st.button(f"📊 Analizar {nombre_modulo}"):
        resultados = mostrar_resultados_validacion(valores)
        st.dataframe(pd.DataFrame(resultados.items(), columns=["Parámetro", "Resultado"]))
        generar_pdf(
            nombre_archivo=f"Informe_{nombre_modulo}_{operador.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            operador=operador,
            explicacion=f"Análisis de {nombre_modulo} realizado en planta LTS.",
            resultados=resultados,
            obs=obs,
            carpeta=nombre_modulo.lower().replace(' ', '_')
        )

# Configuración de parámetros
PARAMETROS_CONFIG = {
    "MEG": [
        {"nombre": "pH", "unidad": "", "min": 6, "max": 8},
        {"nombre": "Concentración", "unidad": "%wt", "min": 60, "max": 84},
        {"nombre": "Densidad", "unidad": "kg/m³", "min": 1050, "max": 1120},
        {"nombre": "Cloruros", "unidad": "mg/L", "min": 0, "max": 10},
        {"nombre": "MDEA", "unidad": "ppm", "min": 0, "max": 1000}
    ],
    "TEG": [
        {"nombre": "pH", "unidad": "", "min": 7, "max": 8.5},
        {"nombre": "Concentración", "unidad": "%", "min": 99, "max": 100},
        {"nombre": "Cloruros", "unidad": "ppm", "min": 0, "max": 50}
    ],
    "Agua Desmineralizada": [
        {"nombre": "pH", "unidad": "", "min": 6, "max": 8},
        {"nombre": "Cloruros", "unidad": "ppm", "min": 0, "max": 10},
        {"nombre": "Densidad", "unidad": "kg/m³", "min": 0, "max": 1500}
    ],
    "Gasolina Estabilizada": [
        {"nombre": "TVR", "unidad": "psia", "min": 0, "max": 12},
        {"nombre": "Salinidad", "unidad": "mg/m³", "min": 0, "max": 100},
        {"nombre": "Densidad", "unidad": "kg/m³", "min": 600, "max": 800}
    ]
}
# Crear carpetas necesarias
for carpeta in PARAMETROS_CONFIG:
    os.makedirs(f"informes/{carpeta.lower().replace(' ', '_')}", exist_ok=True)
os.makedirs("informes/gas_natural", exist_ok=True)

# Página principal
st.title("🧪 LTS Lab Analyzer - Sistema de Análisis de Laboratorio")

analisis = st.selectbox("Seleccioná el tipo de análisis:", 
    ["-- Seleccionar --"] + list(PARAMETROS_CONFIG.keys()) + ["Gas Natural", "📁 Ver Historial", "📖 Manual del Operador"])

DESCRIPCIONES = {
    "MEG": "El MEG evita formación de hidratos. Controlar pH, concentración, cloruros y MDEA previene fallos.",
    "TEG": "El TEG deshidrata gas natural. Niveles de hierro y cloruros indican corrosión.",
    "Agua Desmineralizada": "El agua pura evita incrustaciones y corrosión en calderas y sistemas.",
    "Gasolina Estabilizada": "TVR, sales y densidad definen si la gasolina es comercializable."
}

# Mostrar análisis correspondientes
if analisis in PARAMETROS_CONFIG:
    formulario_analisis(analisis, PARAMETROS_CONFIG[analisis], DESCRIPCIONES[analisis])

elif analisis == "Gas Natural":
    st.subheader("🛢️ Análisis de Gas Natural")

    with st.expander("ℹ️ ¿Qué se calcula?"):
        st.markdown("""
A partir del archivo de cromatografía, se calculan automáticamente:
- **HHV** (Poder calorífico superior)  
- **LHV** (Poder calorífico inferior estimado)  
- **Índice de Wobbe**  
- **Densidad relativa**

**Fórmulas:**
- \\( HHV = \\sum (y_i \\cdot HHV_i) \\)
- \\( W = \\frac{HHV}{\\sqrt{\\rho_{rel}}} \\)
- \\( LHV = HHV - 0.9 \\) _(estimado)_
        """)

    archivo = st.file_uploader("📎 Subí tu archivo CSV de cromatografía", type="csv")
    operador = st.text_input("👤 Operador", key="operador_gas")
    obs = st.text_area("Observaciones", key="obs_gas")

    if archivo is not None:
        try:
            df = pd.read_csv(archivo)
            st.success("✅ Archivo cargado correctamente")
            st.dataframe(df)

            # Supongamos que el CSV tiene las columnas: Componente, %mol
            comp_col = df.columns[0]
            frac_col = df.columns[1]
            composicion = df.set_index(comp_col)[frac_col] / 100  # convertir a fracción molar

            # Valores de HHV [MJ/mol] y densidad relativa aprox.
            HHV_MJ = {
                'CH4': 0.889,
                'C2H6': 1.564,
                'C3H8': 2.222,
                'n-C4H10': 2.873,
                'i-C4H10': 2.873,
                'CO2': 0,
                'N2': 0
            }
            dens_rel = {
                'CH4': 0.55,
                'C2H6': 1.04,
                'C3H8': 1.52,
                'n-C4H10': 2.0,
                'i-C4H10': 2.0,
                'CO2': 1.52,
                'N2': 0.97
            }

            # Calcular HHV y densidad relativa
            hhv = sum(composicion.get(c, 0) * HHV_MJ.get(c, 0) for c in composicion.index)
            rho_rel = sum(composicion.get(c, 0) * dens_rel.get(c, 1) for c in composicion.index)
            wobbe = hhv / np.sqrt(rho_rel)
            lhv = hhv - 0.09  # estimado para mostrar valor

            resultados = {
                "HHV (MJ/mol)": round(hhv, 4),
                "LHV estimado (MJ/mol)": round(lhv, 4),
                "Índice de Wobbe (MJ/mol)": round(wobbe, 4),
                "Densidad relativa": round(rho_rel, 4)
            }

            st.markdown("### 📊 Resultados calculados:")
            st.table(resultados)

            generar_pdf(
                nombre_archivo=f"Informe_Gas_{operador.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                operador=operador,
                explicacion="Análisis composicional del gas natural. Cálculos según GPA 2145 / ISO 6976.",
                resultados=resultados,
                obs=obs,
                carpeta="gas_natural"
            )

        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {e}")


elif analisis == "📁 Ver Historial":
    st.subheader("📂 Historial de Informes")
    if os.path.exists(HISTORIAL_PATH):
        df_hist = pd.read_csv(HISTORIAL_PATH)
        st.dataframe(df_hist)
    else:
        st.info("No se encontraron informes anteriores.")

elif analisis == "📖 Manual del Operador":
    st.subheader("📖 Manual del Operador")
    if os.path.exists(MANUAL_PATH):
        with open(MANUAL_PATH, "rb") as f:
            st.download_button("📘 Descargar Manual PDF", f, file_name="manual_operador_LTS.pdf")
    else:
        st.error("El manual no fue encontrado. Verificá que el archivo 'manual_operador_LTS.pdf' esté en el directorio.")







