-- =============================================================================
-- Pergunta de negócio 5: Qual é o índice de adoção de Inteligência Artificial
-- e seu impacto?
-- Fontes: db_techchallenge_gt_fiap.gold_adocao_ia, gold_prioridade_ia_empresa
-- =============================================================================

-- 5a. Evolução da adoção individual de IA Generativa
SELECT
    ano_pesquisa,
    pct_usa_ia_generativa,
    pct_paga_por_ia,
    pct_usa_ia_para_codigo
FROM db_techchallenge_gt_fiap.gold_adocao_ia
ORDER BY ano_pesquisa;

-- 5b. Prioridade de IA Generativa nas empresas, na visão dos gestores (edição mais recente)
SELECT
    prioridade_ia_empresa,
    pct_gestores
FROM db_techchallenge_gt_fiap.gold_prioridade_ia_empresa
WHERE ano_pesquisa = (SELECT MAX(ano_pesquisa) FROM db_techchallenge_gt_fiap.gold_prioridade_ia_empresa)
ORDER BY pct_gestores DESC;

-- 5c. Gap entre uso individual (todos os respondentes) e prioridade executiva (gestores)
SELECT
    i.ano_pesquisa,
    i.pct_usa_ia_generativa AS pct_uso_individual,
    p.pct_gestores AS pct_empresas_prioridade_alta
FROM db_techchallenge_gt_fiap.gold_adocao_ia i
JOIN db_techchallenge_gt_fiap.gold_prioridade_ia_empresa p
    ON i.ano_pesquisa = p.ano_pesquisa
    AND p.prioridade_ia_empresa = 'Prioridade alta (foco executivo)'
ORDER BY i.ano_pesquisa;
