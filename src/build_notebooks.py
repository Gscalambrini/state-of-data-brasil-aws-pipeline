"""Gera os notebooks (.ipynb) de Bronze, Silver e Gold prontos para rodar no
AWS Glue Studio Notebook, traduzindo fielmente a logica ja validada em
src/silver_harmonization.py e src/gold_builder.py (prototipos locais em pandas)
para PySpark/Spark SQL.

Uso: python build_notebooks.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = ROOT / "notebooks"


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": text.splitlines(keepends=True),
    }


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Glue PySpark", "language": "python", "name": "glue_pyspark"},
            "language_info": {"name": "Python_Glue_Session", "mimetype": "text/x-python", "codemirror_mode": {"name": "python", "version": 3}, "pygments_lexer": "python3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def save(nb: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print(f"salvo: {path}")


GLUE_SESSION_MAGICS = """\
%idle_timeout 2880
%glue_version 4.0
%worker_type G.1X
%number_of_workers 5
"""

# Garante explicitamente que o Glue Data Catalog seja usado como metastore do
# Hive para esta sessao Spark — sem isso, saveAsTable() pode criar as tabelas
# num metastore local/efemero que o Athena nao enxerga. Em notebooks criados
# direto no AWS Glue Studio isso costuma vir habilitado por padrao, mas
# declarar explicitamente remove qualquer ambiguidade (confirmado via
# documentacao oficial do AWS Glue sobre --enable-glue-datacatalog).
GLUE_CATALOG_CONFIG = """\
%%configure
{
  "--enable-glue-datacatalog": "true"
}
"""

GLUE_BOOT = """\
import sys
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
import pyspark.sql.functions as F
import pyspark.sql.types as T

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
"""

CONFIG_CELL = """\
# =============================================================================
# CONFIGURACAO — valores conferidos AO VIVO no console AWS do time em
# 2026-10-18 (Glue Data Catalog + S3). Troque so se os nomes mudarem.
#
# Os 3 CSVs brutos ficam juntos, soltos (sem subpasta por edicao), direto em
# s3://tech-challenge-gt26/bronze/ — e com nomes de arquivo que NAO indicam a
# edicao de forma confiavel. Mapeamento confirmado por inspecao de conteudo
# (S3 Select: formato do cabecalho + pergunta "passou por layoff em <ano>"):
#   - "State_of_data_2022.csv"                      -> edicao 2023-2024
#   - "State_of_data_BR_2023_Kaggle - df_survey_2023.csv" -> edicao 2024-2025
#   - "Final Dataset - State of Data 2025-2026 - Kaggle.csv" -> edicao 2025-2026
#
# Os nomes de tabela abaixo (tb_bronze_*, tb_silver_*, tb_gold_*) usam um
# prefixo "tb_" de proposito para conviver, dentro do MESMO database
# db_techchallenge_gt_fiap, com as tabelas "bronze"/"silver"/"gold" que ja
# existem — nada aqui sobrescreve ou apaga o que ja foi feito.
# =============================================================================
BUCKET = "s3://tech-challenge-gt26"

RAW_PATHS = {
    "2023-2024": f"{BUCKET}/bronze/State_of_data_2022.csv",
    "2024-2025": f"{BUCKET}/bronze/State_of_data_BR_2023_Kaggle - df_survey_2023.csv",
    "2025-2026": f"{BUCKET}/bronze/Final Dataset - State of Data 2025-2026 - Kaggle.csv",
}

# Prefixo NOVO e distinto do "bronze/" (lowercase) onde os CSVs brutos ja
# estao — evita qualquer risco de sobrescrever a fonte original.
BRONZE_PATH = f"{BUCKET}/bronze_parquet/"
SILVER_PATH = f"{BUCKET}/Silver/"
GOLD_PATH = f"{BUCKET}/Gold/"

DB_BRONZE = "db_techchallenge_gt_fiap"
DB_SILVER = "db_techchallenge_gt_fiap"
DB_GOLD = "db_techchallenge_gt_fiap"

for db in (DB_BRONZE, DB_SILVER, DB_GOLD):
    spark.sql(f"CREATE DATABASE IF NOT EXISTS {db}")
"""


def build_bronze_notebook() -> dict:
    cells = [
        md("""\
# Bronze — ingestão e catalogação das 3 edições do State of Data Brasil

**Objetivo da camada Bronze**: carregar os CSVs brutos (um por edição da pesquisa,
baixados manualmente do Kaggle por exigirem login) o mais próximo possível de
como vieram da fonte — convertendo para Parquet (mais eficiente que CSV pro
resto do pipeline) e corrigindo o TIPO dos valores ausentes (ver célula de
normalização abaixo) — e catalogar cada edição como uma tabela no AWS Glue
Data Catalog, para ficar consultável via Athena.

**Por que 3 tabelas separadas (`tb_bronze_2023_2024`, `tb_bronze_2024_2025`,
`tb_bronze_2025_2026`), e não uma tabela `bronze` única?** Cada edição tem um
schema de colunas **diferente** (quantidade e nomes de colunas mudam a cada ano
da pesquisa). Um Crawler apontando pra um prefixo com os 3 CSVs juntos cria uma
tabela "Frankenstein": a união de todas as colunas das 3 edições, com `NULL` em
toda coluna que simplesmente não existe naquela edição — ou seja, boa parte do
volume de nulo que aparece numa tabela `bronze` única não é dado faltando, é
efeito colateral de forçar 3 questionários diferentes dentro da mesma tabela.
Por isso aqui cada edição vira sua própria tabela, com seu schema nativo, sem
nulo artificial — a unificação de verdade (mesma pergunta = mesma coluna, nas
3 edições) é trabalho da Silver, não da Bronze.

Pré-requisito: os 3 arquivos CSV devem já estar enviados para os prefixos
`RAW_PATHS` no S3 (upload simples, feito fora deste notebook)."""),
        code(GLUE_SESSION_MAGICS),
        code(GLUE_CATALOG_CONFIG),
        code(GLUE_BOOT),
        code(CONFIG_CELL),
        md("## Leitura e normalização do tipo dos valores ausentes, por edição"),
        code("""\
# O encoding de origem é UTF-8 com alguns raros bytes corrompidos em campos de
# texto livre (identificado na validação local) — "PERMISSIVE" + multiLine
# evitam que uma linha malformada derrube a leitura inteira do arquivo.
EDICOES = ["2023-2024", "2024-2025", "2025-2026"]

bronze_dfs = {}
for edicao in EDICOES:
    df = (
        spark.read
        .option("header", "true")
        .option("encoding", "UTF-8")
        .option("multiLine", "true")
        .option("escape", '"')
        .option("mode", "PERMISSIVE")
        .csv(RAW_PATHS[edicao])
    )
    bronze_dfs[edicao] = df
    print(f"{edicao}: {df.count():,} linhas, {len(df.columns)} colunas")
"""),
        md("""\
## Renomeação para nomes de coluna compatíveis com o Hive Metastore

O cabeçalho original da edição 2023-2024 vem serializado como tupla Python em
texto (ex: `"('P1_b ', 'Genero')"`) — com vírgula, aspas e parênteses dentro do
nome. O Glue Data Catalog usa o Hive Metastore por trás, que **não aceita
vírgula (nem vários outros caracteres) em nome de coluna** — tentar catalogar
assim gera `AnalysisException: ... column whose name contains commas`.
Isso explica, inclusive, por que o Crawler do time também não preservou os
nomes originais: nenhuma ferramenta compatível com Hive consegue.

A célula abaixo sanitiza os nomes **por posição**, sem depender do significado
de cada coluna — a Silver já seleciona campos pelo índice posicional
(`col_by_idx`), então o nome exato aqui não importa para o resto do pipeline,
só precisa ser válido no Hive e consistente dentro de cada edição."""),
        code("""\
import re

def nomes_seguros(colunas):
    nomes, vistos = [], {}
    for i, c in enumerate(colunas):
        nome = re.sub(r"[^0-9a-zA-Z_]+", "_", c).strip("_")[:120].lower()
        if not nome or nome[0].isdigit():
            nome = f"c_{nome}" if nome else f"col{i}"
        if nome in vistos:
            vistos[nome] += 1
            nome = f"{nome}_{vistos[nome]}"
        else:
            vistos[nome] = 0
        nomes.append(nome)
    return nomes

for edicao, df in bronze_dfs.items():
    bronze_dfs[edicao] = df.toDF(*nomes_seguros(df.columns))
print("colunas renomeadas pra nomes compativeis com o Hive Metastore (mantendo a ordem posicional)")
"""),
        md("""\
O CSV original representa "não respondi"/"não se aplica" como **string vazia**
(`""`), não como nulo de verdade — como texto, uma célula vazia parece igual a
um nulo, mas pra um motor de consulta (Spark, Athena) os dois são tratados de
forma diferente (`COUNT`, `IS NULL`, `GROUP BY` etc. tratam `""` como um valor
válido, não como ausência de valor, o que distorce qualquer contagem). A célula
abaixo corrige isso de forma genérica, sem precisar saber o que cada coluna
significa: tira espaço em branco (`"   "` também vira nulo) e string vazia
passa a ser `NULL` de verdade — aplicado a **todas** as colunas, já que a
Bronze ainda não sabe o significado de cada uma (isso só é decidido na Silver).
Nada além de tipo muda aqui: nenhuma linha é removida, nenhum valor
não-vazio é alterado."""),
        code("""\
def normalizar_nulos(df):
    # Varios cabecalhos da edicao 2023-2024 vem serializados como tupla Python
    # em texto (ex: "('P3_c_1 ', 'Pensar na visao de longo prazo...')"), com
    # ponto/virgula/aspas dentro do nome. Tanto F.col(nome) quanto df[nome]
    # tentam interpretar nomes assim como referencia qualificada/aninhada e
    # quebram com AnalysisException — a unica forma segura e envolver o nome
    # inteiro em crase (`...`), que forca o Spark a trata-lo como um unico
    # identificador literal, sem nenhum parsing de ponto/virgula/aspas.
    #
    # Em vez de 399 .withColumn() encadeados (um plano Spark profundamente
    # aninhado, lento de analisar — e a causa da sessao travando antes), um
    # unico .select() com todas as colunas recalculadas de uma vez: mais
    # rapido e evita reavaliar a cadeia inteira a cada coluna.
    colunas = [
        F.when(F.trim(F.col(f"`{c}`")) == "", None).otherwise(F.trim(F.col(f"`{c}`"))).alias(c)
        for c in df.columns
    ]
    return df.select(*colunas)

bronze_dfs = {edicao: normalizar_nulos(df) for edicao, df in bronze_dfs.items()}
"""),
        md("""\
## Diagnóstico: quanto cada edição tem de valor ausente

Mostra, por edição, o percentual médio de células nulas e as 5 colunas com mais
nulo — serve pra confirmar que o volume alto de nulo é **esperado** (a pesquisa
usa lógica de "pule para": quem não usa cloud, por exemplo, não responde as
perguntas sobre qual cloud usa) e não um efeito colateral de bug de leitura."""),
        code("""\
for edicao, df in bronze_dfs.items():
    total = df.count()
    linha = df.select([
        F.sum(F.col(f"`{c}`").isNull().cast("int")).alias(f"c{i}")
        for i, c in enumerate(df.columns)
    ]).collect()[0]
    pct_por_coluna = [
        (df.columns[i], round(linha[f"c{i}"] / total * 100, 1))
        for i in range(len(df.columns))
    ]
    media = sum(p for _, p in pct_por_coluna) / len(pct_por_coluna)
    piores = sorted(pct_por_coluna, key=lambda t: t[1], reverse=True)[:5]
    print(f"{edicao}: {media:.1f}% de nulo em média por coluna, de {total:,} linhas")
    print(f"  5 colunas com mais nulo: {piores}")
"""),
        md("## Gravação em Parquet e catalogação de cada edição"),
        code("""\
for edicao, df in bronze_dfs.items():
    tabela = "tb_bronze_" + edicao.replace("-", "_")
    caminho = BRONZE_PATH + edicao.replace("-", "_") + "/"
    (
        df.write
        .mode("overwrite")
        .format("parquet")
        .option("path", caminho)
        .saveAsTable(f"{DB_BRONZE}.{tabela}")
    )
    print(f"gravado e catalogado: {DB_BRONZE}.{tabela}  ->  {caminho}")
"""),
        md("""\
## Verificação

Confirma que as 3 tabelas Bronze foram catalogadas corretamente e podem ser
consultadas via Spark SQL (e, depois de publicadas, via Athena)."""),
        code("""\
spark.sql(f"SHOW TABLES IN {DB_BRONZE}").show(truncate=False)
"""),
    ]
    return notebook(cells)


def build_silver_notebook() -> dict:
    cells = [
        md("""\
# Silver — harmonização das 3 edições num schema único

**O desafio desta camada**: cada edição da pesquisa usa um schema de colunas
diferente — por exemplo, a edição 2023-2024 tem cabeçalhos no formato
`('P1_b ', 'Genero')` (tupla Python serializada como texto), enquanto as
edições 2024-2025 e 2025-2026 usam `1.b_genero`. Além disso, campos booleanos
são representados como `'0'/'1'` em duas edições e como `'TRUE'/'FALSE'` em
outra. Esta validado localmente em `src/silver_harmonization.py` (pandas) —
este notebook replica exatamente a mesma lógica em PySpark.

Resultado: duas tabelas Silver —
- `tb_silver_respondentes`: uma linha por respondente, ~28 campos
  padronizados, união das 3 edições (schema largo).
- `tb_silver_tecnologias_adocao`: uma linha por `(respondente, tecnologia)`
  (schema longo/despivotado) — em vez de manter dezenas de colunas 0/1 por
  linguagem/banco/cloud/ferramenta de BI, cada tecnologia marcada como "usa"
  vira uma linha. Isso simplifica MUITO os `GROUP BY` da camada Gold e do
  Athena (ex: "ranking de linguagens mais usadas" é um `GROUP BY tecnologia`
  direto, em vez de somar 15 colunas manualmente)."""),
        code(GLUE_SESSION_MAGICS),
        code(GLUE_CATALOG_CONFIG),
        code(GLUE_BOOT),
        code(CONFIG_CELL),
        md("""\
## Mapeamento de colunas por edição

Os índices abaixo foram determinados inspecionando o header de cada CSV (ver
`docs/_headers_*.txt` e `docs/_diagnostico_categorias.txt` no protótipo local)
e validados comparando distribuições de categorias entre as 3 edições."""),
        code("""\
# ATENCAO — indices abaixo re-mapeados em 2026-10-19 depois de inspecionar os
# CABECALHOS REAIS dos 3 CSVs no S3 (via S3 Select), nao mais os CSVs de
# referencia locais. Achado ao vivo: o arquivo de "2023-2024" do time
# (State_of_data_2022.csv, 353 colunas) e uma revisao MAIS ANTIGA do Kaggle
# que nao tem as perguntas de IA Generativa nem "ferramenta de BI preferida"
# — por isso esses 3 campos ficam de fora do dict dessa edicao (viram NULL
# automaticamente no unionByName(allowMissingColumns=True) mais abaixo, o que
# e o resultado correto: a pergunta nunca existiu pra essa edicao). Ja o
# arquivo real de "2024-2025" (df_survey_2023.csv, 399 colunas) tem a MESMA
# estrutura que o CSV de referencia local de 2023-2024 usado antes — por isso
# os indices que antes estavam em "2023-2024" foram movidos pra "2024-2025".
# "2025-2026" nao mudou (confirmado igual ao arquivo real, 388 colunas).
SCALAR_FIELDS = {
    "2023-2024": {
        "id_respondente": 0, "idade": 1, "faixa_idade": 2, "genero": 3,
        "cor_raca_etnia": 4, "pcd": 5, "vive_no_brasil": 8, "uf": 10,
        "regiao": 11, "nivel_ensino": 14, "area_formacao": 15,
        "situacao_trabalho": 16, "setor": 17, "numero_funcionarios": 18,
        "gestor": 19, "cargo_atual": 21, "nivel_senioridade": 22,
        "faixa_salarial": 23, "tempo_exp_dados": 24, "tempo_exp_ti": 25,
        "satisfeito": 26, "modelo_trabalho_atual": 48, "modelo_trabalho_ideal": 49,
        "area_atuacao": 91, "linguagem_preferida": 126, "cloud_preferida": 162,
        # sem ferramenta_bi_preferida / empresa_prioriza_ia_generativa /
        # uso_ia_generativa_individual — essas perguntas nao existem no CSV
        # real desta edicao (confirmado via S3 Select).
    },
    "2024-2025": {
        "id_respondente": 0, "idade": 1, "faixa_idade": 2, "genero": 3,
        "cor_raca_etnia": 4, "pcd": 5, "vive_no_brasil": 21, "uf": 23,
        "regiao": 24, "nivel_ensino": 27, "area_formacao": 28,
        "situacao_trabalho": 29, "setor": 30, "numero_funcionarios": 31,
        "gestor": 32, "cargo_atual": 34, "nivel_senioridade": 35,
        "faixa_salarial": 36, "tempo_exp_dados": 37, "tempo_exp_ti": 38,
        "satisfeito": 39, "modelo_trabalho_atual": 62, "modelo_trabalho_ideal": 63,
        "area_atuacao": 124, "linguagem_preferida": 160, "cloud_preferida": 203,
        "ferramenta_bi_preferida": 228, "empresa_prioriza_ia_generativa": 103,
        "uso_ia_generativa_individual": 238,
    },
    "2025-2026": {
        "id_respondente": 0, "idade": 2, "faixa_idade": 3, "genero": 4,
        "cor_raca_etnia": 5, "pcd": 6, "vive_no_brasil": 22, "uf": 25,
        "regiao": 26, "nivel_ensino": 31, "area_formacao": 32,
        "situacao_trabalho": 33, "setor": 34, "numero_funcionarios": 35,
        "gestor": 36, "cargo_atual": 38, "nivel_senioridade": 39,
        "faixa_salarial": 40, "tempo_exp_dados": 41, "tempo_exp_ti": 42,
        "satisfeito": 43, "modelo_trabalho_atual": 70, "modelo_trabalho_ideal": 71,
        "area_atuacao": 133, "linguagem_preferida": 144, "cloud_preferida": 197,
        "ferramenta_bi_preferida": 217, "empresa_prioriza_ia_generativa": 112,
        "uso_ia_generativa_individual": 227,
    },
}

MULTI_SELECT_RANGES = {
    "2023-2024": {"linguagem": range(111, 125), "banco_dados": range(128, 161),
                  "cloud": range(163, 166), "ferramenta_bi": range(167, 190)},
    "2024-2025": {"linguagem": range(144, 159), "banco_dados": range(162, 195),
                  "cloud": range(196, 203), "ferramenta_bi": range(205, 228)},
    "2025-2026": {"linguagem": range(145, 155), "banco_dados": range(156, 189),
                  "cloud": range(190, 197), "ferramenta_bi": range(199, 217)},
}

ANO_PESQUISA = {"2023-2024": 2023, "2024-2025": 2024, "2025-2026": 2025}
TRUE_LIKE = ["1", "TRUE", "True", "true"]
FALSE_LIKE = ["0", "FALSE", "False", "false"]
"""),
        md("## Funções de limpeza e recodificação (idênticas à versão pandas validada)"),
        code("""\
import re

def col_by_idx(df, idx):
    # F.col(nome) sozinho (e tambem df[nome]) quebra com AnalysisException em
    # varios cabecalhos da edicao 2023-2024, serializados como tupla Python em
    # texto (ex: "('P1_b ', 'Genero')") — o parser de nomes qualificados do
    # Spark tenta interpretar o ponto/virgula/aspas dentro do nome. Envolver
    # em crase (`...`) forca o nome inteiro a ser tratado como um unico
    # identificador literal.
    return F.col(f"`{df.columns[idx]}`")

def to_bool01(c):
    return F.when(c.isin(TRUE_LIKE), 1).when(c.isin(FALSE_LIKE), 0).otherwise(None).cast("int")

def blank_to_null(c):
    trimmed = F.trim(c)
    return F.when(trimmed == "", None).otherwise(trimmed)

def faixa_salarial_valor_medio(c):
    # "de R$ 8.001/mês a R$ 12.000/mês" -> ponto médio; casos abertos têm valor fixo.
    low = F.regexp_extract(c, r"R\\$\\s*([\\d.]+)/m[êe]s\\s+a\\s+R\\$", 1)
    high = F.regexp_extract(c, r"a\\s+R\\$\\s*([\\d.]+)/m[êe]s", 1)
    low_num = F.regexp_replace(low, r"\\.", "").cast("double")
    high_num = F.regexp_replace(high, r"\\.", "").cast("double")
    return (
        F.when(c.isNull(), None)
        .when(c.contains("Acima de"), F.lit(45000.0))
        .when(c.contains("Menos de"), F.lit(500.0))
        .when((low_num.isNotNull()) & (high_num.isNotNull()), (low_num + high_num) / 2)
        .otherwise(None)
    )

def classificar_prioridade_ia(c):
    t = F.lower(c)
    return (
        F.when(c.isNull(), None)
        .when(t.contains("principal prioridade"), "Prioridade alta (foco executivo)")
        .when(t.contains("próximos 2-4 anos") | t.contains("proximos 2-4 anos"), "Prioridade de médio prazo")
        .when(t.contains("mais ou menos"), "Iniciativa isolada / pouco foco")
        .when(t.contains("não sei") | t.contains("nao sei"), "Não sabe opinar")
        .when(t.contains("não é uma iniciativa") | t.contains("nao e uma iniciativa"), "Não é prioridade")
        .otherwise("Outro")
    )

def classificar_uso_ia(c):
    t = F.lower(c)
    nao_usa = t.contains("não utilizo nenhum") | t.contains("nao utilizo nenhum")
    usa = F.when(c.isNull() | (c == ""), None).when(nao_usa, 0).otherwise(1)
    paga = F.when(t.contains("pagas") | t.contains("pago") | t.contains("paga pela"), 1).otherwise(0)
    codigo = F.when(t.contains("copilot") | t.contains("ai para código") | t.contains("ai para codigo"), 1).otherwise(0)
    return usa, paga, codigo

def rotulo_tecnologia(header: str) -> str:
    m = re.match(r"^\\(?'?[\\w.]+\\s*'?,?\\s*'(.+)'\\)?$", header)
    if m:
        return m.group(1).strip()
    m2 = re.match(r"^\\d+(?:\\.[0-9a-zA-Z]+)*[_ ](.+)$", header)
    if m2:
        return m2.group(1).strip()
    # Formato real das edicoes 2024-2025/2025-2026 no S3 (diferente do CSV de
    # referencia local usado antes): prefixo de letra+numero repetido, com ou
    # sem underscore entre letra e numero (ex. "c_4_c_3_python",
    # "p4_d_1_sql") -> captura so o nome final.
    m3 = re.match(r"^[a-z]_?\\d+(?:_[a-z]_?\\d+)*_(.+)$", header)
    if m3:
        return m3.group(1).strip()
    return header.strip()
"""),
        md("## Construção de `tb_silver_respondentes`"),
        code("""\
CATEGORICAS = [
    "faixa_idade", "genero", "cor_raca_etnia", "pcd", "uf", "regiao",
    "nivel_ensino", "area_formacao", "situacao_trabalho", "setor",
    "numero_funcionarios", "cargo_atual", "nivel_senioridade", "faixa_salarial",
    "tempo_exp_dados", "tempo_exp_ti", "modelo_trabalho_atual",
    "modelo_trabalho_ideal", "area_atuacao", "linguagem_preferida",
    "cloud_preferida", "ferramenta_bi_preferida",
]

respondentes_frames = []
for edicao, col_map in SCALAR_FIELDS.items():
    df = bronze_dfs[edicao] if "bronze_dfs" in dir() else spark.table(
        f"{DB_BRONZE}.tb_bronze_{edicao.replace('-', '_')}"
    )
    # remove respondentes duplicados (encontrados na validacao local: a
    # propria pesquisa tem alguns tokens de respondente repetidos na origem)
    id_col_name = df.columns[col_map["id_respondente"]]
    antes = df.count()
    df = df.dropDuplicates([id_col_name])
    print(f"{edicao}: {antes - df.count()} duplicado(s) removido(s)")

    selecionadas = [col_by_idx(df, idx).alias(nome) for nome, idx in col_map.items()]
    out = df.select(*selecionadas)

    out = out.withColumn("idade", F.col("idade").cast("int"))
    out = out.withColumn(
        "idade", F.when((F.col("idade") < 14) | (F.col("idade") > 80), None).otherwise(F.col("idade"))
    )
    for c in CATEGORICAS:
        # "in out.columns", nao assumindo que toda edicao tem todo campo: a
        # 2023-2024 real nao tem, por exemplo, ferramenta_bi_preferida.
        if c in out.columns:
            out = out.withColumn(c, blank_to_null(F.col(c)))

    out = out.withColumn("vive_no_brasil", to_bool01(F.col("vive_no_brasil")))
    out = out.withColumn("gestor", to_bool01(F.col("gestor")))
    out = out.withColumn("satisfeito_empresa_atual", to_bool01(F.col("satisfeito"))).drop("satisfeito")

    out = out.withColumn("faixa_salarial_valor_medio", faixa_salarial_valor_medio(F.col("faixa_salarial")))

    # A edicao 2023-2024 (arquivo real) nao tem as perguntas de IA Generativa
    # (ver nota no mapeamento de colunas acima) — nesse caso os campos
    # derivados ficam NULL explicitamente, em vez de falhar tentando ler uma
    # coluna que nao existe no select() desta edicao.
    if "empresa_prioriza_ia_generativa" in col_map:
        out = out.withColumn("prioridade_ia_empresa", classificar_prioridade_ia(F.col("empresa_prioriza_ia_generativa")))
    else:
        out = out.withColumn("prioridade_ia_empresa", F.lit(None).cast("string"))

    if "uso_ia_generativa_individual" in col_map:
        usa, paga, codigo = classificar_uso_ia(F.col("uso_ia_generativa_individual"))
    else:
        usa = paga = codigo = F.lit(None).cast("int")
    out = out.withColumn("usa_ia_generativa", usa).withColumn("paga_por_ia_generativa", paga).withColumn("usa_ia_para_codigo", codigo)

    out = out.withColumn("edicao_pesquisa", F.lit(edicao))
    out = out.withColumn("ano_pesquisa", F.lit(ANO_PESQUISA[edicao]))
    out = out.withColumn("id_unico", F.concat(F.lit(edicao + "_"), F.col("id_respondente").cast("string")))

    respondentes_frames.append(out)

tb_silver_respondentes = respondentes_frames[0]
for f in respondentes_frames[1:]:
    tb_silver_respondentes = tb_silver_respondentes.unionByName(f, allowMissingColumns=True)

print(f"tb_silver_respondentes: {tb_silver_respondentes.count():,} linhas")
tb_silver_respondentes.groupBy("edicao_pesquisa").count().show()
"""),
        code("""\
(
    tb_silver_respondentes.write
    .mode("overwrite")
    .format("parquet")
    .option("path", SILVER_PATH + "respondentes/")
    .partitionBy("ano_pesquisa")
    .saveAsTable(f"{DB_SILVER}.tb_silver_respondentes")
)
print(f"gravado e catalogado: {DB_SILVER}.tb_silver_respondentes")
"""),
        md("""\
## Construção de `tb_silver_tecnologias_adocao` (schema longo)

Para cada edição e cada categoria de tecnologia (linguagem, banco de dados,
cloud, ferramenta de BI), cada coluna checkbox (0/1) vira uma linha —
mantendo apenas as linhas onde a tecnologia foi marcada como usada
(`usa = 1`), para não inflar a tabela com zeros."""),
        code("""\
tec_frames = []
for edicao, categorias in MULTI_SELECT_RANGES.items():
    df = bronze_dfs[edicao] if "bronze_dfs" in dir() else spark.table(
        f"{DB_BRONZE}.tb_bronze_{edicao.replace('-', '_')}"
    )
    id_col = df.columns[SCALAR_FIELDS[edicao]["id_respondente"]]
    df = df.dropDuplicates([id_col])  # mesmo criterio de deduplicacao da tb_silver_respondentes

    for categoria, idx_range in categorias.items():
        for idx in idx_range:
            header = df.columns[idx]
            tecnologia = rotulo_tecnologia(header)
            sub = df.select(
                F.concat(F.lit(edicao + "_"), F.col(f"`{id_col}`").cast("string")).alias("id_unico"),
                F.lit(edicao).alias("edicao_pesquisa"),
                F.lit(ANO_PESQUISA[edicao]).alias("ano_pesquisa"),
                F.lit(categoria).alias("categoria_tecnologia"),
                F.lit(tecnologia).alias("tecnologia"),
                F.col(f"`{header}`").cast("int").alias("usa"),
            ).filter(F.col("usa") == 1)
            tec_frames.append(sub)

tb_silver_tecnologias_adocao = tec_frames[0]
for f in tec_frames[1:]:
    tb_silver_tecnologias_adocao = tb_silver_tecnologias_adocao.unionByName(f)

print(f"tb_silver_tecnologias_adocao: {tb_silver_tecnologias_adocao.count():,} linhas")
"""),
        code("""\
(
    tb_silver_tecnologias_adocao.write
    .mode("overwrite")
    .format("parquet")
    .option("path", SILVER_PATH + "tecnologias_adocao/")
    .saveAsTable(f"{DB_SILVER}.tb_silver_tecnologias_adocao")
)
print(f"gravado e catalogado: {DB_SILVER}.tb_silver_tecnologias_adocao")
"""),
    ]
    return notebook(cells)


def build_gold_notebook() -> dict:
    cells = [
        md("""\
# Gold — tabelas especializadas por pergunta de negócio

Lê a Silver consolidada e gera 7 tabelas Gold, cada uma já agregada e pronta
para consulta direta via Athena (sem precisar repetir `GROUP BY` complexos a
cada consulta) — ver `notebooks/05_analytics_athena/*.sql` para as queries
finais sobre estas tabelas. Lógica idêntica à validada em
`src/gold_builder.py` (pandas)."""),
        code(GLUE_SESSION_MAGICS),
        code(GLUE_CATALOG_CONFIG),
        code(GLUE_BOOT),
        code(CONFIG_CELL),
        code("""\
respondentes = spark.table(f"{DB_SILVER}.tb_silver_respondentes")
tecnologias = spark.table(f"{DB_SILVER}.tb_silver_tecnologias_adocao")

def gravar_gold(df, nome_tabela):
    (
        df.write.mode("overwrite").format("parquet")
        .option("path", GOLD_PATH + nome_tabela + "/")
        .saveAsTable(f"{DB_GOLD}.{nome_tabela}")
    )
    print(f"gravado e catalogado: {DB_GOLD}.{nome_tabela}  ({df.count():,} linhas)")
"""),
        md("## gold_perfil_mercado — Q1: estrutura do mercado"),
        code("""\
gold_perfil_mercado = (
    respondentes.filter(F.col("cargo_atual").isNotNull())
    .groupBy("ano_pesquisa", "regiao", "cargo_atual", "nivel_senioridade")
    .agg(F.count("*").alias("n_respondentes"))
)
gravar_gold(gold_perfil_mercado, "gold_perfil_mercado")
"""),
        md("## gold_remuneracao — Q2 (perfis valorizados), Q3 (gap de gênero), Q6 (região/modelo)"),
        code("""\
gold_remuneracao = (
    respondentes.filter(F.col("faixa_salarial_valor_medio").isNotNull())
    .groupBy("ano_pesquisa", "cargo_atual", "nivel_senioridade", "regiao", "genero", "modelo_trabalho_atual")
    .agg(
        F.mean("faixa_salarial_valor_medio").alias("salario_medio"),
        F.expr("percentile_approx(faixa_salarial_valor_medio, 0.5)").alias("salario_mediano"),
        F.count("*").alias("n_respondentes"),
    )
)
gravar_gold(gold_remuneracao, "gold_remuneracao")
"""),
        md("## gold_diversidade_genero — Q3"),
        code("""\
total_por_nivel = (
    respondentes.filter(F.col("nivel_senioridade").isNotNull())
    .groupBy("ano_pesquisa", "nivel_senioridade")
    .agg(F.count("*").alias("total_nivel"))
)
genero_por_nivel = (
    respondentes.filter(F.col("nivel_senioridade").isNotNull())
    .groupBy("ano_pesquisa", "nivel_senioridade", "genero")
    .agg(F.count("*").alias("n"))
)
gold_diversidade_genero = (
    genero_por_nivel.join(total_por_nivel, ["ano_pesquisa", "nivel_senioridade"])
    .withColumn("pct_dentro_do_nivel", F.round(F.col("n") / F.col("total_nivel") * 100, 1))
    .select("ano_pesquisa", "nivel_senioridade", "genero", "pct_dentro_do_nivel")
)
gravar_gold(gold_diversidade_genero, "gold_diversidade_genero")
"""),
        md("## gold_tecnologias_adocao — Q4"),
        code("""\
total_por_ano = respondentes.groupBy("ano_pesquisa").agg(F.count("*").alias("total_respondentes"))
tech_counts = (
    tecnologias.groupBy("ano_pesquisa", "categoria_tecnologia", "tecnologia")
    .agg(F.count("*").alias("n_respondentes"))
)
gold_tecnologias_adocao = (
    tech_counts.join(total_por_ano, "ano_pesquisa")
    .withColumn("pct_adocao", F.round(F.col("n_respondentes") / F.col("total_respondentes") * 100, 1))
    .drop("total_respondentes")
)
gravar_gold(gold_tecnologias_adocao, "gold_tecnologias_adocao")
"""),
        md("## gold_adocao_ia e gold_prioridade_ia_empresa — Q5"),
        code("""\
gold_adocao_ia = respondentes.groupBy("ano_pesquisa").agg(
    F.round(F.mean("usa_ia_generativa") * 100, 1).alias("pct_usa_ia_generativa"),
    F.round(F.mean("paga_por_ia_generativa") * 100, 1).alias("pct_paga_por_ia"),
    F.round(F.mean("usa_ia_para_codigo") * 100, 1).alias("pct_usa_ia_para_codigo"),
)
gravar_gold(gold_adocao_ia, "gold_adocao_ia")

base_gestores = respondentes.filter(F.col("prioridade_ia_empresa").isNotNull())
total_gestores = base_gestores.groupBy("ano_pesquisa").agg(F.count("*").alias("total_gestores"))
gold_prioridade_ia_empresa = (
    base_gestores.groupBy("ano_pesquisa", "prioridade_ia_empresa")
    .agg(F.count("*").alias("n_gestores"))
    .join(total_gestores, "ano_pesquisa")
    .withColumn("pct_gestores", F.round(F.col("n_gestores") / F.col("total_gestores") * 100, 1))
    .drop("total_gestores")
)
gravar_gold(gold_prioridade_ia_empresa, "gold_prioridade_ia_empresa")
"""),
        md("## gold_modelo_trabalho — Q6"),
        code("""\
gold_modelo_trabalho = (
    respondentes.filter(F.col("modelo_trabalho_atual").isNotNull())
    .groupBy("ano_pesquisa", "regiao", "modelo_trabalho_atual")
    .agg(F.count("*").alias("n_respondentes"))
)
gravar_gold(gold_modelo_trabalho, "gold_modelo_trabalho")
"""),
        md("## Verificação final"),
        code("""\
spark.sql(f"SHOW TABLES IN {DB_GOLD}").show(truncate=False)
"""),
    ]
    return notebook(cells)


def build_eda_notebook() -> dict:
    cells = [
        md("""\
# EDA — gráficos direto no Glue Studio Notebook, a partir da Gold

Este notebook roda a análise exploratória **dentro da AWS** (Glue Notebook,
Spark), lendo as 7 tabelas Gold e desenhando os mesmos gráficos que o
protótipo local (`src/eda_charts.py`) gerou a partir dos mesmos dados —
assim dá pra conferir, ao vivo, que os números batem.

Cada célula usa a magic `%matplot plt` do Glue para mostrar o gráfico direto
na saída da célula (Spark → `.toPandas()` nos resultados já agregados da
Gold, que são pequenos → matplotlib normal)."""),
        code(GLUE_SESSION_MAGICS),
        code(GLUE_CATALOG_CONFIG),
        code(GLUE_BOOT),
        code(CONFIG_CELL),
        code("""\
import matplotlib.pyplot as plt

MAGENTA = "#ED145B"
AZUL = "#2A78D6"
VERDE = "#008300"
AMBAR = "#EDA100"
VIOLETA = "#6250D6"
SENIORIDADE_ORDEM = ["Júnior", "Pleno", "Sênior", "Especialista/Staff+"]

plt.rcParams.update({"figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})
"""),
        md("## Q1 — Estrutura do mercado: top 10 cargos"),
        code("""\
perfil = spark.table(f"{DB_GOLD}.gold_perfil_mercado").toPandas()
top_cargos = perfil.groupby("cargo_atual")["n_respondentes"].sum().sort_values().tail(10)

plt.figure(figsize=(8, 5))
plt.barh(top_cargos.index, top_cargos.values, color=MAGENTA)
plt.title("Os 10 cargos mais comuns no mercado de Dados (BR)")
plt.xlabel("Nº de respondentes (2023-2026)")
plt.tight_layout()
%matplot plt
"""),
        md("## Q2 — Perfis mais valorizados: salário médio por cargo"),
        code("""\
remuneracao = spark.table(f"{DB_GOLD}.gold_remuneracao").toPandas()
remuneracao["peso"] = remuneracao["salario_medio"] * remuneracao["n_respondentes"]
por_cargo = remuneracao.groupby("cargo_atual").agg(peso=("peso", "sum"), n=("n_respondentes", "sum"))
por_cargo["salario_medio"] = por_cargo["peso"] / por_cargo["n"]
top_pagos = por_cargo[por_cargo["n"] >= 50].sort_values("salario_medio").tail(10)

plt.figure(figsize=(8, 5))
plt.barh(top_pagos.index, top_pagos["salario_medio"], color=MAGENTA)
plt.title("Remuneração média por cargo (entre os mais comuns)")
plt.xlabel("Salário médio estimado (R$/mês)")
plt.tight_layout()
%matplot plt
"""),
        md("## Q3 — Diversidade de gênero: participação por senioridade e gap salarial"),
        code("""\
import numpy as np

diversidade = spark.table(f"{DB_GOLD}.gold_diversidade_genero").toPandas()
ultimo_ano = diversidade["ano_pesquisa"].max()
dg = diversidade[(diversidade["ano_pesquisa"] == ultimo_ano) & (diversidade["genero"].isin(["Masculino", "Feminino"]))]
pivot_dg = dg.pivot(index="nivel_senioridade", columns="genero", values="pct_dentro_do_nivel").reindex(SENIORIDADE_ORDEM)

x = np.arange(len(pivot_dg.index))
largura = 0.35
plt.figure(figsize=(7.5, 4.5))
plt.bar(x - largura/2, pivot_dg["Masculino"], largura, label="Masculino", color=MAGENTA)
plt.bar(x + largura/2, pivot_dg["Feminino"], largura, label="Feminino", color=AZUL)
plt.xticks(x, pivot_dg.index)
plt.ylabel("% dentro do nível")
plt.title(f"Participação por gênero e senioridade ({ultimo_ano})")
plt.legend()
plt.tight_layout()
%matplot plt
"""),
        code("""\
sal_genero = remuneracao[remuneracao["genero"].isin(["Masculino", "Feminino"])]
sal_genero = sal_genero.groupby(["nivel_senioridade", "genero"]).apply(
    lambda g: (g["salario_medio"] * g["n_respondentes"]).sum() / g["n_respondentes"].sum()
).unstack().reindex(SENIORIDADE_ORDEM)

plt.figure(figsize=(7.5, 4.5))
plt.bar(x - largura/2, sal_genero["Masculino"], largura, label="Masculino", color=MAGENTA)
plt.bar(x + largura/2, sal_genero["Feminino"], largura, label="Feminino", color=AZUL)
plt.xticks(x, sal_genero.index)
plt.ylabel("Salário médio estimado (R$/mês)")
plt.title("Diferença salarial entre gêneros, por senioridade")
plt.legend()
plt.tight_layout()
%matplot plt
"""),
        md("## Q4 — Tecnologias mais adotadas (edição mais recente)"),
        code("""\
tecnologias = spark.table(f"{DB_GOLD}.gold_tecnologias_adocao").toPandas()
ultimo_ano_tec = tecnologias["ano_pesquisa"].max()
fig, axes = plt.subplots(2, 2, figsize=(12, 9))
categorias_labels = {
    "linguagem": "Linguagens de programação",
    "banco_dados": "Bancos de dados",
    "cloud": "Provedores de Cloud",
    "ferramenta_bi": "Ferramentas de BI",
}
for ax, (cat, label) in zip(axes.flat, categorias_labels.items()):
    top = (
        tecnologias[(tecnologias["categoria_tecnologia"] == cat) & (tecnologias["ano_pesquisa"] == ultimo_ano_tec)]
        .nlargest(6, "pct_adocao").sort_values("pct_adocao")
    )
    ax.barh(top["tecnologia"].tolist(), top["pct_adocao"], color=MAGENTA)
    ax.set_title(label, fontsize=12, fontweight="bold")
fig.suptitle(f"Tecnologias mais adotadas ({ultimo_ano_tec})", fontsize=14, fontweight="bold")
plt.tight_layout()
%matplot plt
"""),
        md("## Q5 — Adoção de IA Generativa e prioridade executiva"),
        code("""\
adocao_ia = spark.table(f"{DB_GOLD}.gold_adocao_ia").toPandas().sort_values("ano_pesquisa")

plt.figure(figsize=(7, 4.5))
plt.plot(adocao_ia["ano_pesquisa"], adocao_ia["pct_usa_ia_generativa"], marker="o", linewidth=2.5, markersize=8, color=MAGENTA)
for _, row in adocao_ia.iterrows():
    plt.text(row["ano_pesquisa"], row["pct_usa_ia_generativa"] + 1.5, f"{row['pct_usa_ia_generativa']:.0f}%", ha="center")
plt.ylim(0, 105)
plt.title("Adoção individual de IA Generativa dispara")
plt.ylabel("% que usa IA Generativa no trabalho")
plt.tight_layout()
%matplot plt
"""),
        code("""\
prioridade_ia = spark.table(f"{DB_GOLD}.gold_prioridade_ia_empresa").toPandas()
ultimo_ano_ia = prioridade_ia["ano_pesquisa"].max()
ordem_prioridade = ["Não é prioridade", "Não sabe opinar", "Iniciativa isolada / pouco foco",
                    "Prioridade de médio prazo", "Prioridade alta (foco executivo)"]
pri = prioridade_ia[prioridade_ia["ano_pesquisa"] == ultimo_ano_ia].set_index("prioridade_ia_empresa").reindex(ordem_prioridade)

plt.figure(figsize=(7, 4.5))
plt.barh(pri.index, pri["pct_gestores"], color=[AMBAR, AMBAR, VIOLETA, AZUL, MAGENTA])
plt.xlabel("% dos gestores")
plt.title(f"Prioridade de IA Generativa nas empresas ({ultimo_ano_ia})")
plt.tight_layout()
%matplot plt
"""),
        md("## Q6 — Diferenças por região e modelo de trabalho"),
        code("""\
sal_regiao = remuneracao.groupby("regiao").apply(
    lambda g: (g["salario_medio"] * g["n_respondentes"]).sum() / g["n_respondentes"].sum()
).sort_values()

plt.figure(figsize=(7, 4.5))
plt.barh(sal_regiao.index, sal_regiao.values, color=MAGENTA)
plt.xlabel("Salário médio estimado (R$/mês)")
plt.title("Salário médio por região")
plt.tight_layout()
%matplot plt
"""),
        md("""\
## Conferindo com o resultado local

Compare os números acima com `docs/_eda_achados.txt` e os PNGs em
`presentation/charts/` — devem bater (mesma base, mesma lógica de
harmonização, só rodando em Spark/AWS em vez de pandas local)."""),
    ]
    return notebook(cells)


def main() -> None:
    save(build_bronze_notebook(), NOTEBOOKS / "01_bronze" / "bronze_glue_notebook.ipynb")
    save(build_silver_notebook(), NOTEBOOKS / "02_silver" / "silver_glue_notebook.ipynb")
    save(build_gold_notebook(), NOTEBOOKS / "03_gold" / "gold_glue_notebook.ipynb")
    save(build_eda_notebook(), NOTEBOOKS / "04_eda" / "eda_glue_notebook.ipynb")


if __name__ == "__main__":
    main()
