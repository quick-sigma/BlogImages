# pip install Pillow
"""
Diagrama horizontal del cuello de botella en una arquitectura
codificador–decodificador.

La secuencia de entrada atraviesa el codificador, se comprime en un único
vector de contexto (el cuello de botella, dibujado como un rectángulo rojo) y
el decodificador intenta reconstruir la secuencia. Los bloques grises
discontinuos representan la información que se pierde.

Salida: images/encoder_decoder_bottleneck.avif  (1800 x 800, RGB, calidad 90)
"""

from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# 1. Lienzo y sistema de diseño
# ---------------------------------------------------------------------------
W, H = 1800, 800

BG = "#0B0F19"
CYAN = "#06B6D4"
BLUE = "#3B82F6"
RED = "#DC2626"
RED_LIGHT = "#F87171"
SLATE = "#475569"
TEXT = "#E2E8F0"
MUTED = "#94A3B8"
LINE = "#1E293B"


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
BLUE_RGB = rgb(BLUE)
RED_RGB = rgb(RED)
RED_LIGHT_RGB = rgb(RED_LIGHT)
SLATE_RGB = rgb(SLATE)
TEXT_RGB = rgb(TEXT)
MUTED_RGB = rgb(MUTED)
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


F_MAIN = load_font(27, bold=True)
F_SECTION = load_font(24, bold=True)
F_SUBTITLE = load_font(14)
F_LABEL = load_font(13, bold=True)
F_SMALL = load_font(12)
F_DIM = load_font(14, bold=True)
F_BOTTLENECK = load_font(20, bold=True)


def text_with_shadow(draw, xy, text, font, fill, anchor="la",
                     shadow=(5, 8, 14), offset=(0, 2)):
    """Texto con una sombra sutil para mejorar el contraste."""
    draw.text(
        (xy[0] + offset[0], xy[1] + offset[1]),
        text, font=font, fill=shadow, anchor=anchor,
    )
    draw.text(xy, text, font=font, fill=fill, anchor=anchor)


# ---------------------------------------------------------------------------
# 3. Utilidades de dibujo
# ---------------------------------------------------------------------------
def vertical_gradient_bar(base, box, top_color, bottom_color,
                          radius=12, alpha=255, border=None):
    """Dibuja una barra vertical con degradado y esquinas redondeadas."""
    x, y, w, h = box
    bar = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bar)
    for py in range(h):
        t = py / max(1, h - 1)
        color = mix(top_color, bottom_color, t)
        bd.line([(0, py), (w, py)], fill=color + (255,))

    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, w - 1, h - 1), radius=radius, fill=255
    )
    bar.putalpha(mask)

    if alpha < 255:
        bar.putalpha(
            bar.getchannel("A").point(lambda p: int(p * alpha / 255))
        )

    if border is not None:
        ImageDraw.Draw(bar).rounded_rectangle(
            (0, 0, w - 1, h - 1), radius=radius, outline=border, width=1
        )

    base.alpha_composite(bar, (x, y))


def draw_arrow(draw, x_start, x_end, y, color, width=3, head=14):
    """Flecha horizontal simple, de izquierda a derecha."""
    shaft_end = x_end - head + 2
    draw.line([(x_start, y), (shaft_end, y)], fill=color, width=width)
    draw.polygon(
        [(x_end, y), (x_end - head, y - head * 0.55), (x_end - head, y + head * 0.55)],
        fill=color,
    )


def draw_dimension_label(draw, center_x, top_y, text, color, tick_color):
    """Etiqueta de longitud centrada sobre una barra, con un pequeño tick."""
    draw.text(
        (center_x, top_y - 9),
        text,
        font=F_DIM,
        fill=color,
        anchor="mb",
    )
    draw.line(
        [(center_x, top_y - 7), (center_x, top_y - 2)],
        fill=tick_color,
        width=1,
    )


# ---------------------------------------------------------------------------
# 4. Fondo
# ---------------------------------------------------------------------------
image = Image.new("RGBA", (W, H), BG_RGB + (255,))
draw = ImageDraw.Draw(image)

# Título y subtítulo general.
text_with_shadow(
    draw,
    (900, 48),
    "El cuello de botella en una arquitectura codificador–decodificador",
    F_MAIN,
    TEXT_RGB,
    anchor="mm",
)
draw.text(
    (900, 86),
    "La secuencia de entrada se comprime en un vector de longitud fija; parte de la información se pierde.",
    font=F_SUBTITLE,
    fill=MUTED_RGB,
    anchor="mm",
)

# Línea de separación muy sutil entre la cabecera y el diagrama.
draw.line([(60, 118), (1740, 118)], fill=LINE_RGB + (120,), width=1)

# ---------------------------------------------------------------------------
# 5. Etiquetas de las dos grandes zonas
# ---------------------------------------------------------------------------
text_with_shadow(draw, (425, 154), "CODIFICADOR", F_SECTION, TEXT_RGB, anchor="mm")
draw.text(
    (425, 182), "compresión", font=F_SMALL, fill=(103, 232, 249), anchor="mm"
)

text_with_shadow(draw, (1355, 154), "DECODIFICADOR", F_SECTION, TEXT_RGB, anchor="mm")
draw.text(
    (1355, 182), "reconstrucción", font=F_SMALL, fill=MUTED_RGB, anchor="mm"
)

# ---------------------------------------------------------------------------
# 6. Entrada: una cuadrícula de tokens cian
# ---------------------------------------------------------------------------
input_columns = (40, 82, 124)
input_rows = (343, 385, 427)
for row_index, y in enumerate(input_rows):
    for col_index, x in enumerate(input_columns):
        tone = CYAN_RGB if (row_index + col_index) % 2 == 0 else mix(CYAN_RGB, BG_RGB, 0.18)
        draw.rounded_rectangle(
            (x, y, x + 30, y + 30),
            radius=5,
            fill=tone + (255,),
            outline=(103, 232, 249),
            width=1,
        )

draw.text((97, 500), "ENTRADA", font=F_LABEL, fill=(103, 232, 249), anchor="mm")
draw.text((97, 519), "9 elementos", font=F_SMALL, fill=(71, 85, 105), anchor="mm")

# ---------------------------------------------------------------------------
# 7. Codificador: cinco barras horizontales que se comprimen
# ---------------------------------------------------------------------------
encoder_heights = (300, 250, 200, 150, 100)
encoder_dims = (512, 256, 128, 64, 32)
encoder_width = 70
encoder_gap = 15
encoder_start_x = 220
encoder_center_y = 400

for index, height in enumerate(encoder_heights):
    x = encoder_start_x + index * (encoder_width + encoder_gap)
    y = encoder_center_y - height // 2
    base_color = mix(CYAN_RGB, BLUE_RGB, index / 4)
    top_color = mix(base_color, (255, 255, 255), 0.10)
    bottom_color = mix(base_color, BG_RGB, 0.22)
    border = mix(base_color, (255, 255, 255), 0.30)
    vertical_gradient_bar(
        image,
        (x, y, encoder_width, height),
        top_color,
        bottom_color,
        radius=12,
        border=border,
    )

# ---------------------------------------------------------------------------
# 8. Cuello de botella: solo un rectángulo rojo
# ---------------------------------------------------------------------------
bottleneck_box = (800, 330, 1000, 470)
bottleneck_dim = 8

# Sombra suave para separar el rectángulo del fondo, sin glow.
shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
sd.rounded_rectangle(
    (bottleneck_box[0] + 5, bottleneck_box[1] + 7,
     bottleneck_box[2] + 5, bottleneck_box[3] + 7),
    radius=14,
    fill=(0, 0, 0, 150),
)
shadow = shadow.filter(ImageFilter.GaussianBlur(8))
image = Image.alpha_composite(image, shadow)

draw = ImageDraw.Draw(image)
draw.rounded_rectangle(
    bottleneck_box,
    radius=14,
    fill=RED_RGB + (255,),
    outline=RED_LIGHT_RGB,
    width=2,
)
text_with_shadow(
    draw,
    (900, 400),
    "CUELLO DE\nBOTELLA",
    F_BOTTLENECK,
    (255, 247, 237),
    anchor="mm",
    shadow=(90, 12, 16),
    offset=(0, 2),
)

# ---------------------------------------------------------------------------
# 9. Decodificador: cinco barras apagadas que se expanden
# ---------------------------------------------------------------------------
decoder_heights = (100, 150, 200, 250, 300)
decoder_dims = (32, 64, 128, 256, 512)
decoder_width = 70
decoder_gap = 15
decoder_start_x = 1150
decoder_center_y = 400

for index, height in enumerate(decoder_heights):
    x = decoder_start_x + index * (decoder_width + decoder_gap)
    y = decoder_center_y - height // 2
    base_color = mix(SLATE_RGB, (100, 116, 139), index / 4)
    top_color = mix(base_color, (226, 232, 240), 0.07)
    bottom_color = mix(base_color, BG_RGB, 0.38)
    border = mix(base_color, (148, 163, 184), 0.35)
    vertical_gradient_bar(
        image,
        (x, y, decoder_width, height),
        top_color,
        bottom_color,
        radius=12,
        alpha=158,
        border=border,
    )

# ---------------------------------------------------------------------------
# 10. Salida degradada: cuadrícula gris con huecos
# ---------------------------------------------------------------------------
out_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
od = ImageDraw.Draw(out_layer)
output_columns = (1660, 1702, 1744)
output_rows = (343, 385, 427)
rng = random.Random(23)

for row_index, y in enumerate(output_rows):
    for col_index, x in enumerate(output_columns):
        cell = row_index * 3 + col_index
        bx = x + rng.choice([-2, 0, 0, 2])
        by = y + rng.choice([-2, 0, 1, 2])

        if cell in (1, 5, 7):
            # Contorno discontinuo: bloque que ya no se reconstruye.
            for side in range(4):
                if side == 0:
                    p0, p1 = (bx + 2, by), (bx + 27, by)
                elif side == 1:
                    p0, p1 = (bx + 30, by + 3), (bx + 30, by + 27)
                elif side == 2:
                    p0, p1 = (bx + 2, by + 30), (bx + 27, by + 30)
                else:
                    p0, p1 = (bx, by + 4), (bx, by + 27)
                od.line([p0, p1], fill=(100, 116, 139, 165), width=1)
        else:
            # Bloque relleno con una esquina/y grieta irregulares.
            cut = 5 if cell % 3 == 0 else 2
            polygon = [
                (bx + cut, by),
                (bx + 28, by + 1),
                (bx + 30, by + cut + 2),
                (bx + 28, by + 30),
                (bx + 2, by + 28),
                (bx, by + 30 - cut),
            ]
            od.polygon(polygon, fill=(71, 85, 105, 190))
            od.line(
                [(bx + 8, by + 7), (bx + 24, by + 25)],
                fill=BG_RGB + (170,),
                width=2,
            )

# Motas de información perdida alrededor de la salida.
for _ in range(10):
    px = rng.randint(1645, 1775)
    py = rng.randint(320, 480)
    od.rectangle((px, py, px + 2, py + 2), fill=(100, 116, 139, rng.randint(40, 85)))

image = Image.alpha_composite(image, out_layer)

draw = ImageDraw.Draw(image)
draw.text((1715, 500), "SALIDA", font=F_LABEL, fill=(148, 163, 184), anchor="mm")
draw.text((1715, 519), "degradada", font=F_SMALL, fill=(148, 163, 184), anchor="mm")

# ---------------------------------------------------------------------------
# 11. Longitudes de cada capa
# ---------------------------------------------------------------------------
encoder_label_color = (165, 243, 252)
encoder_tick_color = (14, 116, 144)
for index, (height, dim) in enumerate(zip(encoder_heights, encoder_dims)):
    center_x = encoder_start_x + index * (encoder_width + encoder_gap) + encoder_width // 2
    top_y = encoder_center_y - height // 2
    label = f"Longitud {dim}" if index == 0 else str(dim)
    draw_dimension_label(
        draw, center_x, top_y, label, encoder_label_color, encoder_tick_color
    )

decoder_label_color = (203, 213, 225)
decoder_tick_color = (71, 85, 105)
for index, (height, dim) in enumerate(zip(decoder_heights, decoder_dims)):
    center_x = decoder_start_x + index * (decoder_width + decoder_gap) + decoder_width // 2
    top_y = decoder_center_y - height // 2
    label = f"Longitud {dim}" if index == len(decoder_dims) - 1 else str(dim)
    draw_dimension_label(
        draw, center_x, top_y, label, decoder_label_color, decoder_tick_color
    )

draw_dimension_label(
    draw,
    (bottleneck_box[0] + bottleneck_box[2]) // 2,
    bottleneck_box[1],
    f"Longitud {bottleneck_dim}",
    (254, 202, 202),
    (185, 28, 28),
)

# ---------------------------------------------------------------------------
# 12. Flechas del flujo horizontal
# ---------------------------------------------------------------------------
draw_arrow(draw, 165, 212, 400, CYAN_RGB, width=3, head=14)
draw_arrow(draw, 642, 792, 400, BLUE_RGB, width=3, head=14)
draw_arrow(draw, 1008, 1142, 400, RED_RGB, width=3, head=14)
draw_arrow(draw, 1572, 1650, 400, (100, 116, 139), width=3, head=14)

# ---------------------------------------------------------------------------
# 13. Nota de cierre
# ---------------------------------------------------------------------------
draw.text(
    (900, 694),
    "El codificador comprime toda la entrada en un vector de contexto de longitud fija.",
    font=F_SUBTITLE,
    fill=MUTED_RGB,
    anchor="mm",
)
draw.text(
    (900, 720),
    "El decodificador intenta reconstruirla; los bloques grises discontinuos muestran la información que se pierde.",
    font=F_SMALL,
    fill=(100, 116, 139),
    anchor="mm",
)

# ---------------------------------------------------------------------------
# 13. Exportación AVIF
# ---------------------------------------------------------------------------
output_dir = Path("images")
output_dir.mkdir(exist_ok=True)
output_path = output_dir / "encoder_decoder_bottleneck.avif"

final_image = image.convert("RGB")
final_image.save(output_path, format="AVIF", quality=90)

print(f"Imagen guardada en: {output_path}")
print(f"Dimensiones: {final_image.size[0]}x{final_image.size[1]} | Modo: {final_image.mode}")
