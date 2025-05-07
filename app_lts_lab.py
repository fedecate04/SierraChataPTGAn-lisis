
# LTS Lab Analyzer - App mejorada y corregida

import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
from datetime import datetime
import os
from io import BytesIO
from PIL import Image
import re

# Configuración visual
st.set_page_config(page_title="LTS Lab Analyzer", layout="wide")
LOGO_PATH = "logopetrogas.png"
MANUAL_PATH = "manual_operador_LTS.pdf"
HISTORIAL_PATH = "historial.csv"

# Estilo
st.markdown("""
    <style>
        .stApp { background-color: #2d2d2d; color: #f0f0f0; }
        .stButton>button { background-color: #0d6efd; color: white; border: none; }
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
    texto = texto.replace("\u221a", "sqrt")
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

# Resultado Gas Natural con fórmula y explicaciones
st.title("🧪 LTS Lab Analyzer - Sistema de Análisis de Laboratorio")

try:
    st.markdown("### 📘 Parámetros calculados y fórmulas")
    st.latex("HHV = \sum y_i \cdot HHV_i")
    st.latex("W = \frac{HHV}{\sqrt{\rho_{rel}}}")
    st.latex("LHV \approx HHV - 0.09")

    resultados = {
        "HHV (MJ/mol)": 0.9,
        "LHV estimado (MJ/mol)": 0.81,
        "Índice de Wobbe (MJ/mol)": 1.2,
        "Densidad relativa": 0.65
    }

    explicaciones = {
        "HHV (MJ/mol)": "Energía total liberada al quemar 1 mol de gas, incluyendo condensación de H₂O.",
        "LHV estimado (MJ/mol)": "HHV menos el calor latente de vaporización del agua (estimado).",
        "Índice de Wobbe (MJ/mol)": "Relación entre HHV y raíz de densidad relativa, clave para intercambiabilidad.",
        "Densidad relativa": "Relación entre densidad del gas y la del aire (valor adimensional)."
    }

    st.markdown("### 📊 Resultados:")
    for k, v in resultados.items():
        st.markdown(f"**{k}:** {v} — _{explicaciones[k]}_")

    st.markdown("### 📘 Tabla explicativa de parámetros")
    st.dataframe(pd.DataFrame({
        "Parámetro": list(explicaciones.keys()),
        "Descripción": list(explicaciones.values()),
        "Fórmula": [
            "HHV = Σ(yᵒ · HHVᵒ)",
            "LHV ≈ HHV - 0.09",
            "W = HHV / √ρrel",
            "ρrel = ρgas / ρaire"
        ]
    }))

except Exception as e:
    st.error(f"❌ Error al procesar los parámetros del gas: {e}")
