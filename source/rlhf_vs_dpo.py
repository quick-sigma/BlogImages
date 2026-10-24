# pip install Pillow
"""
RLHF vs DPO: de la complejidad a la elegancia.

Comparativa lado a lado de dos pipelines de alineación:
    - Izquierda (naranja/rojo): RLHF, cinco etapas, reward model aparte y
      múltiples bucles de feedback. Etiquetas de dolor: inestable, costoso,
      reward hacking.
    - Derecha (verde/cian): DPO, cuatro etapas y una única pérdida directa.
      Etiquetas de beneficio: estable, eficiente, sin reward hacking.

Salida: images/rlhf_vs_dpo.avif  (1800 x 1150, RGB, calidad 92)
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# 1. Lienzo y sistema de diseño
# ---------------------------------------------------------------------------
W, H = 1800, 1150

BG = "#060A12"
TEXT = "#E7EEF7"
MUTED = "#9FB0C7"
SLATE = "#64748B"
LINE = "#1E293B"

ORANGE = "#FB923C"
ORANGE_LIGHT = "#FDBA74"
RED = "#EF4444"

GREEN = "#34D399"
GREEN_LIGHT = "#A7F3D0"
CYAN = "#22D3EE"


def rgb(hex_color):
    """Convierte #RRGGBB en una tupla RGB."""
    value = hex_color.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def mix(c1, c2, t):
    """Interpola linealmente dos colores RGB."""
    t = max(0.0, min(1.0, t))
    return tuple(round(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


BG_RGB = rgb(BG)
TEXT_RGB = rgb(TEXT)
MUTED_RGB = rgb(MUTED)
SLATE_RGB = rgb(SLATE)
LINE_RGB = rgb(LINE)
ORANGE_RGB = rgb(ORANGE)
ORANGE_LIGHT_RGB = rgb(ORANGE_LIGHT)
RED_RGB = rgb(RED)
GREEN_RGB = rgb(GREEN)
GREEN_LIGHT_RGB = rgb(GREEN_LIGHT)
CYAN_RGB = rgb(CYAN)


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
F_VS = load_font(30, bold=True)
F_SUBTITLE = load_font(13)
F_PANEL = load_font(34, bold=True)
F_PANEL_SUB = load_font(12)
F_PILL = load_font(9, bold=True)
F_BOX_TITLE = load_font(20, bold=True)
F_BOX_SUB = load_font(12)
F_STEP = load_font(14, bold=True)
F_BADGE = load_font(10, bold=True)
F_BADGE_ICON = load_font(9, bold=True)
F_CAPTION = load_font(11)


# ---------------------------------------------------------------------------
# 3. Utilidades de dibujo
# ---------------------------------------------------------------------------
def vertical_gradient(w, h, top_color, bottom_color):
    """Devuelve una imagen RGBA con un degradado vertical."""
    gradient = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gradient)
    for y in range(h):
        t = y / max(1, h - 1)
        color = mix(top_color, bottom_color, t)
        gd.line([(0, y), (w, y)], fill=color + (255,))
    return gradient


def rounded_mask(w, h, radius):
    """Máscara redondeada para recortar degradados."""
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, w - 1, h - 1), radius=radius, fill=255
    )
    return mask


def gradient_rule(draw, x0, x1, y, stops, alpha=160):
    """Línea horizontal de 1 px con degradado entre paradas."""
    for x in range(x0, x1):
        t = (x - x0) / max(1, x1 - x0 - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if t <= p1:
                local = (t - p0) / (p1 - p0) if p1 > p0 else 0.0
                color = mix(c0, c1, local)
                break
        else:
            color = stops[-1][1]
        draw.point((x, y), fill=color + (alpha,))


# ---------------------------------------------------------------------------
# 4. Paneles
# ---------------------------------------------------------------------------
def draw_panel(base, x0, y0, x1, y1, color, top_fill, bottom_fill):
    """Panel con degradado, borde y halo de color."""
    w, h = x1 - x0, y1 - y0

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle(
        (x0, y0, x1, y1), radius=24,
        outline=color + (75,), width=6,
    )
    glow = glow.filter(ImageFilter.GaussianBlur(20))
    base = Image.alpha_composite(base, glow)

    fill = vertical_gradient(w, h, top_fill, bottom_fill)
    fill.putalpha(rounded_mask(w, h, 24))
    base.alpha_composite(fill, (x0, y0))

    d = ImageDraw.Draw(base)
    d.rounded_rectangle(
        (x0, y0, x1, y1), radius=24,
        outline=color + (135,), width=2,
    )
    return base


# ---------------------------------------------------------------------------
# 5. Cajas
# ---------------------------------------------------------------------------
def draw_box(base, x, y, w, h, number, title, subtitle,
             color, light, top_fill, bottom_fill):
    """Caja de etapa con número, título y subtítulo."""
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle(
        (x, y, x + w, y + h), radius=16,
        outline=color + (90,), width=5,
    )
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    base = Image.alpha_composite(base, glow)

    fill = vertical_gradient(w, h, top_fill, bottom_fill)
    fill.putalpha(rounded_mask(w, h, 16))
    base.alpha_composite(fill, (x, y))

    d = ImageDraw.Draw(base)
    d.rounded_rectangle(
        (x, y, x + w, y + h), radius=16,
        outline=color + (225,), width=2,
    )

    cy = y + h // 2
    d.ellipse((x + 18, cy - 17, x + 52, cy + 17), fill=color + (255,))
    d.text(
        (x + 35, cy),
        str(number),
        font=F_STEP,
        fill=(10, 10, 12, 255),
        anchor="mm",
    )
    d.text(
        (x + 66, cy - 12),
        title,
        font=F_BOX_TITLE,
        fill=TEXT_RGB + (255,),
        anchor="lm",
    )
    d.text(
        (x + 66, cy + 16),
        subtitle,
        font=F_BOX_SUB,
        fill=MUTED_RGB + (255,),
        anchor="lm",
    )
    return base


# ---------------------------------------------------------------------------
# 6. Flechas y bucles de feedback
# ---------------------------------------------------------------------------
def draw_vertical_arrow(base, cx, y0, y1, color_top, color_bottom,
                        shaft=13, head_w=32, head_h=15):
    """Flecha vertical gruesa con degradado y halo."""
    h = y1 - y0
    points = [
        (head_w / 2 - shaft / 2, 0),
        (head_w / 2 + shaft / 2, 0),
        (head_w / 2 + shaft / 2, h - head_h),
        (head_w, h - head_h),
        (head_w / 2, h),
        (0, h - head_h),
        (head_w / 2 - shaft / 2, h - head_h),
    ]

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.polygon(
        [(cx - head_w / 2 + px, y0 + py) for px, py in points],
        fill=color_bottom + (105,),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    base = Image.alpha_composite(base, glow)

    grad = vertical_gradient(head_w, h, color_top, color_bottom)
    mask = Image.new("L", (head_w, h), 0)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    grad.putalpha(mask)
    base.alpha_composite(grad, (int(cx - head_w / 2), y0))

    d = ImageDraw.Draw(base)
    d.line(
        [(cx - shaft / 2 + 2, y0 + 4),
         (cx - shaft / 2 + 2, y1 - head_h - 3)],
        fill=(255, 255, 255, 65),
        width=1,
    )
    return base


def dashed_path(draw, points, color, width=2, dash=7, gap=5):
    """Dibuja una polilínea punteada."""
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        dx, dy = x1 - x0, y1 - y0
        length = (dx * dx + dy * dy) ** 0.5
        if length == 0:
            continue
        ux, uy = dx / length, dy / length
        pos = 0.0
        while pos < length:
            end = min(pos + dash, length)
            draw.line(
                [(x0 + ux * pos, y0 + uy * pos),
                 (x0 + ux * end, y0 + uy * end)],
                fill=color,
                width=width,
            )
            pos += dash + gap


def draw_feedback(base, points, color, light):
    """Bucle de feedback punteado con flecha en el extremo."""
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.line(points, fill=color + (75,), width=6, joint="curve")
    glow = glow.filter(ImageFilter.GaussianBlur(8))
    base = Image.alpha_composite(base, glow)

    d = ImageDraw.Draw(base)
    dashed_path(d, points, color + (235,), width=2, dash=7, gap=5)

    # Punto de salida y punta de flecha.
    d.ellipse(
        (points[0][0] - 3, points[0][1] - 3,
         points[0][0] + 3, points[0][1] + 3),
        fill=light + (255,),
    )
    tip_x, tip_y = points[-1][0] + 7, points[-1][1]
    d.polygon(
        [(tip_x, tip_y), (tip_x - 14, tip_y - 7), (tip_x - 14, tip_y + 7)],
        fill=light + (255,),
    )
    return base


# ---------------------------------------------------------------------------
# 7. Badges de dolor / beneficio
# ---------------------------------------------------------------------------
def draw_badge(base, box_right, box_top, text, color, light, kind):
    """Píldora de advertencia o beneficio sobre la esquina de una caja."""
    tw = ImageDraw.Draw(base).textlength(text, font=F_BADGE)
    icon_w = 14
    gap = 6
    pad = 11
    bw = int(icon_w + gap + tw + pad * 2)
    bh = 26
    x = box_right - bw - 10
    y = box_top - 13

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle(
        (x, y, x + bw, y + bh), radius=bh // 2,
        outline=color + (95,), width=4,
    )
    glow = glow.filter(ImageFilter.GaussianBlur(8))
    base = Image.alpha_composite(base, glow)

    d = ImageDraw.Draw(base)
    d.rounded_rectangle(
        (x, y, x + bw, y + bh), radius=bh // 2,
        fill=mix((10, 8, 8), color, 0.14) + (255,),
        outline=color + (235,), width=1,
    )

    icx = x + pad + icon_w // 2
    icy = y + bh // 2
    d.ellipse(
        (icx - 6, icy - 6, icx + 6, icy + 6),
        outline=light + (255,), width=1,
    )
    if kind == "warning":
        d.text((icx, icy), "!", font=F_BADGE_ICON, fill=light + (255,), anchor="mm")
    else:
        d.line(
            [(icx - 3, icy), (icx - 1, icy + 3), (icx + 4, icy - 3)],
            fill=light + (255,), width=2, joint="curve",
        )

    d.text(
        (x + pad + icon_w + gap, icy),
        text,
        font=F_BADGE,
        fill=light + (255,),
        anchor="lm",
    )
    return base


# ---------------------------------------------------------------------------
# 8. Fondo
# ---------------------------------------------------------------------------
image = Image.new("RGBA", (W, H), BG_RGB + (255,))
draw = ImageDraw.Draw(image)

for gy in range(26, H - 16, 44):
    for gx in range(26, W - 16, 44):
        draw.ellipse((gx, gy, gx + 2, gy + 2), fill=(16, 27, 43, 255))

bg_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(bg_glow)
gd.ellipse((20, 200, 900, 1090), fill=ORANGE_RGB + (17,))
gd.ellipse((900, 200, 1780, 1090), fill=GREEN_RGB + (15,))
gd.ellipse((500, -220, 1300, 210), fill=(255, 255, 255, 7))
bg_glow = bg_glow.filter(ImageFilter.GaussianBlur(110))
image = Image.alpha_composite(image, bg_glow)

draw = ImageDraw.Draw(image)
draw.rounded_rectangle(
    (22, 22, W - 22, H - 22),
    radius=26,
    outline=LINE_RGB + (190,),
    width=1,
)

# ---------------------------------------------------------------------------
# 9. Titular
# ---------------------------------------------------------------------------
title_parts = [
    ("RLHF", F_TITLE, ORANGE_RGB),
    ("  vs  ", F_VS, SLATE_RGB),
    ("DPO:", F_TITLE, GREEN_RGB),
    ("  De la complejidad a la elegancia", F_TITLE, TEXT_RGB),
]
widths = [draw.textlength(text, font=font) for text, font, _ in title_parts]
total_w = sum(widths)
tx = (W - total_w) / 2
baseline = 82
for (text, font, color), width in zip(title_parts, widths):
    draw.text((tx, baseline), text, font=font, fill=color + (255,), anchor="ls")
    tx += width

draw.text(
    (W // 2, 112),
    "Dos caminos para alinear un modelo: el pipeline completo de RLHF "
    "y la ruta directa de DPO",
    font=F_SUBTITLE,
    fill=MUTED_RGB + (255,),
    anchor="mt",
)
gradient_rule(
    draw, W // 2 - 110, W // 2 + 110, 148,
    [(0.0, ORANGE_RGB), (1.0, GREEN_RGB)], alpha=190,
)

# ---------------------------------------------------------------------------
# 10. Paneles
# ---------------------------------------------------------------------------
image = draw_panel(
    image, 50, 205, 880, 1085,
    ORANGE_RGB, (21, 12, 8), (8, 5, 4),
)
image = draw_panel(
    image, 920, 205, 1750, 1085,
    GREEN_RGB, (6, 20, 16), (4, 9, 8),
)
draw = ImageDraw.Draw(image)

# Cabeceras de panel.
draw.text((90, 230), "RLHF", font=F_PANEL, fill=ORANGE_RGB + (255,), anchor="lt")
draw.text(
    (90, 274),
    "Pipeline completo · 5 etapas",
    font=F_PANEL_SUB,
    fill=(214, 184, 168, 255),
    anchor="lt",
)
draw.rounded_rectangle(
    (205, 233, 315, 259), radius=13,
    fill=mix((16, 10, 8), ORANGE_RGB, 0.16) + (255,),
    outline=ORANGE_RGB + (190,), width=1,
)
draw.text((260, 246), "COMPLEJO", font=F_PILL, fill=ORANGE_LIGHT_RGB + (255,), anchor="mm")

draw.text((960, 230), "DPO", font=F_PANEL, fill=GREEN_RGB + (255,), anchor="lt")
draw.text(
    (960, 274),
    "Optimización directa · 4 etapas",
    font=F_PANEL_SUB,
    fill=(167, 216, 200, 255),
    anchor="lt",
)
draw.rounded_rectangle(
    (1050, 233, 1142, 259), radius=13,
    fill=mix((6, 16, 13), GREEN_RGB, 0.16) + (255,),
    outline=GREEN_RGB + (190,), width=1,
)
draw.text((1096, 246), "SIMPLE", font=F_PILL, fill=GREEN_LIGHT_RGB + (255,), anchor="mm")

draw.line([(90, 300), (840, 300)], fill=ORANGE_RGB + (55,), width=1)
draw.line([(960, 300), (1710, 300)], fill=GREEN_RGB + (55,), width=1)

# ---------------------------------------------------------------------------
# 11. Cajas RLHF
# ---------------------------------------------------------------------------
left_boxes = [
    ("Modelo SFT", "punto de partida"),
    ("Genera respuestas", "rollouts del modelo"),
    ("Reward Model", "(entrenado aparte)"),
    ("PPO", "(optimización compleja)"),
    ("Modelo alineado", "resultado final"),
]
LEFT_X, LEFT_W = 195, 560
LEFT_Y0, LEFT_H, LEFT_GAP = 325, 108, 42

for i, (title, subtitle) in enumerate(left_boxes):
    y = LEFT_Y0 + i * (LEFT_H + LEFT_GAP)
    image = draw_box(
        image, LEFT_X, y, LEFT_W, LEFT_H,
        i + 1, title, subtitle,
        ORANGE_RGB, ORANGE_LIGHT_RGB,
        (27, 14, 10), (15, 8, 6),
    )
    draw = ImageDraw.Draw(image)

# ---------------------------------------------------------------------------
# 12. Cajas DPO
# ---------------------------------------------------------------------------
right_boxes = [
    ("Modelo SFT", "punto de partida"),
    ("Compara par", "(preferida vs rechazada)"),
    ("Función de pérdida DPO", "objetivo directo"),
    ("Modelo alineado", "resultado final"),
]
RIGHT_X, RIGHT_W = 1035, 600
RIGHT_Y0, RIGHT_H, RIGHT_GAP = 325, 132, 58

for i, (title, subtitle) in enumerate(right_boxes):
    y = RIGHT_Y0 + i * (RIGHT_H + RIGHT_GAP)
    image = draw_box(
        image, RIGHT_X, y, RIGHT_W, RIGHT_H,
        i + 1, title, subtitle,
        GREEN_RGB, GREEN_LIGHT_RGB,
        (7, 26, 20), (5, 13, 10),
    )
    draw = ImageDraw.Draw(image)

# ---------------------------------------------------------------------------
# 13. Flechas principales
# ---------------------------------------------------------------------------
for i in range(len(left_boxes) - 1):
    y0 = LEFT_Y0 + i * (LEFT_H + LEFT_GAP) + LEFT_H + 3
    y1 = LEFT_Y0 + (i + 1) * (LEFT_H + LEFT_GAP) - 3
    image = draw_vertical_arrow(
        image, LEFT_X + LEFT_W // 2, y0, y1,
        ORANGE_RGB, RED_RGB,
        shaft=12, head_w=30, head_h=14,
    )

for i in range(len(right_boxes) - 1):
    y0 = RIGHT_Y0 + i * (RIGHT_H + RIGHT_GAP) + RIGHT_H + 3
    y1 = RIGHT_Y0 + (i + 1) * (RIGHT_H + RIGHT_GAP) - 3
    image = draw_vertical_arrow(
        image, RIGHT_X + RIGHT_W // 2, y0, y1,
        GREEN_RGB, CYAN_RGB,
        shaft=14, head_w=36, head_h=16,
    )

# ---------------------------------------------------------------------------
# 14. Bucles de feedback RLHF
# ---------------------------------------------------------------------------
left_centers = [
    LEFT_Y0 + i * (LEFT_H + LEFT_GAP) + LEFT_H // 2
    for i in range(len(left_boxes))
]
long_loop = [
    (LEFT_X, left_centers[3]),
    (120, left_centers[3]),
    (120, left_centers[1]),
    (LEFT_X - 7, left_centers[1]),
]
short_loop = [
    (LEFT_X, left_centers[3]),
    (158, left_centers[3]),
    (158, left_centers[2]),
    (LEFT_X - 7, left_centers[2]),
]
image = draw_feedback(image, long_loop, ORANGE_RGB, ORANGE_LIGHT_RGB)
image = draw_feedback(image, short_loop, ORANGE_RGB, ORANGE_LIGHT_RGB)
draw = ImageDraw.Draw(image)


# ---------------------------------------------------------------------------
# 15. Badges
# ---------------------------------------------------------------------------
image = draw_badge(
    image, LEFT_X + LEFT_W, LEFT_Y0 + 2 * (LEFT_H + LEFT_GAP),
    "Costoso", ORANGE_RGB, ORANGE_LIGHT_RGB, "warning",
)
image = draw_badge(
    image, LEFT_X + LEFT_W, LEFT_Y0 + 3 * (LEFT_H + LEFT_GAP),
    "Inestable", ORANGE_RGB, ORANGE_LIGHT_RGB, "warning",
)
image = draw_badge(
    image, LEFT_X + LEFT_W, LEFT_Y0 + 4 * (LEFT_H + LEFT_GAP),
    "Reward hacking", ORANGE_RGB, ORANGE_LIGHT_RGB, "warning",
)

image = draw_badge(
    image, RIGHT_X + RIGHT_W, RIGHT_Y0 + 1 * (RIGHT_H + RIGHT_GAP),
    "Eficiente", GREEN_RGB, GREEN_LIGHT_RGB, "check",
)
image = draw_badge(
    image, RIGHT_X + RIGHT_W, RIGHT_Y0 + 2 * (RIGHT_H + RIGHT_GAP),
    "Estable", GREEN_RGB, GREEN_LIGHT_RGB, "check",
)
image = draw_badge(
    image, RIGHT_X + RIGHT_W, RIGHT_Y0 + 3 * (RIGHT_H + RIGHT_GAP),
    "Sin reward hacking", GREEN_RGB, GREEN_LIGHT_RGB, "check",
)

draw = ImageDraw.Draw(image)

# ---------------------------------------------------------------------------
# 16. Captions de panel
# ---------------------------------------------------------------------------
draw.text(
    ((50 + 880) // 2, 1058),
    "5 etapas · reward model aparte · bucles de feedback",
    font=F_CAPTION,
    fill=(214, 184, 168, 255),
    anchor="mm",
)
draw.text(
    ((920 + 1750) // 2, 1058),
    "4 etapas · una sola pérdida · sin bucle de reward",
    font=F_CAPTION,
    fill=(167, 216, 200, 255),
    anchor="mm",
)

# ---------------------------------------------------------------------------
# 18. Exportación AVIF
# ---------------------------------------------------------------------------
output_dir = Path("images")
output_dir.mkdir(exist_ok=True)
output_path = output_dir / "rlhf_vs_dpo.avif"
preview_path = output_dir / "rlhf_vs_dpo.png"

final_image = image.convert("RGB")
final_image.save(preview_path)
final_image.save(output_path, format="AVIF", quality=92)

print(f"Imagen guardada en: {output_path}")
print(f"Dimensiones: {final_image.size[0]}x{final_image.size[1]} | Modo: {final_image.mode}")
