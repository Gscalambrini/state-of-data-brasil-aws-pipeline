# Guia completo do projeto: conceitos, fluxo, decisões e entregáveis

Este guia assume que você nunca usou AWS. Primeiro explica cada conceito,
depois conta exatamente o que foi construído e rodado de verdade na conta AWS
real do grupo (não é um protótipo teórico — todo o pipeline abaixo rodou,
foi validado e está catalogado em `db_techchallenge_gt_fiap`).

**Atualizado em 2026-10-19**, depois de rodar o pipeline completo contra os
dados reais do time na AWS, corrigir dois bugs encontrados durante essa
execução, e reconstruir o material executivo (relatório em PDF — o desafio
permite PowerPoint ou PDF, e o grupo optou por PDF) e o diagrama com os
números finais e validados.

---

## Parte 1 — Os conceitos, um por um

### O que é "a nuvem" / AWS, na prática

A AWS (Amazon Web Services) é, fisicamente, um monte de computadores dentro
de prédios da Amazon, espalhados pelo mundo (cada grupo de prédios numa
região é uma "região", ex. `us-east-1` = Norte da Virgínia, EUA). Quando você
"usa a AWS", você aluga um pedacinho de processamento ou armazenamento
desses computadores pela internet. O **AWS Console** é o site onde você
clica para pedir esses recursos.

Este projeto roda no **AWS Academy Lab** — um ambiente de estudo com conta
temporária, orçamento limitado (vocês usaram ~US$ 4,40 de um limite de
US$ 50) e sessões de 4h que precisam ser reiniciadas quando o tempo acaba
("Start Lab" de novo).

### Bucket (S3) — "uma pasta gigante na nuvem"

**S3** é o serviço de armazenamento de arquivos da AWS. Um **bucket** é a
pasta raiz. O bucket real deste projeto é `tech-challenge-gt26` — foi criado
pelo colega de equipe (Thales) antes deste trabalho começar.

### AWS Glue (o serviço) — "a cozinha onde os dados são processados"

**Glue** é o serviço de processamento/transformação de dados da AWS. Duas
formas principais de rodar código nele:

- **Glue Job**: um script Spark agendado para rodar sozinho (produção).
- **Glue Studio Notebook**: um notebook interativo (como Jupyter/Colab) —
  roda célula por célula, vê o resultado na hora. **É o que este projeto usa
  para as 4 etapas do pipeline** (Bronze, Silver, Gold, EDA).

Cada Notebook, quando salvo e nomeado no console, também aparece na lista de
**Jobs** do Glue (um Glue Studio Notebook *é* um tipo de Job por baixo dos
panos). Os 4 jobs reais criados neste projeto:

| Job (nome real no console) | O que faz |
|---|---|
| `job_bronze_tech_challenge` | Lê os 3 CSVs brutos do S3 e cataloga a Bronze |
| `job_silver_tech_challenge` | Harmoniza as 3 edições num schema único (Silver) |
| `job_gold_tech_challenge` | Agrega a Silver em 7 tabelas de negócio (Gold) |
| `job_eda_tech_challenge` | Lê a Gold e gera os 11 gráficos da análise (inline, com `%matplot`) |

### Por que este projeto **não usa Glue Crawler**

Um **Crawler** é um robô que varre arquivos no S3 e descobre sozinho as
colunas/tipos, registrando isso no Glue Data Catalog — sem mover nem
transformar nada.

O colega de equipe já tinha criado 1 Crawler (`crawler_bronze_data_gt`)
apontando para os 3 CSVs juntos no mesmo prefixo do S3. Isso gerou um
problema real, confirmado ao vivo no console: o Crawler amostrou só **1** dos
3 arquivos para inferir o schema (as 3 edições têm formatos de cabeçalho
diferentes) e aplicou esse schema errado aos 3 — resultando numa tabela
`bronze` com **399 colunas genéricas (`col0`...`col398`)**, sem os nomes
reais de pergunta da pesquisa.

Reli o PDF oficial do desafio (página 3) e a palavra "Crawler" **não aparece
em nenhum lugar** — o que é exigido é "ETL/ELT e catalogação das tabelas
com o Glue Jobs", ou seja, catalogar **através do** Job/Notebook, não
necessariamente via um Crawler separado. Por isso, a decisão foi: os 4
Notebooks leem os arquivos/tabelas por caminho explícito e se catalogam
sozinhos via `saveAsTable()` — sem precisar de nenhum Crawler. Isso também
evitou qualquer conflito com o que o colega já tinha criado (ver tabela de
nomes mais abaixo — nada foi apagado ou sobrescrito).

### Glue Data Catalog — "o Google de tabelas da sua conta AWS"

Um catálogo central de metadados: "existe uma tabela chamada X, mora em tal
caminho do S3, tem essas colunas". O Glue (ao processar) e o Athena (ao
consultar) usam esse catálogo para saber onde estão as tabelas. Nas 4
camadas deste projeto, as tabelas são catalogadas automaticamente pelo
próprio Notebook, com `df.write.saveAsTable(...)` — sem Crawler.

### Spark / PySpark — "o motor que processa dados em paralelo"

O **Apache Spark** é um motor de processamento distribuído. **PySpark** é
Spark escrito em Python. Os 4 Notebooks deste projeto usam um objeto `spark`
(a "sessão Spark") para ler, transformar e gravar os dados. No AWS Academy
Lab, a sessão Spark de um Notebook demora ~1-3 minutos para "ligar" na
primeira execução (cold start) — depois disso, as células rodam rápido.

### Amazon Athena — "SQL direto em cima dos arquivos do S3"

O **Athena** deixa rodar `SELECT ... FROM ... WHERE ...` direto sobre os
arquivos do S3, desde que estejam catalogados no Glue Data Catalog — sem
precisar de um banco de dados tradicional. Os 7 scripts de
`notebooks/05_analytics_athena/*.sql` (um por pergunta de negócio) rodam
aqui, direto contra as tabelas `gold_*`.

### Bronze, Silver e Gold — "a maturidade dos dados, camada por camada"

Não é um serviço da AWS — é um **padrão de arquitetura** ("medallion
architecture") que organiza os dados por nível de tratamento:

- **Bronze**: os dados exatamente como vieram da fonte (uma "foto fiel" do
  CSV original), sem transformação.
- **Silver**: dados limpos, padronizados e harmonizados — aqui é onde as 3
  edições da pesquisa (com colunas diferentes entre si) viram um formato
  único.
- **Gold**: dados já agregados/especializados, prontos para consumo final —
  as 7 tabelas que respondem diretamente cada pergunta de negócio do
  desafio.

Cada camada é uma pasta diferente dentro do mesmo bucket S3, com suas
tabelas catalogadas no mesmo database.

---

## Parte 2 — O fluxo completo, do jeito que rodou de verdade

```
1. Kaggle — 3 edições da pesquisa "State of Data Brasil" (download manual)
       ↓ (upload feito pelo colega de equipe)
2. S3 — s3://tech-challenge-gt26/bronze/ (3 CSVs brutos, soltos no mesmo prefixo)
       ↓ (lido diretamente, por caminho exato — SEM Crawler)
3. job_bronze_tech_challenge (Glue Studio Notebook, PySpark)
       → grava Parquet em s3://tech-challenge-gt26/bronze_parquet/
       → cataloga 3 tabelas: tb_bronze_2023_2024, tb_bronze_2024_2025, tb_bronze_2025_2026
       ↓
4. job_silver_tech_challenge (Glue Studio Notebook, PySpark)
       → harmoniza as 3 edições (schemas de coluna diferentes) num schema único
       → grava e cataloga: tb_silver_respondentes, tb_silver_tecnologias_adocao
       ↓
5. job_gold_tech_challenge (Glue Studio Notebook, PySpark)
       → agrega a Silver em 7 tabelas, 1 por pergunta de negócio
       → grava e cataloga: gold_perfil_mercado, gold_remuneracao,
         gold_diversidade_genero, gold_tecnologias_adocao, gold_adocao_ia,
         gold_prioridade_ia_empresa, gold_modelo_trabalho
       ↓
6a. Amazon Athena — 7 scripts SQL (notebooks/05_analytics_athena/),
       1 por pergunta de negócio, consultando as tabelas gold_* direto
       ↓ (métricas/números para o texto do material executivo)
6b. job_eda_tech_challenge (Glue Studio Notebook, PySpark + matplotlib)
       → lê as 7 tabelas Gold direto (spark.table) e gera os 11 gráficos
         inline, dentro do próprio notebook (comando %matplot)
       ↓ (os 11 PNGs foram usados no relatório)
7. Material executivo (relatório em PDF, gerado a partir de um .docx) —
   storytelling completo em texto corrido, com os 11 gráficos, os números
   reais validados via Athena, e o diagrama de arquitetura embutido na
   Seção 2 (Metodologia)
```

Todas as 4 etapas (3, 4, 5, 6b) foram **executadas de verdade** no AWS
Academy Lab do grupo — não é só código pronto para rodar, já rodou e os
números abaixo vêm direto dessa execução real.

---

## Parte 3 — As decisões mais importantes tomadas (e por quê)

### 1. Não criar Crawler nem pastas novas para Bronze

Já explicado acima: o PDF não exige Crawler, e o Crawler que já existia
("crawler_bronze_data_gt") tinha produzido um schema quebrado (399 colunas
genéricas). A solução feita por Notebook resolve isso sem precisar mexer no
que o colega já tinha criado.

### 2. Nomes de tabela com prefixo `tb_` para Bronze/Silver

O colega já tinha criado, no mesmo database, as tabelas `bronze` e `silver`
(via o Crawler problemático). As tabelas novas usam nomes diferentes
(`tb_bronze_*`, `tb_silver_*`) para conviver lado a lado sem conflito — nada
do trabalho dele precisou ser apagado.

### 3. Mapeamento de colunas corrigido contra os arquivos REAIS do S3

Os 3 arquivos reais no bucket do time (nomes de arquivo enganosos — ex.
`State_of_data_2022.csv` é na verdade a edição 2023-2024) têm layouts de
coluna **diferentes** dos CSVs de referência usados inicialmente para
desenvolver o mapeamento. Isso causou um bug real: o gráfico de "cargos mais
comuns" misturava cargos de verdade com respostas de outra pergunta (tempo
de experiência). Corrigido inspecionando os headers reais via S3 Select e
reconstruindo o mapeamento de índices de coluna por edição
(`SCALAR_FIELDS`/`MULTI_SELECT_RANGES` em `src/build_notebooks.py`).
Resultado: **13.057 respondentes** (não mais os 14.002 do protótipo local,
que usava CSVs de referência diferentes dos reais).

### 4. Bug dos rótulos de tecnologia (`rotulo_tecnologia()`)

Depois de corrigir o mapeamento, o gráfico de tecnologias mais adotadas
mostrava nomes crus de coluna (`c_4_c_3_python`) em vez de nomes limpos
(`python`). A função que limpa esses rótulos só reconhecia o formato dos
CSVs de referência locais, não o formato real do S3. Corrigida com uma regex
generalizada (`^[a-z]_?\d+(?:_[a-z]_?\d+)*_(.+)$`) que cobre os dois formatos
reais encontrados nas edições 2024-2025 e 2025-2026. Validado via Athena:
sobraram só 4 "nomes crus" residuais, dos quais 3 são valores legítimos
(`s3`, e duas frases de resposta tipo "não utilizo nenhuma...") e 1 é um
artefato raro e irrelevante de colisão de nomes na sanitização da Bronze.

### 5. Bug nos scripts Athena: filtro em maiúsculas não bate com os dados

Ao validar os 7 scripts SQL ao vivo contra o Gold real, achei que
`q4_tecnologias_mais_adotadas.sql` filtrava `tecnologia IN ('Python', 'SQL',
'R')` (maiúsculas) — mas como os valores de `tecnologia` são sempre
**minúsculos** (saem da sanitização de nome de coluna), essa query rodava
sem erro mas devolvia **0 linhas**, silenciosamente. Corrigido para
`IN ('python', 'sql', 'r')`. Os demais filtros em outros scripts (gênero,
senioridade, prioridade de IA) foram conferidos contra os valores reais e já
estavam corretos.

### 6. Material executivo trocado de PowerPoint para relatório em PDF

O desafio permite entregar o material executivo em PowerPoint **ou** PDF. O
grupo decidiu, numa rodada posterior desta sessão, trocar de um PowerPoint
(poucos slides, principalmente imagens) para um **relatório em PDF**, no
formato de um relatório técnico-executivo de verdade — capa, sumário,
resumo executivo, introdução, metodologia, análise detalhada por pergunta de
negócio, diagnóstico, recomendações, conclusão e referências. Isso exigiu
bem mais texto corrido e storytelling do que o PowerPoint tinha, nos moldes
de um relatório de consultoria.

O relatório é gerado por um script Python (`presentation/build_relatorio.py`,
usando a biblioteca `python-docx`), que produz um `.docx` editável — depois
convertido para `.pdf` (abrindo no Word, atualizando o Sumário e salvando
como PDF; ver o passo a passo na Parte 7). Os 11 gráficos (gerados por
`src/eda_charts_aws.py`, com os números reais validados via Athena) e o
diagrama de arquitetura (Seção 2 do relatório) são embutidos como figuras
dentro do texto. A versão anterior em PowerPoint foi arquivada em
`presentation/_obsoleto/` — não é mais a entrega oficial, e o script que a
gerava (`build_deck.js`) foi removido.

---

## Parte 4 — Onde cada entregável está, e como verificar contra o PDF oficial

O desafio oficial (`[DTAT] - Tech Challenge - Fase 3.pdf`) exige 3 entregas:

| # | Exigência oficial | Onde está neste projeto | Status |
|---|---|---|---|
| 1 | Material executivo (PowerPoint ou PDF) com DataViz e Storytelling, respondendo as 7 perguntas de negócio | [`presentation/material_executivo.pdf`](../presentation/material_executivo.pdf) (relatório completo; `.docx` editável também disponível) | ✅ Relatório completo, com dados reais validados (13.057 respondentes) |
| 2 | Diagrama da arquitetura da solução AWS (Draw.io), **embutido no material executivo** | [`diagrams/arquitetura_solucao.drawio`](../diagrams/arquitetura_solucao.drawio) — embutido na Seção 2 (Metodologia) do relatório | ✅ Desenhado em conjunto com o time: sem Crawler, nomes reais de database/tabela |
| 3 | Scripts e notebooks (Spark/PySpark e/ou SQL), organizados, cobrindo ingestão → tratamento → transformação → catalogação → consultas analíticas | [`notebooks/`](../notebooks/) (4 notebooks PySpark + 7 scripts SQL) | ✅ Todos os 4 notebooks rodaram de verdade na AWS; os 7 scripts SQL foram validados contra o Gold real |

As 7 perguntas de negócio do PDF (página 4) são respondidas, uma a uma, na
Seção 4 do relatório (subsções 4.1 a 4.7) — cada subseção corresponde a 1
pergunta e cita o(s) gráfico(s)/número(s) que a respondem.

**Pontos de atenção que NÃO são exigidos, mas valem notar**: o enunciado não
pede print de execução como comprovante — mas como o pipeline rodou de
verdade (não é só "deveria funcionar"), isso já está validado além do
mínimo exigido. Dashboard interativo também não é exigido (o PDF é
explícito sobre isso) — os gráficos estáticos no relatório/notebook cobrem o
requisito.

---

## Parte 5 — Recursos reais na conta AWS (console confirmado)

| Recurso | Nome real |
|---|---|
| Bucket S3 | `tech-challenge-gt26` |
| Database (Bronze + Silver + Gold, única) | `db_techchallenge_gt_fiap` |
| CSVs brutos | `s3://tech-challenge-gt26/bronze/` (3 arquivos, nomes de arquivo não indicam a edição — ver `RAW_PATHS` em `src/build_notebooks.py`) |
| Jobs/Notebooks (novos, deste trabalho) | `job_bronze_tech_challenge`, `job_silver_tech_challenge`, `job_gold_tech_challenge`, `job_eda_tech_challenge` |
| Tabelas Bronze (novas) | `tb_bronze_2023_2024`, `tb_bronze_2024_2025`, `tb_bronze_2025_2026` |
| Tabelas Silver (novas) | `tb_silver_respondentes`, `tb_silver_tecnologias_adocao` |
| Tabelas Gold (novas) | `gold_perfil_mercado`, `gold_remuneracao`, `gold_diversidade_genero`, `gold_tecnologias_adocao`, `gold_adocao_ia`, `gold_prioridade_ia_empresa`, `gold_modelo_trabalho` |
| Recursos do colega (Thales), mantidos intactos | tabelas `bronze`/`silver` (schema quebrado, não usadas), crawler `crawler_bronze_data_gt` |

A decisão de **apagar** os recursos antigos do Thales (tabela `bronze`
quebrada e o crawler) fica para o time decidir — não foi feita aqui, por ser
uma ação destrutiva em cima do trabalho de outra pessoa.

---

## Parte 6 — Estrutura de pastas do projeto

```
data/raw/<edição>/        CSVs brutos de referência usados no protótipo local
notebooks/
  01_bronze/               Notebook PySpark — ingestão e catalogação Bronze
  02_silver/               Notebook PySpark — harmonização Bronze -> Silver
  03_gold/                 Notebook PySpark — agregação Silver -> Gold
  04_eda/                  Notebook PySpark — gera os 11 gráficos a partir da Gold
  05_analytics_athena/     7 scripts SQL (um por pergunta de negócio)
src/
  build_notebooks.py       Gera os 4 .ipynb acima a partir de templates Python — FONTE DA VERDADE do código PySpark
  silver_harmonization.py  Protótipo local (pandas) — intencionalmente baseado em CSVs de referência locais, não sincronizado 1:1 com o real da AWS
  gold_builder.py          Protótipo local (pandas) das tabelas Gold
  eda_charts.py            Gera os 11 gráficos a partir do protótipo LOCAL (pandas) — números diferentes dos reais
  eda_charts_aws.py        Gera os MESMOS 11 gráficos a partir dos números REAIS obtidos via Athena — é este que gerou os PNGs finais usados no relatório
  viz_style.py             Paleta e estilo compartilhado dos gráficos (cor oficial FIAP)
  utils/                   Scripts de diagnóstico/validação usados durante o desenvolvimento
presentation/
  material_executivo.pdf   Entrega 1 oficial — relatório completo (ver também o .docx, editável)
  build_relatorio.py       Script Python (python-docx) que gera o .docx a partir dos dados reais
  charts/                  Os 11 gráficos finais (PNG), gerados por eda_charts_aws.py
  _obsoleto/               Versão anterior em PowerPoint (arquivada, não é mais a entrega oficial)
diagrams/
  arquitetura_solucao.drawio  Entrega 2 (abrir em app.diagrams.net) — desenhado em conjunto com o time
  arquitetura_solucao.png     Exportado diretamente do .drawio (Arquivo > Exportar como > PNG)
docs/
  GUIA_PARA_INICIANTES_AWS.md  Este guia
  _eda_achados.txt              Achados finais em texto (gerados por eda_charts_aws.py)
  _headers_*.txt                 Schema de cada edição (para referência)
  _diagnostico_categorias.txt    Comparação de categorias entre edições
  _validacao_silver.txt          Validação da Silver (nulos, amostras)
```

---

## Parte 7 — Os 11 gráficos e os números reais finais (pós-validação AWS)

1. **Top 10 cargos**: Analista de Dados é o mais comum (2.145 respondentes).
2. **Distribuição regional**: 61% dos profissionais estão no Sudeste.
3. **Pirâmide de senioridade**: Pleno (3.227) e Sênior (3.175) são os níveis
   mais numerosos; Especialista/Staff+ é raro (349).
4. **Remuneração por cargo**: Engenheiro de ML/AI Engineer é o mais bem
   pago entre os cargos com volume relevante (R$ 16.382/mês).
5. **Gênero por senioridade** (edição mais recente): participação feminina
   cai de 28,2% (Júnior) para 20,1% (Especialista/Staff+).
6. **Gap salarial de gênero**: no nível Sênior, mulheres recebem ~15% menos
   que homens.
7. **Painel de tecnologias**: Python/SQL lideram linguagens; PostgreSQL
   lidera bancos; AWS lidera cloud; Power BI lidera ferramentas de BI.
8. **Evolução de linguagens**: Python sobe de 49% (2023) para 55% (2025);
   SQL cai de 55% para 50% — cruzamento entre 2024 e 2025.
9. **Adoção de IA**: uso individual salta de 80% (2024) para 98% (2025) — a
   edição 2023-2024 não tinha essa pergunta na pesquisa.
10. **Gap individual vs. empresa**: 98% dos profissionais usam IA no dia a
    dia, mas só 24% dos gestores tratam isso como prioridade executiva.
11. **Salário por região e modelo de trabalho**: Sudeste paga 36% a mais que
    o Nordeste; modelo híbrido flexível (R$ 12.546) paga mais que 100%
    presencial (R$ 7.361).

---

## Parte 8 — Como reproduzir

```bash
# Protótipo local em pandas (números diferentes dos reais da AWS — ver Parte 3, item 3)
python -m pip install pandas pyarrow matplotlib seaborn
python src/silver_harmonization.py
python src/gold_builder.py
python src/eda_charts.py

# Gráficos finais com os números REAIS validados via Athena (os que estão no relatório)
python src/eda_charts_aws.py

# Reconstruir o material executivo (.docx) depois de qualquer mudança nos gráficos/texto
cd presentation
python -m pip install python-docx
python build_relatorio.py
# PDF: abrir o .docx no Word, atualizar o Sumário (botão direito sobre ele >
# Atualizar campo > Atualizar o índice inteiro) e "Salvar como > PDF"
# (ou via automação COM no Windows — ver comandos no README.md)

# Atualizar o diagrama de arquitetura: editar diagrams/arquitetura_solucao.drawio em
# app.diagrams.net, depois Arquivo > Exportar como > PNG para substituir arquitetura_solucao.png
```
