"""Gera os mesmos 11 graficos de src/eda_charts.py, mas a partir dos numeros
REAIS obtidos ao vivo via Amazon Athena contra as tabelas Gold no AWS real
(db_techchallenge_gt_fiap), em 2026-10-19 — nao a partir do protótipo local em
pandas (que usa CSVs de referencia diferentes dos que estao realmente no S3
do time, e por isso produz numeros levemente diferentes, ex. 14.002 vs os
13.057 respondentes reais).

Os valores abaixo foram copiados manualmente dos resultados do Athena (cada
bloco cita a query equivalente em notebooks/05_analytics_athena/*.sql) — nao
ha leitura de arquivo/parquet neste script, de proposito, para que o numero
aqui seja uma transcricao direta e auditavel do que o Athena retornou.

Uso: python -I eda_charts_aws.py
Saida: presentation/charts/*.png (sobrescreve) + docs/_eda_achados.txt
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from viz_style import CATEGORICAL, GENERO_CORES, INK_MUTED, INK_SECONDARY, SEQUENTIAL_MAGENTA, SURFACE, aplicar_estilo

ROOT = Path(__file__).resolve().parents[1]
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
    for ax in fig.get_axes():
        for txt in ax.texts:
            txt.set_clip_on(True)
    path = CHARTS_DIR / nome
    fig.savefig(path)
    plt.close(fig)
    print(f"  -> {path}")


def fmt_reais(x, _pos=None) -> str:
    return f"R$ {x:,.0f}".replace(",", ".")


def fmt_milhar(x) -> str:
    return f"{x:,.0f}".replace(",", ".")


def main() -> None:
    aplicar_estilo()

    TOTAL_RESPONDENTES = 13_057
    achado(
        f"Base Gold (AWS real): {fmt_milhar(TOTAL_RESPONDENTES)} respondentes "
        f"(2023-2024=4.270, 2024-2025=5.293, 2025-2026=3.494)."
    )

    # ------------------------------------------------------------------
    # Q1 - Como esta estruturado o mercado brasileiro de Dados?
    # Fonte: notebooks/05_analytics_athena/q1_estrutura_mercado.sql (1a, 1c)
    # ------------------------------------------------------------------
    top_cargos = {
        "Analista de Dados": 2145,
        "Cientista de Dados": 1666,
        "Engenheiro de Dados/Arquiteto": 1174,
        "Analista de BI": 1099,
        "Analista de Negócios": 459,
        "Engenheiro de Dados": 402,
        "Analytics Engineer": 344,
        "Dev./Eng. de Software": 317,
        "Analista de Suporte/Técnico": 199,
        "Eng. de Machine Learning/IA": 181,
    }
    items = sorted(top_cargos.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh([k for k, _ in items], [v for _, v in items], color=CATEGORICAL[0])
    ax.set_title("Os 10 cargos mais comuns no mercado de Dados (BR)")
    ax.set_xlabel("Nº de respondentes (2023-2026)")
    for y, (_, v) in enumerate(items):
        ax.text(v, y, f" {v:,}".replace(",", "."), va="center", color=INK_SECONDARY, fontsize=9, clip_on=True)
    salvar(fig, "01_perfil_cargos.png")
    achado(f"Q1: cargo mais comum é '{items[-1][0]}' com {fmt_milhar(items[-1][1])} respondentes.")

    # Fonte: q1_estrutura_mercado.sql (1b) — % entre quem informou a região
    regiao = {
        "Sudeste": 61.1,
        "Sul": 17.7,
        "Nordeste": 11.2,
        "Centro-oeste": 6.2,
        "Não informado": 2.3,
        "Norte": 1.5,
    }
    reg_items = sorted(regiao.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh([k for k, _ in reg_items], [v for _, v in reg_items], color=CATEGORICAL[0])
    ax.set_title("Distribuição geográfica dos profissionais de Dados")
    ax.set_xlabel("% dos respondentes")
    for y, (_, v) in enumerate(reg_items):
        ax.text(v, y, f" {v:.0f}%", va="center", color=INK_SECONDARY, fontsize=9, clip_on=True)
    salvar(fig, "02_perfil_regiao.png")
    achado("Q1: 61% dos profissionais estão na região Sudeste (concentração regional forte).")

    # Fonte: q1_estrutura_mercado.sql (1c), somado por nível (todas as edições)
    senior_counts = {"Júnior": 2587, "Pleno": 3227, "Sênior": 3175, "Especialista/Staff+": 349}
    fig, ax = plt.subplots(figsize=(7, 4))
    vals = [senior_counts[k] for k in SENIORIDADE_ORDEM]
    ax.bar(SENIORIDADE_ORDEM, vals, color=CATEGORICAL[0])
    ax.set_title("Pirâmide de senioridade no mercado de Dados")
    ax.set_ylabel("Nº de respondentes")
    for x, v in enumerate(vals):
        ax.text(x, v, f"{v:,}".replace(",", "."), ha="center", va="bottom", color=INK_SECONDARY, fontsize=9, clip_on=True)
    salvar(fig, "03_perfil_senioridade.png")

    # ------------------------------------------------------------------
    # Q2 - Quais perfis profissionais sao mais valorizados pelo mercado?
    # Fonte: q2_perfis_mais_valorizados.sql (query 1, n >= 50)
    # ------------------------------------------------------------------
    cargo_sal = {
        "Eng. de ML/AI Engineer": 16382,
        "Eng. de Machine Learning": 14414,
        "Eng. de Dados/Data Architect": 14294,
        "Data Product Manager": 13312,
        "Analytics Engineer": 11976,
        "Product Manager/Owner": 11275,
        "Eng. de Dados/Arquiteto": 11050,
        "Cientista de Dados": 10978,
        "Dev./Eng. de Software": 9980,
        "Outras Engenharias": 9089,
    }
    sal_items = sorted(cargo_sal.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh([k for k, _ in sal_items], [v for _, v in sal_items], color=CATEGORICAL[0])
    ax.set_title("Remuneração média por cargo (cargos com ≥ 50 respondentes)")
    ax.set_xlabel("Salário médio estimado (R$/mês)")
    for y, (_, v) in enumerate(sal_items):
        ax.text(v, y, f" {fmt_reais(v)}", va="center", color=INK_SECONDARY, fontsize=9, clip_on=True)
    salvar(fig, "04_salario_por_cargo.png")
    achado(f"Q2: '{sal_items[-1][0]}' tem a maior remuneração média (R$ {fmt_milhar(sal_items[-1][1])}/mês).")

    # ------------------------------------------------------------------
    # Q3 - Diversidade de genero
    # Fonte: tb_silver_respondentes (geral) + q3_diversidade_genero.sql (3a, 3b)
    # ------------------------------------------------------------------
    achado("Q3: 23.9% dos respondentes se identificam como mulheres (mercado ainda majoritariamente masculino: 75.6%).")

    genero_senioridade = {
        "Júnior": {"Masculino": 70.8, "Feminino": 28.2},
        "Pleno": {"Masculino": 77.3, "Feminino": 22.3},
        "Sênior": {"Masculino": 78.7, "Feminino": 20.7},
        "Especialista/Staff+": {"Masculino": 79.1, "Feminino": 20.1},
    }
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    x = np.arange(len(SENIORIDADE_ORDEM))
    width = 0.35
    masc = [genero_senioridade[k]["Masculino"] for k in SENIORIDADE_ORDEM]
    fem = [genero_senioridade[k]["Feminino"] for k in SENIORIDADE_ORDEM]
    ax.bar(x - width / 2, masc, width, label="Masculino", color=GENERO_CORES["Masculino"])
    ax.bar(x + width / 2, fem, width, label="Feminino", color=GENERO_CORES["Feminino"])
    ax.set_xticks(x)
    ax.set_xticklabels(SENIORIDADE_ORDEM)
    ax.set_ylabel("% dentro do nível (edição 2025-2026)")
    ax.set_ylim(0, 92)
    fig.suptitle("Participação feminina cai conforme sobe a senioridade", fontsize=14, fontweight="bold", y=1.04)
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    fig.tight_layout()
    salvar(fig, "05_diversidade_genero_senioridade.png")
    achado("Q3: participação feminina cai de 28,2% (Júnior) para 20,1% (Especialista/Staff+) na edição mais "
           "recente — queda de ~8 p.p., evidência de 'funil furado' (leaky pipeline).")

    sal_genero = {
        "Júnior": {"Masculino": 4025, "Feminino": 3814},
        "Pleno": {"Masculino": 7916, "Feminino": 7731},
        "Sênior": {"Masculino": 14097, "Feminino": 12012},
        "Especialista/Staff+": {"Masculino": 20618, "Feminino": 17543},
    }
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    masc_s = [sal_genero[k]["Masculino"] for k in SENIORIDADE_ORDEM]
    fem_s = [sal_genero[k]["Feminino"] for k in SENIORIDADE_ORDEM]
    ax.bar(x - width / 2, masc_s, width, label="Masculino", color=GENERO_CORES["Masculino"])
    ax.bar(x + width / 2, fem_s, width, label="Feminino", color=GENERO_CORES["Feminino"])
    ax.set_xticks(x)
    ax.set_xticklabels(SENIORIDADE_ORDEM)
    ax.set_ylabel("Salário médio estimado (R$/mês)")
    ax.set_title("Diferença salarial entre gêneros, por senioridade")
    ax.legend(frameon=False)
    salvar(fig, "06_gap_salarial_genero.png")
    gap_senior = (1 - sal_genero["Sênior"]["Feminino"] / sal_genero["Sênior"]["Masculino"]) * 100
    achado(f"Q3: no nível Sênior, mulheres recebem em média {gap_senior:.0f}% menos que homens "
           f"(R$ {fmt_milhar(sal_genero['Sênior']['Feminino'])} vs R$ {fmt_milhar(sal_genero['Sênior']['Masculino'])}).")

    # ------------------------------------------------------------------
    # Q4 - Tecnologias com maior adocao (edição 2025-2026)
    # Fonte: q4_tecnologias_mais_adotadas.sql (4a, 4b)
    # ------------------------------------------------------------------
    categorias_dados = {
        "Linguagens de programação": {"python": 55.2, "sql": 50.5, "r": 9.4, "scala": 2.0, "rust": 1.0},
        "Bancos de dados": {"postgresql": 22.1, "sql_server": 20.1, "databricks": 19.7, "s3": 17.3, "mysql": 17.1},
        "Provedores de Cloud": {"aws": 28.9, "azure": 20.9, "google_cloud": 18.5, "on-premise/não usa": 8.6, "cloud própria": 3.3},
        "Ferramentas de BI": {"power_bi": 35.5, "looker": 13.6, "looker_studio": 9.4, "tableau": 8.2, "nenhuma": 6.8},
    }
    with plt.rc_context(rc=matplotlib.rcParamsDefault):
        fig, axes = plt.subplots(2, 2, figsize=(15, 6.94))
        for ax, (label, vals) in zip(axes.flat, categorias_dados.items()):
            pairs = sorted(vals.items(), key=lambda kv: kv[1])
            ax.barh([k for k, _ in pairs], [v for _, v in pairs], color=CATEGORICAL[0])
            ax.set_title(label, fontsize=12, fontweight="bold")
            ax.tick_params(labelsize=9)
        fig.suptitle("Tecnologias mais adotadas pelos profissionais de Dados (edição 2025-2026)",
                      fontsize=14, fontweight="bold")
        fig.tight_layout(rect=(0, 0, 1, 0.96))
        out_path = CHARTS_DIR / "07_tecnologias_adocao_painel.png"
        fig.savefig(out_path, facecolor=SURFACE, dpi=150, bbox_inches="tight")
        plt.close(fig)
    print(f"  -> {out_path}")

    evol = {
        "python": {2023: 48.9, 2024: 53.4, 2025: 55.2},
        "sql": {2023: 55.4, 2024: 59.6, 2025: 50.5},
        "r": {2023: 9.0, 2024: 7.7, 2025: 9.4},
    }
    cor_linguagem = {"python": CATEGORICAL[0], "sql": CATEGORICAL[1], "r": CATEGORICAL[2]}
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    anos = [2023, 2024, 2025]
    for lang, serie in evol.items():
        ax.plot(anos, [serie[a] for a in anos], marker="o", linewidth=2, markersize=7,
                color=cor_linguagem.get(lang, INK_MUTED), label=lang.upper() if lang != "python" else "Python")
    ax.set_xticks(anos)
    ax.set_ylabel("% dos respondentes que usam")
    ax.set_title("Evolução das linguagens mais usadas (2023-2025)")
    ax.legend(frameon=False)
    ax.set_ylim(0, 100)
    salvar(fig, "08_evolucao_linguagens.png")
    achado(f"Q4: Python passou de {evol['python'][2023]:.0f}% (2023) para {evol['python'][2025]:.0f}% (2025) de "
           f"adoção; SQL caiu de {evol['sql'][2023]:.0f}% (2023) para {evol['sql'][2025]:.0f}% (2025) — Python "
           f"ultrapassa o SQL como linguagem nº 1 entre 2024 e 2025.")

    # ------------------------------------------------------------------
    # Q5 - Adocao de IA e seu impacto
    # Fonte: q5_adocao_ia.sql (5a, 5b) — 2023 não mede IA Generativa nessa edição
    # ------------------------------------------------------------------
    adocao_ano = {2024: 80.3, 2025: 97.9}
    prioridade = {
        "Não é prioridade": 11.3,
        "Não sabe opinar": 2.1,
        "Iniciativa isolada / pouco foco": 25.9,
        "Prioridade de médio prazo": 36.8,
        "Prioridade alta (foco executivo)": 23.8,
    }

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    ax = axes[0]
    anos_ia = sorted(adocao_ano)
    ax.plot(anos_ia, [adocao_ano[a] for a in anos_ia], marker="o", linewidth=2.5, markersize=8, color=CATEGORICAL[0])
    for xi in anos_ia:
        ax.text(xi, adocao_ano[xi] + 1.5, f"{adocao_ano[xi]:.0f}%", ha="center", color=INK_SECONDARY, fontsize=10, clip_on=True)
    ax.set_xticks(anos_ia)
    ax.set_ylim(0, 105)
    ax.set_ylabel("% que usa IA Generativa no trabalho")
    ax.set_title("Adoção individual de IA Generativa dispara\n(2023-2024 não mediu esta pergunta)")

    ax = axes[1]
    prio_items = [(k, prioridade[k]) for k in PRIORIDADE_IA_ORDEM]
    colors_ordinal = [SEQUENTIAL_MAGENTA[i] for i in [1, 2, 3, 4, 5]]
    ax.barh([k for k, _ in prio_items], [v for _, v in prio_items], color=colors_ordinal)
    ax.set_xlabel("% dos gestores (edição 2025-2026)")
    ax.set_title("Prioridade de IA Generativa nas empresas\n(na visão de quem gerencia times de dados)")
    for y, (_, v) in enumerate(prio_items):
        ax.text(v, y, f" {v:.0f}%", va="center", color=INK_SECONDARY, fontsize=9, clip_on=True)
    fig.tight_layout()
    salvar(fig, "09_adocao_ia_e_prioridade.png")
    achado(f"Q5: adoção individual de IA Generativa saltou de {adocao_ano[2024]:.0f}% (2024) para "
           f"{adocao_ano[2025]:.0f}% (2025) — a edição 2023-2024 não incluía essa pergunta.")
    achado(f"Q5: apenas {prioridade['Prioridade alta (foco executivo)']:.0f}% dos gestores dizem que IA "
           f"Generativa é 'prioridade alta' da empresa — gap de "
           f"{adocao_ano[2025] - prioridade['Prioridade alta (foco executivo)']:.0f} p.p. entre uso individual e "
           f"estratégia formal.")

    uso_2025 = adocao_ano[2025]
    prio_alta_2025 = prioridade["Prioridade alta (foco executivo)"]
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
    # Fonte: q6_diferencas_regiao_senioridade_modelo.sql (6a, 6b)
    # ------------------------------------------------------------------
    sal_regiao = {"Nordeste": 8459, "Norte": 8656, "Sul": 10047, "Centro-oeste": 10710, "Sudeste": 11463}
    sal_modelo = {
        "100% presencial": 7361,
        "Híbrido (dias fixos)": 10695,
        "100% remoto": 11833,
        "Híbrido flexível": 12546,
    }

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    reg_sorted = sorted(sal_regiao.items(), key=lambda kv: kv[1])
    axes[0].barh([k for k, _ in reg_sorted], [v for _, v in reg_sorted], color=CATEGORICAL[0])
    axes[0].set_title("Salário médio por região")
    axes[0].set_xlabel("R$/mês (estimado)")
    for y, (_, v) in enumerate(reg_sorted):
        axes[0].text(v, y, f" {fmt_reais(v)}", va="center", fontsize=9, color=INK_SECONDARY, clip_on=True)

    mod_sorted = sorted(sal_modelo.items(), key=lambda kv: kv[1])
    axes[1].barh([k for k, _ in mod_sorted], [v for _, v in mod_sorted], color=CATEGORICAL[0])
    axes[1].set_title("Salário médio por modelo de trabalho")
    axes[1].set_xlabel("R$/mês (estimado)")
    for y, (_, v) in enumerate(mod_sorted):
        axes[1].text(v, y, f" {fmt_reais(v)}", va="center", fontsize=9, color=INK_SECONDARY, clip_on=True)
    fig.tight_layout()
    salvar(fig, "11_salario_regiao_modelo_trabalho.png")
    maior_regiao, maior_sal = reg_sorted[-1]
    menor_regiao, menor_sal = reg_sorted[0]
    achado(f"Q6: região com maior salário médio é {maior_regiao} (R$ {fmt_milhar(maior_sal)}), "
           f"{(maior_sal / menor_sal - 1) * 100:.0f}% acima da região {menor_regiao}.")

    out_path = ROOT / "docs" / "_eda_achados.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(findings))
    print(f"\nAchados salvos em {out_path}")


if __name__ == "__main__":
    main()
