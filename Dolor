import streamlit as st
import pandas as pd
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Mapa de Dolores", page_icon="🧗", layout="centered")

# --- BASE DE DATOS (GOOGLE SHEETS) ---
DATA_FILE = "dolores.csv"

def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=["x", "y", "nombre", "tipo", "fecha"])
    return pd.read_csv(DATA_FILE)

def save_pain(x, y, nombre, tipo):
    df = load_data()
    new_data = pd.DataFrame([{
        "x": x, 
        "y": y, 
        "nombre": nombre, 
        "tipo": tipo,
        "fecha": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    }])
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

# --- 2. CONFIGURACIÓN VISUAL ---
# Mapeo de colores según el tipo de dolor
COLORS = {
    "Tendón (Polea/Codo)": "red",    # Rojo alarma
    "Músculo (Petado)": "orange",    # Naranja carga
    "Articulación": "blue",          # Azul frío
    "Raspón/Moratón": "purple",      # Morado golpe
    "Ego Herido": "grey"             # Gris tristeza
}

# --- 3. INTERFAZ DE USUARIO ---
st.title("🧗 Me duele el hombro")
st.caption("Marca dónde te duele")

# Inputs del usuario
col1, col2 = st.columns(2)
with col1:
    usuario = st.selectbox("¿Quién eres?", ["Álvaro", "Javier", "Jordi", "Miguel"])
with col2:
    tipo_dolor = st.selectbox("Tipo de dolor", list(COLORS.keys()))

# --- 4. LÓGICA DEL MAPA E IMAGEN ---
# Cargar imagen base (Debes tener una imagen 'cuerpo.png' en la carpeta)
# Si no tienes una, usa un placeholder o descarga una silueta humana simple.
try:
    # Intenta cargar imagen local
    img = Image.open("cuerpo.png").convert("RGBA")
except:
    # Crea una imagen gris si no hay fichero (para que el código no falle al probar)
    img = Image.new('RGB', (400, 600), color = (200, 200, 200))
    d = ImageDraw.Draw(img)
    d.text((100,300), "Sube una imagen llamada\n'cuerpo.png'", fill=(0,0,0))

# DIBUJAR LOS PUNTOS EXISTENTES
# Pintamos sobre la imagen ANTES de mostrarla. 
# Esto garantiza que en el móvil los puntos no se muevan de sitio.
df = load_data()
draw = ImageDraw.Draw(img)

# Radio del punto de dolor
r = 10 

for _, row in df.iterrows():
    cx, cy = row['x'], row['y']
    color = COLORS.get(row['tipo'], "black")
    # Dibujar círculo
    draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=color, outline="white", width=2)

# --- 5. COMPONENTE INTERACTIVO ---
st.write("👇 **Toca en el cuerpo para añadir tus dolores**")

# Muestra la imagen y espera el click
value = streamlit_image_coordinates(img, key="pil")

# --- 6. GUARDAR CLICK ---
if value is not None:
    # Verificamos si es un click nuevo comparando con el último guardado
    last_entry = df.iloc[-1] if not df.empty else None
    
    # Lógica simple para evitar duplicados al recargar:
    # Si las coordenadas son idénticas a la última entrada, no guardamos de nuevo
    if last_entry is None or (value['x'] != last_entry['x'] or value['y'] != last_entry['y']):
        save_pain(value['x'], value['y'], usuario, tipo_dolor)
        st.toast(f"¡Ay! Dolor guardado para {usuario}", icon="🩹")
        st.rerun() # Recarga la página para mostrar el punto nuevo

# --- 7. TABLA RESUMEN (OPCIONAL) ---
with st.expander("Ver historial de quejas"):
    st.dataframe(df.sort_values("fecha", ascending=False), use_container_width=True)

# Botón para limpiar (útil para empezar de cero)
if st.button("Borrar datos"):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        st.rerun()

