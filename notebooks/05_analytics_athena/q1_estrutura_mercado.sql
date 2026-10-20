-- =============================================================================
-- Pergunta de negócio 1: Como está estruturado o mercado brasileiro de Dados?
-- Fonte: db_techchallenge_gt_fiap.gold_perfil_mercado
-- (nome real do database do time, confirmado no Glue Data Catalog).
-- =============================================================================

-- 1a. Top 10 cargos mais comuns (todas as edições)
SELECT
    cargo_atual,
    SUM(n_respondentes) AS total_respondentes
FROM db_techchallenge_gt_fiap.gold_perfil_mercado
GROUP BY cargo_atual
ORDER BY total_respondentes DESC
LIMIT 10;

-- 1b. Distribuição por região (% do total)
SELECT
    regiao,
    SUM(n_respondentes) AS total_respondentes,
    ROUND(100.0 * SUM(n_respondentes) / SUM(SUM(n_respondentes)) OVER (), 1) AS pct_do_total
FROM db_techchallenge_gt_fiap.gold_perfil_mercado
GROUP BY regiao
ORDER BY total_respondentes DESC;

-- 1c. Pirâmide de senioridade por edição da pesquisa
SELECT
    ano_pesquisa,
    nivel_senioridade,
    SUM(n_respondentes) AS total_respondentes
FROM db_techchallenge_gt_fiap.gold_perfil_mercado
GROUP BY ano_pesquisa, nivel_senioridade
ORDER BY ano_pesquisa, total_respondentes DESC;
