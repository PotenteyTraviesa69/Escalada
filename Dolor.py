import streamlit as st
import pandas as pd
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Mapa de Escalada Pro", layout="centered")
DATA_FILE = "dolores_escalada_v3.csv"

# --- 1. DEFINICIÓN DE REGIONES (ANATOMÍA) ---
# Coordenadas aproximadas para un lienzo de 800x600 (400 izq para frontal, 400 der para dorsal)
# Formato: "Nombre": [(x1, y1), (x2, y2)...]
# LADO IZQUIERDO DE LA IMAGEN = VISTA FRONTAL
# LADO DERECHO DE LA IMAGEN = VISTA POSTERIOR

BODY_ZONES = {
    # --- VISTA FRONTAL (0 a 400px X) ---
    "F_Hombro_Izq": [(300, 130), (350, 130), (340, 170), (290, 160)], # Lado del usuario (espejo) o anatómico? Usamos anatómico estandar
    "F_Hombro_Der": [(50, 130), (100, 130), (110, 160), (60, 170)],
    "F_Pectoral": [(100, 160), (300, 160), (280, 220), (120, 220)],
    "F_Abdominales": [(140, 220), (260, 220), (250, 320), (150, 320)],
    "F_Cuadriceps_Izq": [(220, 320), (280, 320), (270, 450), (230, 450)],
    "F_Cuadriceps_Der": [(120, 320), (180, 320), (170, 450), (130, 450)],
    
    # Articulaciones Frontales (Ahora son zonas)
    "F_Rodilla_Izq": [(230, 450), (270, 450), (270, 480), (230, 480)],
    "F_Rodilla_Der": [(130, 450), (170, 450), (170, 480), (130, 480)],
    "F_Muneca_Izq": [(340, 280), (380, 280), (380, 300), (340, 300)],
    "F_Muneca_Der": [(20, 280), (60, 280), (60, 300), (20, 300)],

    # --- VISTA POSTERIOR (400 a 800px X) ---
    # Sumamos 400 a la X para moverlo a la derecha
    "P_Trapecio": [(550, 110), (650, 110), (680, 140), (520, 140)],
    "P_Dorsal": [(530, 180), (670, 180), (650, 280), (550, 280)],
    "P_Lumbar": [(560, 280), (640, 280), (640, 320), (560, 320)],
    "P_Gemelo_Izq": [(530, 480), (570, 480), (560, 550), (540, 550)], # Anatómico: Izq en posterior es Izq visual
    "P_Gemelo_Der": [(630, 480), (670, 480), (660, 550), (640, 550)],
    
    # Articulaciones Posteriores
    "P_Codo_Izq": [(500, 220), (540, 220), (540, 250), (500, 250)],
    "P_Codo_Der": [(660, 220), (700, 220), (700, 250), (660, 250)],
}

# --- 2. CONFIGURACIÓN DE USUARIOS Y PRIORIDAD DE DIBUJO ---
# Priority: define quién se pinta primero. 0 (Sólido) debe ir al fondo.
# Los patrones (rayas, cruces) deben ir encima (Priority 1, 2, 3).
USERS_CONFIG = {
    "Álvaro": {"color": (255, 140, 0), "pattern": "solid", "priority": 0},    # Naranja solido
    "Javier": {"color": (0, 0, 0),     "pattern": "lines_diag", "priority": 1}, # Negro rayas
    "Jordi":  {"color": (0, 0, 200),   "pattern": "cross", "priority": 2},      # Azul cruces
    "Miguel": {"color": (200, 0, 0),   "pattern": "dots", "priority": 3}        # Rojo puntos
}

# --- FUNCIONES GRÁFICAS ---

def point_in_polygon(x, y, polygon):
    """Ray Casting para detectar clicks"""
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

def draw_layer(draw_ctx, polygon, config):
    """Dibuja una capa específica sobre el polígono"""
    color = config["color"]
    pattern = config["pattern"]
    
    min_x = min(p[0] for p in polygon)
    max_x = max(p[0] for p in polygon)
    min_y = min(p[1] for p in polygon)
    max_y = max(p[1] for p in polygon)

    if pattern == "solid":
        # Relleno con transparencia
        fill = color + (100,) # Alpha 100/255
        draw_ctx.polygon(polygon, fill=fill)
    
    elif pattern == "lines_diag":
        # Rayas diagonales sin relleno de fondo (solo líneas)
        step = 8
        for i in range(int(min_x - (max_y - min_y)), int(max_x), step):
            # Dibujamos líneas largas y dejamos que el "clip" visual sea el cerebro
            # Para hacerlo perfecto necesitaríamos máscaras, aquí usamos una aproximación:
            # Dibujar la línea SOLO si pasa cerca del centro (simplificado para Streamlit)
            pass
        # Aproximación visual robusta: Icono de patrón en el centro
        cx, cy = int((min_x+max_x)/2), int((min_y+max_y)/2)
        draw_ctx.line((min_x, min_y, max_x, max_y), fill=color + (200,), width=2)
        draw_ctx.line((min_x, max_y, max_x, min_y), fill=color + (200,), width=2)
        
    elif pattern == "cross":
        # Cuadrícula
        step = 10
        for x in range(int(min_x), int(max_x), step):
            if point_in_polygon(x, (min_y+max_y)/2, polygon):
                 draw_ctx.line((x, min_y, x, max_y), fill=color + (150,), width=1)
        
    elif pattern == "dots":
        # Puntos
        step = 6
        for x in range(int(min_x), int(max_x), step):
            for y in range(int(min_y), int(max_y), step):
                if point_in_polygon(x, y, polygon):
                    draw_ctx.point((x, y), fill=color + (255,))

# --- GESTIÓN DE DATOS ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=["usuario", "region", "fecha"])
    return pd.read_csv(DATA_FILE)

def save_pain_region(usuario, region):
    df = load_data()
    # Evitar duplicados del mismo usuario en la misma region
    if not ((df['usuario'] == usuario) & (df['region'] == region)).any():
        new_row = {"usuario": usuario, "region": region, "fecha": pd.Timestamp.now()}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        return True
    return False

def clear_data():
    pd.DataFrame(columns=["usuario", "region", "fecha"]).to_csv(DATA_FILE, index=False)

# --- INTERFAZ ---
st.title("🧗 Mapa de Lesiones Bilateral")

col_u, col_a = st.columns(2)
with col_u:
    usuario_activo = st.selectbox("Selecciona tu nombre", list(USERS_CONFIG.keys()))

# Cargar datos
df = load_data()

# --- PREPARAR IMAGEN ---
# Crear lienzo base (Ancho doble para dos vistas)
W, H = 800, 600
try:
    # Intenta cargar imagen 'cuerpo_completo.png' (debe ser 800x600)
    base_img = Image.open("cuerpo_completo.png").convert("RGBA")
except:
    base_img = Image.new('RGBA', (W, H), (240, 240, 240, 255))
    d_temp = ImageDraw.Draw(base_img)
    d_temp.line((400, 0, 400, 600), fill="black", width=2) # Separador
    d_temp.text((10, 10), "VISTA FRONTAL (Anterior)", fill="black")
    d_temp.text((410, 10), "VISTA POSTERIOR (Dorsal)", fill="black")

# Capa de dibujo transparente
overlay = Image.new('RGBA', base_img.size, (0,0,0,0))
draw = ImageDraw.Draw(overlay)

# --- LÓGICA DE DIBUJO ---
# 1. Agrupar dolores por región
dolores_por_region = df.groupby("region")['usuario'].apply(list).to_dict()

# 2. Iterar regiones activas
for region_name, users_list in dolores_por_region.items():
    if region_name in BODY_ZONES:
        polygon = BODY_ZONES[region_name]
        
        # 3. Ordenar usuarios por prioridad (Sólidos primero, tramas después)
        users_sorted = sorted(users_list, key=lambda u: USERS_CONFIG[u]["priority"])
        
        # 4. Dibujar cada capa secuencialmente
        for u in users_sorted:
            draw_layer(draw, polygon, USERS_CONFIG[u])
        
        # Dibujar borde negro final para delimitar el músculo
        draw.polygon(polygon, outline="black", width=1)

# Componer imagen final
final_img = Image.alpha_composite(base_img, overlay)

# --- SISTEMA DE SELECCIÓN (PESTAÑAS) ---
tab1, tab2 = st.tabs(["🖱️ Tocar en Mapa", "📋 Seleccionar de Lista"])

with tab1:
    st.caption("Izquierda: Frente | Derecha: Espalda")
    value = streamlit_image_coordinates(final_img, key="canvas", width=700) # Ajustar width visual

    if value:
        cx, cy = value['x'], value['y']
        # Mapear click a coordenadas reales de imagen (si hay reescalado)
        # Asumimos escala 1:1 para simplificar, si width=700, factor corrección necesario si img es 800
        factor = W / 700 
        real_x, real_y = cx * factor, cy * factor
        
        found = False
        for name, poly in BODY_ZONES.items():
            if point_in_polygon(real_x, real_y, poly):
                if save_pain_region(usuario_activo, name):
                    st.toast(f"Añadido: {name}")
                    st.rerun()
                found = True
                break

with tab2:
    st.write("Selecciona directamente la zona afectada:")
    # Crear lista amigable
    zonas_disponibles = sorted(list(BODY_ZONES.keys()))
    
    # Multiselect para añadir rápido
    seleccion = st.multiselect("Zonas", zonas_disponibles)
    if st.button("Añadir Zonas Seleccionadas"):
        count = 0
        for zona in seleccion:
            if save_pain_region(usuario_activo, zona):
                count += 1
        if count > 0:
            st.success(f"Se han añadido {count} zonas.")
            st.rerun()
        else:
            st.info("Esas zonas ya estaban marcadas.")

# --- DATOS Y BORRADO ---
st.divider()
c1, c2 = st.columns([2, 1])
with c1:
    st.write("### Historial de Dolores")
    # Mostrar tabla más bonita
    if not df.empty:
        st.dataframe(df.pivot_table(index="region", columns="usuario", values="fecha", aggfunc="count").fillna("-"))
    else:
        st.info("Nadie se ha quejado... todavía.")

with c2:
    st.write("### Acciones")
    if st.button("🗑️ Borrar Todo", type="primary"):
        clear_data()
        st.rerun()
