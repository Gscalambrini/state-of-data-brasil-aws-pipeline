# Análise exploratória (EDA)

O enunciado permite "Glue Notebook **ou** Athena" para tratamento e consultas
analíticas — este projeto usa o **Athena** (ver `../05_analytics_athena/*.sql`)
como camada de consulta sobre a Gold, e os **gráficos** da análise exploratória
são gerados em Python a partir dessa mesma Gold:

- [`../../src/eda_charts.py`](../../src/eda_charts.py) — gera os 11 gráficos em
  `../../presentation/charts/`, um por pergunta de negócio (ou grupo de
  perguntas relacionadas), a partir das tabelas Silver/Gold.
- [`../../docs/_eda_achados.txt`](../../docs/_eda_achados.txt) — os principais
  achados textuais extraídos durante a geração dos gráficos.

Os mesmos agregados que alimentam os gráficos são o resultado direto do
notebook `../03_gold/gold_glue_notebook.ipynb` (Spark) e das queries
`../05_analytics_athena/*.sql` (SQL) — ou seja, a "geração dos dados utilizados
nas análises e gráficos" exigida pelo desafio está coberta em Spark e SQL; só a
etapa final de desenho dos gráficos acontece em Python/matplotlib local.
