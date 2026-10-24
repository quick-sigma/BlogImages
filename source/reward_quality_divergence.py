# pip install matplotlib numpy pillow
"""
El peligro de la sobreoptimización: cuando la recompensa miente.

Gráfico temporal de dos señales durante el entrenamiento:
    - Azul: puntuación del Reward Model (sube de forma sostenida).
    - Roja: calidad percibida por humanos (sube hasta ~400 pasos y después cae).
La zona roja translúcida marca el territorio de reward hacking, donde el
modelo aprende a engañar al juez mientras la calidad real se deteriora.

Salida: images/reward_quality_divergence.avif
Dependencias: numpy, matplotlib y Pillow (para exportar AVIF).
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D

# ---------------------------------------------------------------------------
# 1. Series temporales
# ---------------------------------------------------------------------------
X = np.linspace(0.0, 1000.0, 1001)

# La recompensa del juez sube de forma monótona y se satura lentamente.
REWARD = 15.0 + 85.0 * (1.0 - np.exp(-X / 380.0))

# La calidad humana sube hasta los 400 pasos y luego se deteriora.
PEAK_STEP = 400.0
RISE = 35.0 + 45.0 * (1.0 - np.exp(-X / 140.0))
PEAK_QUALITY = 35.0 + 45.0 * (1.0 - np.exp(-PEAK_STEP / 140.0))
DECLINE = 33.0 * (1.0 - np.exp(-(X - PEAK_STEP) / 220.0))
QUALITY = np.where(X <= PEAK_STEP, RISE, PEAK_QUALITY - DECLINE)

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
ZONE = "#F87171"
GREEN = "#4ADE80"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.unicode_minus": True,
    }
)

fig = plt.figure(figsize=(14.0, 9.0), facecolor=BG)
ax = fig.add_axes([0.085, 0.12, 0.79, 0.68])
ax.set_facecolor(PANEL)

# ---------------------------------------------------------------------------
# 3. Zona de reward hacking
# ---------------------------------------------------------------------------
ax.axvspan(PEAK_STEP, 1000.0, color=ZONE, alpha=0.09, zorder=0)
ax.axvline(
    PEAK_STEP,
    color=ZONE,
    linewidth=1.0,
    linestyle=(0, (3, 4)),
    alpha=0.55,
    zorder=1,
)

# ---------------------------------------------------------------------------
# 4. Líneas con glow
# ---------------------------------------------------------------------------
def glow_plot(x, y, color, linewidth=2.6, zorder=5):
    """Dibuja una línea con varias capas de halo neón."""
    for width, alpha in ((14, 0.035), (8, 0.06), (4, 0.12)):
        ax.plot(
            x, y,
            color=color,
            linewidth=width,
            alpha=alpha,
            solid_capstyle="round",
            zorder=zorder - 1,
        )
    ax.plot(
        x, y,
        color=color,
        linewidth=linewidth,
        solid_capstyle="round",
        zorder=zorder,
    )


glow_plot(X, REWARD, BLUE, linewidth=2.7, zorder=5)
glow_plot(X, QUALITY, RED, linewidth=2.7, zorder=5)

# Hito del pico humano.
ax.scatter(
    [PEAK_STEP], [PEAK_QUALITY],
    s=320, color=RED, alpha=0.09, edgecolors="none", zorder=8,
)
ax.scatter(
    [PEAK_STEP], [PEAK_QUALITY],
    s=70, color=RED, edgecolors=BG, linewidths=1.6, zorder=9,
)

# ---------------------------------------------------------------------------
# 5. Etiqueta del hito y zona
# ---------------------------------------------------------------------------
step_label = ax.text(
    PEAK_STEP, 98.0,
    "400 pasos",
    color=RED_SOFT,
    fontsize=9.5,
    fontweight="bold",
    ha="center",
    va="top",
    zorder=15,
    bbox=dict(
        boxstyle="round,pad=0.30",
        facecolor="#1A0B10",
        edgecolor=RED,
        linewidth=0.8,
        alpha=0.92,
    ),
)

zone_label = ax.text(
    780.0, 12.0,
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
# 6. Anotación de la divergencia
# ---------------------------------------------------------------------------
annotation = ax.annotate(
    "El modelo aprende a engañar al juez",
    xy=(700.0, 69.0),
    xycoords="data",
    xytext=(0.585, 0.965),
    textcoords="axes fraction",
    color="#FECDD3",
    fontsize=11.0,
    fontweight="bold",
    ha="left",
    va="top",
    zorder=20,
    bbox=dict(
        boxstyle="round,pad=0.55",
        facecolor="#1A0B10",
        edgecolor=ZONE,
        linewidth=1.0,
        alpha=0.95,
    ),
    arrowprops=dict(
        arrowstyle="-|>",
        color=ZONE,
        linewidth=1.2,
        alpha=0.85,
        shrinkA=10,
        shrinkB=5,
        connectionstyle="arc3,rad=0.12",
    ),
)

# ---------------------------------------------------------------------------
# 7. Leyenda
# ---------------------------------------------------------------------------
legend = ax.legend(
    handles=[
        Line2D([0], [0], color=BLUE, lw=2.6,
               label="Recompensa del Juez Digital"),
        Line2D([0], [0], color=RED, lw=2.6,
               label="Calidad percibida por humanos"),
    ],
    loc="upper left",
    bbox_to_anchor=(0.015, 0.985),
    borderaxespad=0.0,
    frameon=True,
    facecolor="#0A111C",
    edgecolor=GRID,
    framealpha=0.95,
    fontsize=10.5,
    labelcolor=TEXT,
    handlelength=2.2,
    handletextpad=0.8,
    borderpad=0.8,
)
legend.set_zorder(30)

# ---------------------------------------------------------------------------
# 8. Ejes, rejilla y tipografía
# ---------------------------------------------------------------------------
ax.set_xlim(0.0, 1000.0)
ax.set_ylim(0.0, 100.0)

ax.set_xticks([0, 200, 400, 600, 800, 1000])
ax.set_yticks([0, 20, 40, 60, 80, 100])
ax.set_yticklabels(["0", "20", "40", "60", "80", "100"])

ax.tick_params(
    axis="both",
    colors=MUTED,
    labelsize=11,
    length=4,
    width=0.8,
    pad=8,
)

ax.set_xlabel("Pasos de entrenamiento", color=MUTED, fontsize=13, labelpad=16)
ax.set_ylabel(
    "Puntuación del Reward Model",
    color=BLUE_SOFT,
    fontsize=13,
    labelpad=16,
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

# Eje derecho: misma escala, etiqueta propia.
ax2 = ax.twinx()
ax2.set_ylim(0.0, 100.0)
ax2.set_yticks([0, 20, 40, 60, 80, 100])
ax2.set_yticklabels(["0", "20", "40", "60", "80", "100"])
ax2.tick_params(
    axis="y",
    colors=MUTED,
    labelsize=11,
    length=4,
    width=0.8,
    pad=8,
)
ax2.set_ylabel(
    "Calidad humana real",
    color=RED_SOFT,
    fontsize=13,
    labelpad=16,
)
ax2.grid(False)
for spine in ax2.spines.values():
    spine.set_color("#1E293B")
    spine.set_linewidth(1.0)

# ---------------------------------------------------------------------------
# 9. Titular y subtítulo
# ---------------------------------------------------------------------------
fig.text(
    0.5, 0.975,
    "El peligro de la sobreoptimización:",
    color=RED,
    fontsize=30,
    fontweight="bold",
    ha="center",
    va="top",
)
fig.text(
    0.5, 0.917,
    "Cuando la recompensa miente",
    color=TEXT,
    fontsize=27,
    fontweight="bold",
    ha="center",
    va="top",
)
fig.text(
    0.5, 0.862,
    "Recompensa del juez vs. calidad real a lo largo del entrenamiento",
    color=MUTED,
    fontsize=12.5,
    ha="center",
    va="top",
)

fig.add_artist(
    Line2D(
        [0.462, 0.538], [0.828, 0.828],
        transform=fig.transFigure,
        color=RED,
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
png_path = output_dir / "reward_quality_divergence.png"
avif_path = output_dir / "reward_quality_divergence.avif"

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
    avif_note = f"AVIF unavailable ({exc}); PNG was saved."

plt.show()

print(f"Human peak: step {PEAK_STEP:.0f}, quality {PEAK_QUALITY:.2f}")
print(f"Final reward: {REWARD[-1]:.2f}")
print(f"Final human quality: {QUALITY[-1]:.2f}")
print(f"Saved PNG: {png_path}")
print(avif_note)
