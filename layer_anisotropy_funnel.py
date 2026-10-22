"""
Evolution of embedding anisotropy across transformer layers.

Inspired by Ethayarajh (2019), "How Contextual are Contextualized Word
Embeddings?". Layer 0 is nearly isotropic; deeper layers drift away from the
origin and collapse into increasingly narrow, anisotropic clouds.

The figure uses the semantic axes requested by the brief:
    X  -> embedding dimension 1
    Y  -> layer depth (drawn vertically, 0 at the bottom, 11 at the top)
    Z  -> embedding dimension 2
Matplotlib's internal vertical axis is used for the layer coordinate so that
the layers are literally stacked as horizontal slices.

Dependencies: numpy, matplotlib (with a Pillow build that supports AVIF for
the AVIF export).
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from matplotlib.colors import LinearSegmentedColormap, Normalize
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers 3D projection)

# ---------------------------------------------------------------------------
# 1. Simulation parameters
# ---------------------------------------------------------------------------
N_LAYERS = 12
N_POINTS = 100
N_BACKGROUND = N_POINTS - 2   # two of the 100 points are the tracked words
LAYERS = np.arange(N_LAYERS)
T = LAYERS / (N_LAYERS - 1)

np.random.seed(42)

# Anisotropy grows from 1:1 (isotropic) to 15:1 (strongly anisotropic).
# The exponent delays the collapse until the middle/deep layers.
RATIOS = 1.0 + 14.0 * T ** 1.7

# The absolute spread also contracts slightly, making the funnel visible.
STD_X = 1.0 - 0.40 * T ** 1.2
# The plot's vertical axis is reserved for layer depth, so the visible
# embedding plane is X-Z. The anisotropy ratio below therefore refers to
# var(X) : var(Z) within each layer.
STD_Z = STD_X / np.sqrt(RATIOS)

MEAN_X = 2.0 + 0.5 * LAYERS        # drift away from the origin
MEAN_Z = np.zeros(N_LAYERS)

# ---------------------------------------------------------------------------
# 2. Generate layer-wise point clouds and the two tracked word trajectories
# ---------------------------------------------------------------------------
clouds = []
for layer in range(N_LAYERS):
    # Layer 0 is an isotropic Gaussian (a visually uniform disk), while every
    # deeper layer uses the same generator with an increasingly skewed cov.
    cov = np.array(
        [
            [STD_X[layer] ** 2, 0.0],
            [0.0, STD_Z[layer] ** 2],
        ]
    )
    cloud = np.random.multivariate_normal(
        mean=[MEAN_X[layer], MEAN_Z[layer]],
        cov=cov,
        size=N_BACKGROUND,
    )
    clouds.append(cloud)

# Two words are followed through every layer. Their offsets start far apart
# in the isotropic cloud and are progressively squeezed toward the anisotropic
# X-axis, which is the visual signature of the collapse.
def tracked_word(initial_dx, initial_dz, final_dx, final_dz, phase):
    xs = np.empty(N_LAYERS)
    zs = np.empty(N_LAYERS)
    for layer in range(N_LAYERS):
        t = T[layer]
        collapse = (1.0 - t) ** 1.8
        dx = (1.0 - t) * initial_dx + t * final_dx
        dz = collapse * initial_dz + (1.0 - collapse) * final_dz
        # A diminishing wobble keeps the trajectories organic without
        # destroying the monotonic convergence.
        dx += 0.08 * np.sin(1.9 * layer + phase) * collapse
        dz += 0.05 * np.cos(1.4 * layer + phase) * collapse
        xs[layer] = MEAN_X[layer] + dx
        zs[layer] = MEAN_Z[layer] + dz
    return xs, zs


word_a_x, word_a_z = tracked_word(-0.35, 0.95, 0.28, 0.025, phase=0.4)
word_b_x, word_b_z = tracked_word(0.50, -0.85, -0.32, -0.020, phase=2.1)

# The exact layer centroids (including the two tracked points) are used for
# the drift line.
centroids = []
for layer, cloud in enumerate(clouds):
    layer_x = np.append(cloud[:, 0], [word_a_x[layer], word_b_x[layer]])
    layer_z = np.append(cloud[:, 1], [word_a_z[layer], word_b_z[layer]])
    centroids.append((layer_x.mean(), layer_z.mean(), layer))
centroids = np.asarray(centroids)

# ---------------------------------------------------------------------------
# 3. Funnel envelope: elliptical outer boundary at every layer
# ---------------------------------------------------------------------------
THETA = np.linspace(0.0, 2.0 * np.pi, 72, endpoint=True)
ENVELOPE_SIGMA = 2.45

surf_x = np.empty((N_LAYERS, THETA.size))
surf_z = np.empty((N_LAYERS, THETA.size))
surf_y = np.repeat(LAYERS[:, None], THETA.size, axis=1).astype(float)

for layer in range(N_LAYERS):
    surf_x[layer] = MEAN_X[layer] + ENVELOPE_SIGMA * STD_X[layer] * np.cos(THETA)
    surf_z[layer] = MEAN_Z[layer] + ENVELOPE_SIGMA * STD_Z[layer] * np.sin(THETA)

# ---------------------------------------------------------------------------
# 4. Visual system: dark theme, blue-to-red layer gradient
# ---------------------------------------------------------------------------
plt.style.use("dark_background")

BG = "#070b11"
PANEL = "#0b1119"
TEXT = "#e7eef7"
MUTED = "#94a3b8"
GRID = "#64748b"
SURFACE = "#7dd3fc"
A_COLOR = "#ff4fd8"
B_COLOR = "#c7ff3d"
CENTROID_COLOR = "#f8fafc"

layer_cmap = LinearSegmentedColormap.from_list(
    "layer_blue_to_red",
    [
        "#3b82f6",  # layer 0: blue, isotropic
        "#2563eb",
        "#06b6d4",
        "#22d3ee",
        "#facc15",
        "#fb923c",
        "#ef4444",  # layer 11: red, collapsed
    ],
    N=256,
)
layer_norm = Normalize(vmin=0.0, vmax=N_LAYERS - 1)
layer_colors = layer_cmap(layer_norm(LAYERS))

fig = plt.figure(figsize=(13.2, 9.2), facecolor=BG)
ax = fig.add_subplot(111, projection="3d", facecolor=BG)

# ---------------------------------------------------------------------------
# 5. Funnel surface and its wireframe
# ---------------------------------------------------------------------------
# Neutral translucent skin: it reveals the envelope without hiding the points.
ax.plot_surface(
    surf_x,
    surf_z,
    surf_y,
    color=SURFACE,
    alpha=0.065,
    linewidth=0,
    antialiased=True,
    shade=False,
    rstride=1,
    cstride=1,
)

# One colored ring per layer, plus longitudinal wires that trace the funnel.
for layer in range(N_LAYERS):
    ax.plot(
        surf_x[layer],
        surf_z[layer],
        surf_y[layer],
        color=layer_colors[layer],
        linewidth=0.9,
        alpha=0.48,
    )

for k in range(0, THETA.size, 6):
    ax.plot(
        surf_x[:, k],
        surf_z[:, k],
        surf_y[:, k],
        color="white",
        linewidth=0.45,
        alpha=0.11,
    )

# ---------------------------------------------------------------------------
# 6. Layer clouds
# ---------------------------------------------------------------------------
for layer, cloud in enumerate(clouds):
    ax.scatter(
        cloud[:, 0],
        cloud[:, 1],
        np.full(N_BACKGROUND, layer, dtype=float),
        s=17,
        color=layer_colors[layer],
        alpha=0.62,
        edgecolors="none",
        depthshade=False,
    )

# ---------------------------------------------------------------------------
# 7. Centroid drift trajectory
# ---------------------------------------------------------------------------
# Dark under-stroke keeps the dashed trajectory legible against the clouds.
ax.plot(
    centroids[:, 0],
    centroids[:, 1],
    centroids[:, 2],
    color=BG,
    linewidth=4.4,
    linestyle=(0, (4, 3)),
    alpha=0.7,
    zorder=8,
)
ax.plot(
    centroids[:, 0],
    centroids[:, 1],
    centroids[:, 2],
    color=CENTROID_COLOR,
    linewidth=1.7,
    linestyle=(0, (4, 3)),
    alpha=0.9,
    zorder=9,
)
ax.scatter(
    centroids[:, 0],
    centroids[:, 1],
    centroids[:, 2],
    s=42,
    color=CENTROID_COLOR,
    edgecolors=BG,
    linewidths=0.7,
    depthshade=False,
    zorder=10,
)

# ---------------------------------------------------------------------------
# 8. The two words tracked across all layers
# ---------------------------------------------------------------------------
for word_x, word_z, color in (
    (word_a_x, word_a_z, A_COLOR),
    (word_b_x, word_b_z, B_COLOR),
):
    # Dark under-stroke separates the trajectory from the point cloud.
    ax.plot(
        word_x,
        word_z,
        LAYERS,
        color=BG,
        linewidth=4.6,
        alpha=0.65,
        zorder=12,
    )
    ax.plot(
        word_x,
        word_z,
        LAYERS,
        color=color,
        linewidth=2.0,
        alpha=0.98,
        zorder=13,
    )
    ax.scatter(
        word_x,
        word_z,
        LAYERS,
        s=24,
        color=color,
        edgecolors=BG,
        linewidths=0.55,
        depthshade=False,
        zorder=14,
    )

# Emphasise the first and last occurrence of each tracked word.
for word_x, word_z, color in (
    (word_a_x, word_a_z, A_COLOR),
    (word_b_x, word_b_z, B_COLOR),
):
    for layer in (0, N_LAYERS - 1):
        ax.scatter(
            [word_x[layer]],
            [word_z[layer]],
            [layer],
            s=92 if layer == 0 else 120,
            color=color,
            edgecolors="white",
            linewidths=1.1,
            depthshade=False,
            zorder=20,
        )

# Direct word labels near layer 2, where the trajectories are still separated.
label_a = ax.text(
    word_a_x[2] + 0.22,
    word_a_z[2] + 0.62,
    2.0,
    "Word A",
    color=A_COLOR,
    fontsize=10.5,
    fontweight="bold",
    ha="left",
    va="bottom",
    zorder=25,
    clip_on=False,
)
label_b = ax.text(
    word_b_x[2] + 0.22,
    word_b_z[2] - 0.60,
    2.0,
    "Word B",
    color=B_COLOR,
    fontsize=10.5,
    fontweight="bold",
    ha="left",
    va="top",
    zorder=25,
    clip_on=False,
)
for label in (label_a, label_b):
    label.set_path_effects([path_effects.withStroke(linewidth=3.0, foreground=BG)])

# A subtle label for the centroid path itself.
centroid_label = ax.text(
    centroids[4, 0] + 0.18,
    centroids[4, 1] + 0.50,
    centroids[4, 2],
    "centroid drift",
    color="#dbeafe",
    fontsize=8.5,
    fontstyle="italic",
    alpha=0.9,
    ha="left",
    va="bottom",
    zorder=23,
)
centroid_label.set_path_effects(
    [path_effects.withStroke(linewidth=2.6, foreground=BG)]
)

# ---------------------------------------------------------------------------
# 9. Layer annotations
# ---------------------------------------------------------------------------
ann0 = ax.text(
    MEAN_X[0] - 0.2,
    -2.95,
    -0.45,
    "Layer 0: Isotropic (Uniform)",
    color="#93c5fd",
    fontsize=10.5,
    fontweight="bold",
    ha="center",
    va="top",
    zorder=30,
    clip_on=False,
    bbox=dict(
        boxstyle="round,pad=0.38",
        facecolor="#0c1420",
        edgecolor="#3b82f6",
        linewidth=0.9,
        alpha=0.9,
    ),
)
ann0.set_path_effects([path_effects.withStroke(linewidth=2.4, foreground=BG)])

ann11 = ax.text(
    MEAN_X[-1],
    0.0,
    12.10,
    "Layer 11: Highly Anisotropic (Collapsed)",
    color="#fecaca",
    fontsize=10.5,
    fontweight="bold",
    ha="center",
    va="bottom",
    zorder=30,
    clip_on=False,
    bbox=dict(
        boxstyle="round,pad=0.38",
        facecolor="#1a0c10",
        edgecolor="#ef4444",
        linewidth=0.9,
        alpha=0.9,
    ),
)
ann11.set_path_effects([path_effects.withStroke(linewidth=2.4, foreground=BG)])

# Floating summary card.
ax.text2D(
    0.025,
    0.955,
    "Anisotropy increases with depth\n"
    r"$\sigma_X^2 : \sigma_Z^2$ = 1 : 1  $\rightarrow$  15 : 1"
    "\n"
    "12 layers  ·  100 points / layer",
    transform=ax.transAxes,
    color=TEXT,
    fontsize=11.5,
    fontweight="bold",
    linespacing=1.5,
    va="top",
    ha="left",
    bbox=dict(
        boxstyle="round,pad=0.65",
        facecolor="#0e1621",
        edgecolor="#38bdf8",
        linewidth=1.0,
        alpha=0.93,
    ),
    zorder=40,
)

# ---------------------------------------------------------------------------
# 10. Axes, limits and camera
# ---------------------------------------------------------------------------
ax.set_xlim(-1.4, 9.9)
ax.set_ylim(-3.35, 3.35)
ax.set_zlim(-0.9, 12.45)

# X = embedding dim 1, Y = embedding dim 2. The vertical axis carries the
# layer index and is labelled as the Y (depth) axis requested in the brief.
ax.set_xlabel("Embedding Dim 1 (X)", color=MUTED, fontsize=11, labelpad=14)
ax.set_ylabel("Embedding Dim 2 (Z)", color=MUTED, fontsize=11, labelpad=14)
ax.set_zlabel("Layer Depth (Y)", color=MUTED, fontsize=11, labelpad=12)

ax.set_xticks([0, 2, 4, 6, 8])
ax.set_yticks([-2, 0, 2])
ax.set_zticks(LAYERS)
ax.tick_params(colors=TEXT, labelsize=8.5, pad=4)
ax.tick_params(axis="z", labelsize=8)

ax.view_init(elev=20, azim=-58, roll=0)
ax.set_proj_type("persp", focal_length=1.0)

# Compress depth a little relative to height, keeping the funnel readable.
ax.set_box_aspect((1.22, 0.72, 1.18), zoom=1.08)

for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis.pane.set_facecolor(PANEL)
    axis.pane.set_edgecolor((1.0, 1.0, 1.0, 0.06))
    axis._axinfo["grid"].update(
        color=GRID, linewidth=0.42, linestyle=(0, (2, 4))
    )
    axis._axinfo["axisline"].update(color=(1, 1, 1, 0.22))

fig.suptitle(
    "Evolution of Embedding Anisotropy Across Transformer Layers",
    color=TEXT,
    fontsize=17.5,
    fontweight="bold",
    x=0.5,
    y=0.975,
)

fig.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.92)

# ---------------------------------------------------------------------------
# 11. Export
# ---------------------------------------------------------------------------
output_dir = Path("images")
output_dir.mkdir(exist_ok=True)
png_path = output_dir / "embedding_anisotropy_layers.png"
avif_path = output_dir / "embedding_anisotropy_layers.avif"

plt.savefig(
    png_path,
    dpi=300,
    bbox_inches="tight",
    facecolor=fig.get_facecolor(),
)
try:
    plt.savefig(
        avif_path,
        dpi=300,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        pil_kwargs={"quality": 90},
    )
    avif_note = f"Saved AVIF: {avif_path}"
except Exception as exc:  # optional AVIF support depends on the Pillow build
    avif_note = f"AVIF export unavailable ({exc}); PNG was saved."
plt.show()

# Console diagnostics.
for layer in (0, N_LAYERS - 1):
    print(
        f"Layer {layer:2d}: mean_x={MEAN_X[layer]:.2f}, "
        f"std_x={STD_X[layer]:.3f}, std_z={STD_Z[layer]:.3f}, "
        f"variance ratio={RATIOS[layer]:.1f}:1"
    )
print(f"Word A layer 0 -> 11: {word_a_x[0]:.2f},{word_a_z[0]:.2f} -> "
      f"{word_a_x[-1]:.2f},{word_a_z[-1]:.2f}")
print(f"Word B layer 0 -> 11: {word_b_x[0]:.2f},{word_b_z[0]:.2f} -> "
      f"{word_b_x[-1]:.2f},{word_b_z[-1]:.2f}")
print(f"Saved PNG: {png_path}")
print(avif_note)
