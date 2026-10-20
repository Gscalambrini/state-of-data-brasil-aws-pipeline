"""Constroi a camada Gold: tabelas especializadas, uma por tema de pergunta de
negocio, prontas para consulta direta via Athena (sem necessidade de GROUP BY
complexo no momento da consulta).

Prototipo LOCAL em pandas — mesma logica sera portada para PySpark no notebook
do Glue (notebooks/03_gold/gold_glue_notebook.ipynb).

Uso: python gold_builder.py  (depende de data/silver/*.parquet já existir)
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SILVER = ROOT / "data" / "silver"
GOLD = ROOT / "data" / "gold"

SENIORIDADE_ORDEM = ["Júnior", "Pleno", "Sênior", "Especialista/Staff+"]


def main() -> None:
    GOLD.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(SILVER / "tb_silver_respondentes.parquet")
    tec = pd.read_parquet(SILVER / "tb_silver_tecnologias_adocao.parquet")

    # ------------------------------------------------------------------
    # gold_perfil_mercado — Q1: como esta estruturado o mercado
    # grao: ano_pesquisa x regiao x cargo_atual x nivel_senioridade
    # ------------------------------------------------------------------
    perfil = (
        df.dropna(subset=["cargo_atual"])
        .groupby(["ano_pesquisa", "regiao", "cargo_atual", "nivel_senioridade"], dropna=False)
        .size()
        .reset_index(name="n_respondentes")
    )
    perfil.to_parquet(GOLD / "gold_perfil_mercado.parquet", index=False)
    print(f"gold_perfil_mercado: {len(perfil):,} linhas")

    # ------------------------------------------------------------------
    # gold_remuneracao — Q2, Q3 (gap de genero), Q6 (regiao/senioridade/modelo)
    # grao: ano_pesquisa x cargo_atual x nivel_senioridade x regiao x genero x modelo_trabalho_atual
    # ------------------------------------------------------------------
    base_sal = df.dropna(subset=["faixa_salarial_valor_medio"])
    remuneracao = (
        base_sal.groupby(
            ["ano_pesquisa", "cargo_atual", "nivel_senioridade", "regiao", "genero", "modelo_trabalho_atual"],
            dropna=False,
        )["faixa_salarial_valor_medio"]
        .agg(salario_medio="mean", salario_mediano="median", n_respondentes="count")
        .reset_index()
    )
    remuneracao.to_parquet(GOLD / "gold_remuneracao.parquet", index=False)
    print(f"gold_remuneracao: {len(remuneracao):,} linhas")

    # ------------------------------------------------------------------
    # gold_diversidade_genero — Q3
    # grao: ano_pesquisa x nivel_senioridade x genero
    # ------------------------------------------------------------------
    genero_tab = (
        df.dropna(subset=["nivel_senioridade"])
        .groupby(["ano_pesquisa", "nivel_senioridade"])["genero"]
        .value_counts(normalize=True)
        .mul(100)
        .rename("pct_dentro_do_nivel")
        .reset_index()
    )
    genero_tab.to_parquet(GOLD / "gold_diversidade_genero.parquet", index=False)
    print(f"gold_diversidade_genero: {len(genero_tab):,} linhas")

    # ------------------------------------------------------------------
    # gold_tecnologias_adocao — Q4
    # grao: ano_pesquisa x categoria_tecnologia x tecnologia
    # ------------------------------------------------------------------
    total_respondentes_ano = df.groupby("ano_pesquisa").size().rename("total_respondentes")
    tech_counts = (
        tec.groupby(["ano_pesquisa", "categoria_tecnologia", "tecnologia"])
        .size()
        .rename("n_respondentes")
        .reset_index()
    )
    tech_counts = tech_counts.merge(total_respondentes_ano, on="ano_pesquisa")
    tech_counts["pct_adocao"] = (tech_counts["n_respondentes"] / tech_counts["total_respondentes"] * 100).round(1)
    tech_counts = tech_counts.drop(columns="total_respondentes")
    tech_counts.to_parquet(GOLD / "gold_tecnologias_adocao.parquet", index=False)
    print(f"gold_tecnologias_adocao: {len(tech_counts):,} linhas")

    # ------------------------------------------------------------------
    # gold_adocao_ia — Q5
    # ------------------------------------------------------------------
    adocao_ia = (
        df.groupby("ano_pesquisa")
        .agg(
            pct_usa_ia_generativa=("usa_ia_generativa", lambda s: round(s.mean() * 100, 1)),
            pct_paga_por_ia=("paga_por_ia_generativa", lambda s: round(s.mean() * 100, 1)),
            pct_usa_ia_para_codigo=("usa_ia_para_codigo", lambda s: round(s.mean() * 100, 1)),
        )
        .reset_index()
    )
    adocao_ia.to_parquet(GOLD / "gold_adocao_ia.parquet", index=False)
    print(f"gold_adocao_ia: {len(adocao_ia):,} linhas")

    prioridade_ia = (
        df.dropna(subset=["prioridade_ia_empresa"])
        .groupby(["ano_pesquisa", "prioridade_ia_empresa"])
        .size()
        .rename("n_gestores")
        .reset_index()
    )
    total_gestores_ano = prioridade_ia.groupby("ano_pesquisa")["n_gestores"].transform("sum")
    prioridade_ia["pct_gestores"] = (prioridade_ia["n_gestores"] / total_gestores_ano * 100).round(1)
    prioridade_ia.to_parquet(GOLD / "gold_prioridade_ia_empresa.parquet", index=False)
    print(f"gold_prioridade_ia_empresa: {len(prioridade_ia):,} linhas")

    # ------------------------------------------------------------------
    # gold_modelo_trabalho — Q6
    # grao: ano_pesquisa x regiao x modelo_trabalho_atual
    # ------------------------------------------------------------------
    modelo_trabalho = (
        df.dropna(subset=["modelo_trabalho_atual"])
        .groupby(["ano_pesquisa", "regiao", "modelo_trabalho_atual"])
        .size()
        .rename("n_respondentes")
        .reset_index()
    )
    modelo_trabalho.to_parquet(GOLD / "gold_modelo_trabalho.parquet", index=False)
    print(f"gold_modelo_trabalho: {len(modelo_trabalho):,} linhas")

    print("\nTodas as tabelas Gold geradas em", GOLD)


if __name__ == "__main__":
    main()
