import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
from datetime import datetime
import os
import re

# Configuración de página
st.set_page_config(page_title="LTS Lab Analyzer", layout="wide")
LOGO_PATH = "logopetrogas.png"

# Estilo visual oscuro
st.markdown("""
    <style>
        .stApp { background-color: #2d2d2d; color: #f0f0f0; }
        .stButton>button { background-color: #0d6efd; color: white; }
        input, textarea, .stTextInput, .stTextArea, .stNumberInput, .stSelectbox div {
            background-color: #3a3a3a !important; color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

# Función para limpiar caracteres incompatibles
def limpiar_texto(texto):
    texto = str(texto)
    texto = texto.replace("–", "-").replace("—", "-").replace("“", '"').replace("”", '"')
    texto = texto.replace("\u221a", "sqrt")
    texto = re.sub(r'[^\x00-\x7F]+', '', texto)  # eliminar caracteres no ascii
    return texto

# Clase PDF
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

    def agregar_datos(self, operador, resultados, observaciones, explicacion):
        self.set_font('Arial', '', 10)
        self.cell(0, 10, f"Operador: {limpiar_texto(operador)}", 0, 1)
        self.ln(3)

        self.set_font('Arial', 'B', 11)
        self.cell(0, 10, 'Resultados:', 0, 1)
        self.set_font('Arial', '', 10)
        for k, v in resultados.items():
            self.cell(0, 8, f"{k}: {v}", 0, 1)
        self.ln(3)

        self.set_font('Arial', 'B', 11)
        self.cell(0, 10, 'Explicación técnica:', 0, 1)
        self.set_font('Arial', 'I', 9)
        self.multi_cell(0, 6, limpiar_texto(explicacion))
        self.ln(3)

        self.set_font('Arial', 'B', 11)
        self.cell(0, 10, 'Observaciones:', 0, 1)
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 6, limpiar_texto(observaciones))
        self.ln(5)

# Título
st.title("🧪 LTS Lab Analyzer - Análisis de Gas Natural")

# Fórmulas y explicaciones
st.markdown("### 📘 Fórmulas utilizadas")
st.latex("HHV = \sum y_i \cdot HHV_i")
st.latex("W = \dfrac{HHV}{\sqrt{\\rho_{rel}}}")
st.latex("LHV \\approx HHV - 0.09")

# Resultados de ejemplo
resultados = {
    "HHV (MJ/mol)": 0.9,
    "LHV estimado (MJ/mol)": 0.81,
    "Índice de Wobbe (MJ/mol)": 1.2,
    "Densidad relativa": 0.65
}

explicaciones = {
    "HHV (MJ/mol)": "Energía total liberada al quemar 1 mol de gas, incluyendo condensación de H₂O.",
    "LHV estimado (MJ/mol)": "HHV menos el calor latente de vaporización del agua.",
    "Índice de Wobbe (MJ/mol)": "Relación entre HHV y raíz de densidad relativa, clave para intercambiabilidad.",
    "Densidad relativa": "Relación entre densidad del gas y la del aire."
}

st.markdown("### 📊 Resultados obtenidos")
for k, v in resultados.items():
    st.markdown(f"**{k}:** {v} — _{explicaciones[k]}_")

# Tabla explicativa
st.markdown("### 📘 Tabla de parámetros")
st.dataframe(pd.DataFrame({
    "Parámetro": list(explicaciones.keys()),
    "Descripción": list(explicaciones.values()),
    "Fórmula": [
        "HHV = Σ(yᵢ · HHVᵢ)",
        "LHV ≈ HHV - 0.09",
        "W = HHV / √ρrel",
        "ρrel = ρgas / ρaire"
    ]
}))

# PDF
st.markdown("---")
st.markdown("### 📝 Generar informe PDF")

operador = st.text_input("Nombre del operador", value="Federico Catereniuc")
observaciones = st.text_area("Observaciones adicionales", value="Sin observaciones.")
generar = st.button("📄 Generar PDF de informe")

if generar:
    pdf = PDF()
    pdf.add_page()
    explicacion_completa = "\n".join([f"{k}: {v}" for k, v in explicaciones.items()])
    pdf.agregar_datos(operador, resultados, observaciones, explicacion_completa)

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    st.download_button(
        label="📥 Descargar informe PDF",
        data=buffer,
        file_name=f"informe_gas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf"
    )


