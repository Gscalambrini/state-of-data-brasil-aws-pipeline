r"""Gera o relatorio executivo (Entrega 1) em .docx, no mesmo formato de um
relatorio tecnico-cientifico (capa, sumario, resumo executivo, introducao,
metodologia, analise, diagnostico, recomendacoes, conclusao, referencias,
anexos) usado como referencia pelo grupo na Fase 1, formatado de acordo com
a ABNT NBR 14724 (apresentacao de trabalhos academicos): fonte Arial 12,
espacamento 1,5 no corpo do texto, margens 3/2/3/2 cm e numeracao de pagina
no cabecalho, alinhada a direita.

Diferenca em relacao ao material anterior (PowerPoint): este arquivo e um
DOCUMENTO de texto corrido com storytelling completo, nao um conjunto de
slides com pouco texto. Os 11 graficos finais (gerados por eda_charts_aws.py,
com os numeros REAIS validados via Athena) e o diagrama de arquitetura
(diagrams/arquitetura_solucao.png) sao embutidos como figuras dentro do texto.

Uso: python build_relatorio.py
Saida: material_executivo.docx (neste mesmo diretorio)

Depois de gerar o .docx, abra no Word e atualize o Sumario (botao direito
sobre o sumario > Atualizar campo > Atualizar o indice inteiro) antes de
exportar/salvar como PDF -- ou automatize via COM (PowerShell):
  $app = New-Object -ComObject Word.Application
  $doc = $app.Documents.Open("<caminho completo>\material_executivo.docx")
  $doc.Fields.Update(); $doc.TablesOfContents | % { $_.Update() }
  $doc.SaveAs([ref]"<caminho completo>\material_executivo.pdf", [ref]17)
  $doc.Close(); $app.Quit()
"""
from pathlib import Path

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = Path(__file__).resolve().parents[1]
CHARTS = ROOT / "presentation" / "charts"
DIAGRAMS = ROOT / "diagrams"
OUT_PATH = ROOT / "presentation" / "material_executivo.docx"

MAGENTA = RGBColor(0xED, 0x14, 0x5B)
DARK = RGBColor(0x1A, 0x1A, 0x1A)
GRAY = RGBColor(0x52, 0x51, 0x4E)
MAGENTA_HEX = "ED145B"
LIGHT_PINK_HEX = "FDE7EE"

FONT_NAME = "Arial"
BODY_SIZE = Pt(12)

# ---------------------------------------------------------------------------
# Low-level helpers (python-docx nao expoe tudo via API publica)
# ---------------------------------------------------------------------------

def set_cell_background(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), color_hex)
    tcPr.append(shd)


def set_bottom_border(paragraph, color_hex=MAGENTA_HEX, size=18):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), color_hex)
    pBdr.append(bottom)
    pPr.append(pBdr)


def remove_table_borders(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "nil")
        borders.append(el)
    tblPr.append(borders)


def style_table_borders(table, color_hex=MAGENTA_HEX, size=4):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(size))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color_hex)
        borders.append(el)
    tblPr.append(borders)


def add_page_number_field(paragraph):
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run._r.append(fld_end)


def add_toc(document):
    paragraph = document.add_paragraph()
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-2" \\h \\z \\u'
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    placeholder = OxmlElement("w:t")
    placeholder.text = "Atualize o sumário (clique com o botão direito > Atualizar campo) após abrir no Word."
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    r2 = paragraph.add_run()
    r2._r.append(placeholder)
    r3 = paragraph.add_run()
    r3._r.append(fld_end)


# ---------------------------------------------------------------------------
# High-level content helpers
# ---------------------------------------------------------------------------

def body(document, text, *, lead_bold=None, italic=False, space_after=10):
    p = document.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.first_line_indent = Cm(1.25)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.5
    if lead_bold:
        r = p.add_run(lead_bold)
        r.bold = True
        r.italic = italic
        r.font.name = FONT_NAME
        r.font.size = BODY_SIZE
    r = p.add_run(text)
    r.italic = italic
    r.font.name = FONT_NAME
    r.font.size = BODY_SIZE
    return p


def bullet(document, text):
    p = document.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.5
    r = p.add_run(text)
    r.font.name = FONT_NAME
    r.font.size = BODY_SIZE
    return p


def heading1(document, number, text, *, page_break=True):
    p = document.add_heading(level=1)
    p.paragraph_format.page_break_before = page_break
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(10)
    set_bottom_border(p)
    r = p.add_run(f"{number}. {text}" if number else text)
    r.font.name = FONT_NAME
    r.font.size = Pt(16)
    r.font.bold = True
    r.font.color.rgb = MAGENTA
    return p


def heading2(document, number, text):
    p = document.add_heading(level=2)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(f"{number} {text}" if number else text)
    r.font.name = FONT_NAME
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = DARK
    return p


def caption(document, text, *, bold_prefix=None, center=True, italic=False, size=10, color=None, space_before=6, space_after=4):
    p = document.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    if bold_prefix:
        r = p.add_run(bold_prefix)
        r.bold = True
        r.font.size = Pt(size)
        r.font.name = FONT_NAME
    r = p.add_run(text)
    r.italic = italic
    r.font.size = Pt(size)
    r.font.name = FONT_NAME
    if color:
        r.font.color.rgb = color
    return p


def add_figure(document, image_path, fig_num, title, *, width_cm=15.5, source="Dataset State of Data Brasil (2023-2026), Data Hackers/Kaggle, processado via AWS Glue/Athena."):
    caption(document, title, bold_prefix=f"Gráfico {fig_num}: ")
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(image_path), width=Cm(width_cm))
    caption(document, source, size=9, italic=True, color=GRAY, space_before=2, space_after=14)


def kpi_table(document, rows, col_widths=(8.0, 7.0)):
    table = document.add_table(rows=len(rows) + 1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    style_table_borders(table)
    hdr = table.rows[0].cells
    hdr[0].text = "Indicador"
    hdr[1].text = "Resultado"
    for c in hdr:
        set_cell_background(c, MAGENTA_HEX)
        for p in c.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.bold = True
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                r.font.name = FONT_NAME
                r.font.size = Pt(11)
    for i, (k, v) in enumerate(rows, start=1):
        cells = table.rows[i].cells
        cells[0].text = k
        cells[1].text = v
        for j, c in enumerate(cells):
            for p in c.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:
                    r.font.name = FONT_NAME
                    r.font.size = Pt(11)
            if i % 2 == 0:
                set_cell_background(c, "F8F8F8")
    for col, w in zip(table.columns, col_widths):
        for cell in col.cells:
            cell.width = Cm(w)
    document.add_paragraph().paragraph_format.space_after = Pt(6)
    return table


# ---------------------------------------------------------------------------
# Documento
# ---------------------------------------------------------------------------

doc = Document()

# --- estilo base -----------------------------------------------------------
normal = doc.styles["Normal"]
normal.font.name = FONT_NAME
normal.font.size = BODY_SIZE
section = doc.sections[0]
section.page_width = Cm(21.0)
section.page_height = Cm(29.7)
# Margens conforme ABNT NBR 14724: esquerda/superior 3 cm, direita/inferior 2 cm
section.left_margin = Cm(3.0)
section.right_margin = Cm(2.0)
section.top_margin = Cm(3.0)
section.bottom_margin = Cm(2.0)
section.different_first_page_header_footer = True

# cabecalho (paginas internas): apenas o numero de pagina, alinhado a
# direita, conforme ABNT (a capa conta mas nao exibe numero)
header_p = section.header.paragraphs[0]
header_p.text = ""
header_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
add_page_number_field(header_p)
for run in header_p.runs:
    run.font.size = Pt(10)
    run.font.color.rgb = GRAY
    run.font.name = FONT_NAME
# pagina de capa sem cabecalho nem rodape
section.first_page_header.paragraphs[0].text = ""
section.first_page_footer.paragraphs[0].text = ""

# ===========================================================================
# CAPA
# ===========================================================================
bar = doc.add_table(rows=1, cols=1)
remove_table_borders(bar)
cell = bar.rows[0].cells[0]
set_cell_background(cell, MAGENTA_HEX)
cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
r = cell.paragraphs[0].add_run("RELATÓRIO EXECUTIVO  –  TECH CHALLENGE FASE 3")
r.font.bold = True
r.font.size = Pt(13)
r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
r.font.name = FONT_NAME
cell.paragraphs[0].paragraph_format.space_before = Pt(10)
cell.paragraphs[0].paragraph_format.space_after = Pt(10)

for _ in range(3):
    doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("FIAP – FACULDADE DE INFORMÁTICA E ADMINISTRAÇÃO PAULISTA")
r.font.size = Pt(12)
r.font.name = FONT_NAME
p2 = doc.add_paragraph()
p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p2.add_run("PÓS-TECH EM DATA ANALYTICS")
r.font.bold = True
r.font.size = Pt(12)
r.font.name = FONT_NAME

for _ in range(4):
    doc.add_paragraph()

hr = doc.add_paragraph()
set_bottom_border(hr, color_hex=MAGENTA_HEX, size=12)

for _ in range(2):
    doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("O MERCADO BRASILEIRO DE DADOS E INTELIGÊNCIA ARTIFICIAL")
r.font.bold = True
r.font.size = Pt(22)
r.font.color.rgb = MAGENTA
r.font.name = FONT_NAME

doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Panorama 2023–2026 e recomendações estratégicas a partir da pesquisa State of\nData Brasil, para uma Instituição Financeira que deseja expandir sua área de\nDados, Analytics e Inteligência Artificial")
r.italic = True
r.font.size = Pt(12)
r.font.name = FONT_NAME

for _ in range(4):
    doc.add_paragraph()

hr2 = doc.add_paragraph()
set_bottom_border(hr2, color_hex=MAGENTA_HEX, size=12)
doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Tech Challenge – Fase 3")
r.bold = True
r.font.size = Pt(12)
r.font.name = FONT_NAME

for _ in range(6):
    doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("São Paulo – SP")
r.bold = True
r.font.size = Pt(11)
r.font.name = FONT_NAME
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("2026")
r.bold = True
r.font.size = Pt(11)
r.font.color.rgb = MAGENTA
r.font.name = FONT_NAME

doc.add_page_break()

# ===========================================================================
# SUMÁRIO
# ===========================================================================
h = doc.add_paragraph()
r = h.add_run("SUMÁRIO")
r.bold = True
r.font.size = Pt(16)
r.font.color.rgb = MAGENTA
r.font.name = FONT_NAME
set_bottom_border(h)
doc.add_paragraph()
add_toc(doc)

# ===========================================================================
# RESUMO EXECUTIVO
# ===========================================================================
heading1(doc, None, "RESUMO EXECUTIVO")

body(
    doc,
    "Este relatório analisa o mercado brasileiro de profissionais de Dados e "
    "Inteligência Artificial, a partir da pesquisa State of Data Brasil "
    "(DATA HACKERS, 2026), para "
    "responder a uma pergunta central: como uma Instituição Financeira de "
    "grande porte deve direcionar sua estratégia de contratação, capacitação "
    "e investimento em tecnologia para expandir sua área de Dados, Analytics "
    "e Inteligência Artificial? A resposta, sustentada pelos dados "
    "apresentados nas seções seguintes, aponta para quatro frentes "
    "prioritárias: formalização de uma estratégia de IA Generativa, "
    "equidade de gênero, adoção de trabalho remoto para acesso a talento "
    "fora do Sudeste, e capacitação técnica direcionada a Python e "
    "Engenharia de Dados/Machine Learning."
)

body(
    doc,
    "A base reúne 13.057 respondentes únicos, consolidados a partir de três "
    "edições da pesquisa (2023-2024, 2024-2025 e 2025-2026), cada uma com um "
    "schema de perguntas diferente, harmonizadas num pipeline de dados "
    "próprio construído inteiramente na AWS (Amazon S3, Glue, Athena). O "
    "mercado é concentrado: o cargo mais comum é Analista de Dados (2.145 "
    "respondentes) e 61% dos profissionais estão na região Sudeste. Entre os "
    "cargos mais comuns, Engenheiro de Machine Learning/AI Engineer é o mais "
    "bem remunerado, com média de R$ 16.382 por mês.",
    lead_bold="Principais achados: ",
)

body(
    doc,
    "Apenas 23,9% dos profissionais de Dados se identificam como mulheres, "
    "participação que cai de 28,2% no nível Júnior para 20,1% no nível "
    "Especialista/Staff+, e, no nível Sênior, mulheres recebem em média 15% "
    "menos que homens. Em tecnologia, Python ultrapassou o SQL como "
    "linguagem mais usada entre 2024 e 2025 (de 48,9% para 55,2% de adoção, "
    "contra uma queda de 55,4% para 50,5% do SQL). A adoção individual de IA "
    "Generativa saltou de 80,3% (2024) para 97,9% (2025), mas apenas 23,8% "
    "dos gestores tratam o tema como prioridade executiva em suas empresas, "
    "uma diferença de quase 75 pontos percentuais entre uso individual "
    "e estratégia corporativa formal. Regionalmente, o Sudeste paga, em "
    "média, 36% a mais que o Nordeste, e o modelo de trabalho híbrido "
    "flexível supera o modelo 100% presencial em remuneração média (R$ "
    "12.546 contra R$ 7.361)."
)

body(
    doc,
    "com base nesse diagnóstico, este relatório recomenda quatro frentes de "
    "ação estratégica: (1) formalizar uma estratégia corporativa de IA "
    "Generativa, aproveitando a janela em que o uso individual já é quase "
    "universal mas a governança formal ainda é incipiente; (2) investir em "
    "equidade de gênero, tanto por razões de diversidade quanto como "
    "vantagem competitiva de retenção de talento; (3) adotar o trabalho "
    "remoto como estratégia deliberada de acesso a talento qualificado fora "
    "do eixo Sudeste, a um custo salarial menor; e (4) direcionar a "
    "capacitação técnica interna para Python e para as competências de "
    "Engenharia de Dados e Machine Learning, que concentram os cargos mais "
    "bem remunerados do mercado. O detalhamento de cada recomendação, com o "
    "impacto esperado, está na Seção 6.",
    lead_bold="Recomendações: ",
)

body(
    doc,
    "Vale notar que a harmonização de três edições de pesquisa com schemas "
    "de perguntas diferentes impõe limitações: nem todas as edições "
    "perguntam todos os campos (a edição 2023-2024, por exemplo, não "
    "incluía perguntas sobre Inteligência Artificial Generativa, por isso os "
    "dados de adoção de IA cobrem apenas 2024-2025 e 2025-2026), e algumas "
    "métricas regionais e de senioridade têm uma parcela de respondentes sem "
    "informação. Essas limitações estão detalhadas na Seção 5, junto com o "
    "diagnóstico completo.",
    italic=True,
)

# ===========================================================================
# 1. INTRODUÇÃO
# ===========================================================================
heading1(doc, 1, "INTRODUÇÃO")

body(
    doc,
    "Nos últimos anos, a área de Dados, Analytics e Inteligência Artificial "
    "passou a ocupar um papel cada vez mais central nas estratégias "
    "corporativas, impulsionada pela maturidade crescente de ferramentas de "
    "nuvem, pela popularização da Inteligência Artificial Generativa e pela "
    "pressão competitiva por decisões orientadas por evidências. Nesse "
    "cenário, instituições que pretendem expandir suas áreas de Dados "
    "enfrentam um desafio recorrente: entender, com profundidade e dados "
    "reais, como está estruturado o mercado de profissionais que pretendem "
    "contratar, capacitar e reter."
)

body(
    doc,
    "Para apoiar essa decisão, este relatório utiliza a pesquisa State of "
    "Data Brasil, realizada anualmente pela comunidade Data Hackers "
    "(DATA HACKERS, 2026), uma das mais completas fontes de "
    "informação sobre o perfil dos profissionais de Dados no país, reunindo "
    "dados sobre formação, remuneração, tecnologias utilizadas, modelo de "
    "trabalho, diversidade e adoção de Inteligência Artificial. Foram "
    "utilizadas as três edições mais recentes disponíveis publicamente no "
    "Kaggle (2023-2024, 2024-2025 e 2025-2026), permitindo não apenas um "
    "retrato do mercado em um ponto no tempo, mas também a observação de "
    "tendências de evolução ao longo de três anos."
)

body(
    doc,
    "Diferente de uma análise pontual, este trabalho constrói um pipeline de "
    "dados completo em ambiente de nuvem (AWS), contemplando desde a "
    "ingestão dos dados brutos até a disponibilização de tabelas analíticas "
    "prontas para consulta, reproduzindo, em escala reduzida, o tipo de "
    "arquitetura que uma Instituição Financeira de grande porte utilizaria "
    "para seus próprios dados de mercado e de força de trabalho. A seção 2 "
    "detalha essa arquitetura."
)

body(
    doc,
    "Diante desse contexto, a pergunta norteadora deste relatório é: "
    "como está estruturado o mercado brasileiro de profissionais de Dados, "
    "e que recomendações estratégicas de contratação, capacitação e "
    "investimento em tecnologia podem ser extraídas dele para apoiar a "
    "expansão da área de Dados, Analytics e IA de uma Instituição "
    "Financeira? Para respondê-la, o relatório está estruturado em torno de "
    "sete perguntas de negócio específicas, detalhadas na Seção 4:"
)
for q in [
    "Como está estruturado o mercado brasileiro de Dados?",
    "Quais perfis profissionais são mais valorizados pelo mercado?",
    "Qual é o cenário de diversidade de gênero nas carreiras de Dados?",
    "Quais tecnologias apresentam maior adoção entre os profissionais?",
    "Qual é o índice de adoção de Inteligência Artificial e seu impacto?",
    "Existem diferenças relevantes entre regiões, senioridades ou modelos de trabalho?",
    "Quais oportunidades e desafios podem ser identificados para empresas que desejam investir em Dados e IA?",
]:
    bullet(doc, q)
doc.add_paragraph().paragraph_format.space_after = Pt(4)

# ===========================================================================
# 2. METODOLOGIA
# ===========================================================================
heading1(doc, 2, "METODOLOGIA")

body(
    doc,
    "A metodologia foi estruturada em cinco etapas principais: ingestão e "
    "organização dos dados brutos, catalogação e harmonização de schemas "
    "diferentes entre edições, agregação em tabelas analíticas por tema de "
    "negócio, consulta analítica e, por fim, geração dos gráficos e "
    "indicadores apresentados neste relatório."
)

heading2(doc, "2.1", "Fonte dos dados")
body(
    doc,
    "A base de dados utilizada é composta pelas respostas de 13.057 "
    "profissionais de Dados e Tecnologia no Brasil, coletadas pela pesquisa "
    "State of Data Brasil em três edições (2023-2024, 2024-2025 e "
    "2025-2026), disponibilizadas publicamente pela comunidade Data Hackers "
    "no Kaggle (DATA HACKERS, 2026). Os dados contemplam informações demográficas, cargo atual, "
    "senioridade, faixa salarial, região, modelo de trabalho, tecnologias "
    "utilizadas e uso de Inteligência Artificial."
)

heading2(doc, "2.2", "Arquitetura da solução na AWS")
body(
    doc,
    "Para processar e disponibilizar os dados de forma escalável e "
    "reprodutível, foi construído um pipeline de dados completo na AWS, "
    "seguindo a arquitetura em camadas conhecida como “medallion” "
    "(Bronze, Silver e Gold). O diagrama a seguir, desenhado em conjunto com "
    "a equipe, ilustra o fluxo completo: os três arquivos brutos da pesquisa "
    "são ingeridos no Amazon S3, processados por notebooks do AWS Glue "
    "(AMAZON WEB SERVICES, 2026b) (Apache Spark) em cada camada, catalogados "
    "automaticamente no AWS Glue Data Catalog, consultados via Amazon Athena "
    "(AMAZON WEB SERVICES, 2026a), e finalmente consolidados "
    "neste relatório executivo."
)
add_figure(
    doc,
    DIAGRAMS / "arquitetura_solucao.png",
    1,
    "Arquitetura da solução de dados na AWS (Bronze / Silver / Gold)",
    width_cm=16.0,
    source="Elaborado pela equipe, via app.diagrams.net.",
)
body(
    doc,
    "Na camada Bronze, os três arquivos CSV originais são lidos diretamente "
    "pelo caminho exato no S3 e gravados em formato Parquet, um por edição "
    "da pesquisa, preservando fielmente os dados como vieram da fonte. Na "
    "camada Silver, as três edições (que usam schemas de coluna diferentes "
    "entre si) são harmonizadas num formato único, com aproximadamente 28 "
    "campos-chave padronizados (demografia, cargo, senioridade, salário, "
    "região, modelo de trabalho, tecnologias e uso de IA). Na camada Gold, "
    "os dados harmonizados são agregados em sete tabelas especializadas, uma "
    "para cada pergunta de negócio deste relatório. Todas as etapas rodaram "
    "de fato no ambiente AWS Academy Lab do grupo, catalogando as tabelas "
    "automaticamente a partir do próprio código do notebook (sem o uso de "
    "um Glue Crawler, já que essa catalogação automática via código atende "
    "integralmente à exigência de “catalogação das tabelas com o Glue "
    "Jobs”)."
)

heading2(doc, "2.3", "Preparação e tratamento dos dados")
body(
    doc,
    "Nesta etapa, os dados foram tratados para garantir consistência e "
    "comparabilidade entre as três edições da pesquisa. As ações incluíram: "
    "padronização de valores nulos e em branco; harmonização dos nomes e "
    "índices de coluna entre edições com schemas diferentes; conversão de "
    "faixas salariais categóricas em um valor numérico médio estimado; e "
    "remoção de registros duplicados por identificador de respondente. Como "
    "nem toda edição da pesquisa inclui todas as perguntas (a edição "
    "2023-2024, por exemplo, não contempla perguntas sobre Inteligência "
    "Artificial Generativa), os campos ausentes foram tratados como nulos "
    "explícitos, em vez de preenchidos artificialmente, o que explica "
    "algumas diferenças de cobertura temporal citadas ao longo da Seção 4."
)

heading2(doc, "2.4", "Definição de variáveis de análise")
body(
    doc,
    "As variáveis de análise foram agrupadas em cinco dimensões principais: "
    "Perfil Demográfico e de Mercado (cargo, região, senioridade, gênero), "
    "Remuneração (faixa salarial estimada), Tecnologias (linguagens, bancos "
    "de dados, provedores de nuvem e ferramentas de BI adotados), Adoção de "
    "Inteligência Artificial (uso individual, uso pago, uso para geração de "
    "código, e prioridade estratégica na visão de gestores) e Modelo de "
    "Trabalho (presencial, híbrido ou remoto)."
)

heading2(doc, "2.5", "Ferramentas usadas")
body(doc, "A análise foi realizada com apoio das seguintes ferramentas:")
for t in [
    "Amazon S3, AWS Glue (Apache Spark / PySpark) e AWS Glue Data Catalog, para ingestão, transformação e catalogação dos dados;",
    "Amazon Athena, para consultas analíticas em SQL padrão diretamente sobre as tabelas catalogadas;",
    "Python (pandas, matplotlib), para geração dos gráficos a partir dos resultados das consultas;",
    "Draw.io, para o desenho da arquitetura da solução.",
]:
    bullet(doc, t)
doc.add_paragraph().paragraph_format.space_after = Pt(4)

heading2(doc, "2.6", "Estratégia de consulta e catalogação")
body(
    doc,
    "Cada uma das sete tabelas da camada Gold corresponde a uma pergunta de "
    "negócio específica (perfil de mercado, remuneração, diversidade de "
    "gênero, tecnologias, adoção de IA, prioridade de IA nas empresas e "
    "modelo de trabalho). Para cada uma, foi escrito um script SQL "
    "independente, executado diretamente no Amazon Athena contra essas "
    "tabelas. O conjunto completo dos sete scripts acompanha este relatório "
    "como parte da Entrega 3 (notebooks e scripts)."
)

# ===========================================================================
# 3. DADOS GERAIS DO LEVANTAMENTO
# ===========================================================================
heading1(doc, 3, "DADOS GERAIS DO LEVANTAMENTO")
body(
    doc,
    "A seguir, são apresentados os principais indicadores gerais do "
    "levantamento, consolidados a partir das três edições da pesquisa já "
    "processadas pelo pipeline descrito na Seção 2."
)
caption(doc, "Indicadores gerais do levantamento", bold_prefix="Tabela 1: ", space_after=8)
kpi_table(doc, [
    ("Respondentes únicos (total)", "13.057"),
    ("Edições da pesquisa", "3 (2023-2024, 2024-2025, 2025-2026)"),
    ("Respondentes por edição", "4.270 / 5.293 / 3.494"),
    ("% de mulheres na base", "23,9%"),
    ("Cargo mais comum", "Analista de Dados (2.145 respondentes)"),
    ("Região com mais profissionais", "Sudeste (61%)"),
    ("Cargo mais bem remunerado (≥ 50 respondentes)", "Eng. de ML/AI Engineer (R$ 16.382/mês)"),
    ("Linguagem de programação líder (2025)", "Python (55,2% de adoção)"),
    ("Adoção individual de IA Generativa (2025)", "97,9%"),
    ("Empresas com IA como prioridade executiva (2025)", "23,8%"),
])

# ===========================================================================
# 4. ANÁLISE DETALHADA POR PERGUNTA DE NEGÓCIO
# ===========================================================================
heading1(doc, 4, "ANÁLISE DETALHADA POR PERGUNTA DE NEGÓCIO")
body(
    doc,
    "Esta seção apresenta a análise detalhada de cada uma das sete perguntas "
    "de negócio que orientam este relatório, com os gráficos e indicadores "
    "extraídos diretamente das tabelas Gold via Amazon Athena."
)

heading2(doc, "4.1", "Como está estruturado o mercado brasileiro de Dados?")
body(
    doc,
    "O mercado brasileiro de Dados é dominado por cargos de análise e "
    "engenharia: Analista de Dados é o cargo mais comum (2.145 "
    "respondentes), seguido por Cientista de Dados (1.666) e Engenheiro de "
    "Dados/Arquiteto (1.174). Juntos, os dez cargos mais comuns concentram a "
    "grande maioria da base."
)
add_figure(doc, CHARTS / "01_perfil_cargos.png", 2, "Os 10 cargos mais comuns no mercado de Dados (BR)", width_cm=15.5)
body(
    doc,
    "A distribuição geográfica revela uma concentração relevante: entre os "
    "respondentes que informaram sua região, 61% estão no Sudeste, seguidos "
    "a distância por Sul (18%) e Nordeste (11%). Essa concentração é um dado "
    "estrutural importante para qualquer estratégia de contratação que "
    "dependa de presença regional."
)
add_figure(doc, CHARTS / "02_perfil_regiao.png", 3, "Distribuição geográfica dos profissionais de Dados", width_cm=14.5)
body(
    doc,
    "Em termos de senioridade, o mercado é relativamente maduro: os níveis "
    "Pleno (3.227) e Sênior (3.175) somados superam o nível Júnior (2.587), "
    "e o nível Especialista/Staff+ ainda é raro (349 respondentes), um "
    "indício de que o topo da carreira técnica em Dados, no Brasil, ainda "
    "está em formação."
)
add_figure(doc, CHARTS / "03_perfil_senioridade.png", 4, "Pirâmide de senioridade no mercado de Dados", width_cm=14.0)

heading2(doc, "4.2", "Quais perfis profissionais são mais valorizados pelo mercado?")
body(
    doc,
    "Entre os cargos com volume relevante de respostas (50 ou mais "
    "respondentes), os perfis técnicos mais avançados, como Engenharia de "
    "Machine Learning, Engenharia de Dados e Product Management técnico, "
    "são consistentemente os mais bem remunerados. O Engenheiro de "
    "Machine Learning/AI Engineer lidera com média de R$ 16.382 por mês, "
    "seguido pelo Engenheiro de Machine Learning (R$ 14.414) e pelo "
    "Engenheiro de Dados/Data Architect (R$ 14.294). Por outro lado, cargos "
    "de análise mais tradicionais, como Analista de Dados e Analista de BI, "
    "aparecem com remuneração média sensivelmente menor, um sinal claro de "
    "onde o mercado mais sente a falta de certas competências."
)
add_figure(doc, CHARTS / "04_salario_por_cargo.png", 5, "Remuneração média por cargo (cargos com ≥ 50 respondentes)", width_cm=15.5)

heading2(doc, "4.3", "Qual é o cenário de diversidade de gênero nas carreiras de Dados?")
body(
    doc,
    "A diversidade de gênero no mercado de Dados brasileiro segue um padrão "
    "preocupante e consistente com o observado em outras áreas de "
    "tecnologia: apenas 23,9% dos respondentes se identificam como "
    "mulheres. Pior, essa participação não é estável ao longo da carreira: "
    "ela cai de 28,2% no nível Júnior para 22,3% no Pleno, 20,7% no Sênior e "
    "20,1% no Especialista/Staff+ (dados da edição mais recente), um "
    "cenário em que mais mulheres do que homens deixam a carreira técnica "
    "ou são promovidas com menos frequência."
)
add_figure(doc, CHARTS / "05_diversidade_genero_senioridade.png", 6, "Participação feminina cai conforme sobe a senioridade", width_cm=14.0)
body(
    doc,
    "Esse padrão se soma a uma diferença salarial relevante: no nível "
    "Sênior, mulheres recebem em média R$ 12.012, contra R$ 14.097 dos "
    "homens, uma diferença de aproximadamente 15%. No nível "
    "Especialista/Staff+, a diferença é semelhante (R$ 17.543 contra R$ "
    "20.618, cerca de 15%). Já nos níveis iniciais (Júnior e Pleno), a "
    "diferença é bem menor (entre 2% e 5%), sugerindo que a desigualdade se "
    "acumula ao longo da carreira, em "
    "vez de já estar presente na entrada do mercado."
)
add_figure(doc, CHARTS / "06_gap_salarial_genero.png", 7, "Diferença salarial entre gêneros, por senioridade", width_cm=14.5)

heading2(doc, "4.4", "Quais tecnologias apresentam maior adoção entre os profissionais?")
body(
    doc,
    "Na edição mais recente da pesquisa, Python (55,2%) e SQL (50,5%) são as "
    "linguagens de programação dominantes, seguidas a grande distância por R "
    "(9,4%). Entre bancos de dados, PostgreSQL lidera (22,1%), seguido por "
    "SQL Server (20,1%) e Databricks (19,7%). No provimento de nuvem, a AWS "
    "é a líder isolada (28,9%), à frente de Azure (20,9%) e Google Cloud "
    "(18,5%). Entre ferramentas de Business Intelligence, o Microsoft Power "
    "BI domina com folga (35,5%), mais que o dobro do segundo colocado "
    "(Looker, 13,6%)."
)
add_figure(doc, CHARTS / "07_tecnologias_adocao_painel.png", 8, "Tecnologias mais adotadas pelos profissionais de Dados (edição 2025-2026)", width_cm=16.0)
body(
    doc,
    "Um dos achados mais relevantes deste relatório é a inversão de "
    "liderança entre as duas linguagens mais usadas: Python saiu de 48,9% de "
    "adoção em 2023 para 55,2% em 2025, enquanto o SQL caiu de 55,4% para "
    "50,5% no mesmo período (depois de um pico de 59,6% em 2024). O "
    "cruzamento entre as duas curvas acontece exatamente entre as edições de "
    "2024 e 2025, um sinal direto de para onde a demanda de mercado está "
    "migrando, e um indicativo claro de prioridade para programas de "
    "capacitação técnica."
)
add_figure(doc, CHARTS / "08_evolucao_linguagens.png", 9, "Evolução das linguagens mais usadas (2023-2025)", width_cm=14.5)

heading2(doc, "4.5", "Qual é o índice de adoção de Inteligência Artificial e seu impacto?")
body(
    doc,
    "A adoção individual de Inteligência Artificial Generativa no dia a dia "
    "de trabalho avançou de forma expressiva: de 80,3% dos profissionais em "
    "2024 para 97,9% em 2025, praticamente universal (a edição 2023-2024 "
    "não incluía essa pergunta na pesquisa, por isso a comparação começa em "
    "2024). O uso pago de ferramentas de IA também cresceu, de 9,3% para "
    "39,0% dos profissionais, e o uso de IA especificamente para geração de "
    "código subiu de 8,4% para 18,0%."
)
add_figure(doc, CHARTS / "09_adocao_ia_e_prioridade.png", 10, "Adoção de IA Generativa e prioridade nas empresas", width_cm=16.0)
body(
    doc,
    "Entretanto, essa adoção individual quase universal não se traduz, na "
    "mesma proporção, em prioridade estratégica formal dentro das empresas: "
    "apenas 23,8% dos gestores entrevistados classificam a IA Generativa "
    "como “prioridade alta (foco executivo)”; a maior parte (36,8%) trata o "
    "tema como “prioridade de médio prazo”, e 11,3% afirmam que a IA "
    "Generativa “não é prioridade” na empresa. Esse descompasso de "
    "quase 75 pontos percentuais entre uso individual (97,9%) e priorização "
    "corporativa (23,8%) representa, ao mesmo tempo, um risco de governança "
    "e uma oportunidade estratégica clara para quem formalizar uma "
    "estratégia de IA primeiro."
)
add_figure(doc, CHARTS / "10_gap_individual_vs_empresa_ia.png", 11, "O uso individual de IA corre à frente da estratégia corporativa", width_cm=12.0)

heading2(doc, "4.6", "Existem diferenças relevantes entre regiões, senioridades ou modelos de trabalho?")
body(
    doc,
    "Sim, e de forma expressiva. Regionalmente, o Sudeste segue pagando os "
    "maiores salários médios (R$ 11.463), seguido por Centro-Oeste (R$ "
    "10.710) e Sul (R$ 10.047); o Nordeste tem a menor média (R$ 8.459), "
    "uma diferença de 36% entre as duas pontas. Já em relação ao modelo de "
    "trabalho, o padrão observado desafia a intuição de que o trabalho "
    "presencial seria mais valorizado: o modelo híbrido flexível (em que o "
    "profissional escolhe quando ir ao escritório) tem a maior remuneração "
    "média (R$ 12.546), seguido pelo modelo 100% remoto (R$ 11.833); o "
    "modelo 100% presencial tem a menor média de todos (R$ 7.361), quase "
    "70% menor que o híbrido flexível."
)
add_figure(doc, CHARTS / "11_salario_regiao_modelo_trabalho.png", 12, "Salário médio por região e por modelo de trabalho", width_cm=16.0)

heading2(doc, "4.7", "Quais oportunidades e desafios podem ser identificados?")
body(
    doc,
    "A leitura conjunta dos seis pontos anteriores aponta para quatro "
    "oportunidades/desafios centrais, detalhados como recomendações na Seção "
    "6: (1) a janela de oportunidade para formalizar uma estratégia de IA, "
    "enquanto a maioria das empresas ainda não o fez; (2) o desafio e a "
    "oportunidade de reter talento feminino, hoje perdido ao longo da "
    "carreira; (3) a oportunidade de acessar talento qualificado fora do "
    "Sudeste via trabalho remoto, a um custo salarial menor; e (4) a "
    "necessidade de direcionar capacitação técnica para Python e para "
    "competências de Engenharia de Dados e Machine Learning, que concentram "
    "a maior remuneração do mercado."
)

# ===========================================================================
# 5. DIAGNÓSTICO
# ===========================================================================
heading1(doc, 5, "DIAGNÓSTICO")
body(
    doc,
    "Os resultados apresentados na Seção 4 mostram um mercado de Dados "
    "brasileiro em maturação acelerada, mas com desequilíbrios estruturais "
    "claros. Em conjunto, os indicadores de tecnologia (Seção 4.4) e de "
    "Inteligência Artificial (Seção 4.5) mostram uma velocidade de mudança "
    "muito alta. A inversão Python/SQL e o salto de adoção de IA "
    "aconteceram em menos de dois anos, o que significa que uma estratégia "
    "de capacitação desenhada hoje com base em dados de dois ou três anos "
    "atrás já estaria defasada."
)
body(
    doc,
    "Ao mesmo tempo, os indicadores de diversidade de gênero (Seção 4.3) e "
    "das diferenças regionais e de modelo de trabalho (Seção 4.6) mostram "
    "desigualdades que persistem ao longo do tempo e que não desaparecem "
    "naturalmente com a evolução do mercado, exigindo medidas específicas "
    "para mudar esse cenário. A diferença salarial de gênero no nível "
    "Sênior (15%) e a concentração de 61% dos profissionais no Sudeste são padrões "
    "consistentes nas três edições da pesquisa, não uma anomalia pontual."
)
body(
    doc,
    "Por fim, a diferença entre uso individual de IA Generativa (97,9%) e "
    "prioridade executiva (23,8%) é, possivelmente, o achado mais "
    "acionável deste relatório: diferente dos desequilíbrios estruturais de "
    "gênero e região, que exigem políticas de longo prazo, formalizar uma "
    "estratégia de IA é uma decisão que uma Instituição Financeira pode "
    "tomar imediatamente, com efeito relativamente rápido."
)
body(
    doc,
    "Vale destacar uma limitação desta análise: como foram reunidas três "
    "edições da pesquisa com questionários diferentes, algumas informações, "
    "principalmente sobre região, senioridade e uso de IA Generativa, não "
    "estão disponíveis em todas as edições, ou aparecem apenas "
    "parcialmente. A edição de 2023 a 2024, por exemplo, não incluía "
    "perguntas sobre IA Generativa. Os indicadores de região e senioridade "
    "apresentados abrangem cerca de 72% da base total (9.338 dos 13.057 "
    "respondentes), já que os demais não informaram esses dados. Portanto, "
    "não se trata de um erro no processamento dos dados, e isso não "
    "compromete as principais tendências identificadas na análise.",
    italic=True,
)

# ===========================================================================
# 6. RECOMENDAÇÕES ESTRATÉGICAS
# ===========================================================================
heading1(doc, 6, "RECOMENDAÇÕES ESTRATÉGICAS")
body(
    doc,
    "Com base nos resultados obtidos nas análises de estrutura de mercado, "
    "remuneração, diversidade, tecnologia, adoção de IA e diferenças "
    "regionais, são propostas as seguintes ações estratégicas para a "
    "Instituição Financeira."
)

recs = [
    ("Formalize uma estratégia corporativa de IA Generativa",
     "98% dos profissionais já usam IA Generativa no dia a dia, mas apenas "
     "24% das empresas tratam isso como prioridade executiva, uma janela "
     "de oportunidade clara. É importante criar regras claras para o uso "
     "de IA nas empresas, definindo quais ferramentas podem ser usadas e "
     "oferecendo treinamento aos funcionários. Assim, é possível evitar "
     "riscos à segurança das informações e aproveitar melhor as "
     "oportunidades de aumentar a produtividade.",
     "Redução de risco de uso não-governado de IA, ganho de produtividade "
     "e vantagem de ser uma das primeiras empresas do setor financeiro a "
     "formalizar a estratégia."),
    ("Invista em equidade de gênero como vantagem de retenção",
     "A participação feminina cai de 28% (Júnior) para 20% (Especialista), "
     "com diferença salarial de 15% no nível Sênior. Recomenda-se revisar "
     "políticas de equidade salarial por nível de senioridade, criar "
     "programas de mentoria e desenvolvimento de liderança para mulheres "
     "em Dados, e monitorar a taxa de promoção por gênero como um "
     "indicador formal de RH.",
     "Mais opções de profissionais para contratar, menor risco de perder "
     "mulheres que estão no meio da carreira, e fortalecimento da imagem "
     "da empresa como um bom lugar para trabalhar."),
    ("Adote o trabalho remoto para acessar talento fora do Sudeste",
     "61% do talento e os maiores salários estão concentrados no Sudeste, "
     "que paga 36% a mais que o Nordeste. Recomenda-se estruturar vagas "
     "remotas ou híbridas flexíveis, que, segundo os próprios dados da "
     "pesquisa, já pagam mais que o modelo presencial, como estratégia "
     "deliberada de acesso a profissionais qualificados em outras regiões, "
     "a um custo salarial regional menor.",
     "Mais profissionais disponíveis para contratar, redução dos custos "
     "de contratação em comparação com vagas limitadas ao Sudeste, e "
     "maior rapidez para preencher vagas técnicas."),
    ("Direcione capacitação para Python e Engenharia de Dados/ML",
     "Python já ultrapassou o SQL como linguagem mais usada, e os cargos de "
     "Engenharia de Dados e Machine Learning/AI Engineering são os mais "
     "bem remunerados do mercado. A recomendação é focar o orçamento de "
     "treinamentos internos e os critérios de contratação nas competências "
     "que o mercado mais valoriza, em vez de investir em capacitações "
     "genéricas na área de Dados.",
     "Alinhar os investimentos em treinamento às competências que estão "
     "em falta no mercado, evitando gastar recursos na formação de "
     "profissionais em tecnologias cuja demanda está diminuindo."),
]
for i, (title, text, impact) in enumerate(recs, start=1):
    heading2(doc, f"6.{i}", title)
    body(doc, text)
    body(doc, impact, lead_bold="Impacto esperado: ")

# ===========================================================================
# 7. CONCLUSÃO
# ===========================================================================
heading1(doc, 7, "CONCLUSÃO")
body(
    doc,
    "A análise da pesquisa State of Data Brasil, realizada por meio de um "
    "pipeline de dados completo na AWS, ajuda a entender melhor o cenário "
    "do mercado brasileiro de profissionais de Dados. Os resultados "
    "mostram um mercado concentrado no Sudeste, com salários mais altos "
    "para quem domina competências técnicas avançadas, como Engenharia de "
    "Dados e Machine Learning, e uma diversidade de gênero que ainda está "
    "desequilibrada. Também mostram que o uso de Inteligência Artificial "
    "Generativa cresceu rapidamente e, em menos de dois anos, passou de "
    "novidade para algo comum entre os profissionais, enquanto as empresas "
    "ainda avançam mais lentamente na criação de estratégias formais para "
    "seu uso."
)
body(
    doc,
    "Para uma Instituição Financeira que deseja expandir sua área de Dados, "
    "Analytics e IA, esses achados sugerem que a vantagem competitiva não "
    "está apenas em contratar mais profissionais, mas em contratar e "
    "desenvolver nas competências certas (Python, Engenharia de Dados, "
    "Machine Learning), acessar talento além do eixo Sudeste via modelos "
    "de trabalho flexíveis, corrigir deliberadamente desequilíbrios de "
    "gênero que o mercado não corrige sozinho, e formalizar (antes da "
    "concorrência) uma estratégia de Inteligência Artificial que hoje "
    "ainda é exceção, não regra."
)
body(
    doc,
    "Do ponto de vista técnico, este relatório também mostra que é "
    "possível criar um processo completo e replicável de tratamento e "
    "análise de dados usando ferramentas de nuvem bastante acessíveis, "
    "como Amazon S3, Glue e Athena. Esse processo vai desde a coleta de "
    "dados brutos de diferentes formatos até a geração de indicadores para "
    "apoiar decisões, tudo dentro de um prazo e custo viáveis para um "
    "projeto piloto. Isso reforça que as recomendações apresentadas aqui "
    "podem ser colocadas em prática."
)

# ===========================================================================
# 8. REFERÊNCIAS
# ===========================================================================
heading1(doc, 8, "REFERÊNCIAS")

refs = [
    ("AMAZON WEB SERVICES.", " Amazon Athena User Guide.", " 2026a. Disponível em: https://docs.aws.amazon.com/athena/latest/ug/. Acesso em: 19 out. 2026."),
    ("AMAZON WEB SERVICES.", " AWS Glue Developer Guide.", " 2026b. Disponível em: https://docs.aws.amazon.com/glue/latest/dg/. Acesso em: 18 out. 2026."),
    ("DATA HACKERS.", " State of Data Brazil Dataset.", " 2026. Disponível em: https://www.kaggle.com/datasets/datahackers/state-of-data-brazil. Acesso em: 19 out. 2026."),
]
# Referencias conforme ABNT NBR 6023: alinhamento a esquerda (sem recuo),
# espacamento simples dentro de cada referencia, espaco maior entre elas.
for lead, mid, rest in refs:
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.space_after = Pt(12)
    pf.line_spacing = 1.0
    r = p.add_run(lead)
    r.font.name = FONT_NAME
    r.font.size = BODY_SIZE
    r = p.add_run(mid)
    r.italic = True
    r.font.name = FONT_NAME
    r.font.size = BODY_SIZE
    r = p.add_run(rest)
    r.font.name = FONT_NAME
    r.font.size = BODY_SIZE

# ===========================================================================
# ANEXOS
# ===========================================================================
heading1(doc, None, "ANEXOS")
body(doc, "Repositório do projeto (notebooks, scripts SQL e código-fonte deste relatório): https://github.com/Gscalambrini/state-of-data-brasil-aws-pipeline.", space_after=8)
body(doc, "Diagrama de arquitetura editável (Draw.io): diagrams/arquitetura_solucao.drawio.", space_after=8)
body(doc, "Scripts de consulta analítica (Amazon Athena): notebooks/05_analytics_athena/*.sql.", space_after=8)

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
doc.save(str(OUT_PATH))
print(f"Relatório salvo em {OUT_PATH}")
