import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
import unicodedata
import os
import base64

# Configuración inicial
st.set_page_config(page_title="LTS Lab Analyzer", layout="wide")

st.markdown("""
    <style>
        .stApp {
            background-color: #0d1117;
            color: #e0e0e0;
            font-family: 'Segoe UI', sans-serif;
        }

        input, textarea, .stTextInput, .stTextArea, .stNumberInput, .stSelectbox, .stDownloadButton, .stFileUploader {
            background-color: #1e2228 !important;
            color: #e0e0e0 !important;
            border: 1px solid #5a5f66 !important;
            border-radius: 6px;
            padding: 0.3rem;
            box-shadow: 1px 1px 3px rgba(0,0,0,0.3);
        }

        button {
            background-color: #0078D7 !important;
            color: white !important;
            font-weight: 500;
            border-radius: 6px;
            padding: 0.4rem 1rem;
            box-shadow: 1px 1px 5px rgba(0,0,0,0.2);
        }

        .stSelectbox > div {
            color: black !important;
        }

        .logo-container {
            text-align: center;
            margin-bottom: 1rem;
        }

        .stTitle {
            font-size: 2.2em;
            font-weight: bold;
            color: #58a6ff;
        }
    </style>
""", unsafe_allow_html=True)


# Logo
def cargar_logo_base64(path):
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

LOGO_PATH = "logopetrogas.png"
try:
    base64_logo = cargar_logo_base64(LOGO_PATH)
    st.markdown(
        f"""
        <div style="text-align:center;">
            <img src="data:image/png;base64,{base64_logo}" width="180">
        </div>
        """,
        unsafe_allow_html=True
    )
except:
    st.warning("⚠️ No se pudo cargar el logo.")

st.title("🧪 Laboratorio de Planta LTS")
st.markdown("Sistema profesional de análisis y validación de laboratorio con informes PDF.")

st.sidebar.header("⚙️ Opciones")
activar_validaciones = st.sidebar.checkbox("Activar validación de rangos", value=True)

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
        {"nombre": "Concentración", "unidad": "%wt", "min": 99, "max": 100},
        {"nombre": "Cloruros", "unidad": "mg/L", "min": 0, "max": 50},
        {"nombre": "Hierro", "unidad": "ppm", "min": 0, "max": 10}
    ],
    "Agua Desmineralizada": [
        {"nombre": "pH", "unidad": "", "min": 6, "max": 8},
        {"nombre": "Cloruros", "unidad": "mg/L", "min": 0, "max": 10},
        {"nombre": "Densidad", "unidad": "kg/m³", "min": 0, "max": 1500}
    ],
    "Gasolina Estabilizada": [
        {"nombre": "TVR", "unidad": "psia", "min": 0, "max": 12},
        {"nombre": "Salinidad", "unidad": "mg/m³", "min": 0, "max": 100},
        {"nombre": "Densidad", "unidad": "kg/m³", "min": 600, "max": 800}
    ]
}

for carpeta in PARAMETROS_CONFIG:
    os.makedirs(f"informes/{carpeta.lower().replace(' ', '_')}", exist_ok=True)
os.makedirs("informes/gas_natural", exist_ok=True)

def limpiar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    texto = texto.replace("–", "-").replace("—", "-")
    return unicodedata.normalize("NFKD", texto).encode("latin1", "ignore").decode("latin1")

class PDF(FPDF):
    def header(self):
        try:
            self.image(LOGO_PATH, 10, 8, 33)
        except:
            pass
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'INFORME DE ANÁLISIS DE LABORATORIO', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 10, datetime.now().strftime('%Y-%m-%d %H:%M'), 0, 1, 'R')
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Confidencial - Uso interno Petrobras LTS', 0, 0, 'C')

    def add_block(self, title, content):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, title, 0, 1)
        self.set_font('Arial', '', 9)
        self.multi_cell(0, 6, limpiar_texto(content))
        self.ln(2)

def validar_parametro(valor, minimo, maximo):
    if valor is None:
        return "—"
    return "✅ Cumple" if minimo <= valor <= maximo else "❌ No cumple"

def mostrar_resultados_validacion(parametros):
    filas = []
    for nombre, val, unidad, minimo, maximo in parametros:
        estado = validar_parametro(val, minimo, maximo) if activar_validaciones else ""
        filas.append((nombre, f"{val} {unidad} | {estado}"))
    return dict(filas)

def generar_pdf(nombre_archivo, operador, explicacion, resultados, obs, carpeta):
    pdf = PDF()
    pdf.add_page()
    pdf.add_block("Operador", operador)
    pdf.add_block("Explicación", explicacion)
    for k, v in resultados.items():
        pdf.add_block(k, str(v))
    pdf.add_block("Observaciones", obs or "Sin observaciones.")
    buffer = BytesIO()
    pdf_data = pdf.output(dest="S").encode("latin1")
    buffer.write(pdf_data)
    buffer.seek(0)
    st.download_button("⬇️ Descargar informe PDF", buffer, nombre_archivo, mime="application/pdf")

def formulario_analisis(nombre_modulo, parametros):
    st.subheader(f"🔬 Análisis de {nombre_modulo}")
    valores = []
    for param in parametros:
        label = param["nombre"]
        unidad_sel = param["unidad"]
        valor = st.number_input(f"{label} ({unidad_sel})", step=0.1, key=f"{label}_{nombre_modulo}")
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

def mostrar_analisis_gas():
    st.subheader("🛢️ Análisis de Gas Natural")
    st.markdown("Subí el archivo CSV generado por el cromatógrafo con la composición en % molar.")
    archivo = st.file_uploader("📎 Subir archivo CSV", type="csv")
    operador = st.text_input("👤 Operador (gas)")
    obs = st.text_area("Observaciones (gas)")

    if archivo:
        try:
            df = pd.read_csv(archivo)
            st.dataframe(df)
            # Aquí deben ir tus cálculos energéticos del gas natural
            st.success("✅ Archivo cargado y listo para procesar.")
        except Exception as e:
            st.error(f"❌ Error en el cálculo: {e}")

def main():
    opciones = ["-- Seleccionar --"] + list(PARAMETROS_CONFIG.keys()) + ["Gas Natural"]
    analisis = st.selectbox("Seleccioná el tipo de análisis:", opciones)

    if analisis == "-- Seleccionar --":
        st.info("📌 Seleccioná un análisis en el menú desplegable.")
    elif analisis in PARAMETROS_CONFIG:
        formulario_analisis(analisis, PARAMETROS_CONFIG[analisis])
    elif analisis == "Gas Natural":
        mostrar_analisis_gas()

if __name__ == "__main__":
    main()


