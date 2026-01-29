import streamlit as st
import pandas as pd
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import gspread
import json

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Me duele el hombro", layout="centered")

# --- CONEXIÓN CON GOOGLE SHEETS (MÉTODO MODERNO) ---
@st.cache_resource
def get_google_sheet():
    try:
        # 1. Recuperamos el secreto como un diccionario normal
        # Usamos .get() para evitar errores si la clave no existe, aunque debería
        creds_dict = dict(st.secrets["gcp_service_account"])

        # 2. PARCHE IMPORTANTE: Arreglar el formato de la clave privada
        # Streamlit a veces interpreta el "\n" como texto literal en lugar de salto de línea.
        # Esto lo corrige automáticamente:
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        # 3. Autenticación nativa de gspread (sin oauth2client)
        gc = gspread.service_account_from_dict(creds_dict)

        # 4. Abrir la hoja
        sh = gc.open("dolores_escalada") # Asegúrate que este nombre es EXACTO al de tu Drive
        return sh.sheet1
        
    except Exception as e:
        st.error(f"❌ Error crítico de conexión: {e}")
        return None
        
# --- 1. DEFINICIÓN DE REGIONES (ZONAS) ---
# ... (MANTÉN TUS DICCIONARIOS ZONAS_MUSCULARES, ZONAS_ARTICULARES Y USERS_CONFIG AQUÍ IGUAL QUE ANTES) ...
# Para ahorrar espacio en la respuesta, asumo que copias aquí tus diccionarios ZONAS_...
# COPIA AQUÍ TUS VARIABLES ZONAS_MUSCULARES, ZONAS_ARTICULARES, ETC.
# ---------------------------------------------------------------------------------
# ⬇️ SOLO A MODO DE EJEMPLO PONGO UNOS POCOS, TÚ PEGA LOS TUYOS COMPLETOS ⬇️
ZONAS_MUSCULARES = {
    "F_Pectoral_Izq": [(317, 337), (303, 409), (308, 452), (337, 476), (382, 478), (418, 449), (433, 418), (435, 366), (416, 344), (356, 322)],
    # ... PEGA EL RESTO ...
}
ZONAS_ARTICULARES = {
    "F_Muneca_Izq": [(509, 708), (541, 702), (574, 708), (576, 740), (543, 737), (512, 740)],
    # ... PEGA EL RESTO ...
}
# ---------------------------------------------------------------------------------

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

# --- NUEVAS FUNCIONES DE DATOS (GOOGLE SHEETS) ---

def load_data():
    """Descarga los datos de Google Sheets."""
    try:
        sheet = get_google_sheet()
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        # Asegurar columnas si está vacía
        if df.empty:
            return pd.DataFrame(columns=["x", "y", "usuario", "tipo", "region", "fecha"])
        return df
    except Exception as e:
        st.error(f"Error conectando con Google Sheets: {e}")
        return pd.DataFrame(columns=["x", "y", "usuario", "tipo", "region", "fecha"])

def save_pain(x, y, usuario, tipo, region=None):
    """Guarda el dolor añadiendo una fila a Google Sheets."""
    print(f"DEBUG: Intentando guardar para {usuario}")
    df = load_data()
    
    # Comprobar duplicados
    duplicate = False
    if region and not df.empty:
        # Convertimos a string para comparar fácil con lo que viene de sheets
        duplicate = not df[(df['usuario'] == usuario) & (df['region'] == region) & (df['tipo'] == tipo)].empty
    
    if not duplicate:
        try:
            sheet = get_google_sheet()
            fecha = str(pd.Timestamp.now())
            # Añadir fila al final
            sheet.append_row([x, y, usuario, tipo, region, fecha])
            # Limpiar caché de datos para que al recargar aparezca el nuevo
            st.cache_data.clear()
            return True
        except Exception as e:
            st.error(f"Error guardando en la nube: {e}")
            return False
    else:
        print("DEBUG: Duplicado.")
        return False

def undo_last_pain():
    """Borra la última fila de la Google Sheet."""
    try:
        sheet = get_google_sheet()
        # Obtener número de filas
        row_count = len(sheet.get_all_values())
        if row_count > 1: # Asumiendo que la fila 1 son encabezados
            sheet.delete_rows(row_count)
            st.cache_data.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Error al deshacer: {e}")
        return False

# ... (MANTÉN LA FUNCIÓN draw_pattern_in_region IGUAL) ...
def draw_pattern_in_region(draw_ctx, polygon, user_pattern, color_rgb):
    # Pega aquí tu función draw_pattern_in_region original
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
st.title("🧗 Dolores del roco tronko (Cloud Edition)")

if 'last_click_coords' not in st.session_state:
    st.session_state['last_click_coords'] = None

# --- SELECTORES ---
c1, c2 = st.columns(2)
with c1:
    usuario_activo = st.selectbox("Usuario", list(USERS_CONFIG.keys()))
with c2:
    tipo_dolor = st.selectbox("Tipo de Dolor", ["Músculo", "Articulación", "Herida"])

# --- BOTÓN DESHACER ---
c_undo, c_dummy = st.columns([1, 3])
with c_undo:
    if st.button("↩️ Deshacer último", help="Borra el último dolor registrado en la nube"):
        if undo_last_pain():
            st.toast("Último registro eliminado de la nube")
            st.rerun()
        else:
            st.warning("No se pudo deshacer.")

# --- IMAGEN ---
W, H = 1200, 1600
try:
    base_img = Image.open("cuerpo.jpg").convert("RGBA")
except:
    base_img = Image.new('RGBA', (W, H), (240, 240, 240, 255))
    d = ImageDraw.Draw(base_img)
    d.text((10,10), "ERROR: Sube 'cuerpo.jpg'", fill="red")

overlay = Image.new('RGBA', base_img.size, (0,0,0,0))
draw = ImageDraw.Draw(overlay)

# Cargar datos desde Google Sheets
df = load_data()

# 1. DIBUJAR CAPAS
# Une tus diccionarios
ALL_ZONES = {**ZONAS_MUSCULARES, **ZONAS_ARTICULARES}

if not df.empty:
    regiones_activas = df[df['tipo'].isin(["Músculo", "Articulación"])]
    if not regiones_activas.empty:
        # Aseguramos que 'region' existe y agrupamos
        mapa_dolor = regiones_activas.groupby("region").apply(lambda x: x[['usuario', 'tipo']].to_dict('records')).to_dict()

        for region_name, entries in mapa_dolor.items():
            if region_name in ALL_ZONES:
                poly = ALL_ZONES[region_name]
                entries_sorted = sorted(entries, key=lambda x: USERS_CONFIG.get(x['usuario'], {"priority":99})["priority"])
                
                for entry in entries_sorted:
                    u_name = entry['usuario']
                    t_dolor = entry['tipo']
                    color = TYPE_COLORS.get(t_dolor, (0,0,0))
                    # Fallback por si hay usuarios viejos en csv
                    pattern = USERS_CONFIG.get(u_name, {"pattern": "solid"})["pattern"]
                    draw_pattern_in_region(draw, poly, pattern, color)

    # 2. DIBUJAR HERIDAS
    heridas = df[df['tipo'] == "Herida"]
    for _, row in heridas.iterrows():
        try:
            cx, cy = float(row['x']), float(row['y'])
            draw.ellipse((cx-5, cy-5, cx+5, cy+5), fill=(255, 0, 0, 255), outline="white", width=2)
        except:
            pass

# 3. ZONAS ACTIVAS (BORDES AMARILLOS)
zones_to_check = {}
if tipo_dolor == "Músculo":
    zones_to_check = ZONAS_MUSCULARES
elif tipo_dolor == "Articulación":
    zones_to_check = ZONAS_ARTICULARES
else:
    zones_to_check = ALL_ZONES

for name, poly in zones_to_check.items():
    draw.polygon(poly, outline="yellow", width=5)

final_img = Image.alpha_composite(base_img, overlay)

# --- INTERACCIÓN ---
st.info(f"Marcando: {tipo_dolor}. Los datos se guardan en Google Sheets.")
value = streamlit_image_coordinates(final_img, key="main_canvas", width=700)

if value:
    current_coords = (value['x'], value['y'])
    
    if st.session_state['last_click_coords'] != current_coords:
        st.session_state['last_click_coords'] = current_coords
        
        click_x = value['x'] * (W/700) 
        click_y = value['y'] * (W/700)
        
        if tipo_dolor == "Herida":
            if save_pain(click_x, click_y, usuario_activo, "Herida"):
                st.toast("Herida guardada en la nube")
                st.rerun()
            else:
                st.error("Error guardando herida")

        else:
            found = False
            for name, poly in zones_to_check.items():
                if point_in_polygon(click_x, click_y, poly):
                    if save_pain(click_x, click_y, usuario_activo, tipo_dolor, region=name):
                        st.toast(f"Guardado: {name}")
                    else:
                        st.toast("Dolor ya registrado o error de conexión")
                    found = True
                    st.rerun()
                    break
            
            if not found:
                st.warning(f"Click fuera de zona {tipo_dolor} válida.")

# --- DATOS ---
st.divider()

if not df.empty:
    st.write("### Historial (Google Sheets)")
    st.dataframe(df[['fecha', 'usuario', 'tipo', 'region']].tail(5).sort_values("fecha", ascending=False))
