"""Diagnostico LOCAL (fora de data/): confere encoding e valores unicos dos
campos categoricos chave em cada edicao, para alinhar a harmonizacao da Silver.

Uso: python -I diagnostico_categorias.py
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "2023-2024": ROOT / "data/raw/2023-2024/state_of_data_2023_2024.csv",
    "2024-2025": ROOT / "data/raw/2024-2025/state_of_data_2024_2025.csv",
    "2025-2026": ROOT / "data/raw/2025-2026/state_of_data_2025_2026.csv",
}

# indices posicionais (0-based) dos campos categoricos chave, por edicao
KEY_FIELDS = {
    "2023-2024": {
        "genero": 3,
        "cor_raca_etnia": 4,
        "pcd": 5,
        "regiao": 24,
        "nivel_ensino": 27,
        "situacao_trabalho": 29,
        "gestor": 32,
        "nivel_senioridade": 35,
        "faixa_salarial": 36,
        "tempo_exp_dados": 37,
        "modelo_trabalho_atual": 62,
        "empresa_prioriza_ia_generativa": 103,
        "uso_ia_generativa_individual": 238,
    },
    "2025-2026": {
        "genero": 4,
        "cor_raca_etnia": 5,
        "pcd": 6,
        "regiao": 26,
        "nivel_ensino": 31,
        "situacao_trabalho": 33,
        "gestor": 36,
        "nivel_senioridade": 39,
        "faixa_salarial": 40,
        "tempo_exp_dados": 41,
        "modelo_trabalho_atual": 70,
        "empresa_prioriza_ia_generativa": 112,
        "uso_ia_generativa_individual": 227,
    },
    "2024-2025": {
        "genero": 4,
        "cor_raca_etnia": 5,
        "pcd": 6,
        "vive_no_brasil": 26,
        "regiao": 22,
        "nivel_ensino": 31,
        "situacao_trabalho": 33,
        "gestor": 36,
        "satisfeito": 43,
        "nivel_senioridade": 39,
        "faixa_salarial": 40,
        "tempo_exp_dados": 41,
        "modelo_trabalho_atual": 70,
        "empresa_prioriza_ia_generativa": 112,
        "uso_ia_generativa_individual": 242,
    },
}

out_path = ROOT / "docs" / "_diagnostico_categorias.txt"
with open(out_path, "w", encoding="utf-8") as out:
    for edition, path in FILES.items():
        out.write(f"\n{'#' * 100}\n# EDICAO {edition}\n{'#' * 100}\n")
        df = pd.read_csv(path, encoding="utf-8", encoding_errors="replace", dtype=str, keep_default_na=False)
        out.write(f"Shape: {df.shape}\n")
        for field_name, idx in KEY_FIELDS[edition].items():
            col = df.columns[idx]
            out.write(f"\n--- {field_name}  (coluna [{idx}]: {col!r}) ---\n")
            vc = df.iloc[:, idx].value_counts(dropna=False)
            out.write(vc.to_string() + "\n")
print(f"Diagnostico escrito em {out_path}")
