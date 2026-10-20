"""Utilitario local (fora da pasta de dados) para extrair e comparar os headers
dos CSVs brutos do Data Hackers. Nao depende de pandas - usa so a stdlib,
para funcionar mesmo antes da instalacao de pacotes terminar.

Uso: python -I inspect_headers.py <arquivo1.csv> [arquivo2.csv ...]
"""
import csv
import sys


def read_header(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        first_row = next(reader)
    return header, first_row


def main(paths: list[str]) -> None:
    for path in paths:
        header, first_row = read_header(path)
        print(f"\n{'=' * 100}\nARQUIVO: {path}")
        print(f"Total de colunas: {len(header)}")
        print(f"{'-' * 100}")
        for i, (col, val) in enumerate(zip(header, first_row)):
            val_preview = (val[:60] + "...") if len(val) > 60 else val
            print(f"[{i:3d}] {col!r:90s} -> {val_preview!r}")


if __name__ == "__main__":
    main(sys.argv[1:])
