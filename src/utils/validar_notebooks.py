"""Valida que os .ipynb gerados sao JSON valido e que cada celula de codigo
compila como Python valido (nao executa - so checa sintaxe), para pegar erros
de escaping antes de levar ao Glue de verdade.
Uso: python validar_notebooks.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOKS = [
    ROOT / "notebooks/01_bronze/bronze_glue_notebook.ipynb",
    ROOT / "notebooks/02_silver/silver_glue_notebook.ipynb",
    ROOT / "notebooks/03_gold/gold_glue_notebook.ipynb",
    ROOT / "notebooks/04_eda/eda_glue_notebook.ipynb",
]

for path in NOTEBOOKS:
    print(f"\n=== {path.name} ===")
    nb = json.loads(path.read_text(encoding="utf-8"))
    print(f"  JSON ok, {len(nb['cells'])} celulas")
    ok = True
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        if src.strip().startswith("%"):
            continue  # celula e so magic do Glue/Jupyter, nao e Python puro
        # remove linhas de magic (ex: "%matplot plt") que podem aparecer no
        # meio de uma celula mista de codigo Python + magic
        src_sem_magics = "\n".join(l for l in src.splitlines() if not l.strip().startswith("%"))
        try:
            compile(src_sem_magics, f"{path.name}:cell{i}", "exec")
        except SyntaxError as e:
            ok = False
            print(f"  ERRO DE SINTAXE na celula {i}: {e}")
            print(f"  --- conteudo ---\n{src}\n----------------")
    if ok:
        print("  todas as celulas de codigo compilam OK")
