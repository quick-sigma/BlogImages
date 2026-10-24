# pip install Pillow
"""
DPO: la partitura implícita del lenguaje.

Analogía visual: la estructura correcta de una respuesta ya está en los datos,
igual que una melodía correcta está escrita en una partitura. Las notas verdes
marcan lo correcto; las rojas, la alternativa incorrecta. Las flechas llevan
esa estructura a las dos respuestas (A: París, B: Londres).

Salida: images/dpo_music_score.avif  (1800 x 1000, RGB, calidad 92)
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# 1. Lienzo y sistema de diseño
# ---------------------------------------------------------------------------
W, H = 1800, 900

BG = "#060A12"
TEXT = "#E7EEF7"
MUTED = "#9FB0C7"
SLATE = "#64748B"
LINE = "#1E293B"

GREEN = "#34D399"
GREEN_LIGHT = "#A7F3D0"
RED = "#F87171"
RED_LIGHT = "#FECDD3"


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
GREEN_RGB = rgb(GREEN)
GREEN_LIGHT_RGB = rgb(GREEN_LIGHT)
RED_RGB = rgb(RED)
RED_LIGHT_RGB = rgb(RED_LIGHT)


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


def load_clef_font(size):
    """Fuente con el glifo de clave de sol (U+1D11E)."""
    candidates = [
        "C:/Windows/Fonts/seguisym.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Symbol.ttf",
    ]
    for name in candidates:
        if Path(name).exists():
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                pass
    return None


F_TITLE = load_font(40, bold=True)
F_SUBTITLE = load_font(15)
F_SECTION = load_font(11, bold=True)
F_PANEL_TITLE = load_font(20, bold=True)
F_PANEL_SUB = load_font(12)
F_LEGEND = load_font(12)
F_CARD_LABEL = load_font(11, bold=True)
F_CARD_TEXT = load_font(16)
F_CARD_ANSWER = load_font(36, bold=True)
F_CARD_NOTE = load_font(11)
F_CLEF = load_clef_font(170)
F_TIME = load_font(13, bold=True)
F_FOOTER = load_font(12)


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


def gradient_rule(draw, x0, x1, y, stops, alpha=170):
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


def bezier(p0, c1, c2, p1, t):
    """Punto de una curva de Bézier cúbica."""
    mt = 1.0 - t
    x = (mt ** 3 * p0[0] + 3 * mt ** 2 * t * c1[0]
         + 3 * mt * t ** 2 * c2[0] + t ** 3 * p1[0])
    y = (mt ** 3 * p0[1] + 3 * mt ** 2 * t * c1[1]
         + 3 * mt * t ** 2 * c2[1] + t ** 3 * p1[1])
    return x, y


def draw_curve_arrow(base, p0, c1, c2, p1, color, light, width=2.6):
    """Flecha curva con halo y punta."""
    samples = [bezier(p0, c1, c2, p1, i / 60.0) for i in range(61)]

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.line(samples, fill=color + (65,), width=7, joint="curve")
    glow = glow.filter(ImageFilter.GaussianBlur(8))
    base = Image.alpha_composite(base, glow)

    d = ImageDraw.Draw(base)
    d.line(samples, fill=color + (230,), width=int(round(width)), joint="curve")

    # Punta de flecha orientada por la tangente final.
    tx, ty = samples[-1]
    px, py = samples[-6]
    angle = (ty - py, tx - px)
    length = (angle[0] ** 2 + angle[1] ** 2) ** 0.5 or 1.0
    ux, uy = angle[0] / length, angle[1] / length
    nx, ny = -uy, ux
    tip = (tx + ux * 2, ty + uy * 2)
    base_center = (tx - ux * 13, ty - uy * 13)
    d.polygon(
        [tip,
         (base_center[0] + nx * 6, base_center[1] + ny * 6),
         (base_center[0] - nx * 6, base_center[1] - ny * 6)],
        fill=light + (255,),
    )

    d.ellipse((p0[0] - 3, p0[1] - 3, p0[0] + 3, p0[1] + 3),
              fill=light + (255,))
    return base


def draw_note(draw, x, y, color, light, stem_up=True):
    """Nota musical estilizada: cabeza, plica y brillo."""
    draw.ellipse((x - 11, y - 7, x + 11, y + 7), fill=color + (255,),
                 outline=light + (255,), width=1)
    if stem_up:
        draw.line([(x + 8, y), (x + 8, y - 38)], fill=color + (255,), width=2)
    else:
        draw.line([(x + 8, y), (x + 8, y + 38)], fill=color + (255,), width=2)


# ---------------------------------------------------------------------------
# 4. Fondo
# ---------------------------------------------------------------------------
image = Image.new("RGBA", (W, H), BG_RGB + (255,))
draw = ImageDraw.Draw(image)

for gy in range(26, H - 16, 44):
    for gx in range(26, W - 16, 44):
        draw.ellipse((gx, gy, gx + 2, gy + 2), fill=(16, 27, 43, 255))

bg_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(bg_glow)
gd.ellipse((70, 230, 1000, 880), fill=GREEN_RGB + (13,))
gd.ellipse((520, 380, 1780, 930), fill=RED_RGB + (11,))
gd.ellipse((560, -220, 1240, 200), fill=(255, 255, 255, 7))
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
# 5. Titular
# ---------------------------------------------------------------------------
prefix = "DPO:"
accent_title = "  La partitura implícita del lenguaje"
prefix_w = draw.textlength(prefix, font=F_TITLE)
title_w = draw.textlength(accent_title, font=F_TITLE)
title_x = (W - prefix_w - title_w) / 2
draw.text((title_x, 78), prefix, font=F_TITLE, fill=GREEN_RGB + (255,), anchor="ls")
draw.text(
    (title_x + prefix_w, 78),
    accent_title,
    font=F_TITLE,
    fill=TEXT_RGB + (255,),
    anchor="ls",
)
draw.text(
    (W // 2, 112),
    "No necesitas un juez; las preferencias están en los datos",
    font=F_SUBTITLE,
    fill=MUTED_RGB + (255,),
    anchor="mt",
)
gradient_rule(
    draw, W // 2 - 90, W // 2 + 90, 150,
    [(0.0, GREEN_RGB), (1.0, RED_RGB)], alpha=190,
)

# ---------------------------------------------------------------------------
# 6. Panel de la partitura
# ---------------------------------------------------------------------------
SCORE_X0, SCORE_Y0 = 70, 210
SCORE_X1, SCORE_Y1 = 780, 780

score_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sgd = ImageDraw.Draw(score_glow)
sgd.rounded_rectangle(
    (SCORE_X0, SCORE_Y0, SCORE_X1, SCORE_Y1), radius=24,
    outline=GREEN_RGB + (55,), width=5,
)
score_glow = score_glow.filter(ImageFilter.GaussianBlur(18))
image = Image.alpha_composite(image, score_glow)

score_fill = vertical_gradient(
    SCORE_X1 - SCORE_X0, SCORE_Y1 - SCORE_Y0,
    (12, 20, 30), (7, 12, 18),
)
score_fill.putalpha(rounded_mask(SCORE_X1 - SCORE_X0, SCORE_Y1 - SCORE_Y0, 24))
image.alpha_composite(score_fill, (SCORE_X0, SCORE_Y0))

draw = ImageDraw.Draw(image)
draw.rounded_rectangle(
    (SCORE_X0, SCORE_Y0, SCORE_X1, SCORE_Y1), radius=24,
    outline=LINE_RGB + (230,), width=1,
)

draw.text((110, 250), "LA ESTRUCTURA", font=F_SECTION,
          fill=MUTED_RGB + (255,), anchor="lt")
draw.text((110, 270), "La melodía correcta", font=F_PANEL_TITLE,
          fill=TEXT_RGB + (255,), anchor="lt")
draw.text((110, 300), "ya está en los datos", font=F_PANEL_SUB,
          fill=GREEN_LIGHT_RGB + (220,), anchor="lt")

# Pentagrama.
staff_y = [430, 466, 502, 538, 574]
for y in staff_y:
    draw.line([(120, y), (730, y)], fill=(71, 85, 105, 210), width=1)

# Clave de sol.
if F_CLEF is not None:
    draw.text((178, 502), "\U0001D11E", font=F_CLEF,
              fill=(203, 213, 225, 255), anchor="mm")
else:
    draw.text((178, 502), "G", font=load_font(90, bold=True),
              fill=(203, 213, 225, 255), anchor="mm")

# Compás 4/4.
draw.text((220, 484), "4", font=F_TIME, fill=(100, 116, 139, 255), anchor="mm")
draw.text((220, 520), "4", font=F_TIME, fill=(100, 116, 139, 255), anchor="mm")

# Líneas de compás.
for x in (310, 440, 570, 700):
    draw.line([(x, 430), (x, 574)], fill=(51, 65, 85, 210), width=1)
draw.line([(726, 430), (726, 574)], fill=(100, 116, 139, 210), width=1)
draw.line([(732, 430), (732, 574)], fill=(100, 116, 139, 210), width=1)

# Melodía correcta (notas verdes).
green_notes = [(260, 556), (330, 520), (400, 484), (470, 520), (540, 556), (610, 520)]
red_notes = [(400, 574), (540, 448)]

note_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ngd = ImageDraw.Draw(note_glow)
for nx, ny in green_notes:
    ngd.ellipse((nx - 13, ny - 9, nx + 13, ny + 9), fill=GREEN_RGB + (150,))
for nx, ny in red_notes:
    ngd.ellipse((nx - 13, ny - 9, nx + 13, ny + 9), fill=RED_RGB + (150,))
note_glow = note_glow.filter(ImageFilter.GaussianBlur(8))
image = Image.alpha_composite(image, note_glow)

draw = ImageDraw.Draw(image)
# Contorno de la melodía correcta.
draw.line(green_notes, fill=GREEN_RGB + (80,), width=2, joint="curve")
# Alternativa incorrecta, punteada.
draw.line(red_notes, fill=RED_RGB + (90,), width=1, joint="curve")

for nx, ny in green_notes:
    draw_note(draw, nx, ny, GREEN_RGB, GREEN_LIGHT_RGB, stem_up=True)
for nx, ny in red_notes:
    draw_note(draw, nx, ny, RED_RGB, RED_LIGHT_RGB, stem_up=False)

# Leyenda y cierre del panel.
draw.ellipse((120, 680, 136, 696), fill=GREEN_RGB + (255,))
draw.text((146, 688), "Correcta", font=F_LEGEND,
          fill=GREEN_LIGHT_RGB + (255,), anchor="lm")
draw.ellipse((300, 680, 316, 696), fill=RED_RGB + (255,))
draw.text((326, 688), "Incorrecta", font=F_LEGEND,
          fill=RED_LIGHT_RGB + (255,), anchor="lm")
draw.text(
    (120, 825),
    "Las preferencias ya están implícitas en los datos.",
    font=F_PANEL_SUB,
    fill=SLATE_RGB + (255,),
    anchor="lm",
)

# ---------------------------------------------------------------------------
# 7. Flechas de la partitura a las respuestas
# ---------------------------------------------------------------------------
# Verdes: notas correctas -> Respuesta A.
image = draw_curve_arrow(
    image, (610, 520), (760, 440), (900, 430), (1012, 430),
    GREEN_RGB, GREEN_LIGHT_RGB,
)
image = draw_curve_arrow(
    image, (470, 520), (700, 505), (860, 500), (1012, 500),
    GREEN_RGB, GREEN_LIGHT_RGB,
)
# Rojas: notas incorrectas -> Respuesta B.
image = draw_curve_arrow(
    image, (540, 448), (720, 630), (1040, 640), (1382, 640),
    RED_RGB, RED_LIGHT_RGB,
)
image = draw_curve_arrow(
    image, (400, 574), (700, 720), (1120, 730), (1382, 700),
    RED_RGB, RED_LIGHT_RGB,
)
draw = ImageDraw.Draw(image)

# ---------------------------------------------------------------------------
# 8. Separador central "vs"
# ---------------------------------------------------------------------------
for y in range(300, 780):
    t = (y - 300) / 580
    color = mix(GREEN_RGB, RED_RGB, t)
    draw.point((900, y), fill=color + (45,))

vs_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
vgd = ImageDraw.Draw(vs_glow)
vgd.ellipse((864, 529, 936, 601), outline=(148, 163, 184, 120), width=4)
vs_glow = vs_glow.filter(ImageFilter.GaussianBlur(12))
image = Image.alpha_composite(image, vs_glow)

draw = ImageDraw.Draw(image)
draw.ellipse((864, 529, 936, 601), fill=(10, 17, 28, 255),
             outline=(71, 85, 105, 255), width=1)
draw.text((900, 565), "vs", font=load_font(20, bold=True),
          fill=(203, 213, 225, 255), anchor="mm")

# ---------------------------------------------------------------------------
# 9. Tarjetas de respuesta
# ---------------------------------------------------------------------------
def draw_response_card(base, x, y, w, h, color, light, label, sentence,
                       answer, note, kind):
    """Tarjeta de respuesta con check/cross y texto grande."""
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle(
        (x, y, x + w, y + h), radius=18,
        outline=color + (95,), width=5,
    )
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    base = Image.alpha_composite(base, glow)

    top = mix((11, 20, 28), color, 0.08)
    bottom = (7, 12, 18)
    fill = vertical_gradient(w, h, top, bottom)
    fill.putalpha(rounded_mask(w, h, 18))
    base.alpha_composite(fill, (x, y))

    d = ImageDraw.Draw(base)
    d.rounded_rectangle(
        (x, y, x + w, y + h), radius=18,
        outline=color + (230,), width=2,
    )
    d.rounded_rectangle((x + 18, y + 18, x + 22, y + h - 18),
                        radius=2, fill=color + (255,))

    # Icono check / cross.
    icx, icy = x + 44, y + 42
    d.ellipse((icx - 9, icy - 9, icx + 9, icy + 9),
              outline=light + (255,), width=1)
    if kind == "check":
        d.line([(icx - 4, icy), (icx - 1, icy + 4), (icx + 5, icy - 4)],
               fill=light + (255,), width=2, joint="curve")
    else:
        d.line([(icx - 4, icy - 4), (icx + 4, icy + 4)],
               fill=light + (255,), width=2)
        d.line([(icx - 4, icy + 4), (icx + 4, icy - 4)],
               fill=light + (255,), width=2)

    d.text((x + 62, y + 34), label, font=F_CARD_LABEL,
           fill=light + (255,), anchor="lt")
    d.text((x + 30, y + 82), sentence, font=F_CARD_TEXT,
           fill=(199, 210, 224, 255), anchor="lt")
    d.text((x + 30, y + 116), answer, font=F_CARD_ANSWER,
           fill=color + (255,), anchor="lt")
    d.text((x + 30, y + h - 42), note, font=F_CARD_NOTE,
           fill=light + (190,), anchor="lt")

    # Nota musical tenue como marca de agua.
    if F_CLEF is not None:
        d.text((x + w - 34, y + h - 36), "\u266A", font=load_font(28),
               fill=color + (38,), anchor="mm")

    return base


image = draw_response_card(
    image, 1020, 330, 340, 270,
    GREEN_RGB, GREEN_LIGHT_RGB,
    "RESPUESTA A",
    "La capital de Francia es",
    "París",
    "coherente con la estructura",
    "check",
)
image = draw_response_card(
    image, 1390, 520, 340, 270,
    RED_RGB, RED_LIGHT_RGB,
    "RESPUESTA B",
    "La capital de Francia es",
    "Londres",
    "rompe la estructura",
    "cross",
)
draw = ImageDraw.Draw(image)

# ---------------------------------------------------------------------------
# 10. Pie de figura
# ---------------------------------------------------------------------------
draw.text(
    (1375, 825),
    "La preferencia A > B ya es la señal de entrenamiento.",
    font=F_FOOTER,
    fill=SLATE_RGB + (255,),
    anchor="mm",
)

# ---------------------------------------------------------------------------
# 11. Exportación AVIF
# ---------------------------------------------------------------------------
output_dir = Path("images")
output_dir.mkdir(exist_ok=True)
output_path = output_dir / "dpo_music_score.avif"
preview_path = output_dir / "dpo_music_score.png"

final_image = image.convert("RGB")
final_image.save(preview_path)
final_image.save(output_path, format="AVIF", quality=92)

print(f"Imagen guardada en: {output_path}")
print(f"Dimensiones: {final_image.size[0]}x{final_image.size[1]} | Modo: {final_image.mode}")
