"""Paleta e estilo compartilhado para os graficos da EDA / material executivo.

Paleta ancorada na cor oficial da marca FIAP (magenta #ED145B, extraida
diretamente das variaveis CSS de fiap.com.br), combinada com as demais cores
do skill de dataviz usado no desenvolvimento (references/palette.md) e
checada manualmente para CVD-safety e contraste em modo claro e escuro.
"""
import matplotlib.pyplot as plt

FIAP_MAGENTA = "#ED145B"
FIAP_BLACK = "#0E0F10"
FIAP_GRAY = "#75838B"

# Ordem fixa e validada (CVD-safe); magenta FIAP como cor hero/primaria.
CATEGORICAL = [
    FIAP_MAGENTA,  # 1 magenta (marca FIAP): serie primaria / destaque
    "#2a78d6",     # 2 azul
    "#008300",     # 3 verde
    "#eda100",     # 4 amarelo/ambar (usar sempre com rotulo direto no valor)
    "#6250d6",     # 5 violeta
]

# Ramp sequencial de magnitude (ex: prioridade ordinal), do claro ao escuro,
# na mesma tonalidade da marca.
SEQUENTIAL_MAGENTA = ["#fcd9e5", "#f9b3ca", "#f57aa2", "#ed145b", "#bd0f48", "#8e0b36"]

INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"

GENERO_CORES = {
    "Masculino": CATEGORICAL[0],
    "Feminino": CATEGORICAL[1],
    "Outro": CATEGORICAL[3],
    "Prefiro não informar": INK_MUTED,
}


def aplicar_estilo():
    plt.rcParams.update({
        "font.family": ["Calibri", "Segoe UI", "Arial", "DejaVu Sans", "sans-serif"],
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": BASELINE,
        "axes.labelcolor": INK_SECONDARY,
        "axes.titlecolor": INK_PRIMARY,
        "axes.titleweight": "bold",
        "axes.titlesize": 14,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRIDLINE,
        "grid.linewidth": 0.8,
        "xtick.color": INK_MUTED,
        "ytick.color": INK_MUTED,
        "text.color": INK_PRIMARY,
        "font.size": 11,
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "savefig.facecolor": SURFACE,
        "savefig.bbox": "tight",
    })
