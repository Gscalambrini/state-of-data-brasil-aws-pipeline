# Tech Challenge Fase 3 — O Mercado Brasileiro de Dados e IA

Projeto de Engenharia de Dados e Analytics para a pós-graduação, respondendo ao
desafio: construir uma solução completa de Big Data & Analytics na AWS, usando
as 3 últimas edições da pesquisa **State of Data Brasil** (comunidade Data
Hackers), e produzir um material executivo com recomendações estratégicas para
uma Instituição Financeira fictícia que quer expandir sua área de Dados,
Analytics e IA.

**Nunca usou AWS?** Comece por
[`docs/GUIA_PARA_INICIANTES_AWS.md`](docs/GUIA_PARA_INICIANTES_AWS.md) — guia
completo (conceitos, fluxo, decisões, recursos reais criados e checklist
contra o PDF oficial) escrito depois do pipeline já ter rodado de ponta a
ponta contra a conta AWS real do grupo.

## As 3 entregas do desafio (e onde encontrá-las aqui)

| Entrega exigida | Onde está |
|---|---|
| 1. Material executivo (PDF) com DataViz e Storytelling | [`presentation/material_executivo.pdf`](presentation/material_executivo.pdf) (relatório em texto corrido, não slides — ver `.docx` para editar) |
| 2. Diagrama de arquitetura da solução AWS (Draw.io) | [`diagrams/arquitetura_solucao.drawio`](diagrams/arquitetura_solucao.drawio) — também embutido na Seção 2 do material executivo |
| 3. Scripts e notebooks (Spark/PySpark e/ou SQL) | [`notebooks/`](notebooks/) — ver detalhes abaixo |

O desafio permite entregar o material executivo em PowerPoint **ou** PDF — o
grupo optou por PDF, no formato de relatório (capa, sumário, resumo
executivo, introdução, metodologia, análise, diagnóstico, recomendações,
conclusão e referências), em vez de slides. Uma versão anterior em
PowerPoint existiu durante o desenvolvimento e foi arquivada em
`presentation/_obsoleto/` — não é mais a entrega oficial.

## Como este projeto foi construído

O pipeline abaixo **rodou de verdade** contra a conta AWS real do grupo
(AWS Academy Lab), não é só código pronto para rodar — os 4 notebooks em
`notebooks/01_bronze` a `04_eda` foram executados no AWS Glue Studio, geraram
as tabelas reais listadas na seção "Nomes reais dos recursos AWS" abaixo, e
os 7 scripts SQL de `05_analytics_athena/` foram validados ao vivo no Amazon
Athena contra essas tabelas.

Em paralelo, existe também um **protótipo local em pandas**
(`src/silver_harmonization.py`, `src/gold_builder.py`, `src/eda_charts.py`),
usado para validar a lógica de harmonização antes de rodar no Glue. Esse
protótipo usa arquivos CSV de referência que **não são exatamente os mesmos**
que estão no bucket real do time, então seus números (ex. 14.002
respondentes) divergem levemente dos números reais finais (13.057
respondentes) — os números e gráficos do material executivo vêm do pipeline
real na AWS (via `src/eda_charts_aws.py`), não do protótipo local. Detalhes
em [`docs/GUIA_PARA_INICIANTES_AWS.md`](docs/GUIA_PARA_INICIANTES_AWS.md).

## Pipeline de dados (arquitetura Bronze / Silver / Gold)

```
Kaggle (3 edições, download manual)
  -> S3 (raw, 1 prefixo com os 3 CSVs)
  -> Glue Studio Notebook (Spark) -- lê os CSVs por caminho exato, SEM Crawler
       -> S3 Bronze (3 tabelas, 1 por edição) -> Glue Data Catalog
  -> Glue Studio Notebook (Spark) -> S3 Silver (harmonizado, 2 tabelas) -> Glue Data Catalog
  -> Glue Studio Notebook (Spark) -> S3 Gold (7 tabelas por tema) -> Glue Data Catalog
  -> Amazon Athena (7 scripts SQL, 1 por pergunta de negócio) -> métricas para o texto do relatório
  -> Glue Studio Notebook — EDA (Spark + matplotlib, roda dentro do Glue) -> 11 gráficos
  -> Material executivo (relatório em PDF)
```

Ver o diagrama completo em [`diagrams/arquitetura_solucao.png`](diagrams/arquitetura_solucao.png)
— sem Crawler, com os nomes reais de database e tabela.

### O desafio de harmonização

As 3 edições da pesquisa (2023-2024, 2024-2025, 2025-2026) usam **schemas de
colunas diferentes** — nomes, posição e até a codificação de valores booleanos
mudam a cada ano. A Silver mapeia ~28 campos-chave (demografia, cargo,
senioridade, salário, região, modelo de trabalho, tecnologias, uso de IA) para
um schema único. Detalhes do mapeamento e da investigação de schema estão em
`docs/_headers_*.txt` e `docs/_diagnostico_categorias.txt`.

## Estrutura de pastas

```
data/
  raw/<edição>/        CSVs brutos baixados do Kaggle
  silver/               Parquet harmonizado (protótipo local, pandas)
  gold/                 Parquet agregado por tema (protótipo local, pandas)
notebooks/
  01_bronze/            Notebook PySpark — ingestão e catalogação Bronze (sem Crawler)
  02_silver/            Notebook PySpark — harmonização Bronze -> Silver
  03_gold/              Notebook PySpark — agregação Silver -> Gold
  04_eda/               Notebook PySpark — gera os 11 gráficos a partir da Gold real
  05_analytics_athena/  7 scripts SQL (um por pergunta de negócio), validados contra o Gold real
src/
  build_notebooks.py         Gera os 4 .ipynb acima — fonte da verdade do código PySpark que rodou na AWS
  silver_harmonization.py    Protótipo local (pandas) — baseado em CSVs de referência locais,
                              não sincronizado 1:1 com os arquivos reais do S3 (ver guia)
  gold_builder.py             Protótipo local (pandas) das tabelas Gold
  eda_charts.py                Gera os 11 gráficos a partir do protótipo LOCAL (números diferentes dos reais)
  eda_charts_aws.py            Gera os mesmos 11 gráficos a partir dos números REAIS obtidos via Athena —
                                este é o que gerou os PNGs finais usados no material executivo
  viz_style.py                 Paleta e estilo compartilhado dos gráficos
  utils/                       Scripts de diagnóstico/validação usados durante o desenvolvimento
presentation/
  material_executivo.pdf    Entrega 1 oficial — relatório completo (ver também o .docx, editável)
  build_relatorio.py         Script Python (python-docx) que gera o .docx a partir dos dados reais
  charts/                     Os 11 gráficos finais (PNG), gerados por eda_charts_aws.py, embutidos no relatório
  _obsoleto/                  Versão anterior em PowerPoint (não é mais a entrega oficial)
diagrams/
  arquitetura_solucao.drawio Entrega 2 (abrir em app.diagrams.net) — sem Crawler, nomes reais;
                             desenhado em conjunto com o time
  arquitetura_solucao.png    Exportado diretamente do .drawio (Arquivo > Exportar como > PNG),
                             embutido na Seção 2 do material executivo
docs/
  GUIA_PARA_INICIANTES_AWS.md       Guia completo (conceitos, fluxo, decisões, entregáveis)
  _headers_*.txt                     Schema completo de cada edição (referência local)
  _diagnostico_categorias.txt        Comparação de categorias entre edições
  _validacao_silver.txt              Validação da Silver (nulos, amostras, consistência)
  _eda_achados.txt                    Achados finais em texto (números reais, via eda_charts_aws.py)
```

## Nomes reais dos recursos AWS (confirmados no console, pipeline já executado)

| Recurso | Nome real |
|---|---|
| Bucket S3 | `s3://tech-challenge-gt26` |
| Database (Bronze + Silver + Gold, única) | `db_techchallenge_gt_fiap` |
| CSVs brutos | soltos em `s3://tech-challenge-gt26/bronze/` (sem subpasta por edição — ver `RAW_PATHS` em `src/build_notebooks.py` pros 3 nomes de arquivo exatos) |
| Jobs/Notebooks no Glue Studio | `job_bronze_tech_challenge`, `job_silver_tech_challenge`, `job_gold_tech_challenge`, `job_eda_tech_challenge` |
| Tabelas Bronze (novas, uma por edição) | `tb_bronze_2023_2024`, `tb_bronze_2024_2025`, `tb_bronze_2025_2026` |
| Tabelas Silver (novas) | `tb_silver_respondentes`, `tb_silver_tecnologias_adocao` |
| Tabelas Gold (novas) | `gold_perfil_mercado`, `gold_remuneracao`, `gold_diversidade_genero`, `gold_tecnologias_adocao`, `gold_adocao_ia`, `gold_prioridade_ia_empresa`, `gold_modelo_trabalho` |

O prefixo `tb_` nas tabelas Bronze/Silver é proposital: o colega de equipe já
tinha criado, no mesmo database, as tabelas `bronze` e `silver` (via 1
Crawler apontando pros 3 CSVs juntos — schema quebrado, 399 colunas
genéricas `col0`...`col398`, confirmado ao vivo no Glue Data Catalog). As
tabelas `tb_*` são aditivas, não colidem com o que ele já fez.

## Validação técnica contra documentação oficial da AWS

Antes de considerar os notebooks prontos, validei os pontos abaixo contra a
documentação oficial da AWS (AWS Glue Developer Guide):

- **Magics de sessão** (`%idle_timeout`, `%glue_version`, `%worker_type`,
  `%number_of_workers`) — confirmados na doc oficial de [Interactive Sessions
  magics](https://docs.aws.amazon.com/glue/latest/dg/interactive-sessions-magics.html).
- **Versão do Glue** — Glue 5.0 é a versão mais atual (Spark 3.5.4, Python
  3.11), mas o **AWS Academy Lab costuma demorar para liberar versões novas**.
  Os notebooks usam `%glue_version 4.0` (Spark 3.3.0) por segurança — troque
  para `5.0` se seu lab já oferecer essa opção no Glue Studio.
- **Glue Data Catalog como metastore** — adicionei uma célula explícita
  `%%configure {"--enable-glue-datacatalog": "true"}` em todos os 3 notebooks.
  Notebooks criados direto no console do Glue Studio costumam já vir com isso
  habilitado, mas a doc oficial trata isso como uma configuração explícita de
  sessão, então preferi não depender de um comportamento implícito.
- **AWS Academy Learner Lab** — o ambiente usa uma role fixa chamada
  **`LabRole`** (vocês não criam roles IAM próprias) e fica restrito às
  regiões **us-east-1** ou **us-west-2**. Ao criar cada Glue Job/Studio
  Notebook, selecione sempre o `LabRole` existente como a IAM role.

## Como reproduzir

```bash
# Protótipo local em pandas (números diferentes dos reais da AWS — ver o guia)
python -m pip install pandas pyarrow matplotlib seaborn
python src/silver_harmonization.py   # gera data/silver/*.parquet
python src/gold_builder.py           # gera data/gold/*.parquet
python src/eda_charts.py             # gera presentation/charts/*.png (números locais)

# Gráficos finais com os números REAIS validados via Athena (os que estão no relatório)
python src/eda_charts_aws.py
```

## Como reproduzir o material executivo (.docx/.pdf)

```bash
cd presentation
python -m pip install python-docx
python build_relatorio.py   # gera material_executivo.docx

# PDF: abra o .docx no Word, atualize o Sumário (botão direito sobre ele >
# Atualizar campo > Atualizar o índice inteiro) e use "Salvar como > PDF".
# No Windows, isso também pode ser automatizado via COM (PowerShell):
#   $app = New-Object -ComObject Word.Application
#   $doc = $app.Documents.Open("<caminho completo>\material_executivo.docx")
#   $doc.Fields.Update(); $doc.TablesOfContents | % { $_.Update() }
#   $doc.SaveAs([ref]"<caminho completo>\material_executivo.pdf", [ref]17)
#   $doc.Close(); $app.Quit()
```

## As 7 perguntas de negócio e os principais achados (dados reais, AWS, 13.057 respondentes)

1. **Estrutura do mercado**: concentrado em Analista/Cientista/Engenheiro de
   Dados; 61% dos profissionais estão no Sudeste.
2. **Perfis mais valorizados**: Engenheiro de ML/AI Engineer é o cargo mais
   bem pago entre os mais comuns (~R$ 16,4 mil/mês).
3. **Diversidade de gênero**: só 23,9% dos profissionais são mulheres;
   participação cai de 28,2% (Júnior) para 20,1% (Especialista/Staff+); gap
   salarial de ~15% no nível Sênior.
4. **Tecnologias mais adotadas**: Python ultrapassa SQL como linguagem nº1
   entre 2024 e 2025 (49%→55% vs. 55%→50%); AWS lidera entre clouds; Power BI
   lidera entre ferramentas de BI.
5. **Adoção de IA**: uso individual salta de 80% (2024) para 98% (2025) — a
   edição 2023-2024 não tinha essa pergunta —, mas só ~24% dos gestores
   tratam IA Generativa como prioridade executiva.
6. **Diferenças regionais/modelo de trabalho**: Sudeste paga 36% a mais que o
   Nordeste; modelo híbrido flexível paga mais que 100% presencial.
7. **Oportunidades e desafios**: formalizar estratégia de IA, investir em
   equidade de gênero, usar trabalho remoto para acessar talento fora do
   Sudeste, e direcionar capacitação para Python e Engenharia de
   Dados/ML — ver recomendações completas no material executivo.
