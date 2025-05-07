import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os
from io import BytesIO
import unicodedata

# Configuración inicial
st.set_page_config(page_title="LTS Lab Analyzer", layout="wide")
LOGO_PATH = "logopetrogas.png"

# Mostrar logo
try:
    with open(LOGO_PATH, "rb") as logo_file:
        st.image(logo_file.read(), width=180)
except Exception:
    st.warning("⚠️ No se pudo cargar el logo.")

st.title("🧪 Laboratorio de Planta LTS")
st.markdown("""
Sistema profesional de análisis y validación de laboratorio con informes PDF para plantas de tratamiento de gas natural.
""")

st.sidebar.header("⚙️ Opciones")
activar_validaciones = st.sidebar.checkbox("Activar validación de rangos", value=True)

# Explicaciones pedagógicas por módulo
EXPLICACIONES = {
    "MEG": (
        "📘 **¿Qué analizamos en el MEG (Monoetilenglicol)?**\n\n"
        "- **pH**: controla la acidez, fundamental para prevenir corrosión.\n"
        "- **Concentración**: asegura la capacidad anticongelante.\n"
        "- **Densidad y Cloruros**: determinan pureza y contaminantes.\n"
        "- **MDEA**: presencia de aminas utilizadas en tratamientos químicos."
    ),
    "TEG": (
        "📘 **¿Qué analizamos en el TEG (Trietilenglicol)?**\n\n"
        "- **pH**: estabilidad química.\n"
        "- **Concentración**: eficiencia de deshidratación del gas.\n"
        "- **Cloruros y Hierro**: indicadores de corrosión o contaminación."
    ),
    "Agua Desmineralizada": (
        "📘 **¿Por qué se analiza el agua desmineralizada?**\n\n"
        "- **pH**: neutralidad deseada.\n"
        "- **Cloruros**: impurezas que afectan turbinas, calderas, etc.\n"
        "- **Densidad**: indicador indirecto de sales u otros compuestos."
    ),
    "Gasolina Estabilizada": (
        "📘 **Parámetros importantes en la gasolina estabilizada:**\n\n"
        "- **TVR**: presión de vapor, clave para seguridad.\n"
        "- **Salinidad**: sales disueltas que generan corrosión.\n"
        "- **Densidad**: control de calidad del producto final."
    ),
    "Gas Natural": (
        "📘 **¿Qué analizamos en el gas natural?**\n\n"
        "- **Poder Calorífico (HHV)**: energía liberada en combustión.\n"
        "- **Índice de Wobbe**: permite comparar diferentes gases.\n"
        "- **Fracciones molares**: necesarias para todos los cálculos energéticos y normativos."
    )
}

# Parámetros por módulo
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

# Crear carpetas
for carpeta in PARAMETROS_CONFIG:
    os.makedirs(f"informes/{carpeta.lower().replace(' ', '_')}", exist_ok=True)
os.makedirs("informes/gas_natural", exist_ok=True)

def limpiar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    texto = texto.replace("–", "-").replace("—", "-").replace("“", '"').replace("”", '"')
    return unicodedata.normalize("NFKD", texto).encode("latin1", "ignore").decode("latin1")

class PDF(FPDF):
    def header(self):
        try:
            self.image(LOGO_PATH, 10, 8, 33)
        except Exception:
            pass
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
    pdf.add_operator(operador)
    pdf.add_explanation(explicacion)
    pdf.add_results(resultados)
    pdf.add_observaciones(obs)
    ruta = os.path.join(f"informes/{carpeta}", nombre_archivo)
    pdf_bytes = pdf.output(dest="S").encode("latin1", errors="ignore")
    with open(ruta, "wb") as f:
        f.write(pdf_bytes)
    st.download_button("⬇️ Descargar informe PDF", BytesIO(pdf_bytes), nombre_archivo, mime="application/pdf")

def formulario_analisis(nombre_modulo, parametros):
    st.subheader(f"🔬 Análisis de {nombre_modulo}")
    st.markdown(EXPLICACIONES[nombre_modulo])
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
            explicacion=EXPLICACIONES[nombre_modulo],
            resultados=resultados,
            obs=obs,
            carpeta=nombre_modulo.lower().replace(' ', '_')
        )

def mostrar_analisis_gas():
    st.subheader("🛢️ Análisis de Gas Natural")
    st.markdown(EXPLICACIONES["Gas Natural"])
    archivo = st.file_uploader("📎 Subir archivo CSV", type="csv")
    operador = st.text_input("👤 Operador", key="operador_gas")
    obs = st.text_area("Observaciones", key="obs_gas")
    if archivo is not None:
        try:
            df = pd.read_csv(archivo)
            st.dataframe(df)
            resultados = df.set_index(df.columns[0]).iloc[:, 0].to_dict() if df.shape[1] >= 2 else {df.columns[0]: df.iloc[:, 0].values.tolist()}
            generar_pdf(
                nombre_archivo=f"Informe_Gas_{operador.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                operador=operador,
                explicacion=EXPLICACIONES["Gas Natural"],
                resultados=resultados,
                obs=obs,
                carpeta="gas_natural"
            )
        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {e}")

def main():
    analisis_nuevo = st.selectbox("Seleccioná el tipo de análisis:", ["-- Seleccionar --"] + list(PARAMETROS_CONFIG.keys()) + ["Gas Natural"], key="tipo_analisis")
    if analisis_nuevo == "-- Seleccionar --":
        st.info("📌 Elegí un análisis en el menú desplegable para comenzar.")
    elif analisis_nuevo in PARAMETROS_CONFIG:
        formulario_analisis(analisis_nuevo, PARAMETROS_CONFIG[analisis_nuevo])
    elif analisis_nuevo == "Gas Natural":
        mostrar_analisis_gas()

if __name__ == "__main__":
    main()

