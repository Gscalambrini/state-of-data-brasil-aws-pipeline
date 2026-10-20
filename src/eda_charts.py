"""Gera os graficos da analise exploratoria (EDA) respondendo as 7 perguntas
de negocio do Tech Challenge, a partir da camada Silver harmonizada.

Uso: python -I eda_charts.py
Saida: presentation/charts/*.png + docs/_eda_achados.txt (achados em texto)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # backend nao-interativo: evita artefatos de janela/toolbar no PNG salvo
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from viz_style import CATEGORICAL, GENERO_CORES, INK_MUTED, INK_SECONDARY, SEQUENTIAL_MAGENTA, SURFACE, aplicar_estilo

ROOT = Path(__file__).resolve().parents[1]
SILVER = ROOT / "data" / "silver"
CHARTS_DIR = ROOT / "presentation" / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

SENIORIDADE_ORDEM = ["Júnior", "Pleno", "Sênior", "Especialista/Staff+"]
PRIORIDADE_IA_ORDEM = [
    "Não é prioridade",
    "Não sabe opinar",
    "Iniciativa isolada / pouco foco",
    "Prioridade de médio prazo",
    "Prioridade alta (foco executivo)",
]

findings = []


def achado(texto: str) -> None:
    findings.append(texto)
    print(texto)


def salvar(fig, nome: str) -> None:
    # Rede de seguranca contra o bug de "fantasma" do matplotlib/Agg: com
    # bbox_inches="tight" e rotulos de eixo longos, uma anotacao de texto
    # (ax.text) sem clip_on pode vazar um fragmento fora da area do grafico.
    # (Tentei aplicar isso tambem aos rotulos de tick via
    # ax.get_yticklabels(), mas isso quebra a renderizacao normal dos ticks
    # — os proprios rotulos somem. Por isso o fix aqui cobre so anotacoes.)
    for ax in fig.get_axes():
        for txt in ax.texts:
            txt.set_clip_on(True)
    path = CHARTS_DIR / nome
    fig.savefig(path)
    plt.close(fig)
    print(f"  -> {path}")


def fmt_milhar(x, _pos=None) -> str:
    return f"{x:,.0f}".replace(",", ".")


def fmt_reais(x, _pos=None) -> str:
    return f"R$ {x:,.0f}".replace(",", ".")


def main() -> None:
    aplicar_estilo()
    df = pd.read_parquet(SILVER / "tb_silver_respondentes.parquet")
    tec = pd.read_parquet(SILVER / "tb_silver_tecnologias_adocao.parquet")

    achado(f"Base Silver: {len(df):,} respondentes (2023-2024: {(df.ano_pesquisa==2023).sum()}, "
           f"2024-2025: {(df.ano_pesquisa==2024).sum()}, 2025-2026: {(df.ano_pesquisa==2025).sum()})")

    # ------------------------------------------------------------------
    # Q1 - Como esta estruturado o mercado brasileiro de Dados?
    # ------------------------------------------------------------------
    top_cargos = df["cargo_atual"].value_counts().head(10).sort_values()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(top_cargos.index.tolist(), top_cargos.values, color=CATEGORICAL[0])
    ax.set_title("Os 10 cargos mais comuns no mercado de Dados (BR)")
    ax.set_xlabel("Nº de respondentes (2023-2026)")
    # clip_on=True em todo ax.text() deste arquivo: sem isso, o matplotlib
    # (Agg) deixa vazar um fragmento fantasma de um dos rotulos no canto
    # inferior esquerdo da figura quando o eixo tem rotulos de categoria
    # longos (como os nomes de cargo abaixo) — bug reproduzido e isolado
    # durante o desenvolvimento, ver historico de depuracao.
    for y, v in enumerate(top_cargos.values):
        ax.text(v, y, f" {fmt_milhar(v)}", va="center", color=INK_SECONDARY, fontsize=9, clip_on=True)
    salvar(fig, "01_perfil_cargos.png")
    achado(f"Q1: cargo mais comum e '{top_cargos.index[-1]}' com {top_cargos.values[-1]:,} respondentes.")

    regiao = df["regiao"].value_counts(normalize=True).mul(100).sort_values()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(regiao.index.tolist(), regiao.values, color=CATEGORICAL[0])
    ax.set_title("Distribuição geográfica dos profissionais de Dados")
    ax.set_xlabel("% dos respondentes")
    for y, v in enumerate(regiao.values):
        ax.text(v, y, f" {v:.0f}%", va="center", color=INK_SECONDARY, fontsize=9, clip_on=True)
    salvar(fig, "02_perfil_regiao.png")
    achado(f"Q1: {regiao.iloc[-1]:.0f}% dos profissionais estão na região {regiao.index[-1]} "
           f"(concentração regional forte).")

    senior_counts = df["nivel_senioridade"].value_counts().reindex(SENIORIDADE_ORDEM).fillna(0)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(senior_counts.index.tolist(), senior_counts.values, color=CATEGORICAL[0])
    ax.set_title("Pirâmide de senioridade no mercado de Dados")
    ax.set_ylabel("Nº de respondentes")
    for x, v in enumerate(senior_counts.values):
        ax.text(x, v, f"{fmt_milhar(v)}", ha="center", va="bottom", color=INK_SECONDARY, fontsize=9, clip_on=True)
    salvar(fig, "03_perfil_senioridade.png")

    # ------------------------------------------------------------------
    # Q2 - Quais perfis profissionais sao mais valorizados pelo mercado?
    # ------------------------------------------------------------------
    cargo_stats = df.groupby("cargo_atual")["faixa_salarial_valor_medio"].agg(["mean", "count"])
    cargo_stats = cargo_stats[cargo_stats["count"] >= 50].sort_values("count", ascending=False).head(10)
    cargo_stats = cargo_stats.sort_values("mean")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(cargo_stats.index.tolist(), cargo_stats["mean"], color=CATEGORICAL[0])
    ax.set_title("Remuneração média por cargo (entre os 10 cargos mais comuns)")
    ax.set_xlabel("Salário médio estimado (R$/mês)")
    for y, v in enumerate(cargo_stats["mean"]):
        ax.text(v, y, f" {fmt_reais(v)}", va="center", color=INK_SECONDARY, fontsize=9, clip_on=True)
    salvar(fig, "04_salario_por_cargo.png")
    top_pago = cargo_stats.index[-1]
    achado(f"Q2: entre os cargos mais comuns, '{top_pago}' tem a maior remuneração média "
           f"(R$ {cargo_stats['mean'].iloc[-1]:,.0f}/mês).")

    # ------------------------------------------------------------------
    # Q3 - Diversidade de genero
    # ------------------------------------------------------------------
    genero_geral = df["genero"].value_counts(normalize=True).mul(100)
    achado(f"Q3: {genero_geral.get('Feminino', 0):.1f}% dos respondentes se identificam como mulheres "
           f"(mercado ainda majoritariamente masculino: {genero_geral.get('Masculino', 0):.1f}%).")

    gs = df[df["genero"].isin(["Masculino", "Feminino"])]
    ct = pd.crosstab(gs["nivel_senioridade"], gs["genero"], normalize="index").mul(100)
    ct = ct.reindex(SENIORIDADE_ORDEM)
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    x = np.arange(len(ct.index))
    width = 0.35
    ax.bar(x - width / 2, ct["Masculino"], width, label="Masculino", color=GENERO_CORES["Masculino"])
    ax.bar(x + width / 2, ct["Feminino"], width, label="Feminino", color=GENERO_CORES["Feminino"])
    ax.set_xticks(x)
    ax.set_xticklabels(ct.index.tolist())
    ax.set_ylabel("% dentro do nível")
    ax.set_ylim(0, 92)
    fig.suptitle("Participação feminina cai conforme sobe a senioridade", fontsize=14, fontweight="bold", y=1.04)
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    fig.tight_layout()
    salvar(fig, "05_diversidade_genero_senioridade.png")
    queda = ct["Feminino"].iloc[0] - ct["Feminino"].iloc[-1]
    achado(f"Q3: participação feminina cai de {ct['Feminino'].iloc[0]:.0f}% (Júnior) para "
           f"{ct['Feminino'].loc['Sênior']:.0f}% (Sênior) — queda de {queda:.0f} p.p., evidência de "
           f"'funil furado' (leaky pipeline).")

    sal_genero = gs.groupby(["nivel_senioridade", "genero"])["faixa_salarial_valor_medio"].mean().unstack()
    sal_genero = sal_genero.reindex(SENIORIDADE_ORDEM)
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.bar(x - width / 2, sal_genero["Masculino"], width, label="Masculino", color=GENERO_CORES["Masculino"])
    ax.bar(x + width / 2, sal_genero["Feminino"], width, label="Feminino", color=GENERO_CORES["Feminino"])
    ax.set_xticks(x)
    ax.set_xticklabels(sal_genero.index.tolist())
    ax.set_ylabel("Salário médio estimado (R$/mês)")
    ax.set_title("Diferença salarial entre gêneros, por senioridade")
    ax.legend(frameon=False)
    salvar(fig, "06_gap_salarial_genero.png")
    gap_senior = (1 - sal_genero["Feminino"].loc["Sênior"] / sal_genero["Masculino"].loc["Sênior"]) * 100
    achado(f"Q3: no nível Sênior, mulheres recebem em média {gap_senior:.0f}% menos que homens "
           f"(R$ {sal_genero['Feminino'].loc['Sênior']:,.0f} vs R$ {sal_genero['Masculino'].loc['Sênior']:,.0f}).")

    # ------------------------------------------------------------------
    # Q4 - Tecnologias com maior adocao
    #
    # Esta figura de 4 paineis e gerada dentro de um plt.rc_context resetado
    # para o padrao do matplotlib (em vez do estilo global de aplicar_estilo).
    # Motivo: com o estilo global ativo, plotar 4 categorias desta mesma
    # tabela longa (tec) em sequencia numa figura de 4 eixos causava uma
    # corrupcao de renderizacao reprodutivel do matplotlib/Agg — rotulos de
    # eixo sumindo e fragmentos de texto de OUTRAS categorias vazando entre
    # paineis. Isolar a geracao num rc_context com os parametros padrao
    # elimina o bug (bug isolado e confirmado durante o desenvolvimento;
    # a causa exata da interacao dentro do matplotlib nao foi determinada).
    # As cores/estilo da marca sao reaplicadas manualmente aqui dentro.
    # ------------------------------------------------------------------
    categorias_labels = {
        "linguagem": "Linguagens de programação",
        "banco_dados": "Bancos de dados",
        "cloud": "Provedores de Cloud",
        "ferramenta_bi": "Ferramentas de BI",
    }
    with plt.rc_context(rc=matplotlib.rcParamsDefault):
        # figsize com proporcao ~2.16:1 (casa com a caixa de imagem do slide,
        # 12.1x5.6pol no build_deck.js) — antes era 12x9 (4:3), que o "contain"
        # do pptxgenjs encolhia pela altura, desperdicando largura e deixando
        # os 4 paineis pequenos/apertados no slide final.
        fig, axes = plt.subplots(2, 2, figsize=(15, 6.94))
        for ax, (cat, label) in zip(axes.flat, categorias_labels.items()):
            top = (
                tec[tec["categoria_tecnologia"] == cat]["tecnologia"]
                .value_counts().head(6).sort_values()
            )
            ax.barh(top.index.tolist(), top.values, color=CATEGORICAL[0])
            ax.set_title(label, fontsize=12, fontweight="bold")
            ax.tick_params(labelsize=9)
        fig.suptitle("Tecnologias mais adotadas pelos profissionais de Dados (2023-2026)",
                      fontsize=14, fontweight="bold")
        fig.tight_layout(rect=(0, 0, 1, 0.96))
        out_path = CHARTS_DIR / "07_tecnologias_adocao_painel.png"
        fig.savefig(out_path, facecolor=SURFACE, dpi=150, bbox_inches="tight")
        plt.close(fig)
    print(f"  -> {out_path}")

    linguagens_top = tec[tec["categoria_tecnologia"] == "linguagem"]["tecnologia"].value_counts().head(3).index.tolist()
    evol = (
        tec[(tec["categoria_tecnologia"] == "linguagem") & (tec["tecnologia"].isin(linguagens_top))]
        .groupby(["ano_pesquisa", "tecnologia"]).size().unstack()
    )
    totais_por_ano = df.groupby("ano_pesquisa").size()
    evol_pct = evol.div(totais_por_ano, axis=0).mul(100)
    # Python recebe a cor hero (magenta) de propósito — é o protagonista do achado.
    cor_linguagem = {"Python": CATEGORICAL[0], "SQL": CATEGORICAL[1], "R": CATEGORICAL[2]}
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for lang in linguagens_top:
        ax.plot(evol_pct.index, evol_pct[lang], marker="o", linewidth=2, markersize=7,
                color=cor_linguagem.get(lang, INK_MUTED), label=lang)
    ax.set_xticks(evol_pct.index)
    ax.set_ylabel("% dos respondentes que usam")
    ax.set_title("Evolução das linguagens mais usadas (2023-2026)")
    ax.legend(frameon=False)
    ax.set_ylim(0, 100)
    salvar(fig, "08_evolucao_linguagens.png")
    py_2023 = evol_pct.loc[2023, "Python"] if "Python" in evol_pct.columns else None
    py_2025 = evol_pct.loc[2025, "Python"] if "Python" in evol_pct.columns else None
    sql_2023 = evol_pct.loc[2023, "SQL"] if "SQL" in evol_pct.columns else None
    sql_2025 = evol_pct.loc[2025, "SQL"] if "SQL" in evol_pct.columns else None
    if py_2023 is not None and sql_2023 is not None:
        achado(f"Q4: Python passou de {py_2023:.0f}% (2023) para {py_2025:.0f}% (2025) de adoção, "
               f"ultrapassando o SQL (de {sql_2023:.0f}% para {sql_2025:.0f}%) como linguagem nº 1.")

    # ------------------------------------------------------------------
    # Q5 - Adocao de IA e seu impacto
    # ------------------------------------------------------------------
    adocao_ano = df.groupby("ano_pesquisa")["usa_ia_generativa"].mean().mul(100)
    prioridade = df["prioridade_ia_empresa"].value_counts(normalize=True).mul(100).reindex(PRIORIDADE_IA_ORDEM).fillna(0)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    ax = axes[0]
    ax.plot(adocao_ano.index, adocao_ano.values, marker="o", linewidth=2.5, markersize=8, color=CATEGORICAL[0])
    for xi, yi in zip(adocao_ano.index, adocao_ano.values):
        ax.text(xi, yi + 1.5, f"{yi:.0f}%", ha="center", color=INK_SECONDARY, fontsize=10, clip_on=True)
    ax.set_xticks(adocao_ano.index)
    ax.set_ylim(0, 105)
    ax.set_ylabel("% que usa IA Generativa no trabalho")
    ax.set_title("Adoção individual de IA Generativa dispara")

    ax = axes[1]
    colors_ordinal = [SEQUENTIAL_MAGENTA[i] for i in [1, 2, 3, 4, 5]]
    ax.barh(prioridade.index.tolist(), prioridade.values, color=colors_ordinal)
    ax.set_xlabel("% dos gestores")
    ax.set_title("Prioridade de IA Generativa nas empresas\n(na visão de quem gerencia times de dados)")
    for y, v in enumerate(prioridade.values):
        ax.text(v, y, f" {v:.0f}%", va="center", color=INK_SECONDARY, fontsize=9, clip_on=True)
    fig.tight_layout()
    salvar(fig, "09_adocao_ia_e_prioridade.png")
    achado(f"Q5: adoção individual de IA Generativa saltou de {adocao_ano.loc[2023]:.0f}% (2023) para "
           f"{adocao_ano.loc[2025]:.0f}% (2025).")
    achado(f"Q5: apenas {prioridade['Prioridade alta (foco executivo)']:.0f}% dos gestores dizem que IA "
           f"Generativa é 'prioridade alta' da empresa — gap entre uso individual e estratégia formal.")

    # gap individual vs empresa (mesma edicao 2025, bases diferentes: todos vs gestores)
    uso_2025 = adocao_ano.loc[2025]
    prio_alta_2025 = df.loc[df.ano_pesquisa == 2025, "prioridade_ia_empresa"].value_counts(normalize=True).mul(100).get(
        "Prioridade alta (foco executivo)", 0
    )
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    bars = ax.bar(
        ["Profissionais que usam\nIA no dia a dia\n(todos, 2025)",
         "Empresas com IA como\n'prioridade alta'\n(visão de gestores, 2025)"],
        [uso_2025, prio_alta_2025],
        color=[CATEGORICAL[0], CATEGORICAL[1]],
    )
    ax.set_ylim(0, 105)
    ax.set_ylabel("%")
    ax.set_title("O uso individual de IA corre à frente da estratégia corporativa")
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + 1.5, f"{h:.0f}%", ha="center", color=INK_SECONDARY, clip_on=True)
    salvar(fig, "10_gap_individual_vs_empresa_ia.png")

    # ------------------------------------------------------------------
    # Q6 - Diferencas por regiao, senioridade e modelo de trabalho
    # ------------------------------------------------------------------
    sal_regiao = df.groupby("regiao")["faixa_salarial_valor_medio"].mean().sort_values()
    sal_modelo = df.groupby("modelo_trabalho_atual")["faixa_salarial_valor_medio"].mean().sort_values()
    sal_modelo.index = [i.split(" (")[0].replace("Modelo ", "") for i in sal_modelo.index]

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    axes[0].barh(sal_regiao.index.tolist(), sal_regiao.values, color=CATEGORICAL[0])
    axes[0].set_title("Salário médio por região")
    axes[0].set_xlabel("R$/mês (estimado)")
    for y, v in enumerate(sal_regiao.values):
        axes[0].text(v, y, f" {fmt_reais(v)}", va="center", fontsize=9, color=INK_SECONDARY, clip_on=True)

    axes[1].barh(sal_modelo.index.tolist(), sal_modelo.values, color=CATEGORICAL[0])
    axes[1].set_title("Salário médio por modelo de trabalho")
    axes[1].set_xlabel("R$/mês (estimado)")
    for y, v in enumerate(sal_modelo.values):
        axes[1].text(v, y, f" {fmt_reais(v)}", va="center", fontsize=9, color=INK_SECONDARY, clip_on=True)
    fig.tight_layout()
    salvar(fig, "11_salario_regiao_modelo_trabalho.png")
    achado(f"Q6: região com maior salário médio é {sal_regiao.index[-1]} "
           f"(R$ {sal_regiao.values[-1]:,.0f}), {(sal_regiao.values[-1]/sal_regiao.values[0]-1)*100:.0f}% "
           f"acima da região {sal_regiao.index[0]}.")

    out_path = ROOT / "docs" / "_eda_achados.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(findings))
    print(f"\nAchados salvos em {out_path}")


if __name__ == "__main__":
    main()
