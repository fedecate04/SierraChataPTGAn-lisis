import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
from datetime import datetime
import os
from io import BytesIO
from PIL import Image
import re

# Configuración de la página
st.set_page_config(page_title="LTS Lab Analyzer", layout="wide")

# Mostrar logo
LOGO_PATH = "logopetrogas.png"
try:
    logo = Image.open(LOGO_PATH)
    st.image(logo, width=180)
except Exception as e:
    st.warning(f"⚠️ No se pudo cargar el logo: {e}")

st.title("🧪 Laboratorio de Planta LTS")

st.markdown("""
Sistema profesional de análisis y validación de laboratorio con informes PDF para plantas de tratamiento de gas natural.

### 📌 Importancia del Análisis
Garantizar que los fluidos cumplan con las especificaciones evita corrosión, fallas operativas y asegura la eficiencia de la planta LTS.
""")

# Sidebar
st.sidebar.header("⚙️ Opciones")
activar_validaciones = st.sidebar.checkbox("Activar validación de rangos", value=True)

# Parámetros configurables
PARAMETROS_CONFIG = {
    "MEG": [
        {"nombre": "pH", "unidad": "", "min": 6, "max": 8},
        {"nombre": "Concentración", "unidad": "%wt", "min": 60, "max": 84, "key_unidad": ["%", "%wt"]},
        {"nombre": "Densidad", "unidad": "kg/m³", "min": 1050, "max": 1120},
        {"nombre": "Cloruros", "unidad": "mg/L", "min": 0, "max": 10, "key_unidad": ["ppm", "mg/L"]},
        {"nombre": "MDEA", "unidad": "ppm", "min": 0, "max": 1000}
    ],
    "TEG": [
        {"nombre": "pH", "unidad": "", "min": 7, "max": 8.5},
        {"nombre": "Concentración", "unidad": "%wt", "min": 99, "max": 100, "key_unidad": ["%", "%wt"]},
        {"nombre": "Cloruros", "unidad": "mg/L", "min": 0, "max": 50, "key_unidad": ["ppm", "mg/L"]},
        {"nombre": "Hierro", "unidad": "ppm", "min": 0, "max": 10}
    ],
    "Agua Desmineralizada": [
        {"nombre": "pH", "unidad": "", "min": 6, "max": 8},
        {"nombre": "Cloruros", "unidad": "mg/L", "min": 0, "max": 10, "key_unidad": ["ppm", "mg/L"]},
        {"nombre": "Densidad", "unidad": "kg/m³", "min": 0, "max": 1500}
    ],
    "Gasolina Estabilizada": [
        {"nombre": "TVR", "unidad": "psia", "min": 0, "max": 12},
        {"nombre": "Salinidad", "unidad": "mg/m³", "min": 0, "max": 100},
        {"nombre": "Densidad", "unidad": "kg/m³", "min": 600, "max": 800}
    ]
}

# Crear carpetas de informes
for carpeta in PARAMETROS_CONFIG:
    os.makedirs(f"informes/{carpeta.lower().replace(' ', '_')}", exist_ok=True)
os.makedirs("informes/gas_natural", exist_ok=True)

# Limpieza de texto
def limpiar_texto(texto):
    texto = str(texto)
    texto = texto.replace("–", "-").replace("—", "-").replace("“", '"').replace("”", '"')
    texto = texto.replace("√", "sqrt")  # conversión segura
    texto = re.sub(r'[^\x00-\xFF]', '', texto)  # solo caracteres latin-1
    return texto

# Clase para generar PDF
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

# Validación y lógica
def validar_parametro(valor, minimo, maximo):
    if valor is None:
        return "—"
    return "✅ Cumple" if minimo <= valor <= maximo else "❌ No cumple"

def mostrar_resultados_validacion(parametros):
    filas = []
    for nombre, val, unidad, minimo, maximo in parametros:
        if activar_validaciones:
            estado = validar_parametro(val, minimo, maximo)
            label = f"Parámetro: {nombre}\nValor: {val} {unidad}\nRango esperado: {minimo} - {maximo} {unidad}\nResultado: {estado}"
        else:
            label = f"{val} {unidad}"
        filas.append((nombre, label))
    return dict(filas)

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
    st.download_button("⬇️ Descargar informe PDF", BytesIO(pdf_bytes), nombre_archivo, mime="application/pdf")

def formulario_analisis(nombre_modulo, parametros):
    st.subheader(f"🔬 Análisis de {nombre_modulo}")
    try:
        logo = Image.open(LOGO_PATH)
        st.image(logo, width=180)
    except:
        pass
    valores = []
    for param in parametros:
        label = param["nombre"]
        unidad_sel = param["unidad"]
        if "key_unidad" in param:
            unidad_sel = st.selectbox(f"Unidad de {label}", param["key_unidad"], key=f"unidad_{label}_{nombre_modulo}")
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

# Menú principal
st.session_state.analisis_actual = st.selectbox("Seleccioná el tipo de análisis:", ["-- Seleccionar --"] + list(PARAMETROS_CONFIG.keys()) + ["Gas Natural"], key="tipo_analisis")

if st.session_state.analisis_actual in PARAMETROS_CONFIG:
    formulario_analisis(st.session_state.analisis_actual, PARAMETROS_CONFIG[st.session_state.analisis_actual])

elif st.session_state.analisis_actual == "Gas Natural":
    st.subheader("🛢️ Análisis de Gas Natural")
    try:
        logo = Image.open(LOGO_PATH)
        st.image(logo, width=180)
    except:
        pass

    st.markdown("Cargá el archivo CSV generado por el cromatógrafo con la composición del gas natural.")
    archivo = st.file_uploader("📎 Subir archivo CSV", type="csv")
    operador = st.text_input("👤 Operador", key="operador_gas")
    obs = st.text_area("Observaciones", key="obs_gas")
    if archivo is not None:
        try:
            df = pd.read_csv(archivo)
            st.dataframe(df)
            if df.shape[1] >= 2:
                resultados = df.set_index(df.columns[0]).iloc[:, 0].apply(lambda x: str(x)).to_dict()
            else:
                resultados = {df.columns[0]: [str(x) for x in df.iloc[:, 0].values]}
            resultados["Explicación"] = "Poder Calorífico calculado como suma ponderada de componentes (ver GPA 2145). Índice de Wobbe: W = HHV / sqrt(Densidad relativa)."
            generar_pdf(
                nombre_archivo=f"Informe_Gas_{operador.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                operador=operador,
                explicacion="Análisis composicional del gas natural. Fórmulas según GPA 2145 e ISO 6976.",
                resultados=resultados,
                obs=obs,
                carpeta="gas_natural"
            )
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")











