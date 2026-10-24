-- =============================================================================
-- Pergunta de negócio 4: Quais tecnologias apresentam maior adoção entre os profissionais?
-- Fonte: db_techchallenge_gt_fiap.gold_tecnologias_adocao
-- =============================================================================

-- 4a. Top 5 tecnologias por categoria, na edição mais recente
WITH ranked AS (
    SELECT
        categoria_tecnologia,
        tecnologia,
        pct_adocao,
        ROW_NUMBER() OVER (PARTITION BY categoria_tecnologia ORDER BY pct_adocao DESC) AS rk
    FROM db_techchallenge_gt_fiap.gold_tecnologias_adocao
    WHERE ano_pesquisa = (SELECT MAX(ano_pesquisa) FROM db_techchallenge_gt_fiap.gold_tecnologias_adocao)
)
SELECT categoria_tecnologia, tecnologia, pct_adocao
FROM ranked
WHERE rk <= 5
ORDER BY categoria_tecnologia, rk;

-- 4b. Evolução de adoção das linguagens mais usadas, ano a ano
-- Observação: os valores de "tecnologia" na Gold são sempre minúsculos (saem
-- da sanitização de nomes de coluna feita na Bronze), por isso o filtro usa
-- 'python'/'sql'/'r' em vez de 'Python'/'SQL'/'R': a versão com maiúsculas
-- roda sem erro mas retorna 0 linhas.
SELECT
    ano_pesquisa,
    tecnologia,
    pct_adocao
FROM db_techchallenge_gt_fiap.gold_tecnologias_adocao
WHERE categoria_tecnologia = 'linguagem'
  AND tecnologia IN ('python', 'sql', 'r')
ORDER BY tecnologia, ano_pesquisa;
