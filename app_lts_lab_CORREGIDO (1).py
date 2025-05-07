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
            color: #ffffff;
        }

        input, textarea, .stTextInput, .stTextArea, .stNumberInput, .stSelectbox, .stDownloadButton, .stFileUploader {
            background-color: #0d1117 !important;
            color: white !important;
            border: 1px solid #5a5f66 !important;
            box-shadow: 1px 1px 3px rgba(0,0,0,0.3);
            border-radius: 6px;
        }

        button {
            background-color: #0078D7 !important;
            color: white !important;
            font-weight: 500;
            border-radius: 6px;
            padding: 0.4rem 1rem;
            box-shadow: 1px 1px 5px rgba(0,0,0,0.2);
        }

        .logo-container {
            text-align: center;
            margin-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# Logo
LOGO_PATH = "logopetrogas.png"
def cargar_logo_base64(path):
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

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
st.markdown("""
Bienvenido al sistema **LTS Lab Analyzer**, una herramienta profesional para el registro, validación y generación de informes PDF de análisis de laboratorio en plantas de tratamiento de gas natural.

La aplicación cuenta con los siguientes módulos:
- **Gas Natural:** cálculo de poder calorífico, poder calorífico inferior, peso molecular, densidad relativa e índice de Wobbe, a partir de un archivo CSV generado por cromatografía.
- **MEG (Monoetilenglicol):** utilizado como inhibidor de hidratos, se analizan parámetros críticos que indican eficiencia y pureza.
- **TEG (Trietilenglicol):** se controla su calidad para garantizar la correcta deshidratación del gas.
- **Agua Desmineralizada:** se analiza su pureza para asegurar que no provoque incrustaciones o corrosión en equipos sensibles.
- **Gasolina Estabilizada:** se revisan parámetros que impactan en la calidad del combustible como presión de vapor, sales y densidad.

Cada análisis cuenta con:
✅ Validación automática de rangos aceptables  
📤 Descarga de informe profesional en PDF  
🧠 Explicaciones pedagógicas de cada parámetro  
📐 Fórmulas visibles utilizadas en los cálculos

---
### 📘 ¿Por qué es importante?
Un laboratorio confiable previene fallas operativas, reduce costos de mantenimiento y garantiza el cumplimiento de normas técnicas. Esta app digitaliza, valida y profesionaliza cada paso.
""")

st.sidebar.header("⚙️ Opciones")
activar_validaciones = st.sidebar.checkbox("Activar validación de rangos", value=True)

PARAMETROS_CONFIG = {
    "MEG": [
        {"nombre": "pH", "unidad": "", "min": 6, "max": 8, "explicacion": "El pH fuera de rango puede indicar presencia de contaminantes como ácidos orgánicos o bases aminas que afectan la eficiencia del MEG."},
        {"nombre": "Concentración", "unidad": "%wt", "min": 60, "max": 84, "explicacion": "Una concentración insuficiente reduce la capacidad del MEG para inhibir la formación de hidratos."},
        {"nombre": "Densidad", "unidad": "kg/m³", "min": 1050, "max": 1120, "explicacion": "Valores anormales pueden revelar contaminación con agua o hidrocarburos pesados."},
        {"nombre": "Cloruros", "unidad": "mg/L", "min": 0, "max": 10, "explicacion": "Los cloruros son corrosivos. Un exceso puede dañar equipos metálicos."},
        {"nombre": "MDEA", "unidad": "ppm", "min": 0, "max": 1000, "explicacion": "Presencia elevada de aminas puede afectar propiedades del MEG y generar espuma o arrastre."}
    ],
    "TEG": [
        {"nombre": "pH", "unidad": "", "min": 7, "max": 8.5, "explicacion": "El pH permite detectar descomposición térmica o presencia de ácidos en el sistema de deshidratación."},
        {"nombre": "Concentración", "unidad": "%wt", "min": 99, "max": 100, "explicacion": "El TEG debe ser lo más puro posible para maximizar su eficiencia de remoción de agua."},
        {"nombre": "Cloruros", "unidad": "mg/L", "min": 0, "max": 50, "explicacion": "Detectar sales en TEG permite evitar corrosión interna en los regeneradores."},
        {"nombre": "Hierro", "unidad": "ppm", "min": 0, "max": 10, "explicacion": "Concentraciones elevadas pueden ser indicativas de corrosión interna del sistema."}
    ],
    "Agua Desmineralizada": [
        {"nombre": "pH", "unidad": "", "min": 6, "max": 8, "explicacion": "El pH refleja la estabilidad química del agua. Valores extremos pueden generar problemas en calderas o reactores."},
        {"nombre": "Cloruros", "unidad": "mg/L", "min": 0, "max": 10, "explicacion": "Altas concentraciones son corrosivas para intercambiadores y sistemas cerrados."},
        {"nombre": "Densidad", "unidad": "kg/m³", "min": 0, "max": 1500, "explicacion": "Desviaciones pueden señalar contaminación o mezclas no deseadas."}
    ],
    "Gasolina Estabilizada": [
        {"nombre": "TVR", "unidad": "psia", "min": 0, "max": 12, "explicacion": "La presión de vapor (TVR) indica la volatilidad del producto. Valores elevados pueden ser peligrosos en transporte y almacenamiento."},
        {"nombre": "Salinidad", "unidad": "mg/m³", "min": 0, "max": 100, "explicacion": "Las sales pueden corroer válvulas, bombas y otros equipos sensibles."},
        {"nombre": "Densidad", "unidad": "kg/m³", "min": 600, "max": 800, "explicacion": "La densidad es clave para cálculos de volumen, calidad y compatibilidad del combustible."}
    ]
}

# Menú de selección
analisis = st.selectbox("Seleccioná el tipo de análisis:", ["-- Seleccionar --"] + list(PARAMETROS_CONFIG.keys()) + ["Gas Natural"])

if analisis != "-- Seleccionar --":
    st.session_state["tipo_analisis"] = analisis

# Continúa con la lógica del análisis seleccionado en los siguientes módulos...



