# pip install Pillow
"""
Paralelismo de modelo: un modelo de 175B parámetros no cabe en una sola GPU,
así que se reparte en 8 GPUs de 22B conectadas por una interconexión de alta
velocidad.

Diagrama de bloques horizontal, tema oscuro y neón:
    - Cubo grande a la izquierda: modelo completo (175B).
    - Flecha de partición hacia la derecha.
    - 8 cubos pequeños: GPUs 1..8, cada una con 22B parámetros.
    - Bus punteado magenta sobre la fila: comunicación de alta velocidad.

Salida: images/model_parallelism.avif  (1800 x 940, RGB, calidad 92)
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# 1. Lienzo y sistema de diseño
# ---------------------------------------------------------------------------
W, H = 1800, 940

BG = "#060A12"
CYAN = "#22D3EE"
CYAN_BRIGHT = "#67E8F9"
CYAN_DARK = "#0E7490"
MAGENTA = "#FF36C8"
MAGENTA_SOFT = "#F0ABFC"
WARNING = "#FF4D6D"
WARNING_SOFT = "#FFB3C1"
TEXT = "#E7EEF7"
MUTED = "#9FB0C7"
SLATE = "#64748B"
LINE = "#16233A"


def rgb(hex_color):
    """Convierte #RRGGBB en una tupla RGB."""
    value = hex_color.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def mix(c1, c2, t):
    """Interpola linealmente dos colores RGB."""
    t = max(0.0, min(1.0, t))
    return tuple(round(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


BG_RGB = rgb(BG)
CYAN_RGB = rgb(CYAN)
CYAN_BRIGHT_RGB = rgb(CYAN_BRIGHT)
CYAN_DARK_RGB = rgb(CYAN_DARK)
MAGENTA_RGB = rgb(MAGENTA)
MAGENTA_SOFT_RGB = rgb(MAGENTA_SOFT)
WARNING_RGB = rgb(WARNING)
WARNING_SOFT_RGB = rgb(WARNING_SOFT)
TEXT_RGB = rgb(TEXT)
MUTED_RGB = rgb(MUTED)
SLATE_RGB = rgb(SLATE)
LINE_RGB = rgb(LINE)


# ---------------------------------------------------------------------------
# 2. Tipografía
# ---------------------------------------------------------------------------
def load_font(size, bold=False):
    """Usa Arial/Helvetica si existe; si no, una fuente del sistema."""
    candidates = (
        [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        if bold
        else [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for name in candidates:
        if Path(name).exists():
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


F_TITLE = load_font(38, bold=True)
F_TITLE_2 = load_font(44, bold=True)
F_SUBTITLE = load_font(20)
F_SECTION = load_font(15, bold=True)
F_MODEL_SIZE = load_font(86, bold=True)
F_MODEL_UNIT = load_font(18)
F_GPU_NAME = load_font(13, bold=True)
F_GPU_SIZE = load_font(28, bold=True)
F_GPU_UNIT = load_font(11)
F_WARN = load_font(17, bold=True)
F_LINK = load_font(16)
F_LINK_BOLD = load_font(16, bold=True)
F_NOTE = load_font(14)


# ---------------------------------------------------------------------------
# 3. Utilidades de dibujo
# ---------------------------------------------------------------------------
def text_with_shadow(draw, xy, text, font, fill, anchor="la",
                     shadow=(2, 5, 10), offset=(0, 2)):
    """Texto con una sombra sutil para mejorar el contraste."""
    draw.text(
        (xy[0] + offset[0], xy[1] + offset[1]),
        text, font=font, fill=shadow, anchor=anchor,
    )
    draw.text(xy, text, font=font, fill=fill, anchor=anchor)


def vertical_gradient(w, h, top_color, bottom_color):
    """Devuelve una imagen RGBA con un degradado vertical."""
    gradient = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gradient)
    for y in range(h):
        t = y / max(1, h - 1)
        color = mix(top_color, bottom_color, t)
        gd.line([(0, y), (w, y)], fill=color + (255,))
    return gradient


def horizontal_gradient(w, h, left_color, right_color):
    """Devuelve una imagen RGBA con un degradado horizontal."""
    gradient = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gradient)
    for x in range(w):
        t = x / max(1, w - 1)
        color = mix(left_color, right_color, t)
        gd.line([(x, 0), (x, h)], fill=color + (255,))
    return gradient


def cube_geometry(x, y, w, h, depth):
    """Devuelve las tres caras de un cubo isométrico simple."""
    front = (x, y, x + w, y + h)
    top = [
        (x, y),
        (x + depth, y - depth),
        (x + w + depth, y - depth),
        (x + w, y),
    ]
    side = [
        (x + w, y),
        (x + w + depth, y - depth),
        (x + w + depth, y + h - depth),
        (x + w, y + h),
    ]
    return front, top, side


def draw_cube(image, x, y, w, h, depth, top_fill, side_fill,
              front_top, front_bottom, edge, edge_width=1.5):
    """Dibuja un cubo 3D con la cara frontal en degradado y aristas neón."""
    front, top, side = cube_geometry(x, y, w, h, depth)
    draw = ImageDraw.Draw(image)

    draw.polygon(top, fill=top_fill + (255,))
    draw.polygon(side, fill=side_fill + (255,))

    gradient = vertical_gradient(w, h, front_top, front_bottom)
    image.alpha_composite(gradient, (x, y))

    draw.rectangle(front, outline=edge + (255,), width=int(edge_width))
    draw.line(top + [top[0]], fill=edge + (190,), width=1)
    draw.line(side + [side[0]], fill=edge + (130,), width=1)

    # Pequeño brillo en la arista superior frontal.
    draw.line(
        [(x, y), (x + w, y)],
        fill=mix(edge, (255, 255, 255), 0.55) + (180,),
        width=1,
    )


def dotted_h(draw, x0, x1, y, color, spacing=12, radius=2.2):
    """Línea horizontal de puntos."""
    steps = max(1, int(abs(x1 - x0) / spacing))
    for i in range(steps + 1):
        x = x0 + (x1 - x0) * i / steps
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=color,
        )


def dotted_v(draw, x, y0, y1, color, spacing=8, radius=1.6):
    """Línea vertical de puntos."""
    steps = max(1, int(abs(y1 - y0) / spacing))
    for i in range(steps + 1):
        y = y0 + (y1 - y0) * i / steps
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=color,
        )


# ---------------------------------------------------------------------------
# 4. Fondo: rejilla tenue, halos neón y marco
# ---------------------------------------------------------------------------
image = Image.new("RGBA", (W, H), BG_RGB + (255,))
draw = ImageDraw.Draw(image)

# Rejilla de puntos muy sutil.
for gy in range(28, H - 18, 44):
    for gx in range(28, W - 18, 44):
        draw.ellipse((gx, gy, gx + 2, gy + 2), fill=(16, 27, 43, 255))

# Halos de color de fondo.
bg_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(bg_glow)
gd.ellipse((640, 230, 1800, 780), fill=CYAN_RGB + (16,))
gd.ellipse((60, 250, 560, 760), fill=CYAN_RGB + (12,))
gd.ellipse((470, 300, 790, 650), fill=MAGENTA_RGB + (28,))
gd.ellipse((520, -220, 1300, 240), fill=CYAN_RGB + (10,))
bg_glow = bg_glow.filter(ImageFilter.GaussianBlur(110))
image = Image.alpha_composite(image, bg_glow)

draw = ImageDraw.Draw(image)

# Marco exterior.
draw.rounded_rectangle(
    (22, 22, W - 22, H - 22),
    radius=26,
    outline=LINE_RGB + (190,),
    width=1,
)

# ---------------------------------------------------------------------------
# 5. Titular y subtítulo
# ---------------------------------------------------------------------------
text_with_shadow(
    draw,
    (W // 2, 48),
    "Paralelismo de Modelo:",
    F_TITLE,
    CYAN_RGB + (255,),
    anchor="mt",
)
text_with_shadow(
    draw,
    (W // 2, 98),
    "Dividir el modelo para entrenarlo",
    F_TITLE_2,
    TEXT_RGB + (255,),
    anchor="mt",
)
draw.text(
    (W // 2, 162),
    "Cientos de GPUs coordinadas trabajan como una sola unidad",
    font=F_SUBTITLE,
    fill=MUTED_RGB + (255,),
    anchor="mt",
)

# Línea de acento cian -> magenta bajo el subtítulo.
accent_w, accent_h = 180, 2
accent = horizontal_gradient(accent_w, accent_h, CYAN_RGB, MAGENTA_RGB)
image.alpha_composite(accent, (W // 2 - accent_w // 2, 199))

# ---------------------------------------------------------------------------
# 6. Modelo grande a la izquierda
# ---------------------------------------------------------------------------
MODEL_X, MODEL_Y = 140, 310
MODEL_W, MODEL_H, MODEL_DEPTH = 300, 320, 60

model_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
mgd = ImageDraw.Draw(model_glow)
front, top, side = cube_geometry(
    MODEL_X, MODEL_Y, MODEL_W, MODEL_H, MODEL_DEPTH
)
mgd.rectangle(front, outline=CYAN_RGB + (150,), width=7)
mgd.line(top + [top[0]], fill=CYAN_RGB + (130,), width=6)
mgd.line(side + [side[0]], fill=CYAN_RGB + (90,), width=6)
model_glow = model_glow.filter(ImageFilter.GaussianBlur(20))
image = Image.alpha_composite(image, model_glow)
draw = ImageDraw.Draw(image)

draw_cube(
    image,
    MODEL_X, MODEL_Y, MODEL_W, MODEL_H, MODEL_DEPTH,
    top_fill=(14, 43, 59),
    side_fill=(4, 16, 26),
    front_top=(12, 34, 51),
    front_bottom=(6, 16, 25),
    edge=CYAN_RGB,
    edge_width=2,
)
draw = ImageDraw.Draw(image)

# Detalle de chip: rejilla apenas visible y esquinas marcadas.
for gx in (MODEL_X + MODEL_W // 4,
           MODEL_X + MODEL_W // 2,
           MODEL_X + 3 * MODEL_W // 4):
    draw.line(
        [(gx, MODEL_Y + 18), (gx, MODEL_Y + MODEL_H - 18)],
        fill=CYAN_RGB + (16,),
        width=1,
    )
for gy in (MODEL_Y + MODEL_H // 4,
           MODEL_Y + MODEL_H // 2,
           MODEL_Y + 3 * MODEL_H // 4):
    draw.line(
        [(MODEL_X + 18, gy), (MODEL_X + MODEL_W - 18, gy)],
        fill=CYAN_RGB + (16,),
        width=1,
    )

inset = 16
bracket = 24
for bx, by, dx, dy in (
    (MODEL_X + inset, MODEL_Y + inset, 1, 1),
    (MODEL_X + MODEL_W - inset, MODEL_Y + inset, -1, 1),
    (MODEL_X + inset, MODEL_Y + MODEL_H - inset, 1, -1),
    (MODEL_X + MODEL_W - inset, MODEL_Y + MODEL_H - inset, -1, -1),
):
    draw.line(
        [(bx, by), (bx + dx * bracket, by)],
        fill=CYAN_BRIGHT_RGB + (150,),
        width=2,
    )
    draw.line(
        [(bx, by), (bx, by + dy * bracket)],
        fill=CYAN_BRIGHT_RGB + (150,),
        width=2,
    )

# Etiquetas del modelo.
draw.text(
    (MODEL_X + MODEL_W // 2, MODEL_Y + 88),
    "M O D E L O",
    font=F_SECTION,
    fill=CYAN_BRIGHT_RGB + (255,),
    anchor="mm",
)
text_with_shadow(
    draw,
    (MODEL_X + MODEL_W // 2, MODEL_Y + 170),
    "175B",
    F_MODEL_SIZE,
    TEXT_RGB + (255,),
    anchor="mm",
    shadow=(2, 7, 12),
    offset=(0, 3),
)
draw.text(
    (MODEL_X + MODEL_W // 2, MODEL_Y + 232),
    "parámetros",
    font=F_MODEL_UNIT,
    fill=MUTED_RGB + (255,),
    anchor="mm",
)

# ---------------------------------------------------------------------------
# 7. Aviso: el modelo no cabe en una GPU
# ---------------------------------------------------------------------------
PILL_X, PILL_Y, PILL_W, PILL_H = 140, 672, 360, 58

warning_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
wgd = ImageDraw.Draw(warning_glow)
wgd.rounded_rectangle(
    (PILL_X, PILL_Y, PILL_X + PILL_W, PILL_Y + PILL_H),
    radius=PILL_H // 2,
    outline=WARNING_RGB + (140,),
    width=4,
)
warning_glow = warning_glow.filter(ImageFilter.GaussianBlur(14))
image = Image.alpha_composite(image, warning_glow)
draw = ImageDraw.Draw(image)

draw.rounded_rectangle(
    (PILL_X, PILL_Y, PILL_X + PILL_W, PILL_Y + PILL_H),
    radius=PILL_H // 2,
    fill=(42, 11, 20, 255),
    outline=WARNING_RGB + (255,),
    width=2,
)
draw.line(
    [(PILL_X + 24, PILL_Y + 1), (PILL_X + PILL_W - 24, PILL_Y + 1)],
    fill=WARNING_SOFT_RGB + (46,),
    width=1,
)

warning_text = "NO CABE EN 1 GPU"
warning_tw = draw.textlength(warning_text, font=F_WARN)
icon_d = 18
gap = 11
group_w = icon_d + gap + warning_tw
group_x = PILL_X + PILL_W / 2 - group_w / 2
icon_cx = group_x + icon_d / 2
icon_cy = PILL_Y + PILL_H / 2
draw.ellipse(
    (icon_cx - icon_d / 2, icon_cy - icon_d / 2,
     icon_cx + icon_d / 2, icon_cy + icon_d / 2),
    outline=WARNING_RGB + (255,),
    width=2,
)
draw.line(
    [(icon_cx - 6, icon_cy - 6), (icon_cx + 6, icon_cy + 6)],
    fill=WARNING_RGB + (255,),
    width=2,
)
draw.text(
    (group_x + icon_d + gap, icon_cy),
    warning_text,
    font=F_WARN,
    fill=WARNING_SOFT_RGB + (255,),
    anchor="lm",
)

# ---------------------------------------------------------------------------
# 8. Flecha de partición
# ---------------------------------------------------------------------------
ARROW_X0, ARROW_X1 = 530, 690
ARROW_Y = 470
shaft = 19
head_half = 42
head_len = 45

arrow_points = [
    (ARROW_X0, ARROW_Y - shaft),
    (ARROW_X1 - head_len, ARROW_Y - shaft),
    (ARROW_X1 - head_len, ARROW_Y - head_half),
    (ARROW_X1, ARROW_Y),
    (ARROW_X1 - head_len, ARROW_Y + head_half),
    (ARROW_X1 - head_len, ARROW_Y + shaft),
    (ARROW_X0, ARROW_Y + shaft),
]

arrow_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
agd = ImageDraw.Draw(arrow_glow)
agd.polygon(arrow_points, fill=MAGENTA_RGB + (120,))
arrow_glow = arrow_glow.filter(ImageFilter.GaussianBlur(18))
image = Image.alpha_composite(image, arrow_glow)

arrow_w = ARROW_X1 - ARROW_X0 + 8
arrow_h = 2 * head_half + 8
arrow_layer = horizontal_gradient(arrow_w, arrow_h, CYAN_RGB, MAGENTA_RGB)
arrow_mask = Image.new("L", (arrow_w, arrow_h), 0)
amd = ImageDraw.Draw(arrow_mask)
amd.polygon(
    [(px - ARROW_X0 + 4, py - (ARROW_Y - head_half) + 4)
     for px, py in arrow_points],
    fill=255,
)
arrow_layer.putalpha(arrow_mask)
image.alpha_composite(
    arrow_layer, (ARROW_X0 - 4, ARROW_Y - head_half - 4)
)

draw = ImageDraw.Draw(image)
draw.text(
    ((ARROW_X0 + ARROW_X1) // 2, 407),
    "dividir",
    font=F_LINK,
    fill=MAGENTA_SOFT_RGB + (230,),
    anchor="mm",
)

# ---------------------------------------------------------------------------
# 9. Ocho GPUs en fila
# ---------------------------------------------------------------------------
GPU_COUNT = 8
GPU_X0 = 720
GPU_STEP = 128
GPU_Y = 405
GPU_W, GPU_H, GPU_DEPTH = 100, 130, 16

gpu_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ggd = ImageDraw.Draw(gpu_glow)
for i in range(GPU_COUNT):
    x = GPU_X0 + i * GPU_STEP
    front, top, side = cube_geometry(x, GPU_Y, GPU_W, GPU_H, GPU_DEPTH)
    ggd.rectangle(front, outline=CYAN_RGB + (95,), width=4)
    ggd.line(top + [top[0]], fill=CYAN_RGB + (80,), width=3)
    ggd.line(side + [side[0]], fill=CYAN_RGB + (60,), width=3)
gpu_glow = gpu_glow.filter(ImageFilter.GaussianBlur(10))
image = Image.alpha_composite(image, gpu_glow)

for i in range(GPU_COUNT):
    x = GPU_X0 + i * GPU_STEP
    draw_cube(
        image,
        x, GPU_Y, GPU_W, GPU_H, GPU_DEPTH,
        top_fill=(14, 43, 59),
        side_fill=(4, 16, 26),
        front_top=(11, 31, 46),
        front_bottom=(6, 16, 25),
        edge=CYAN_RGB,
        edge_width=1,
    )
    draw = ImageDraw.Draw(image)

    # LED de actividad.
    led_x, led_y = x + GPU_W - 13, GPU_Y + 14
    draw.ellipse(
        (led_x - 3, led_y - 3, led_x + 3, led_y + 3),
        fill=CYAN_BRIGHT_RGB + (255,),
    )

    draw.text(
        (x + GPU_W // 2, GPU_Y + 32),
        f"GPU {i + 1}",
        font=F_GPU_NAME,
        fill=CYAN_BRIGHT_RGB + (255,),
        anchor="mm",
    )
    draw.text(
        (x + GPU_W // 2, GPU_Y + 78),
        "22B",
        font=F_GPU_SIZE,
        fill=TEXT_RGB + (255,),
        anchor="mm",
    )
    draw.text(
        (x + GPU_W // 2, GPU_Y + 109),
        "parámetros",
        font=F_GPU_UNIT,
        fill=MUTED_RGB + (255,),
        anchor="mm",
    )

# ---------------------------------------------------------------------------
# 10. Bus de comunicación de alta velocidad
# ---------------------------------------------------------------------------
BUS_Y = 355
bus_x0 = GPU_X0 + GPU_W // 2 + 8
bus_x1 = GPU_X0 + (GPU_COUNT - 1) * GPU_STEP + GPU_W // 2 + 8

bus_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bgd = ImageDraw.Draw(bus_glow)
dotted_h(bgd, bus_x0, bus_x1, BUS_Y, MAGENTA_RGB + (150,), spacing=10, radius=4)
for i in range(GPU_COUNT):
    cx = GPU_X0 + i * GPU_STEP + GPU_W // 2 + 8
    bgd.ellipse((cx - 7, BUS_Y - 7, cx + 7, BUS_Y + 7), fill=MAGENTA_RGB + (170,))
bus_glow = bus_glow.filter(ImageFilter.GaussianBlur(8))
image = Image.alpha_composite(image, bus_glow)

draw = ImageDraw.Draw(image)
dotted_h(draw, bus_x0, bus_x1, BUS_Y, MAGENTA_RGB + (255,), spacing=12, radius=2.2)

for i in range(GPU_COUNT):
    cx = GPU_X0 + i * GPU_STEP + GPU_W // 2 + 8
    # Bajante punteado hasta la cara superior del cubo.
    dotted_v(
        draw, cx, BUS_Y + 6, GPU_Y - GPU_DEPTH - 2,
        MAGENTA_RGB + (190,), spacing=7, radius=1.5,
    )
    draw.ellipse(
        (cx - 5, BUS_Y - 5, cx + 5, BUS_Y + 5),
        fill=MAGENTA_RGB + (255,),
    )
    draw.ellipse(
        (cx - 2, BUS_Y - 2, cx + 2, BUS_Y + 2),
        fill=(255, 228, 251, 255),
    )

draw.text(
    ((bus_x0 + bus_x1) // 2, 320),
    "Comunicación de alta velocidad",
    font=F_LINK,
    fill=MAGENTA_SOFT_RGB + (255,),
    anchor="mm",
)

# ---------------------------------------------------------------------------
# 11. Resumen de la fila de GPUs
# ---------------------------------------------------------------------------
summary_y = 565
draw.line(
    [(bus_x0, summary_y), (bus_x1, summary_y)],
    fill=CYAN_DARK_RGB + (160,),
    width=1,
)
for x in (bus_x0, bus_x1):
    draw.line([(x, summary_y), (x, summary_y + 7)], fill=CYAN_DARK_RGB + (160,), width=1)

draw.text(
    ((bus_x0 + bus_x1) // 2, summary_y + 19),
    "8 GPUs  ·  22B cada una  ·  ≈175B en total",
    font=F_NOTE,
    fill=MUTED_RGB + (255,),
    anchor="mm",
)

# ---------------------------------------------------------------------------
# 12. Pie de figura
# ---------------------------------------------------------------------------
for x in range(140, 1661):
    t = (x - 140) / (1660 - 140)
    alpha = int(120 * (t ** 0.6) * ((1 - t) ** 0.6) / (0.5 ** 1.2))
    if alpha > 0:
        draw.point((x, 800), fill=LINE_RGB + (min(alpha, 150),))

draw.text(
    (W // 2, 835),
    "Cada GPU aloja una parte del modelo; las activaciones se sincronizan en cada paso.",
    font=F_NOTE,
    fill=SLATE_RGB + (255,),
    anchor="mm",
)

# ---------------------------------------------------------------------------
# 13. Exportación AVIF
# ---------------------------------------------------------------------------
output_dir = Path("images")
output_dir.mkdir(exist_ok=True)
output_path = output_dir / "model_parallelism.avif"
preview_path = output_dir / "model_parallelism.png"

final_image = image.convert("RGB")
final_image.save(preview_path)
final_image.save(output_path, format="AVIF", quality=92)

print(f"Imagen guardada en: {output_path}")
print(f"Dimensiones: {final_image.size[0]}x{final_image.size[1]} | Modo: {final_image.mode}")
