import streamlit as st
import pandas as pd
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Mapa de Escalada", layout="centered")
DATA_FILE = "dolores_escalada.csv"

# Definición de Polígonos Musculares (Coordenadas aproximadas para 400x600)
# Formato: "Nombre": [(x1, y1), (x2, y2), (x3, y3)...]
BODY_POLYGONS = {
    # Torso
    "Pectoral": [(130, 160), (270, 160), (260, 210), (140, 210)],
    "Abdominales": [(160, 210), (240, 210), (230, 310), (170, 310)],
    "Dorsal": [(110, 180), (130, 180), (140, 250), (100, 230)],
    "Trapecio": [(150, 110), (250, 110), (280, 140), (120, 140)],
    "Cuello": [(180, 70), (220, 70), (220, 110), (180, 110)],
    
    # Brazos
    "Hombros": [(100, 130), (150, 130), (150, 170), (90, 160)],
    "Bíceps": [(100, 170), (140, 170), (130, 210), (90, 200)],
    "Tríceps": [(80, 170), (100, 170), (90, 210), (70, 200)], # Visible si es vista posterior/lateral
    "Antebrazos": [(80, 210), (130, 210), (120, 280), (70, 270)],
    "Mano": [(60, 280), (130, 280), (120, 310), (60, 310)],
    "Dedos (Mano)": [(50, 310), (130, 310), (130, 330), (50, 330)],

    # Piernas
    "Cuádriceps": [(140, 310), (260, 310), (250, 420), (150, 420)],
    "Isquiotibiales": [(150, 420), (250, 420), (240, 460), (160, 460)], # Posterior
    "Gemelos": [(150, 460), (250, 460), (240, 530), (160, 530)],
    "Dedos (Pie)": [(140, 560), (260, 560), (260, 580), (140, 580)],
}

# Configuración de Usuarios (Forma del punto y Tipo de Trama para músculo)
USERS_CONFIG = {
    "Álvaro": {"shape": "circle", "pattern": "solid"},       # Relleno sólido
    "Javier": {"shape": "square", "pattern": "lines_diag"},  # Rayas diagonales
    "Jordi":  {"shape": "triangle", "pattern": "lines_cross"}, # Cuadrícula/Cruces
    "Miguel": {"shape": "diamond", "pattern": "dots"}        # Puntos
}

COLORS = {
    "Músculo": (255, 165, 0),     # Naranja
    "Herida": (255, 0, 0),        # Rojo
    "Articulación": (0, 0, 255)   # Azul
}

# --- FUNCIONES AUXILIARES ---

def point_in_polygon(x, y, polygon):
    """Algoritmo Ray Casting para detectar si un click está dentro de un músculo"""
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def draw_pattern(draw_obj, polygon, pattern_type, color):
    """Dibuja texturas manuales dentro del polígono (Rayas, puntos, etc.)"""
    # 1. Dibujar contorno siempre
    draw_obj.polygon(polygon, outline=color, width=2)
    
    # Bounding box del polígono para iterar
    min_x = min(p[0] for p in polygon)
    max_x = max(p[0] for p in polygon)
    min_y = min(p[1] for p in polygon)
    max_y = max(p[1] for p in polygon)
    
    # Color con transparencia para el relleno
    fill_color = color + (100,) # Añadir canal Alpha (0-255)

    if pattern_type == "solid":
        draw_obj.polygon(polygon, fill=fill_color)
    
    elif pattern_type == "lines_diag":
        step = 10
        for i in range(min_x - (max_y - min_y), max_x, step):
            # Dibujamos líneas y dejamos que PIL recorte visualmente no es nativo, 
            # pero simulamos dibujando solo si el centro está dentro.
            # Método simplificado: Dibujar polígono transparente + Líneas encima
            pass 
        # *Nota*: Hacer clipping de líneas en PIL puro es complejo y lento.
        # Alternativa visual efectiva: Relleno semitransparente + Símbolo central
        draw_obj.polygon(polygon, fill=fill_color)
        cx = int((min_x + max_x)/2)
        cy = int((min_y + max_y)/2)
        draw_obj.line((cx-10, cy-10, cx+10, cy+10), fill="black", width=2)
        draw_obj.line((cx-5, cy-5, cx+5, cy+5), fill="black", width=2)
        
    elif pattern_type == "lines_cross":
        draw_obj.polygon(polygon, fill=fill_color)
        # Dibujar una 'X' grande sobre el músculo para representar la trama
        draw_obj.line((min_x, min_y, max_x, max_y), fill="white", width=1)
        draw_obj.line((min_x, max_y, max_x, min_y), fill="white", width=1)

    elif pattern_type == "dots":
        draw_obj.polygon(polygon, fill=fill_color)
        # Punteado simple
        step = 8
        for x in range(min_x, max_x, step):
            for y in range(min_y, max_y, step):
                if point_in_polygon(x, y, polygon):
                    draw_obj.point((x, y), fill="white")

# --- GESTIÓN DE DATOS ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=["x", "y", "nombre", "tipo", "region", "fecha"])
    return pd.read_csv(DATA_FILE)

def save_pain(x, y, nombre, tipo, region=None):
    df = load_data()
    new_row = {"x": x, "y": y, "nombre": nombre, "tipo": tipo, "region": region, "fecha": pd.Timestamp.now()}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

def clear_data():
    # ARREGLO PROBLEMA 1: Sobrescribir con DataFrame vacío (solo headers)
    empty_df = pd.DataFrame(columns=["x", "y", "nombre", "tipo", "region", "fecha"])
    empty_df.to_csv(DATA_FILE, index=False)

# --- APP ---
st.title("🧗 Mapa de Lesiones 2.0")

# Controles
c1, c2, c3 = st.columns(3)
with c1:
    usuario = st.selectbox("Usuario", list(USERS_CONFIG.keys()))
with c2:
    modo = st.radio("¿Qué marcas?", ["Músculo (Zona)", "Punto (Herida/Articulación)"])
with c3:
    if modo == "Punto (Herida/Articulación)":
        tipo_punto = st.selectbox("Tipo", ["Herida", "Articulación"])
    else:
        st.info("Marca zonas musculares")

# Imagen
try:
    base_img = Image.open("cuerpo.png").convert("RGBA")
except:
    base_img = Image.new('RGBA', (400, 600), (220, 220, 220, 255))

overlay = Image.new('RGBA', base_img.size, (0,0,0,0))
draw = ImageDraw.Draw(overlay)
df = load_data()

# 1. PINTAR MÚSCULOS (Zonas)
musculos_df = df[df['tipo'] == "Músculo"]
for _, row in musculos_df.iterrows():
    if pd.notna(row['region']) and row['region'] in BODY_POLYGONS:
        poly = BODY_POLYGONS[row['region']]
        u_conf = USERS_CONFIG.get(row['nombre'], USERS_CONFIG["Álvaro"])
        color_rgb = COLORS["Músculo"]
        
        # Función personalizada de tramado
        draw_pattern(draw, poly, u_conf['pattern'], color_rgb)

# 2. PINTAR PUNTOS (Heridas/Articulaciones)
puntos_df = df[df['tipo'] != "Músculo"]
for _, row in puntos_df.iterrows():
    cx, cy = row['x'], row['y']
    u_conf = USERS_CONFIG.get(row['nombre'], USERS_CONFIG["Álvaro"])
    color = COLORS.get(row['tipo'], (0,0,0))
    r = 6
    
    # Formas geométricas
    if u_conf['shape'] == "circle":
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=color, outline="white")
    elif u_conf['shape'] == "square":
        draw.rectangle((cx-r, cy-r, cx+r, cy+r), fill=color, outline="white")
    elif u_conf['shape'] == "triangle":
        draw.polygon([(cx, cy-r), (cx-r, cy+r), (cx+r, cy+r)], fill=color, outline="white")
    elif u_conf['shape'] == "diamond":
        draw.polygon([(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy)], fill=color, outline="white")

# Componer imagen final
final_img = Image.alpha_composite(base_img, overlay)

st.write(f"**Turno de: {usuario}** ({USERS_CONFIG[usuario]['shape']} / {USERS_CONFIG[usuario]['pattern']})")
value = streamlit_image_coordinates(final_img, key="body_canvas")

# Lógica de Click
if value:
    click_x, click_y = value['x'], value['y']
    
    # Evitar doble click al refrescar
    last_x = df.iloc[-1]['x'] if not df.empty else -1
    last_y = df.iloc[-1]['y'] if not df.empty else -1
    
    if click_x != last_x or click_y != last_y:
        
        saved = False
        if modo == "Músculo (Zona)":
            # Detectar si click cae en algún polígono
            for nombre_musculo, poly in BODY_POLYGONS.items():
                if point_in_polygon(click_x, click_y, poly):
                    save_pain(click_x, click_y, usuario, "Músculo", region=nombre_musculo)
                    st.toast(f"Músculo marcado: {nombre_musculo}")
                    saved = True
                    st.rerun()
                    break
            if not saved:
                st.warning("Click fuera de zona muscular definida. Intenta en el centro del músculo.")
        
        else: # Modo Punto
            save_pain(click_x, click_y, usuario, tipo_punto)
            st.toast(f"{tipo_punto} marcado")
            st.rerun()

# Tabla y Borrado
with st.expander("Ver Datos"):
    st.dataframe(df)

if st.button("Borrar TODO el historial"):
    clear_data()
    st.rerun()
