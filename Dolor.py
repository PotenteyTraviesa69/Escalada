import streamlit as st
import pandas as pd
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw, ImageFont
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Escalada: Mapa de Dolores", layout="centered")

DATA_FILE = "dolores_escalada.csv"

# Definición de regiones musculares (X_min, Y_min, X_max, Y_max)
# NOTA: Deberás ajustar estos números según las dimensiones de tu 'cuerpo.png'
MUSCLE_REGIONS = {
    "Antebrazos": (100, 250, 300, 350),
    "Hombros": (120, 100, 280, 150),
    "Dorsales": (130, 160, 270, 240),
    "Core/Abdominales": (160, 240, 240, 320),
}

USERS_SHAPES = {
    "Álvaro": "circle",
    "Javier": "square",
    "Jordi": "triangle",
    "Miguel": "diamond"
}

COLORS = {
    "Músculo": "#FFA500",      # Naranja (Sombreado)
    "Herida": "#FF0000",       # Rojo (Punto)
    "Articulación": "#0000FF", # Azul (Punto)
}

# --- FUNCIONES DE DATOS ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=["x", "y", "nombre", "tipo", "region", "fecha"])
    return pd.read_csv(DATA_FILE)

def save_pain(x, y, nombre, tipo, region=None):
    df = load_data()
    new_data = pd.DataFrame([{"x": x, "y": y, "nombre": nombre, "tipo": tipo, "region": region, "fecha": pd.Timestamp.now()}])
    pd.concat([df, new_data], ignore_index=True).to_csv(DATA_FILE, index=False)

def get_region(x, y):
    for name, coords in MUSCLE_REGIONS.items():
        if coords[0] <= x <= coords[2] and coords[1] <= y <= coords[3]:
            return name
    return None

# --- INTERFAZ ---
st.title("🧗 Reporte de Averías")

col1, col2 = st.columns(2)
with col1:
    usuario = st.selectbox("¿Quién eres?", list(USERS_SHAPES.keys()))
with col2:
    tipo_dolor = st.radio("Tipo de lesión", list(COLORS.keys()), horizontal=True)

# --- PROCESAMIENTO DE IMAGEN ---
try:
    base_img = Image.open("cuerpo.png").convert("RGBA")
except:
    base_img = Image.new('RGBA', (400, 600), (240, 240, 240, 255))

draw = ImageDraw.Draw(base_img)
df = load_data()

# 1. Dibujar sombreado de músculos afectados
for region in df[df['tipo'] == "Músculo"]['region'].unique():
    if region in MUSCLE_REGIONS:
        draw.rectangle(MUSCLE_REGIONS[region], fill=(255, 165, 0, 80)) # Naranja transparente

# 2. Dibujar marcas de usuarios
for _, row in df.iterrows():
    cx, cy = row['x'], row['y']
    shape = USERS_SHAPES.get(row['nombre'], "circle")
    color = COLORS.get(row['tipo'], "black")
    r = 8
    
    if shape == "circle":
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=color, outline="white")
    elif shape == "square":
        draw.rectangle((cx-r, cy-r, cx+r, cy+r), fill=color, outline="white")
    elif shape == "triangle":
        draw.polygon([(cx, cy-r), (cx-r, cy+r), (cx+r, cy+r)], fill=color, outline="white")
    else: # Diamond
        draw.polygon([(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy)], fill=color, outline="white")

# --- MOSTRAR MAPA ---
st.write("Haz clic en el músculo o zona afectada:")
value = streamlit_image_coordinates(base_img, key="body_map")

if value:
    reg = get_region(value['x'], value['y'])
    # Evitar duplicados por refresco
    if df.empty or not ((df.iloc[-1]['x'] == value['x']) and (df.iloc[-1]['y'] == value['y'])):
        save_pain(value['x'], value['y'], usuario, tipo_dolor, reg)
        st.rerun()

# --- LEYENDA Y TABLA ---
st.markdown(f"**Leyenda de formas:** 🔵 Álvaro (Círculo) | 🟦 Javier (Cuadrado) | 🔺 Jordi (Triángulo) | 💠 Miguel (Diamante)")

with st.expander("Historial de pupas"):
    st.table(df.tail(10))

if st.button("Limpiar Mapa"):
    if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
    st.rerun()
