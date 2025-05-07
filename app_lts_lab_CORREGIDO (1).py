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

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
import os

# Parámetros de poder calorífico y peso molecular
pcs_data = {
    "CH4": 39.82, "C2H6": 68.47, "C3H8": 93.1, "i-C4H10": 114.2,
    "n-C4H10": 114.0, "i-C5H12": 133.9, "n-C5H12": 134.2, "C6H14": 152.4,
    "N2": 0.0, "CO2": 0.0
}
pm_data = {
    "CH4": 16.04, "C2H6": 30.07, "C3H8": 44.1, "i-C4H10": 58.12,
    "n-C4H10": 58.12, "i-C5H12": 72.15, "n-C5H12": 72.15, "C6H14": 86.18,
    "N2": 28.01, "CO2": 44.01
}

alias = {
    "Methane": "CH4", "Ethane": "C2H6", "Propane": "C3H8", "i-Butane": "i-C4H10",
    "n-Butane": "n-C4H10", "i-Pentane": "i-C5H12", "n-Pentane": "n-C5H12", "Hexane": "C6H14",
    "Nitrogen": "N2", "Carbon Dioxide": "CO2"
}

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Informe de Análisis de Gas Natural", ln=True, align="C")
        self.set_font("Arial", "", 10)
        self.cell(0, 10, datetime.now().strftime("%Y-%m-%d %H:%M"), ln=True, align="R")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, "Confidencial - Uso interno Petrobras LTS", 0, 0, "C")

    def add_block(self, title, content):
        self.set_font("Arial", "B", 10)
        self.cell(0, 8, title, ln=True)
        self.set_font("Arial", "", 9)
        self.multi_cell(0, 6, str(content))
        self.ln(2)

def mostrar_analisis_gas():
    st.subheader("🛢️ Análisis de Gas Natural")
    st.markdown("Subí el archivo CSV generado por el cromatógrafo con la composición en % molar.")

    archivo = st.file_uploader("📎 Subir archivo CSV", type="csv")
    operador = st.text_input("👤 Operador (Gas Natural)")
    obs = st.text_area("📝 Observaciones")

    if archivo:
        try:
            df = pd.read_csv(archivo)
            st.dataframe(df)

            datos = df.set_index(df.columns[0]).iloc[:, 0].to_dict()
            comp = {}
            for k, v in datos.items():
    nombre = alias.get(k.strip(), k.strip())
    if nombre in pcs_data:
        comp[nombre] = float(v)


            fracciones = {k: v / 100 for k, v in comp.items()}

            pcs = sum(fracciones[k] * pcs_data[k] for k in fracciones)
            pci = pcs - 2.44 * fracciones.get("CH4", 0)
            pm_gas = sum(fracciones[k] * pm_data[k] for k in fracciones)
            dens_rel = pm_gas / 28.964 if pm_gas else 0
            wobbe = pcs / np.sqrt(dens_rel) if dens_rel > 0 else 0

            resultados = {
                "Poder Calorífico Superior (PCS) [MJ/m³]": round(pcs, 2),
                "Poder Calorífico Inferior (PCI) [MJ/m³]": round(pci, 2),
                "Peso Molecular del Gas [g/mol]": round(pm_gas, 2),
                "Densidad Relativa (a aire seco)": round(dens_rel, 4),
                "Índice de Wobbe [MJ/m³]": round(wobbe, 2)
            }

            st.markdown("### 📊 Resultados del Cálculo")
            st.write(resultados)

            st.markdown("""
                #### 📐 Fórmulas Utilizadas
                - $\text{PCS} = \sum x_i \cdot \text{PCS}_i$
                - $\text{PCI} = \text{PCS} - 2.44 \cdot x_{CH_4}$
                - $\text{PM}_{\text{gas}} = \sum x_i \cdot PM_i$
                - $\text{Densidad Relativa} = \frac{PM_{gas}}{28.964}$
                - $\text{Índice de Wobbe} = \frac{PCS}{\sqrt{\text{Densidad Relativa}}}$
            """, unsafe_allow_html=True)

            pdf = PDF()
            pdf.add_page()
            pdf.add_block("Operador", operador)
            pdf.add_block("Explicación", "Cálculo de propiedades energéticas y fisicoquímicas del gas natural según ISO 6976 y GPA 2145.")
            for k, v in resultados.items():
                pdf.add_block(k, v)

            pdf.add_block("Fórmulas Utilizadas", """
- PCS = Σ (xi * PCSi)  
- PCI = PCS - 2.44 * x_CH4  
- PM_gas = Σ (xi * PMi)  
- Densidad Relativa = PM_gas / 28.964  
- Índice de Wobbe = PCS / sqrt(Densidad Relativa)
            """)
            pdf.add_block("Observaciones", obs or "Sin observaciones.")

            buffer = BytesIO()
            pdf_data = pdf.output(dest="S").encode("latin1")
            buffer.write(pdf_data)
            buffer.seek(0)

            st.download_button("⬇️ Descargar informe PDF", buffer, file_name=f"Informe_Gas_{operador.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"❌ Error en el procesamiento del archivo: {e}")

mostrar_analisis_gas()





