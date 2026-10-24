"""Harmonizacao Bronze -> Silver das 3 edicoes do State of Data Brasil.

Prototipo LOCAL em pandas. A mesma logica (mesmos indices de coluna, mesmas
regras de recodificacao) e portada para PySpark no notebook do Glue em
notebooks/02_silver/silver_glue_notebook.ipynb. Aqui serve para validar a
harmonizacao e já deixar uma base real disponivel para a EDA local.

Cada edicao da pesquisa tem um schema de colunas diferente (ver docs/_headers_*.txt
e docs/_diagnostico_categorias.txt), por isso o mapeamento e feito por POSICAO
da coluna (indice), nao pelo nome literal do header.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
SILVER_DIR = ROOT / "data" / "silver"

# Nome padronizado -> indice posicional (0-based) da coluna na edicao.
SCALAR_FIELDS = {
    "2023-2024": {
        "id_respondente": 0,
        "idade": 1,
        "faixa_idade": 2,
        "genero": 3,
        "cor_raca_etnia": 4,
        "pcd": 5,
        "vive_no_brasil": 21,
        "uf": 23,
        "regiao": 24,
        "nivel_ensino": 27,
        "area_formacao": 28,
        "situacao_trabalho": 29,
        "setor": 30,
        "numero_funcionarios": 31,
        "gestor": 32,
        "cargo_atual": 34,
        "nivel_senioridade": 35,
        "faixa_salarial": 36,
        "tempo_exp_dados": 37,
        "tempo_exp_ti": 38,
        "satisfeito": 39,
        "modelo_trabalho_atual": 62,
        "modelo_trabalho_ideal": 63,
        "area_atuacao": 124,
        "linguagem_preferida": 160,
        "cloud_preferida": 203,
        "ferramenta_bi_preferida": 228,
        "empresa_prioriza_ia_generativa": 103,
        "uso_ia_generativa_individual": 238,
    },
    "2024-2025": {
        "id_respondente": 0,
        "idade": 2,
        "faixa_idade": 3,
        "genero": 4,
        "cor_raca_etnia": 5,
        "pcd": 6,
        "vive_no_brasil": 26,
        "uf": 12,
        "regiao": 22,
        "nivel_ensino": 31,
        "area_formacao": 32,
        "situacao_trabalho": 33,
        "setor": 34,
        "numero_funcionarios": 35,
        "gestor": 36,
        "cargo_atual": 38,
        "nivel_senioridade": 39,
        "faixa_salarial": 40,
        "tempo_exp_dados": 41,
        "tempo_exp_ti": 42,
        "satisfeito": 43,
        "modelo_trabalho_atual": 70,
        "modelo_trabalho_ideal": 71,
        "area_atuacao": 133,
        "linguagem_preferida": 169,
        "cloud_preferida": 212,
        "ferramenta_bi_preferida": 232,
        "empresa_prioriza_ia_generativa": 112,
        "uso_ia_generativa_individual": 242,
    },
    "2025-2026": {
        "id_respondente": 0,
        "idade": 2,
        "faixa_idade": 3,
        "genero": 4,
        "cor_raca_etnia": 5,
        "pcd": 6,
        "vive_no_brasil": 22,
        "uf": 25,
        "regiao": 26,
        "nivel_ensino": 31,
        "area_formacao": 32,
        "situacao_trabalho": 33,
        "setor": 34,
        "numero_funcionarios": 35,
        "gestor": 36,
        "cargo_atual": 38,
        "nivel_senioridade": 39,
        "faixa_salarial": 40,
        "tempo_exp_dados": 41,
        "tempo_exp_ti": 42,
        "satisfeito": 43,
        "modelo_trabalho_atual": 70,
        "modelo_trabalho_ideal": 71,
        "area_atuacao": 133,
        "linguagem_preferida": 144,
        "cloud_preferida": 197,
        "ferramenta_bi_preferida": 217,
        "empresa_prioriza_ia_generativa": 112,
        "uso_ia_generativa_individual": 227,
    },
}

# categoria -> range de indices (inclusive) das colunas checkbox 0/1 de multipla escolha.
MULTI_SELECT_RANGES = {
    "2023-2024": {
        "linguagem": range(144, 159),
        "banco_dados": range(162, 195),
        "cloud": range(196, 203),
        "ferramenta_bi": range(205, 228),
    },
    "2024-2025": {
        "linguagem": range(153, 168),
        "banco_dados": range(171, 204),
        "cloud": range(205, 212),
        "ferramenta_bi": range(214, 232),
    },
    "2025-2026": {
        "linguagem": range(145, 155),
        "banco_dados": range(156, 189),
        "cloud": range(190, 197),
        "ferramenta_bi": range(199, 217),
    },
}

ANO_PESQUISA = {"2023-2024": 2023, "2024-2025": 2024, "2025-2026": 2025}

RAW_PATHS = {
    "2023-2024": RAW_DIR / "2023-2024" / "state_of_data_2023_2024.csv",
    "2024-2025": RAW_DIR / "2024-2025" / "state_of_data_2024_2025.csv",
    "2025-2026": RAW_DIR / "2025-2026" / "state_of_data_2025_2026.csv",
}

TRUE_LIKE = {"1", "TRUE", "True", "true"}
FALSE_LIKE = {"0", "FALSE", "False", "false"}


def _load_raw(edicao: str) -> pd.DataFrame:
    raw = pd.read_csv(
        RAW_PATHS[edicao],
        encoding="utf-8",
        encoding_errors="replace",
        dtype=str,
        keep_default_na=False,
    )
    id_col = raw.columns[SCALAR_FIELDS[edicao]["id_respondente"]]
    antes = len(raw)
    raw = raw.drop_duplicates(subset=[id_col], keep="first")
    removidas = antes - len(raw)
    if removidas:
        print(f"  [{edicao}] {removidas} respondente(s) duplicado(s) removido(s) na origem")
    return raw


def _to_bool01(series: pd.Series) -> pd.Series:
    return series.map(lambda v: 1 if v in TRUE_LIKE else (0 if v in FALSE_LIKE else pd.NA)).astype("Int64")


def _blank_to_na(series: pd.Series) -> pd.Series:
    return series.str.strip().replace({"": pd.NA})


_FAIXA_RE = re.compile(r"R\$\s*([\d.]+)/m[êe]s\s+a\s+R\$\s*([\d.]+)/m[êe]s")


def _faixa_salarial_para_valor_medio(faixa) -> float | None:
    if faixa is None or pd.isna(faixa) or faixa == "":
        return None
    if "Acima de" in faixa:
        return 45_000.0
    if "Menos de" in faixa:
        return 500.0
    m = _FAIXA_RE.search(faixa)
    if not m:
        return None
    low = float(m.group(1).replace(".", ""))
    high = float(m.group(2).replace(".", ""))
    return (low + high) / 2


def _classificar_prioridade_ia(texto) -> str | None:
    if texto is None or pd.isna(texto) or texto == "":
        return None
    t = texto.lower()
    if "principal prioridade" in t:
        return "Prioridade alta (foco executivo)"
    if "próximos 2-4 anos" in t or "proximos 2-4 anos" in t:
        return "Prioridade de médio prazo"
    if "mais ou menos" in t:
        return "Iniciativa isolada / pouco foco"
    if "não sei" in t or "nao sei" in t:
        return "Não sabe opinar"
    if "não é uma iniciativa" in t or "nao e uma iniciativa" in t:
        return "Não é prioridade"
    return "Outro"


def _classificar_uso_ia_individual(texto) -> dict:
    if texto is None or pd.isna(texto) or texto == "":
        return {"usa_ia_generativa": pd.NA, "paga_por_ia_generativa": 0, "usa_ia_para_codigo": 0}
    t = texto.lower()
    nao_usa = "não utilizo nenhum" in t or "nao utilizo nenhum" in t
    return {
        "usa_ia_generativa": 0 if nao_usa else 1,
        "paga_por_ia_generativa": 1 if ("pagas" in t or "pago" in t or "paga pela" in t) else 0,
        "usa_ia_para_codigo": 1 if ("copilot" in t or "ai para código" in t or "ai para codigo" in t) else 0,
    }


def build_respondentes_silver() -> pd.DataFrame:
    frames = []
    for edicao, col_map in SCALAR_FIELDS.items():
        raw = _load_raw(edicao)
        cols = {name: raw.iloc[:, idx] for name, idx in col_map.items()}
        df = pd.DataFrame(cols)

        df["edicao_pesquisa"] = edicao
        df["ano_pesquisa"] = ANO_PESQUISA[edicao]

        df["idade"] = pd.to_numeric(df["idade"], errors="coerce")
        df.loc[(df["idade"] < 14) | (df["idade"] > 80), "idade"] = pd.NA

        for cat_col in [
            "faixa_idade", "genero", "cor_raca_etnia", "pcd", "uf", "regiao",
            "nivel_ensino", "area_formacao", "situacao_trabalho", "setor",
            "numero_funcionarios", "cargo_atual", "nivel_senioridade",
            "faixa_salarial", "tempo_exp_dados", "tempo_exp_ti",
            "modelo_trabalho_atual", "modelo_trabalho_ideal", "area_atuacao",
            "linguagem_preferida", "cloud_preferida", "ferramenta_bi_preferida",
        ]:
            df[cat_col] = _blank_to_na(df[cat_col])

        df["vive_no_brasil"] = _to_bool01(df["vive_no_brasil"])
        df["gestor"] = _to_bool01(df["gestor"])
        df["satisfeito_empresa_atual"] = _to_bool01(df["satisfeito"])
        df = df.drop(columns=["satisfeito"])

        df["faixa_salarial_valor_medio"] = df["faixa_salarial"].map(_faixa_salarial_para_valor_medio)

        df["prioridade_ia_empresa"] = df["empresa_prioriza_ia_generativa"].map(_classificar_prioridade_ia)

        uso_ia = df["uso_ia_generativa_individual"].map(_classificar_uso_ia_individual).apply(pd.Series)
        df = pd.concat([df, uso_ia], axis=1)

        frames.append(df)

    silver = pd.concat(frames, ignore_index=True)
    silver["id_unico"] = silver["edicao_pesquisa"] + "_" + silver["id_respondente"].astype(str)
    return silver


def _rotulo_tecnologia(header: str) -> str:
    m = re.match(r"^\(?'?[\w.]+\s*'?,?\s*'(.+)'\)?$", header)
    if m:
        return m.group(1).strip()
    m2 = re.match(r"^\d+(?:\.[0-9a-zA-Z]+)*[_ ](.+)$", header)
    if m2:
        return m2.group(1).strip()
    return header.strip()


def build_tecnologias_long_silver() -> pd.DataFrame:
    rows = []
    for edicao, ranges in MULTI_SELECT_RANGES.items():
        raw = _load_raw(edicao)
        id_idx = SCALAR_FIELDS[edicao]["id_respondente"]
        ids = raw.iloc[:, id_idx]
        for categoria, idx_range in ranges.items():
            for idx in idx_range:
                header = raw.columns[idx]
                tecnologia = _rotulo_tecnologia(header)
                usa = pd.to_numeric(raw.iloc[:, idx], errors="coerce").fillna(0).astype(int)
                sub = pd.DataFrame({
                    "id_unico": edicao + "_" + ids.astype(str),
                    "edicao_pesquisa": edicao,
                    "ano_pesquisa": ANO_PESQUISA[edicao],
                    "categoria_tecnologia": categoria,
                    "tecnologia": tecnologia,
                    "usa": usa,
                })
                rows.append(sub[sub["usa"] == 1])
    return pd.concat(rows, ignore_index=True)


def main() -> None:
    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    print("Construindo tb_silver_respondentes...")
    respondentes = build_respondentes_silver()
    print(f"  {len(respondentes):,} linhas, {respondentes.shape[1]} colunas")
    print(respondentes["edicao_pesquisa"].value_counts().to_string())

    out1 = SILVER_DIR / "tb_silver_respondentes.parquet"
    respondentes.to_parquet(out1, index=False)
    print(f"  salvo em {out1}")

    print("\nConstruindo tb_silver_tecnologias_adocao (long/melted)...")
    tecnologias = build_tecnologias_long_silver()
    print(f"  {len(tecnologias):,} linhas (apenas usa=1)")

    out2 = SILVER_DIR / "tb_silver_tecnologias_adocao.parquet"
    tecnologias.to_parquet(out2, index=False)
    print(f"  salvo em {out2}")


if __name__ == "__main__":
    main()
