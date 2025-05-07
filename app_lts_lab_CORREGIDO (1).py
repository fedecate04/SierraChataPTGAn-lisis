import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
from datetime import datetime
import os
from io import BytesIO
import unicodedata

# Configuración inicial
st.set_page_config(page_title="Gas Natural Analyzer", layout="wide")
LOGO_PATH = "logopetrogas.png"

# Mostrar logo
try:
    with open(LOGO_PATH, "rb") as logo_file:
        st.image(logo_file.read(), width=180)
except Exception:
    st.warning("⚠️ No se pudo cargar el logo.")

st.title("🛢️ Análisis de Gas Natural")
st.markdown("Subí el archivo CSV generado por el cromatógrafo con la composición del gas natural.")

# 📘 Explicaciones técnicas
with st.expander("📘 ¿Qué se calcula y por qué es importante?"):
    st.markdown("""
**Poder Calorífico Superior (PCS):** Energía total liberada por la combustión completa del gas.  
**Poder Calorífico Inferior (PCI):** Energía útil, sin contar el calor del vapor de agua formado.  
**Índice de Wobbe (W):** Relación entre PCS y la raíz cuadrada de la densidad relativa. Sirve para comparar gases distintos.  
**Densidad Relativa:** Relación entre la densidad del gas y la del aire seco.  
**Peso Molecular del Gas:** Masa promedio de una molécula de la mezcla.

**Fórmulas utilizadas:**

- `PCS = Σ(xᵢ × PCSᵢ)`
- `PCI = PCS - Hᵥᵃᵖ × x_H₂O` (simplificado para CH₄)
- `PM_gas = Σ(xᵢ × PMᵢ)`
- `ρ_rel = PM_gas / 28.964`
- `Wobbe = PCS / √ρ_rel`
    """)

st.latex(r"PCS = \sum_{i} x_i \cdot PCS_i")
st.latex(r"PCI = PCS - H_{vap} \cdot x_{H_2O}")
st.latex(r"PM_{gas} = \sum_{i} x_i \cdot PM_i")
st.latex(r"\rho_r = \frac{PM_{gas}}{28.964}")
st.latex(r"W = \frac{PCS}{\sqrt{\rho_r}}")

# Poder calorífico por componente [MJ/m³]
pcs_data = {
    'CH4': 39.82, 'C2H6': 68.39, 'C3H8': 93.57,
    'i-C4H10': 119.96, 'n-C4H10': 119.96,
    'CO2': 0.0, 'N2': 0.0
}

# Pesos moleculares [g/mol]
pm_data = {
    'CH4': 16.04, 'C2H6': 30.07, 'C3H8': 44.10,
    'i-C4H10': 58.12, 'n-C4H10': 58.12,
    'CO2': 44.01, 'N2': 28.01
}

# Función limpieza para PDF
def limpiar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    texto = texto.replace("–", "-").replace("—", "-").replace("“", '"').replace("”", '"')
    return unicodedata.normalize("NFKD", texto).encode("latin1", "ignore").decode("latin1")

# Clase PDF personalizada
class PDF(FPDF):
    def header(self):
        try:
            self.image(LOGO_PATH, 10, 8, 33)
        except:
            pass
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'INFORME DE ANÁLISIS DE GAS NATURAL', 0, 1, 'C')
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

# Cálculo de propiedades
def calcular_propiedades(df):
    composicion = df.set_index(df.columns[0]).iloc[:, 0].to_dict()
    composicion = {k: float(v) for k, v in composicion.items() if k in pcs_data}
    fracciones = {k: v/100 for k, v in composicion.items()}

    pcs = sum(fracciones[k] * pcs_data[k] for k in fracciones)
    pci = pcs - 2.44 * fracciones.get('CH4', 0)  # simplificación para CH₄
    pm_gas = sum(fracciones[k] * pm_data[k] for k in fracciones)
    dens_rel = pm_gas / 28.964
    wobbe = pcs / np.sqrt(dens_rel)

    return {
        "PCS [MJ/m³]": round(pcs, 2),
        "PCI [MJ/m³]": round(pci, 2),
        "PM Gas [g/mol]": round(pm_gas, 2),
        "Densidad Relativa": round(dens_rel, 4),
        "Índice de Wobbe": round(wobbe, 2)
    }

# Generación del PDF
def generar_pdf(resultados, operador, obs):
    pdf = PDF()
    pdf.add_page()
    pdf.add_block("Operador", operador)
    pdf.add_block("Explicación Técnica", (
        "Parámetros calculados a partir de la composición del gas natural:\n\n"
        "PCS = Σ(xᵢ · PCSᵢ)\n"
        "PCI = PCS - H_vap × x_CH4\n"
        "PM_gas = Σ(xᵢ × PMᵢ)\n"
        "ρ_rel = PM_gas / 28.964\n"
        "Wobbe = PCS / √(ρ_rel)\n\n"
        "Normas: ISO 6976, GPA 2145"
    ))
    for k, v in resultados.items():
        pdf.add_block(k, str(v))
    pdf.add_block("Observaciones", obs or "Sin observaciones.")
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    st.download_button("⬇️ Descargar informe PDF", buffer, "Informe_Gas.pdf", mime="application/pdf")

# Interfaz
archivo = st.file_uploader("📎 Subí archivo CSV", type="csv")
operador = st.text_input("👤 Operador")
obs = st.text_area("📝 Observaciones")

if archivo:
    try:
        df = pd.read_csv(archivo)
        st.dataframe(df)
        resultados = calcular_propiedades(df)
        st.markdown("### 📊 Resultados del cálculo")
        st.write(resultados)
        generar_pdf(resultados, operador, obs)
    except Exception as e:
        st.error(f"❌ Error en el cálculo: {e}")


