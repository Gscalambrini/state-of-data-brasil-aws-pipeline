"""Extrai texto plano de word/document.xml de um .docx ja extraido, sem
depender de bibliotecas externas (so stdlib). Util quando pandoc/python-docx
nao estao disponiveis no ambiente.

Uso: python -I extrair_texto_docx.py <pasta_extraida>/word/document.xml
"""
import re
import sys
from xml.etree import ElementTree as ET

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def main(path: str) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    for para in root.iter(f"{W_NS}p"):
        texto = "".join(t.text or "" for t in para.iter(f"{W_NS}t"))
        if texto.strip():
            print(texto)
        else:
            print()


if __name__ == "__main__":
    main(sys.argv[1])
