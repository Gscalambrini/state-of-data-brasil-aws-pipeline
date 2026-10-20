"""Valida o resultado da harmonizacao Silver: nulos, distribuicoes, amostras.
Uso: python -I validar_silver.py
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SILVER = ROOT / "data" / "silver"

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 50)

out_path = ROOT / "docs" / "_validacao_silver.txt"
with open(out_path, "w", encoding="utf-8") as out:
    df = pd.read_parquet(SILVER / "tb_silver_respondentes.parquet")

    out.write(f"Shape: {df.shape}\n\n")
    out.write("--- dtypes ---\n")
    out.write(df.dtypes.to_string() + "\n\n")

    out.write("--- % nulos por coluna ---\n")
    out.write((df.isna().mean() * 100).round(1).sort_values(ascending=False).to_string() + "\n\n")

    out.write("--- amostra (5 linhas aleatorias, colunas chave) ---\n")
    cols_amostra = [
        "id_unico", "ano_pesquisa", "genero", "regiao", "cargo_atual",
        "nivel_senioridade", "faixa_salarial", "faixa_salarial_valor_medio",
        "modelo_trabalho_atual", "prioridade_ia_empresa",
        "usa_ia_generativa", "paga_por_ia_generativa", "usa_ia_para_codigo",
    ]
    out.write(df[cols_amostra].sample(5, random_state=42).to_string() + "\n\n")

    out.write("--- nivel_senioridade por ano_pesquisa (conta 'Especialista/Staff+' por ano) ---\n")
    out.write(pd.crosstab(df["ano_pesquisa"], df["nivel_senioridade"]).to_string() + "\n\n")

    out.write("--- salario medio por nivel_senioridade e ano ---\n")
    pivot = df.pivot_table(
        values="faixa_salarial_valor_medio", index="nivel_senioridade",
        columns="ano_pesquisa", aggfunc="mean",
    ).round(0)
    out.write(pivot.to_string() + "\n\n")

    out.write("--- genero por nivel_senioridade (% dentro de cada nivel) ---\n")
    ct = pd.crosstab(df["nivel_senioridade"], df["genero"], normalize="index") * 100
    out.write(ct.round(1).to_string() + "\n\n")

    out.write("--- usa_ia_generativa (%) por ano_pesquisa ---\n")
    out.write((df.groupby("ano_pesquisa")["usa_ia_generativa"].mean() * 100).round(1).to_string() + "\n\n")

    tec = pd.read_parquet(SILVER / "tb_silver_tecnologias_adocao.parquet")
    out.write(f"\n\nTecnologias long shape: {tec.shape}\n")
    out.write("--- top 10 linguagens por ano (contagem) ---\n")
    top_lang = (
        tec[tec["categoria_tecnologia"] == "linguagem"]
        .groupby(["ano_pesquisa", "tecnologia"]).size()
        .reset_index(name="n")
        .sort_values(["ano_pesquisa", "n"], ascending=[True, False])
    )
    for ano, grp in top_lang.groupby("ano_pesquisa"):
        out.write(f"\n{ano}:\n")
        out.write(grp.head(10)[["tecnologia", "n"]].to_string(index=False) + "\n")

print(f"Validacao escrita em {out_path}")
