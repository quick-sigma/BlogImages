# pip install matplotlib numpy pillow
"""
Penalización KL: el resorte que previene el reward hacking.

Visualización 2D del espacio de políticas. La curva azul es la distribución
del modelo SFT; la curva roja, la del modelo PPO desplazada hacia respuestas
más complejas y con un pico más alto. La línea punteada verde une ambos picos
(el "resorte KL") y la zona roja marca el territorio de reward hacking.

Salida: images/kl_penalty_spring.avif  (alta resolución, tema oscuro)
Dependencias: numpy, matplotlib y Pillow (para exportar AVIF).
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D

# ---------------------------------------------------------------------------
# 1. Distribuciones del espacio de políticas
# ---------------------------------------------------------------------------
X = np.linspace(0.0, 10.0, 700)

MU_SFT, SIGMA_SFT = 4.30, 1.15
MU_PPO, SIGMA_PPO = 6.40, 0.72


def gaussian(x, mu, sigma):
    """Densidad normal (integral 1) para una distribución suave."""
    return np.exp(-0.5 * ((x - mu) / sigma) ** 2) / (sigma * np.sqrt(2.0 * np.pi))


Y_SFT = gaussian(X, MU_SFT, SIGMA_SFT)
Y_PPO = gaussian(X, MU_PPO, SIGMA_PPO)
PEAK_SFT = gaussian(MU_SFT, MU_SFT, SIGMA_SFT)
PEAK_PPO = gaussian(MU_PPO, MU_PPO, SIGMA_PPO)

# ---------------------------------------------------------------------------
# 2. Sistema visual
# ---------------------------------------------------------------------------
BG = "#070B12"
PANEL = "#0A111C"
TEXT = "#E7EEF7"
MUTED = "#9FB0C7"
GRID = "#1E293B"
BLUE = "#38BDF8"
BLUE_SOFT = "#7DD3FC"
RED = "#FB7185"
RED_SOFT = "#FECDD3"
GREEN = "#4ADE80"
GREEN_SOFT = "#BBF7D0"
ZONE = "#F87171"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.unicode_minus": True,
    }
)

fig = plt.figure(figsize=(14.0, 9.0), facecolor=BG)
ax = fig.add_axes([0.085, 0.12, 0.885, 0.68])
ax.set_facecolor(PANEL)

# ---------------------------------------------------------------------------
# 3. Zona de reward hacking
# ---------------------------------------------------------------------------
ZONE_START = 7.2
ax.axvspan(ZONE_START, 10.0, color=ZONE, alpha=0.075, zorder=0)
ax.axvline(
    ZONE_START,
    color=ZONE,
    linewidth=1.0,
    linestyle=(0, (3, 4)),
    alpha=0.45,
    zorder=1,
)

# ---------------------------------------------------------------------------
# 4. Curvas SFT y PPO con glow
# ---------------------------------------------------------------------------
def glow_plot(x, y, color, linewidth=2.6, linestyle="-", zorder=5):
    """Dibuja una línea con varias capas de halo neón."""
    for width, alpha in ((14, 0.035), (8, 0.06), (4, 0.12)):
        ax.plot(
            x, y,
            color=color,
            linewidth=width,
            alpha=alpha,
            linestyle=linestyle,
            solid_capstyle="round",
            dash_capstyle="round",
            zorder=zorder - 1,
        )
    ax.plot(
        x, y,
        color=color,
        linewidth=linewidth,
        linestyle=linestyle,
        solid_capstyle="round",
        dash_capstyle="round",
        zorder=zorder,
    )


ax.fill_between(X, Y_SFT, color=BLUE, alpha=0.05, zorder=2)
ax.fill_between(X, Y_PPO, color=RED, alpha=0.05, zorder=2)
glow_plot(X, Y_SFT, BLUE, linewidth=2.6, zorder=5)
glow_plot(X, Y_PPO, RED, linewidth=2.6, zorder=5)

# Líneas verticales tenues bajo los picos: hacen visible el desplazamiento.
ax.plot(
    [MU_SFT, MU_SFT], [0.0, PEAK_SFT],
    color=BLUE, linewidth=1.0, linestyle=(0, (2, 4)), alpha=0.28, zorder=3,
)
ax.plot(
    [MU_PPO, MU_PPO], [0.0, PEAK_PPO],
    color=RED, linewidth=1.0, linestyle=(0, (2, 4)), alpha=0.28, zorder=3,
)

# ---------------------------------------------------------------------------
# 5. Resorte KL: línea punteada verde entre los picos
# ---------------------------------------------------------------------------
glow_plot(
    [MU_SFT, MU_PPO], [PEAK_SFT, PEAK_PPO],
    GREEN, linewidth=2.2, linestyle=(0, (2, 3)), zorder=8,
)

ax.scatter(
    [MU_SFT, MU_PPO], [PEAK_SFT, PEAK_PPO],
    s=300, color=GREEN, alpha=0.08, edgecolors="none", zorder=9,
)
ax.scatter(
    [MU_SFT, MU_PPO], [PEAK_SFT, PEAK_PPO],
    s=70, color=GREEN, edgecolors=BG, linewidths=1.6, zorder=10,
)

# ---------------------------------------------------------------------------
# 6. Etiquetas directas
# ---------------------------------------------------------------------------
sft_label = ax.text(
    2.55, 0.415,
    "Modelo SFT (Fase 1)",
    color=BLUE_SOFT,
    fontsize=11.5,
    fontweight="bold",
    ha="left",
    va="center",
    zorder=15,
)
sft_label.set_path_effects([pe.withStroke(linewidth=4.0, foreground=BG)])

ppo_label = ax.text(
    6.55, 0.605,
    "Modelo PPO (optimizando recompensa)",
    color=RED_SOFT,
    fontsize=11.5,
    fontweight="bold",
    ha="left",
    va="center",
    zorder=15,
)
ppo_label.set_path_effects([pe.withStroke(linewidth=4.0, foreground=BG)])

kl_label = ax.text(
    5.42, 0.500,
    "Resorte KL",
    color=GREEN_SOFT,
    fontsize=11.0,
    fontweight="bold",
    ha="left",
    va="bottom",
    zorder=16,
    bbox=dict(
        boxstyle="round,pad=0.35",
        facecolor="#061A12",
        edgecolor=GREEN,
        linewidth=0.9,
        alpha=0.92,
    ),
)

zone_label = ax.text(
    8.55, 0.090,
    "Reward Hacking Zone",
    color="#FCA5A5",
    fontsize=11.5,
    fontweight="bold",
    ha="center",
    va="center",
    zorder=15,
)
zone_label.set_path_effects([pe.withStroke(linewidth=4.0, foreground=BG)])

# ---------------------------------------------------------------------------
# 7. Anotación explicativa
# ---------------------------------------------------------------------------
annotation = ax.annotate(
    "El resorte tira del modelo PPO\n"
    "hacia el modelo SFT si se aleja demasiado",
    xy=(5.25, 0.440),
    xycoords="data",
    xytext=(0.03, 0.835),
    textcoords="axes fraction",
    color="#D1FAE5",
    fontsize=10.8,
    linespacing=1.55,
    ha="left",
    va="top",
    zorder=20,
    bbox=dict(
        boxstyle="round,pad=0.65",
        facecolor="#061A12",
        edgecolor=GREEN,
        linewidth=1.0,
        alpha=0.95,
    ),
    arrowprops=dict(
        arrowstyle="-|>",
        color=GREEN,
        linewidth=1.2,
        alpha=0.85,
        shrinkA=10,
        shrinkB=5,
        connectionstyle="arc3,rad=-0.12",
    ),
)

# ---------------------------------------------------------------------------
# 8. Ejes, rejilla y tipografía
# ---------------------------------------------------------------------------
ax.set_xlim(0.0, 10.0)
ax.set_ylim(0.0, 0.66)

ax.set_xticks([0, 2, 4, 6, 8, 10])
ax.set_xticklabels(["Baja", "", "", "", "", "Alta"])
ax.set_yticks([0.0, 0.2, 0.4, 0.6])
ax.set_yticklabels(["0", "0.2", "0.4", "0.6"])

ax.tick_params(
    axis="both",
    colors=MUTED,
    labelsize=11,
    length=4,
    width=0.8,
    pad=8,
)

ax.set_xlabel("Complejidad de la respuesta", color=MUTED, fontsize=13, labelpad=16)
ax.set_ylabel(
    "Probabilidad asignada por el modelo",
    color=MUTED,
    fontsize=13,
    labelpad=14,
)

ax.grid(
    True,
    color=GRID,
    linestyle=(0, (2, 4)),
    linewidth=0.6,
    alpha=0.7,
)
ax.set_axisbelow(True)

for spine in ax.spines.values():
    spine.set_color("#1E293B")
    spine.set_linewidth(1.0)

# ---------------------------------------------------------------------------
# 9. Titular y subtítulo
# ---------------------------------------------------------------------------
fig.text(
    0.5, 0.975,
    "Penalización KL:",
    color=GREEN,
    fontsize=32,
    fontweight="bold",
    ha="center",
    va="top",
)
fig.text(
    0.5, 0.917,
    "El resorte que previene el reward hacking",
    color=TEXT,
    fontsize=27,
    fontweight="bold",
    ha="center",
    va="top",
)
fig.text(
    0.5, 0.862,
    "Cómo la penalización KL mantiene al modelo PPO cerca de la distribución SFT",
    color=MUTED,
    fontsize=12.5,
    ha="center",
    va="top",
)

fig.add_artist(
    Line2D(
        [0.462, 0.538], [0.828, 0.828],
        transform=fig.transFigure,
        color=GREEN,
        linewidth=2.0,
        alpha=0.9,
        solid_capstyle="round",
    )
)

# ---------------------------------------------------------------------------
# 10. Exportación
# ---------------------------------------------------------------------------
output_dir = Path("images")
output_dir.mkdir(exist_ok=True)
png_path = output_dir / "kl_penalty_spring.png"
avif_path = output_dir / "kl_penalty_spring.avif"

plt.savefig(
    png_path,
    dpi=300,
    bbox_inches="tight",
    facecolor=fig.get_facecolor(),
    pad_inches=0.22,
)
try:
    plt.savefig(
        avif_path,
        dpi=300,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        pad_inches=0.22,
        pil_kwargs={"quality": 92},
    )
    avif_note = f"Saved AVIF: {avif_path}"
except Exception as exc:  # la exportación AVIF depende del build de Pillow
    avif_note = f"AVIF export unavailable ({exc}); PNG was saved."

plt.show()

print(f"SFT peak: ({MU_SFT:.2f}, {PEAK_SFT:.4f})")
print(f"PPO peak: ({MU_PPO:.2f}, {PEAK_PPO:.4f})")
print(f"Shift: {MU_PPO - MU_SFT:.2f} complexity units")
print(f"Saved PNG: {png_path}")
print(avif_note)
