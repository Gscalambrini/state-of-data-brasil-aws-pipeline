-- =============================================================================
-- Pergunta de negócio 3: Qual é o cenário de diversidade de gênero nas carreiras de dados?
-- Fontes: db_techchallenge_gt_fiap.gold_diversidade_genero, gold_remuneracao
-- =============================================================================

-- 3a. Participação por gênero dentro de cada nível de senioridade (edição mais recente)
SELECT
    nivel_senioridade,
    genero,
    pct_dentro_do_nivel
FROM db_techchallenge_gt_fiap.gold_diversidade_genero
WHERE ano_pesquisa = (SELECT MAX(ano_pesquisa) FROM db_techchallenge_gt_fiap.gold_diversidade_genero)
  AND genero IN ('Masculino', 'Feminino')
ORDER BY
    CASE nivel_senioridade
        WHEN 'Júnior' THEN 1 WHEN 'Pleno' THEN 2 WHEN 'Sênior' THEN 3 ELSE 4
    END,
    genero;

-- 3b. Gap salarial entre homens e mulheres, por nível de senioridade
WITH sal_genero AS (
    SELECT
        nivel_senioridade,
        genero,
        SUM(salario_medio * n_respondentes) / SUM(n_respondentes) AS salario_medio_estimado
    FROM db_techchallenge_gt_fiap.gold_remuneracao
    WHERE genero IN ('Masculino', 'Feminino')
    GROUP BY nivel_senioridade, genero
)
SELECT
    m.nivel_senioridade,
    ROUND(m.salario_medio_estimado, 0) AS salario_masculino,
    ROUND(f.salario_medio_estimado, 0) AS salario_feminino,
    ROUND(100.0 * (1 - f.salario_medio_estimado / m.salario_medio_estimado), 1) AS gap_percentual
FROM sal_genero m
JOIN sal_genero f ON m.nivel_senioridade = f.nivel_senioridade
WHERE m.genero = 'Masculino' AND f.genero = 'Feminino';
