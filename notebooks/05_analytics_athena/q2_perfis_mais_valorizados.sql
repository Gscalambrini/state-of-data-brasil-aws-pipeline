-- =============================================================================
-- Pergunta de negócio 2: Quais perfis profissionais são mais valorizados pelo mercado?
-- Fonte: db_techchallenge_gt_fiap.gold_remuneracao
-- "Valorizado" = maior remuneração média, considerando apenas cargos com volume
-- relevante de respostas (evita ruído de cargos muito raros).
-- =============================================================================

WITH cargo_stats AS (
    SELECT
        cargo_atual,
        SUM(salario_medio * n_respondentes) / SUM(n_respondentes) AS salario_medio_ponderado,
        SUM(n_respondentes) AS n_respondentes
    FROM db_techchallenge_gt_fiap.gold_remuneracao
    GROUP BY cargo_atual
)
SELECT
    cargo_atual,
    ROUND(salario_medio_ponderado, 0) AS salario_medio_estimado,
    n_respondentes
FROM cargo_stats
WHERE n_respondentes >= 50
ORDER BY salario_medio_ponderado DESC
LIMIT 15;

-- Evolução da remuneração por senioridade ao longo das 3 edições
SELECT
    ano_pesquisa,
    nivel_senioridade,
    ROUND(SUM(salario_medio * n_respondentes) / SUM(n_respondentes), 0) AS salario_medio_estimado
FROM db_techchallenge_gt_fiap.gold_remuneracao
GROUP BY ano_pesquisa, nivel_senioridade
ORDER BY ano_pesquisa,
    CASE nivel_senioridade
        WHEN 'Júnior' THEN 1 WHEN 'Pleno' THEN 2 WHEN 'Sênior' THEN 3 ELSE 4
    END;
