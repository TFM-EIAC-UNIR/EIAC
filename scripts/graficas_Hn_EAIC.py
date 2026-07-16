# ============================================================
#  Gráficas comparativas Hn(X) vs EIAC — 3 escenarios + dispersión
# ============================================================

import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.lines import Line2D
import pandas as pd

rcParams["font.family"] = "serif"
rcParams["mathtext.fontset"] = "dejavuserif"
rcParams["axes.linewidth"] = 0.6
rcParams["savefig.bbox"] = "tight"

# Paleta
C_HN   = "#9aa6b2"   # gris-azul: métrica cruda (Shannon normalizado)
C_EIAC = "#0f6e74"   # teal: métrica propuesta (EIAC)
C_LINE = "#d2d7dc"   # línea de unión
C_GRID = "#e9ecef"

# ------------------------------------------------------------
# DATOS  (nombre, Hn, EIAC)
# ------------------------------------------------------------
# Escenario 1: CAPEC (615 registros)
url_esc1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS4_2arw77tW16ChDX_jqpA3LrqtK_g-rdyW8_nM82yWr83HZsJyuHqVnbXM_LmzNkHPjnne8nsbj70/pub?gid=668138267&single=true&output=csv"
df_esc1 = pd.read_csv(url_esc1)
df_esc1 = df_esc1.rename(columns={'Hn(X)': 'Hn_val', 'EIAC': 'EIAC_val'})
esc1 = list(df_esc1[['Columna', 'Hn_val', 'EIAC_val']].itertuples(index=False, name=None))

url_esc2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQq3xyff0g4D__UaZIiuohFSXZVChd8D0rhfzmnI9kIWGc5RrsoTGSXLJChpevgsEXFEx9LIGhxCbgI/pub?gid=206387260&single=true&output=csv"
df_esc2 = pd.read_csv(url_esc2)
df_esc2 = df_esc2.rename(columns={'Hn(X)': 'Hn_val', 'EIAC': 'EIAC_val'})
esc2 = list(df_esc2[['Columna', 'Hn_val', 'EIAC_val']].itertuples(index=False, name=None))

url_esc3 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSdodLca7vizGH77Bcy9rw28DQ-0v2ee3BmBtonTFQCmNFt5vAC8ILHf2IZmk3CB549uB7yYtf9SCWT/pub?output=csv"
df_esc3 = pd.read_csv(url_esc3)
df_esc3 = df_esc3.rename(columns={'Hn(X)': 'Hn_val', 'EIAC': 'EIAC_val'})
esc3 = list(df_esc3[['Columna', 'Hn_val', 'EIAC_val']].itertuples(index=False, name=None))

# ------------------------------------------------------------
# Gráfico de mancuerna (dumbbell)
# ------------------------------------------------------------
def dumbbell(data, title, fname, row_h=0.30):
    data = sorted(data, key=lambda d: d[2])      # mayor relevancia arriba
    names = [d[0] for d in data]
    hn    = [d[1] for d in data]
    eiac  = [d[2] for d in data]
    n = len(data); y = list(range(n))

    fig_h = max(3.0, n * row_h + 1.1)
    fig, ax = plt.subplots(figsize=(7.4, fig_h))
    for yi, h, e in zip(y, hn, eiac):
        ax.plot([e, h], [yi, yi], color=C_LINE, lw=1.6, zorder=1, solid_capstyle="round")
    ax.scatter(hn, y, color=C_HN, s=34, zorder=3, edgecolor="white", linewidth=0.6)
    ax.scatter(eiac, y, color=C_EIAC, s=34, zorder=4, edgecolor="white", linewidth=0.6)

    ax.set_yticks(y); ax.set_yticklabels(names, fontsize=7.2)
    ax.set_ylim(-0.7, n - 0.3); ax.set_xlim(-0.02, 1.06)
    ax.set_xlabel("Valor de la métrica (rango 0–1)", fontsize=9)
    ax.set_title(title, fontsize=10.5, pad=10, weight="bold")
    ax.xaxis.grid(True, color=C_GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0); ax.tick_params(axis="x", labelsize=8)

    legend = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=C_HN,
               markersize=8, label=r"$H_n(X)$  (Shannon normalizado)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=C_EIAC,
               markersize=8, label="EIAC  (índice propuesto)"),
    ]
    ax.legend(handles=legend, loc="lower right", fontsize=8.5,
              frameon=True, framealpha=0.95, edgecolor="#cccccc")
    fig.savefig(fname + ".pdf"); fig.savefig(fname + ".png", dpi=200)
    plt.show()

# ------------------------------------------------------------
# Diagrama de dispersión resumen (3 escenarios)
# ------------------------------------------------------------
def scatter_resumen(fname):
    fig, ax = plt.subplots(figsize=(6.4, 6.0))
    ax.plot([0, 1], [0, 1], ls="--", color="#9aa6b2", lw=1.1, zorder=1,
            label="$y=x$  (sin ajuste)")
    sets = [
        ("Esc. 1 – CAPEC", esc1, "#0f6e74", "o"),
        ("Esc. 2 – Sintético", esc2, "#c1531b", "s"),
        ("Esc. 3 – SR-BH 2022", esc3, "#3b4a6b", "^"),
    ]
    for label, data, color, marker in sets:
        xs = [d[1] for d in data]; ys = [d[2] for d in data]
        ax.scatter(xs, ys, s=42, color=color, marker=marker, alpha=0.8,
                   edgecolor="white", linewidth=0.5, zorder=3, label=label)
    ax.fill_between([0, 1], [0, 1], [0, 0], color="#f2c94c", alpha=0.10, zorder=0)
    ax.text(0.72, 0.22, "EIAC reduce\na Shannon", fontsize=8.5,
            color="#8a6d1d", ha="center", style="italic")
    for x, y, txt, xy in [(1.000, 0.000, "ID / Name\n(unicidad máxima)", (0.62, 0.045)),
                          (0.991, 0.184, "timestamp", (0.78, 0.30)),
                          (0.987, 0.728, "Typical Severity\n(sintético)", (0.55, 0.80))]:
        ax.annotate(txt, xy=(x, y), xytext=xy, fontsize=7.6, color="#444", ha="center",
                    arrowprops=dict(arrowstyle="-", color="#999", lw=0.7))
    ax.set_xlim(-0.03, 1.05); ax.set_ylim(-0.03, 1.05)
    ax.set_xlabel(r"$H_n(X)$  — entropía normalizada de Shannon", fontsize=9.5)
    ax.set_ylabel("EIAC  — índice de entropía informativa ajustada", fontsize=9.5)
    ax.grid(True, color=C_GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.set_aspect("equal")
    ax.legend(loc="upper left", fontsize=8.5, frameon=True, framealpha=0.95, edgecolor="#cccccc")
    fig.savefig(fname + ".pdf"); fig.savefig(fname + ".png", dpi=200)
    plt.show()

# ------------------------------------------------------------
# Generar las 4 figuras
# ------------------------------------------------------------
dumbbell(esc1, "",
         "comparacion_hn_eiac_escenario1")
dumbbell(esc2, "",
         "comparacion_hn_eiac_escenario2", row_h=0.38)
dumbbell(esc3, "",
         "comparacion_hn_eiac_escenario3", row_h=0.27)
scatter_resumen("comparacion_hn_eiac_dispersion")

# ------------------------------------------------------------
# Empaquetar y descargar todo en un .zip
# ------------------------------------------------------------
import zipfile
archivos = [
    "comparacion_hn_eiac_escenario1", "comparacion_hn_eiac_escenario2",
    "comparacion_hn_eiac_escenario3", "comparacion_hn_eiac_dispersion",
]
with zipfile.ZipFile("graficas_eiac.zip", "w") as z:
    for base in archivos:
        z.write(base + ".pdf"); z.write(base + ".png")

try:
    from google.colab import files

    files.download("graficas_eiac.zip")
except ImportError:
    print("Gráficas generadas correctamente.")
    print("ZIP disponible en: graficas_eiac.zip")