import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
import unicodedata
import os

# Configuración
st.set_page_config(page_title="LTS Lab Analyzer", layout="wide")
LOGO_PATH = "logopetrogas.png"

# Mostrar logo
try:
    with open(LOGO_PATH, "rb") as logo_file:
        st.image(logo_file.read(), width=180)
except:
    st.warning("⚠️ No se pudo cargar el logo.")

st.title("🧪 Laboratorio de Planta LTS")
st.markdown("Sistema profesional de análisis y validación de laboratorio con informes PDF.")

# Sidebar
st.sidebar.header("⚙️ Opciones")
activar_validaciones = st.sidebar.checkbox("Activar validación de rangos", value=True)

# Parámetros de los módulos físico-químicos
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

# Crear carpetas de informes
for carpeta in PARAMETROS_CONFIG:
    os.makedirs(f"informes/{carpeta.lower().replace(' ', '_')}", exist_ok=True)
os.makedirs("informes/gas_natural", exist_ok=True)

# Función de limpieza
def limpiar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    texto = texto.replace("–", "-").replace("—", "-")
    return unicodedata.normalize("NFKD", texto).encode("latin1", "ignore").decode("latin1")

# Clase PDF
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
# Función de validación
def validar_parametro(valor, minimo, maximo):
    if valor is None:
        return "—"
    return "✅ Cumple" if minim <= valor <= maximo else "❌ No cumple"

# Generar resultados validados
def mostrar_resultados_validacion(parametros):
    filas = []
    for nombre, val, unidad, minimo, maximo in parametros:
        estado = validar_parametro(val, minimo, maximo) if activar_validaciones else ""
        filas.append((nombre, f"{val} {unidad} | {estado}"))
    return dict(filas)

# Generar informe PDF
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

# Formulario para módulos físico-químicos
def formulario_analisis(nombre_modulo, parametros):
    st.subheader(f"🔬 Análisis de {nombre_modulo}")
    valores  []
    for param in parametros:
        label = param["nombre"]
        unidad_sel = param["unidad"]
        valor = st.number_input(f"{label} ({unidad_sel})", step=0.1, key=f"{label}_{nombre_modulo}")
        valores.append((label, valor, unidad_sel, param["min"], param["max"]))
    operador = st.text_input("👤 Operador", key=f"operador_{nombre_modulo}")
    obs = st.text_area("Observaciones", key=f"obs_{nombre_modulo}")
    if st.button("📊 Analizar {nombre_modulo}"):
        resultados = mostrar_resultados_validacion(valores)
        st.dataframe(pd.DataFrame(resultados.items(), columns=["Parmetro", "Resultado"]))
        generar_pdf(
            nombre_archivo=f"Informe_{nombre_modulo}_{operador.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            operador=operador,
            explicacion=f"Análisis de {nombre_modulo} realizado en planta LTS.",
            resultados=resultados,
            obs=obs,
            carpeta=nombre_modulo.lower().replace(' ', '_')
        )

# Módulo de GAS NATURAL
def mostrar_analisis_gas():
    st.subheader("🛢️ Análisis de Gas Natural")
    st.markdown("Subí el archivo CSV generado por el cromatógrafo co la composición en % molar.")
    
    # Fórmulas visibles
    with st.expander("📘 ¿Qué se calcula?"):
        st.latex(r"PCS = \sum_{i} x_i \cdot PCS_i")
        st.latex(r"PCI = PCS - H_{vap} \cdot x_{CH_4}")
        st.latex("PM_{gas} = \sum_{i} x_i \cdot PM_i")
        st.latex(r"\rho_r = \frac{PM_{gas}}{28.964}")
        st.latex(r"W = \frac{PCS}{\sqrt{\rho_r}}")

    # Datos
    pcs_data = {'CH4': 39.82, 'C2H6': 68.39, 'C3H8': 93.57, 'i-C4H10': 119.96, 'n-C4H10': 119.96, 'CO2': 0.0, 'N2': 0.0}
    pm_data = {'CH4': 16.04, 'C2H6': 30.07, 'C3H8': 44.10, 'i-C4H10': 58.12, 'n-C4H10': 58.12, 'CO2': 44.01, 'N2': 28.01}
    alias = {
        "Metano": "CH4", "CH₄": "CH4", "C1": "CH4", "CH4": "CH4",
        "Etano": "C2H6", "C2": "C2H6", "C2H6": "C2H6",
        "Propano": "C3H8", "C3": "C3H8", "C3H8": "C3H8",
        "i-Butano": "i-C4H10", "iC4": "i-C4H10",
        "n-Butano": "n-C4H10", "nC4": "n-C4H10",
        "Dióxido de carbono": "CO2", "CO2": "CO2",
        "Nitrógeno": "N2", "N2": "N2"
    }

    archivo = st.file_uploader("📎 Subir archivo CSV", type="csv")
   operador = st.text_input("👤 Operador (gas)")
    obs = st.text_area("Observaciones (gas)")

    if archivo:
        try:
            df = pd.read_csv(archivo)
            st.dataframe(df)            datos = df.set_index(df.columns[0]).iloc[:, 0].to_dict()
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
                "PCS [MJ/m³]": round(pcs, 2),
                "PCI [MJ/m³]": round(pci, 2),
                "PM Gas [g/mol]": round(pm_gas, 2),
                "Densidad Relativa": round(dens_rel, 4),
                "Índice de Wobbe": round(wobbe, 2)
            }

            st.markdown("### 📊 Resultados del cálculo")
            st.write(resultados)

            generar_pdf(
                nombre_archivo=f"Informe_Gas_{operador.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pd",
                operador=operador,
                explicacion="Cálculo de propiedades energéticas y fisicoquímicas del gas natural según ISO 6976 y GPA 2145.",
                resultados=resultados,
                obs=obs,
                carpeta="gas_natural"
            )
        except Exception as e:
            st.error(f"❌ Error en el cálculo: {e}")

# MENÚ PRINCIPAL
def main():
    opciones = ["-- Seleccionar --"] + list(PARAMETROS_CONFIG.keys()) + ["Gas Natural"]
    analisis = st.selectbox("Seleccioná el tipo de análisis:", opciones)
    
    if analisis == "-- Seleccionar --":
        st.info("📌 Seleccioná un análisis en el menú desplegable.")
    elif anaisis in PARAMETROS_CONFIG:
        formulario_analisis(analisis, PARAMETROS_CONFIG[analisis])
    elif analisis == "Gas Natural":
        mostrar_analisis_gas()

if __name__ == "__main__":
    main()

