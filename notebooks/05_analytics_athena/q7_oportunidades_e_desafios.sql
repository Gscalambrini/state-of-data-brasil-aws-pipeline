-- =============================================================================
-- Pergunta de negócio 7: Quais oportunidades e desafios podem ser identificados
-- para empresas que desejam investir em Dados e Inteligência Artificial?
--
-- Esta pergunta é de síntese (não tem uma única tabela Gold dedicada): a query
-- abaixo reúne, lado a lado, os 3 indicadores quantitativos mais fortes que
-- embasam as recomendações estratégicas do material executivo:
--   1) o gap entre uso individual de IA e prioridade executiva (oportunidade de
--      governança/estratégia formal de IA);
--   2) o gap salarial de gênero no topo da pirâmide (oportunidade de ampliar o
--      pool de talentos / risco de retenção);
--   3. a concentração regional de talentos e salários (oportunidade de acessar
--      talento fora do Sudeste via trabalho remoto).
-- =============================================================================

-- Indicador 1: gap estratégia de IA (uso individual vs prioridade executiva), edição mais recente
SELECT
    'Gap de estratégia de IA' AS indicador,
    i.pct_usa_ia_generativa AS metrica_1_uso_individual_pct,
    p.pct_gestores AS metrica_2_empresa_prioridade_alta_pct,
    ROUND(i.pct_usa_ia_generativa - p.pct_gestores, 1) AS gap_pontos_percentuais
FROM db_techchallenge_gt_fiap.gold_adocao_ia i
JOIN db_techchallenge_gt_fiap.gold_prioridade_ia_empresa p
    ON i.ano_pesquisa = p.ano_pesquisa
    AND p.prioridade_ia_empresa = 'Prioridade alta (foco executivo)'
WHERE i.ano_pesquisa = (SELECT MAX(ano_pesquisa) FROM db_techchallenge_gt_fiap.gold_adocao_ia);

-- Indicador 2: gap salarial de gênero no nível Sênior+, edição mais recente
WITH sal_genero AS (
    SELECT nivel_senioridade, genero,
           SUM(salario_medio * n_respondentes) / SUM(n_respondentes) AS salario_medio_estimado
    FROM db_techchallenge_gt_fiap.gold_remuneracao
    WHERE genero IN ('Masculino', 'Feminino') AND nivel_senioridade IN ('Sênior', 'Especialista/Staff+')
    GROUP BY nivel_senioridade, genero
)
SELECT
    'Gap salarial de gênero (sênior+)' AS indicador,
    nivel_senioridade,
    ROUND(100.0 * (1 - MIN(CASE WHEN genero = 'Feminino' THEN salario_medio_estimado END)
                       / MIN(CASE WHEN genero = 'Masculino' THEN salario_medio_estimado END)), 1) AS gap_percentual
FROM sal_genero
GROUP BY nivel_senioridade;

-- Indicador 3: concentração regional (Sudeste vs demais regiões)
SELECT
    'Concentração regional' AS indicador,
    regiao,
    SUM(n_respondentes) AS n_respondentes,
    ROUND(100.0 * SUM(n_respondentes) / SUM(SUM(n_respondentes)) OVER (), 1) AS pct_do_total
FROM db_techchallenge_gt_fiap.gold_perfil_mercado
GROUP BY regiao
ORDER BY pct_do_total DESC;
