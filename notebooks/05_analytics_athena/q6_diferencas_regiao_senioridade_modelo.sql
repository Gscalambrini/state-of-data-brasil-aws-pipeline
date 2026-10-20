-- =============================================================================
-- Pergunta de negócio 6: Existem diferenças relevantes entre regiões,
-- senioridades ou modelos de trabalho?
-- Fontes: db_techchallenge_gt_fiap.gold_remuneracao, gold_modelo_trabalho
-- =============================================================================

-- 6a. Salário médio por região
SELECT
    regiao,
    ROUND(SUM(salario_medio * n_respondentes) / SUM(n_respondentes), 0) AS salario_medio_estimado,
    SUM(n_respondentes) AS n_respondentes
FROM db_techchallenge_gt_fiap.gold_remuneracao
GROUP BY regiao
ORDER BY salario_medio_estimado DESC;

-- 6b. Salário médio por modelo de trabalho
SELECT
    modelo_trabalho_atual,
    ROUND(SUM(salario_medio * n_respondentes) / SUM(n_respondentes), 0) AS salario_medio_estimado,
    SUM(n_respondentes) AS n_respondentes
FROM db_techchallenge_gt_fiap.gold_remuneracao
GROUP BY modelo_trabalho_atual
ORDER BY salario_medio_estimado DESC;

-- 6c. Distribuição do modelo de trabalho por região (% dentro da região)
SELECT
    regiao,
    modelo_trabalho_atual,
    ROUND(100.0 * n_respondentes / SUM(n_respondentes) OVER (PARTITION BY regiao), 1) AS pct_dentro_da_regiao
FROM db_techchallenge_gt_fiap.gold_modelo_trabalho
ORDER BY regiao, pct_dentro_da_regiao DESC;
