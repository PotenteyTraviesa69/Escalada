import streamlit as st
import pandas as pd
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Mapa de Escalada v6.1", layout="centered")
DATA_FILE = "dolores_escalada_v6.csv"

# --- 1. DEFINICIÓN DE REGIONES ---
# Lienzo 800x600.

ZONAS_MUSCULARES = {
    # --- VISTA FRONTAL (Izq) ---
    "F_Pectoral_Izq": [(200, 160), (300, 160), (280, 220), (200, 220)], 
    "F_Pectoral_Der": [(100, 160), (200, 160), (200, 220), (120, 220)],
    "F_Abdominales": [(140, 220), (260, 220), (250, 320), (150, 320)],
    "F_Biceps_Izq": [(300, 170), (340, 170), (330, 210), (290, 210)],
    "F_Biceps_Der": [(60, 170), (100, 170), (110, 210), (70, 210)],
    "F_Antebrazo_Izq": [(330, 230), (370, 230), (360, 280), (320, 280)],
    "F_Antebrazo_Der": [(30, 230), (70, 230), (80, 280), (40, 280)],
    "F_Cuadriceps_Izq": [(220, 320), (280, 320), (270, 440), (230, 440)],
    "F_Cuadriceps_Der": [(120, 320), (180, 320), (170, 440), (130, 440)],

    # --- VISTA POSTERIOR (Der) ---
    "P_Trapecio_Izq": [(520, 110), (600, 110), (600, 140), (520, 140)],
    "P_Trapecio_Der": [(600, 110), (680, 110), (680, 140), (600, 140)],
    "P_Dorsal_Izq": [(530, 180), (600, 180), (600, 280), (550, 280)],
    "P_Dorsal_Der": [(600, 180), (670, 180), (650, 280), (600, 280)],
    "P_Triceps_Izq": [(500, 170), (540, 170), (530, 210), (490, 210)],
    "P_Triceps_Der": [(660, 170), (700, 170), (710, 210), (670, 210)],
    "P_Lumbar": [(560, 280), (640, 280), (640, 320), (560, 320)],
    "P_Isquios_Izq": [(530, 350), (580, 350), (570, 440), (540, 440)],
    "P_Isquios_Der": [(620, 350), (670, 350), (660, 440), (630, 440)],
    "P_Gemelo_Izq": [(530, 480), (570, 480), (560, 550), (540, 550)],
    "P_Gemelo_Der": [(630, 480), (670, 480), (660, 550), (640, 550)],
}

ZONAS_ARTICULARES = {
    # --- VISTA FRONTAL ---
    "F_Hombro_Izq": [(300, 130), (350, 130), (340, 170), (290, 160)],
    "F_Hombro_Der": [(50, 130), (100, 130), (110, 160), (60, 170)],
    "F_Codo_Izq": [(320, 210), (360, 210), (350, 230), (310, 230)],
    "F_Codo_Der": [(40, 210), (80, 210), (90, 230), (50, 230)],
    "F_Muneca_Izq": [(340, 280), (380, 280), (380, 300), (340, 300)],
    "F_Muneca_Der": [(20, 280), (60, 280), (60, 300), (20, 300)],
    "F_Rodilla_Izq": [(230, 440), (270, 440), (270, 480), (230, 480)],
    "F_Rodilla_Der": [(130, 440), (170, 440), (170, 480), (130, 480)],
    "F_Tobillo_Izq": [(230, 550), (270, 550), (270, 570), (230, 570)],
    "F_Tobillo_Der": [(130, 550), (170, 550), (170, 570), (130, 570)],
    "F_Cadera_Izq": [(480, 290), (530, 290), (530, 340), (480, 340)],
    "F_Cadera_Der": [(670, 290), (720, 290), (720, 340), (670, 340)],

    # --- VISTA POSTERIOR ---
    "P_Codo_Izq": [(500, 210), (540, 210), (540, 230), (500, 230)],
    "P_Codo_Der": [(660, 210), (700, 210), (700, 230), (660, 230)],
}

# --- 2. CONFIGURACIÓN DE USUARIOS ---
USERS_CONFIG = {
    "Álvaro": {"pattern": "solid",         "priority": 0}, 
    "Javier": {"pattern": "lines_oblique", "priority": 1}, 
    "Jordi":  {"pattern": "cross",         "priority": 2}, 
    "Miguel": {"pattern": "dots",          "priority": 3}  
}

TYPE_COLORS = {
    "Músculo": (255, 140, 0),      # Naranja
    "Articulación": (0, 0, 255),   # Azul
    "Herida": (255, 0, 0)          # Rojo
}

# --- FUNCIONES ---

def point_in_polygon(x, y, polygon):
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

def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=["x", "y", "usuario", "tipo", "region", "fecha"])
    return pd.read_csv(DATA_FILE)

def save_pain(x, y, usuario, tipo, region=None):
    df = load_data()
    duplicate = False
    if region:
        duplicate = not df[(df['usuario'] == usuario) & (df['region'] == region) & (df['tipo'] == tipo)].empty
    
    if not duplicate:
        new_row = {"x": x, "y": y, "usuario": usuario, "tipo": tipo, "region": region, "fecha": pd.Timestamp.now()}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        return True
    return False

def draw_pattern_in_region(draw_ctx, polygon, user_pattern, color_rgb):
    min_x = int(min(p[0] for p in polygon))
    max_x = int(max(p[0] for p in polygon))
    min_y = int(min(p[1] for p in polygon))
    max_y = int(max(p[1] for p in polygon))

    if user_pattern == "solid":
        fill_color = color_rgb + (140,) 
        draw_ctx.polygon(polygon, fill=fill_color)
    
    elif user_pattern == "lines_oblique":
        line_color = color_rgb + (255,) 
        for x in range(min_x, max_x, 6):
            for y in range(min_y, max_y, 6):
                if (x + y) % 10 == 0: 
                    if point_in_polygon(x, y, polygon):
                        draw_ctx.line((x, y, x+4, y+4), fill=line_color, width=2)

    elif user_pattern == "cross":
        cross_color = color_rgb + (255,)
        for x in range(min_x, max_x, 14):
            for y in range(min_y, max_y, 14):
                if point_in_polygon(x, y, polygon):
                    draw_ctx.line((x-3, y, x+3, y), fill=cross_color, width=1)
                    draw_ctx.line((x, y-3, x, y+3), fill=cross_color, width=1)

    elif user_pattern == "dots":
        dot_color = color_rgb + (255,)
        for x in range(min_x, max_x, 10):
            for y in range(min_y, max_y, 10):
                if point_in_polygon(x, y, polygon):
                    draw_ctx.rectangle((x, y, x+3, y+3), fill=dot_color)

# --- INICIO DE APP ---
st.title("🧗 Mapa de Escalada v6.1")

if 'last_click_coords' not in st.session_state:
    st.session_state['last_click_coords'] = None

c1, c2 = st.columns(2)
with c1:
    usuario_activo = st.selectbox("Usuario", list(USERS_CONFIG.keys()))
with c2:
    tipo_dolor = st.selectbox("Tipo de Dolor", ["Músculo", "Articulación", "Herida"])

# --- IMAGEN ---
W, H = 1200, 1600
try:
    base_img = Image.open("cuerpo.jpg").convert("RGBA")
except:
    base_img = Image.new('RGBA', (W, H), (240, 240, 240, 255))
    d = ImageDraw.Draw(base_img)
    d.text((10,10), "ERROR: Sube 'cuerpo_completo.png'", fill="red")

overlay = Image.new('RGBA', base_img.size, (0,0,0,0))
draw = ImageDraw.Draw(overlay)

df = load_data()

# 1. DIBUJAR CAPAS
ALL_ZONES = {**ZONAS_MUSCULARES, **ZONAS_ARTICULARES}
regiones_activas = df[df['tipo'].isin(["Músculo", "Articulación"])]
mapa_dolor = regiones_activas.groupby("region").apply(lambda x: x[['usuario', 'tipo']].to_dict('records')).to_dict()

for region_name, entries in mapa_dolor.items():
    if region_name in ALL_ZONES:
        poly = ALL_ZONES[region_name]
        entries_sorted = sorted(entries, key=lambda x: USERS_CONFIG[x['usuario']]["priority"])
        
        for entry in entries_sorted:
            u_name = entry['usuario']
            t_dolor = entry['tipo']
            color = TYPE_COLORS.get(t_dolor, (0,0,0))
            pattern = USERS_CONFIG[u_name]["pattern"]
            draw_pattern_in_region(draw, poly, pattern, color)

# 2. DIBUJAR HERIDAS
for _, row in df[df['tipo'] == "Herida"].iterrows():
    cx, cy = row['x'], row['y']
    draw.ellipse((cx-5, cy-5, cx+5, cy+5), fill=(255, 0, 0, 255), outline="white", width=2)

# 3. DEBUG: BORDES MORADOS
zones_to_check = {}
if tipo_dolor == "Músculo":
    zones_to_check = ZONAS_MUSCULARES
elif tipo_dolor == "Articulación":
    zones_to_check = ZONAS_ARTICULARES
else:
    zones_to_check = ALL_ZONES

for name, poly in zones_to_check.items():
    draw.polygon(poly, outline="purple", width=2)

final_img = Image.alpha_composite(base_img, overlay)

# --- INTERACCIÓN ---
st.info(f"Marcando: {tipo_dolor}. Haz click en las zonas moradas.")
value = streamlit_image_coordinates(final_img, key="main_canvas", width=700)

if value:
    current_coords = (value['x'], value['y'])
    
    if st.session_state['last_click_coords'] != current_coords:
        st.session_state['last_click_coords'] = current_coords
        
        click_x = value['x'] * (W/700) 
        click_y = value['y'] * (W/700)
        
        if tipo_dolor == "Herida":
            save_pain(click_x, click_y, usuario_activo, "Herida")
            st.toast("Herida guardada")
            st.rerun()
        else:
            found = False
            for name, poly in zones_to_check.items():
                if point_in_polygon(click_x, click_y, poly):
                    if save_pain(click_x, click_y, usuario_activo, tipo_dolor, region=name):
                        st.toast(f"Guardado: {name}")
                    else:
                        st.toast("Dolor ya registrado")
                    found = True
                    st.rerun()
                    break
            
            if not found:
                st.warning(f"Click fuera de zona {tipo_dolor} válida.")

# --- DATOS ---
st.divider()
if not df.empty:
    st.write("### Historial Reciente")
    st.dataframe(df[['fecha', 'usuario', 'tipo', 'region']].sort_values("fecha", ascending=False).head(5))
