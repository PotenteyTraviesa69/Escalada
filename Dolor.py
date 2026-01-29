import streamlit as st
import pandas as pd
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Me duele el hombro", layout="centered")
DATA_FILE = "dolores_escalada.csv"

# --- 1. DEFINICIÓN DE REGIONES ---
ZONAS_MUSCULARES = {
    # --- VISTA FRONTAL ---
    "F_Pectoral_Izq": [(317, 337), (303, 409), (308, 452), (337, 476), (382, 478), (418, 449), (433, 418), (435, 366), (416, 344), (356, 322)],
    "F_Pectoral_Der": [(166,389),(195,470),(225,490),(288,473),(290,411),(274,365),(283,336),(216,338)],
    "F_Abdominales": [(245, 493), (240, 534), (238, 618), (241, 651), (286, 793), (320, 793), (365, 665), (365, 632), (370, 584), (373, 541), (360, 480), (308, 473)],
    "F_Hombro_Der": [(118, 447), (106, 430), (104, 402), (114, 360), (140, 330), (169, 317), (209, 332), (162, 382), (152, 409)],
    "F_Hombro_Izq": [(375, 324), (423, 336), (444, 368), (447, 392), (486, 435), (502, 454), (505, 397), (495, 354), (471, 324), (442, 305)],
    "F_Biceps_Der": [(114, 462), (162, 408), (181, 476), (157, 536), (130, 574), (106, 581), (90, 507)],
    "F_Biceps_Izq": [(442, 397), (493, 452), (514, 464), (526, 522), (504, 560), (468, 546), (445, 505), (437, 440)],
    "F_Antebrazo_Izq": [(459, 546), (502, 565), (528, 531), (541, 567), (545, 605), (562, 701), (541, 694), (521, 702), (480, 639), (466, 603)],
    "F_Antebrazo_Der": [(80, 543), (68, 579), (53, 730), (72, 730), (90, 735), (133, 661), (150, 594), (152, 555), (114, 603), (101, 581)],
    "F_Cuadriceps_Izq": [(432, 738), (330, 860), (363, 975), (394, 1076), (423, 1080), (426, 1035), (461, 1026), (473, 1068), (486, 1011), (480, 901), (459, 804)],
    "F_Cuadriceps_Der": [(183, 740), (305, 869), (305, 908), (293, 990), (293, 1062), (246, 1088), (228, 1028), (200, 1026), (195, 1066), (178, 1013), (166, 936), (164, 857)],
    "F_Cuello": [(253, 241), (291, 236), (322, 264), (346, 265), (344, 315), (296, 332), (260, 329), (257, 284)],
    "F_Oblicuos_Der": [(219, 500), (197, 516), (204, 584), (197, 642), (222, 687), (226, 630), (229, 553)],
    "F_Oblicuos_Izq": [(377, 490), (382, 548), (377, 615), (373, 696), (421, 670), (416, 613), (428, 540), (438, 502), (430, 454)],

    # --- VISTA POSTERIOR ---
    "P_Trapecio_Izq": [(929, 212), (912, 246), (884, 272), (831, 294), (884, 313), (894, 334), (894, 387), (893, 428), (906, 476), (927, 545), (951, 414), (951, 320), (934, 248)],
    "P_Trapecio_Der": [(954, 216), (948, 245), (960, 317), (965, 413), (949, 548), (984, 495), (1016, 447), (1025, 396), (1021, 342), (1052, 320), (1002, 293), (972, 264)],
    "P_Dorsal_Izq": [(834, 433), (862, 437), (884, 433), (898, 483), (922, 552), (889, 594), (867, 636), (857, 677), (822, 596), (805, 545), (829, 492)],
    "P_Dorsal_Der": [(954, 548), (997, 490), (1021, 449), (1042, 454), (1059, 457), (1050, 490), (1035, 529), (1021, 553), (1009, 591), (1006, 651), (997, 685), (982, 668), (984, 615), (966, 579)],
    "P_Triceps_Izq": [(752, 425), (809, 378), (826, 397), (829, 445), (814, 504), (781, 555), (745, 546), (738, 510), (738, 478)],
    "P_Triceps_Der": [(1076, 406), (1092, 399), (1117, 425), (1134, 461), (1136, 500), (1148, 564), (1133, 564), (1119, 582), (1090, 562), (1073, 538), (1054, 490), (1068, 452)],
    "P_Lumbar": [(864, 687), (906, 721), (934, 764), (965, 726), (996, 696), (977, 666), (978, 617), (939, 560), (894, 600), (874, 646)],
    "P_Isquios_Izq": [(788, 805), (812, 862), (845, 858), (888, 858), (877, 942), (860, 1028), (843, 1105), (822, 1047), (798, 1068), (773, 1119), (768, 1008), (764, 917)],
    "P_Isquios_Der": [(918, 843), (958, 860), (1002, 860), (1004, 927), (996, 975), (978, 1064), (966, 1044), (939, 1081), (922, 1119), (898, 1076), (894, 987), (898, 949), (893, 889)],
    "P_Gemelo_Izq": [(774, 1128), (802, 1081), (822, 1102), (841, 1112), (855, 1224), (841, 1280), (793, 1268), (762, 1198)],
    "P_Gemelo_Der": [(920, 1124), (948, 1080), (978, 1073), (994, 1116), (1014, 1162), (1016, 1229), (972, 1239), (946, 1254), (927, 1194)],
    "P_Gluteo_Izq": [(809, 774), (828, 822), (864, 852), (908, 822), (925, 800), (908, 735), (872, 706), (831, 682), (816, 740)],
    "P_Gluteo_Der": [(937, 774), (924, 831), (958, 853), (1004, 838), (1023, 810), (1020, 764), (1016, 708), (1013, 682), (996, 708), (965, 744)],
    "P_Infraespinoso_Izq": [(828, 344), (819, 372), (833, 396), (838, 421), (882, 421), (888, 385), (881, 334), (857, 339)],
    "P_Infraespinoso_Der": [(1028, 354), (1030, 389), (1025, 438), (1064, 450), (1071, 406), (1090, 392), (1071, 368)],
}

ZONAS_ARTICULARES = {
    # --- VISTA FRONTAL ---
    "F_Muneca_Izq": [(509, 708), (541, 702), (574, 708), (576, 740), (543, 737), (512, 740)],
    "F_Muneca_Der": [(41, 732), (68, 735), (97, 740), (96, 774), (70, 768), (41, 776)],
    "F_Rodilla_Izq": [(408, 1136), (438, 1174), (464, 1181), (473, 1109), (476, 1080), (452, 1050), (433, 1050), (433, 1092)],
    "F_Rodilla_Der": [(205, 1047), (224, 1052), (241, 1093), (267, 1122), (248, 1189), (222, 1189), (200, 1116)],
    "F_Tobillo_Izq": [(447, 1350), (476, 1357), (493, 1350), (498, 1392), (476, 1395), (449, 1385)],
    "F_Tobillo_Der": [(212, 1361), (234, 1364), (257, 1350), (267, 1397), (240, 1398), (210, 1392)],
    "F_Cadera_Izq": [(315, 822), (372, 706), (420, 685), (430, 711), (337, 838)],
    "F_Cadera_Der": [(305, 826), (289, 843), (188, 728), (195, 682), (229, 696)],
    "F_Dedos_Pie_Der": [(171, 1469), (195, 1465), (216, 1467), (231, 1486), (204, 1498), (181, 1493), (166, 1489)],
    "F_Dedos_Pie_Izq": [(541, 1462), (541, 1476), (567, 1481), (582, 1472), (577, 1448), (560, 1452)],
    "F_Dedos_Mano_Der": [(42, 826), (73, 807), (102, 785), (123, 840), (114, 882), (80, 889)],
    "F_Dedos_Mano_Izq": [(509, 757), (550, 774), (582, 780), (579, 824), (560, 848), (522, 852), (498, 817)],

    # --- VISTA POSTERIOR ---
    "P_Hombro_Der": [(1028, 341), (1078, 365), (1114, 416), (1116, 366), (1090, 324), (1066, 324)],
    "P_Hombro_Izq": [(761, 332), (749, 370), (750, 416), (795, 377), (824, 339), (884, 324), (814, 300)],
    "P_Codo_Izq": [(744, 552), (721, 576), (747, 608), (781, 610), (783, 569)],
    "P_Codo_Der": [(1150, 572), (1133, 574), (1117, 586), (1109, 603), (1129, 618), (1155, 603)],
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
st.title("🧗 Dolores del roco tronko")

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
    draw.polygon(poly, outline="yellow", width=5)

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
