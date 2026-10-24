# pip install matplotlib numpy pillow
"""
El entrenamiento es navegar este paisaje de pérdida hasta encontrar el valle
más profundo.

Superficie 3D de la función no convexa
    f(x, y) = x^2 + y^2 + 0.5 * sin(3x) * cos(3y)
sobre el dominio [-5, 5] x [-5, 5]. El color codifica la pérdida: azul para
los valores bajos (el valle) y rojo para los altos (las laderas).

La trayectoria amarilla no es decorativa: se obtiene aplicando descenso de
gradiente real desde un punto de partida aleatorio (semilla fija) hasta que
la norma del gradiente es despreciable. El punto rojo marca el mínimo global.

Salida: images/loss_landscape_gradient_descent.avif
Dependencias: numpy, matplotlib y Pillow (para exportar AVIF).
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LightSource, LinearSegmentedColormap, Normalize
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registra la proyección 3D)
from mpl_toolkits.mplot3d import proj3d

# ---------------------------------------------------------------------------
# 1. Función de pérdida y su gradiente analítico
# ---------------------------------------------------------------------------
def loss(x, y):
    """Pérdida no convexa: un cuenco parabólico con ondulaciones suaves."""
    return x**2 + y**2 + 0.5 * np.sin(3.0 * x) * np.cos(3.0 * y)


def loss_grad(x, y):
    """Gradiente de `loss`, calculado a mano."""
    dl_dx = 2.0 * x + 1.5 * np.cos(3.0 * x) * np.cos(3.0 * y)
    dl_dy = 2.0 * y - 1.5 * np.sin(3.0 * x) * np.sin(3.0 * y)
    return dl_dx, dl_dy


# ---------------------------------------------------------------------------
# 2. Malla de evaluación y descenso de gradiente
# ---------------------------------------------------------------------------
LIMIT = 5.0
MESH_POINTS = 220

axis = np.linspace(-LIMIT, LIMIT, MESH_POINTS)
X, Y = np.meshgrid(axis, axis)
Z = loss(X, Y)

# Punto de partida aleatorio pero reproducible: cerca de una esquina del dominio.
rng = np.random.default_rng(5)
SIGNS = rng.choice([-1.0, 1.0], size=2)
START = SIGNS * rng.uniform(3.2, 4.8, size=2)

LEARNING_RATE = 0.05
STEPS = 260

path = np.empty((STEPS + 1, 2))
path[0] = START
for step in range(STEPS):
    gx, gy = loss_grad(path[step, 0], path[step, 1])
    path[step + 1] = path[step] - LEARNING_RATE * np.array([gx, gy])

# El descenso converge al único mínimo de la función; lo usamos como mínimo
# global y comprobamos que coincide con el mínimo de la malla muestreada.
MIN_X, MIN_Y = path[-1]
MIN_LOSS = loss(MIN_X, MIN_Y)
assert MIN_LOSS <= Z.min() + 1e-6, "El descenso no alcanzó el mínimo global"

path_loss = loss(path[:, 0], path[:, 1])

# Puntos amarillos equiespaciados en longitud de arco: se ven igual de densos
# en la bajada rápida y en la convergencia lenta junto al valle.
segments = np.linalg.norm(np.diff(path, axis=0), axis=1)
arc_length = np.concatenate(([0.0], np.cumsum(segments)))
dot_positions = np.linspace(0.0, arc_length[-1], 34)
dot_indices = np.searchsorted(arc_length, dot_positions)
dot_indices[-1] = len(path) - 1
dots = path[dot_indices]
dots_loss = path_loss[dot_indices]

# ---------------------------------------------------------------------------
# 3. Sistema visual: tema oscuro, azul (pérdida baja) -> rojo (pérdida alta)
# ---------------------------------------------------------------------------
BG = "#070b11"
PANEL = "#0a1119"
TEXT = "#e7eef7"
MUTED = "#9fb0c7"
GRID = (0.45, 0.52, 0.62, 0.30)
YELLOW = "#ffd43b"
RED = "#ff3b30"

loss_cmap = LinearSegmentedColormap.from_list(
    "loss_blue_to_red",
    [
        "#1e3a8a",  # pérdida mínima: azul profundo
        "#2563eb",
        "#0ea5e9",
        "#22d3ee",
        "#a3e635",
        "#facc15",
        "#f97316",
        "#ef4444",
        "#dc2626",  # pérdida máxima: rojo
    ],
    N=512,
)
loss_norm = Normalize(vmin=float(Z.min()), vmax=float(Z.max()))

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.unicode_minus": True,
    }
)

fig = plt.figure(figsize=(14.0, 9.8), facecolor=BG)
# computed_zorder=False: la superficie, la trayectoria y los marcadores se
# dibujan en el orden que fijamos con zorder, sin que el pintado por
# profundidad de mplot3d oculte la ruta que descansa sobre la superficie.
ax = fig.add_subplot(111, projection="3d", computed_zorder=False)
ax.set_facecolor(BG)

# ---------------------------------------------------------------------------
# 4. Superficie con iluminación suave
# ---------------------------------------------------------------------------
light = LightSource(azdeg=315, altdeg=42)
facecolors = light.shade(
    Z,
    cmap=loss_cmap,
    norm=loss_norm,
    vert_exag=0.18,
    blend_mode="soft",
)

ax.plot_surface(
    X,
    Y,
    Z,
    facecolors=facecolors,
    rstride=1,
    cstride=1,
    linewidth=0,
    antialiased=False,
    shade=False,
    zorder=1,
)

# ---------------------------------------------------------------------------
# 5. Trayectoria de descenso de gradiente
# ---------------------------------------------------------------------------
# Trazo oscuro de fondo para separar la ruta de la superficie.
ax.plot(
    path[:, 0],
    path[:, 1],
    path_loss,
    color=BG,
    linewidth=4.6,
    alpha=0.55,
    zorder=4,
)
ax.plot(
    path[:, 0],
    path[:, 1],
    path_loss,
    color=YELLOW,
    linewidth=1.25,
    alpha=0.68,
    zorder=5,
)

ax.scatter(
    dots[:, 0],
    dots[:, 1],
    dots_loss,
    s=36,
    color=YELLOW,
    edgecolors=BG,
    linewidths=0.75,
    depthshade=False,
    zorder=6,
)

# El punto de partida se destaca para que la dirección del descenso se lea.
ax.scatter(
    [START[0]],
    [START[1]],
    [loss(*START)],
    s=110,
    color=YELLOW,
    edgecolors="white",
    linewidths=1.2,
    depthshade=False,
    zorder=7,
)

start_label = ax.text(
    START[0],
    START[1],
    loss(*START) + 1.15,
    "Inicio",
    color="#fde68a",
    fontsize=10,
    fontweight="bold",
    fontstyle="italic",
    ha="center",
    va="bottom",
    zorder=20,
    clip_on=False,
)
start_label.set_path_effects(
    [path_effects.withStroke(linewidth=3.0, foreground=BG)]
)

# ---------------------------------------------------------------------------
# 6. Mínimo global: halo, marcador brillante y etiqueta
# ---------------------------------------------------------------------------
# Halo en capas: da la sensación de punto "encendido" sin usar blur.
for size, alpha in ((1000, 0.05), (560, 0.08), (300, 0.14)):
    ax.scatter(
        [MIN_X],
        [MIN_Y],
        [MIN_LOSS + 0.25],
        s=size,
        color=RED,
        alpha=alpha,
        edgecolors="none",
        depthshade=False,
        zorder=8,
    )

ax.scatter(
    [MIN_X],
    [MIN_Y],
    [MIN_LOSS + 0.25],
    s=150,
    color=RED,
    edgecolors="#fff1f2",
    linewidths=1.3,
    depthshade=False,
    zorder=9,
)

# ---------------------------------------------------------------------------
# 7. Ejes, rejilla y cámara
# ---------------------------------------------------------------------------
ax.set_xlim(-LIMIT, LIMIT)
ax.set_ylim(-LIMIT, LIMIT)
ax.set_zlim(-3.0, 52.0)

ax.set_xticks([-5, -2.5, 0, 2.5, 5])
ax.set_yticks([-5, -2.5, 0, 2.5, 5])
ax.set_zticks([0, 10, 20, 30, 40, 50])

ax.set_xlabel("Parámetro 1", color=MUTED, fontsize=12, labelpad=14)
ax.set_ylabel("Parámetro 2", color=MUTED, fontsize=12, labelpad=14)
ax.set_zlabel("Función de pérdida (Loss)", color=MUTED, fontsize=12, labelpad=12)

ax.tick_params(colors=TEXT, labelsize=9, pad=4)
ax.tick_params(axis="z", labelsize=8.5)

for axis_ in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis_.pane.set_facecolor(PANEL)
    axis_.pane.set_edgecolor((1.0, 1.0, 1.0, 0.05))
    axis_._axinfo["grid"].update(
        color=GRID, linewidth=0.4, linestyle=(0, (2, 4))
    )
    axis_._axinfo["axisline"].update(color=(1.0, 1.0, 1.0, 0.18))
    axis_.line.set_color((1.0, 1.0, 1.0, 0.18))

ax.view_init(elev=48, azim=-58, roll=0)
ax.set_proj_type("persp", focal_length=1.0)
ax.set_box_aspect((1.25, 1.25, 0.72), zoom=1.06)

# ---------------------------------------------------------------------------
# 8. Titular, tarjeta técnica y barra de color
# ---------------------------------------------------------------------------
fig.text(
    0.5,
    0.962,
    "El entrenamiento es navegar este paisaje",
    color=TEXT,
    fontsize=23,
    fontweight="bold",
    ha="center",
    va="top",
)
fig.text(
    0.5,
    0.910,
    "hasta encontrar el valle más profundo",
    color=TEXT,
    fontsize=23,
    fontweight="bold",
    ha="center",
    va="top",
)
fig.text(
    0.5,
    0.868,
    "Descenso de gradiente sobre una función de pérdida no convexa",
    color=MUTED,
    fontsize=12,
    ha="center",
    va="top",
)

ax.text2D(
    0.005,
    0.975,
    "ESPACIO DE PARÁMETROS\n"
    r"$f(\theta_1,\theta_2)=\theta_1^2+\theta_2^2"
    r"+0.5\,\sin(3\theta_1)\cos(3\theta_2)$"
    "\n"
    f"Descenso de gradiente · lr = {LEARNING_RATE} · {STEPS} pasos",
    transform=ax.transAxes,
    color=TEXT,
    fontsize=9.0,
    linespacing=1.55,
    ha="left",
    va="top",
    bbox=dict(
        boxstyle="round,pad=0.5",
        facecolor="#0b1220",
        edgecolor="#38bdf8",
        linewidth=0.9,
        alpha=0.92,
    ),
    zorder=40,
)

colorbar_ax = fig.add_axes([0.935, 0.255, 0.011, 0.335])
colorbar = fig.colorbar(
    ScalarMappable(norm=loss_norm, cmap=loss_cmap),
    cax=colorbar_ax,
)
colorbar.set_ticks([0, 10, 20, 30, 40, 50])
colorbar.outline.set_edgecolor((1.0, 1.0, 1.0, 0.14))
colorbar.ax.tick_params(colors=MUTED, labelsize=8, length=2, width=0.6)
colorbar.set_label("Loss", color=MUTED, fontsize=10, labelpad=10)

fig.subplots_adjust(left=0.0, right=0.945, bottom=0.015, top=0.845)

# ---------------------------------------------------------------------------
# 9. Etiqueta del mínimo, anclada a su posición proyectada
# ---------------------------------------------------------------------------
fig.canvas.draw()
min_x2d, min_y2d, _ = proj3d.proj_transform(
    MIN_X, MIN_Y, MIN_LOSS + 0.25, ax.get_proj()
)
min_label = ax.annotate(
    f"Mínimo global  ·  f* = {MIN_LOSS:.2f}",
    xy=(min_x2d, min_y2d),
    xytext=(-54, 30),
    textcoords="offset points",
    color="#ffe4e6",
    fontsize=11.5,
    fontweight="bold",
    ha="right",
    va="bottom",
    arrowprops=dict(
        arrowstyle="-",
        color="#f87171",
        linewidth=1.0,
        alpha=0.8,
        shrinkA=4,
        shrinkB=7,
    ),
    zorder=50,
)
min_label.set_path_effects(
    [path_effects.withStroke(linewidth=3.4, foreground=BG)]
)

# ---------------------------------------------------------------------------
# 10. Exportación
# ---------------------------------------------------------------------------
output_dir = Path("images")
output_dir.mkdir(exist_ok=True)
png_path = output_dir / "loss_landscape_gradient_descent.png"
avif_path = output_dir / "loss_landscape_gradient_descent.avif"

plt.savefig(
    png_path,
    dpi=300,
    bbox_inches="tight",
    facecolor=fig.get_facecolor(),
    pad_inches=0.25,
)
try:
    plt.savefig(
        avif_path,
        dpi=300,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        pad_inches=0.25,
        pil_kwargs={"quality": 92},
    )
    avif_note = f"Saved AVIF: {avif_path}"
except Exception as exc:  # la exportación AVIF depende del build de Pillow
    avif_note = f"AVIF export unavailable ({exc}); PNG was saved."
plt.show()

# ---------------------------------------------------------------------------
# 11. Diagnóstico por consola
# ---------------------------------------------------------------------------
print(f"Start point: ({START[0]:.3f}, {START[1]:.3f})")
print(
    f"Global minimum: ({MIN_X:.4f}, {MIN_Y:.4f})  "
    f"loss = {MIN_LOSS:.4f}"
)
gx, gy = loss_grad(MIN_X, MIN_Y)
print(f"Gradient norm at minimum: {np.hypot(gx, gy):.2e}")
print(f"Trajectory length: {arc_length[-1]:.3f} parameter units")
print(f"Saved PNG: {png_path}")
print(avif_note)
