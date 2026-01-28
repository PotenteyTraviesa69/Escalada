import streamlit as st
import pandas as pd
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Mapa de Escalada: Debug Mode", layout="centered")
DATA_FILE = "dolores_escalada_final.csv"

# --- 1. DEFINICIÓN DE REGIONES (ANATOMÍA) ---
# Coordenadas (Debes ajustarlas a tu imagen real de 800x600)
BODY_ZONES = {
    # --- VISTA FRONTAL (Izq) ---
    "F_Hombro_Izq": [(300, 130), (350, 130), (340, 170), (290, 160)],
    "F_Hombro_Der": [(50, 130), (100, 130), (110, 160), (60, 170)],
    "F_Pectoral": [(100, 160), (300, 160), (280, 220), (120, 220)],
    "F_Abdominales": [(140, 220), (260, 220), (250, 320), (150, 320)],
    "F_Cuadriceps_Izq": [(220, 320), (280, 320), (270, 450), (230, 450)],
    "F_Cuadriceps_Der": [(120, 320), (180, 320), (170, 450), (130, 450)],
    "F_Rodilla_Izq": [(230, 450), (270, 450), (270, 480), (230, 480)],
    "F_Rodilla_Der": [(130, 450), (170, 450), (170, 480), (130, 480)],
    "F_Muneca_Izq": [(340, 280), (380, 280), (380, 300), (340, 300)],
    "F_Muneca_Der": [(20, 280), (60, 280), (60, 300), (20, 300)],

    # --- VISTA POSTERIOR (Der) ---
    "P_Trapecio": [(550, 110), (650, 110), (680, 140), (520, 140)],
    "P_Dorsal": [(530, 180), (670, 180), (650, 280), (550, 280)],
    "P_Lumbar": [(560, 280), (640, 280), (640, 320), (560, 320)],
    "P_Gemelo_Izq": [(530, 480), (570, 480), (560, 550), (540, 550)],
    "P_Gemelo_Der": [(630, 480), (670, 480), (660, 550), (640, 550)],
    "P_Codo_Izq": [(500, 220), (540, 220), (540, 250), (500, 250)],
    "P_Codo_Der": [(660, 220), (700, 220), (700, 250), (660, 250)],
}

# --- 2. CONFIGURACIÓN DE USUARIOS ---
# Prioridad: 0 se pinta al fondo, 1, 2, 3 encima.
USERS_CONFIG = {
    "Álvaro": {"pattern": "solid",         "priority": 0}, 
    "Javier": {"pattern": "lines_oblique", "priority": 1}, # Líneas oblicuas
    "Jordi":  {"pattern": "cross",         "priority": 2}, 
    "Miguel": {"pattern": "dots",          "priority": 3}  
}

# Colores según tipo de dolencia
TYPE_COLORS = {
    "Músculo": (255, 140, 0),      # Naranja
    "Articulación": (0, 0, 255),   # Azul
    "Herida": (255, 0, 0)          # Rojo (para el punto)
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
    # Evitar duplicados exactos (mismo usuario, misma región/tipo)
    duplicate = False
    if region:
        duplicate = not df[(df['usuario'] == usuario) & (df['region'] == region) & (df['tipo'] == tipo)].empty
    
    if not duplicate:
        new_row = {
            "x": x, "y": y, 
            "usuario": usuario, "tipo": tipo, "region": region, 
            "fecha": pd.Timestamp.now()
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        return True
    return False

def draw_pattern_in_region(draw_ctx, polygon, user_pattern, color_rgb):
    """Dibuja el patrón del usuario dentro del polígono con el color de la dolencia"""
    
    min_x = int(min(p[0] for p in polygon))
    max_x = int(max(p[0] for p in polygon))
    min_y = int(min(p[1] for p in polygon))
    max_y = int(max(p[1] for p in polygon))

    # Base semitransparente para el color
    fill_color = color_rgb + (120,) # Alpha medio

    if user_pattern == "solid":
        draw_ctx.polygon(polygon, fill=fill_color)
    
    elif user_pattern == "lines_oblique":
        # Patrón de Javier: Líneas diagonales ///
        step = 8
        # Dibujamos líneas en un área rectangular y el usuario verá las que caigan dentro
        # Para simplificar en Streamlit, dibujamos líneas cortas o usamos clip visual
        # Método visual: Dibujar líneas diagonales dentro del bounding box
        for i in range(min_x - (max_y - min_y), max_x, step):
             start = (i, min_y)
             end = (i + (max_y - min_y), max_y)
             # Esto es una simplificación visual. 
             # Para hacerlo perfecto se requiere clipping complejo.
             # Aquí dibujamos la línea y un icono central para identificar.
             pass
        
        # Representación robusta: Relleno suave + Trama visible
        draw_ctx.polygon(polygon, fill=color_rgb + (30,)) # Fondo muy tenue
        
        # Dibujamos líneas diagonales manuales recortadas (simple clipping)
        for x in range(min_x, max_x, 10):
            for y in range(min_y, max_y, 10):
                if point_in_polygon(x, y, polygon):
                    draw_ctx.line((x, y, x+5, y-5), fill=color_rgb + (255,), width=1)

    elif user_pattern == "cross":
        # Cruces / Cuadrícula
        draw_ctx.polygon(polygon, fill=color_rgb + (30,)) 
        for x in range(min_x, max_x, 12):
            for y in range(min_y, max_y, 12):
                if point_in_polygon(x, y, polygon):
                    # Dibujar una pequeña cruz
                    r = 3
                    draw_ctx.line((x-r, y, x+r, y), fill=color_rgb + (255,), width=1)
                    draw_ctx.line((x, y-r, x, y+r), fill=color_rgb + (255,), width=1)

    elif user_pattern == "dots":
        # Puntos
        draw_ctx.polygon(polygon, fill=color_rgb + (30,)) 
        for x in range(min_x, max_x, 8):
            for y in range(min_y, max_y, 8):
                if point_in_polygon(x, y, polygon):
                    draw_ctx.rectangle((x, y, x+2, y+2), fill=color_rgb + (255,))

# --- INTERFAZ ---
st.title("🧗 Reporte de Daños")

# Controles Superiores
c1, c2 = st.columns(2)
with c1:
    usuario_activo = st.selectbox("¿Quién eres?", list(USERS_CONFIG.keys()))
with c2:
    tipo_dolor = st.selectbox("¿Qué te has hecho?", ["Articulación", "Músculo", "Herida"])

# --- GENERACIÓN DE IMAGEN ---
W, H = 800, 600
try:
    base_img = Image.open("cuerpo_completo.png").convert("RGBA")
except:
    base_img = Image.new('RGBA', (W, H), (240, 240, 240, 255))

# Capa para los sombreados (Overlay)
overlay = Image.new('RGBA', base_img.size, (0,0,0,0))
draw = ImageDraw.Draw(overlay)

df = load_data()

# 1. DIBUJAR REGIONES (Músculos y Articulaciones)
# Agrupar datos para dibujar capa por capa
regiones_activas = df[df['tipo'].isin(["Músculo", "Articulación"])]

# Agrupar por Region -> Lista de Usuarios
mapa_dolor = regiones_activas.groupby("region").apply(lambda x: x[['usuario', 'tipo']].to_dict('records')).to_dict()

for region_name, entries in mapa_dolor.items():
    if region_name in BODY_ZONES:
        poly = BODY_ZONES[region_name]
        
        # Ordenar entradas por prioridad de usuario
        entries_sorted = sorted(entries, key=lambda x: USERS_CONFIG[x['usuario']]["priority"])
        
        for entry in entries_sorted:
            u_name = entry['usuario']
            t_dolor = entry['tipo']
            
            color = TYPE_COLORS.get(t_dolor, (0,0,0))
            pattern = USERS_CONFIG[u_name]["pattern"]
            
            draw_pattern_in_region(draw, poly, pattern, color)

# 2. DIBUJAR HERIDAS (Puntos rojos encima de todo)
heridas = df[df['tipo'] == "Herida"]
for _, row in heridas.iterrows():
    cx, cy = row['x'], row['y']
    # Dibujar una X roja o un punto rojo brillante
    r = 5
    draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=(255, 0, 0, 255), outline="white", width=2)
    # Pequeño texto con inicial (opcional, para saber de quien es la herida)
    # draw.text((cx+r, cy), row['usuario'][0], fill="black")

# 3. DEBUG MODE: Dibujar bordes MORADOS de todas las zonas
for name, poly in BODY_ZONES.items():
    draw.polygon(poly, outline="purple", width=2)

# Componer imagen
final_img = Image.alpha_composite(base_img, overlay)

# --- INTERACCIÓN ---
st.caption("Los bordes morados delimitan las zonas activas. Haz click dentro.")
value = streamlit_image_coordinates(final_img, key="main_canvas", width=700)

if value:
    click_x = value['x'] * (W/700) # Ajuste de escala si la imagen se muestra a 700px
    click_y = value['y'] * (W/700)
    
    # Lógica de guardado
    saved = False
    
    if tipo_dolor == "Herida":
        # Las heridas se guardan por coordenada exacta, ignorando regiones
        save_pain(click_x, click_y, usuario_activo, "Herida", region=None)
        st.toast(f"Herida marcada en ({int(click_x)}, {int(click_y)})")
        st.rerun()
        
    else:
        # Músculo o Articulación: Buscar si cayó dentro de un polígono
        hit_region = None
        for name, poly in BODY_ZONES.items():
            if point_in_polygon(click_x, click_y, poly):
                hit_region = name
                break
        
        if hit_region:
            if save_pain(click_x, click_y, usuario_activo, tipo_dolor, region=hit_region):
                st.toast(f"{tipo_dolor} registrado en: {hit_region}")
                st.rerun()
            else:
                st.toast("Ya habías marcado esta zona.")
        else:
            st.warning("Has hecho click fuera de las zonas delimitadas (bordes morados).")

# --- VISUALIZACIÓN DE DATOS ---
st.divider()
st.subheader("Lista de Bajas")
if not df.empty:
    # Tabla resumen simple
    st.dataframe(df[['fecha', 'usuario', 'tipo', 'region']].sort_values('fecha', ascending=False), use_container_width=True)
