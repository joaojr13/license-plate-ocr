"""Alternativa à interface, para rodar no terminal e guardar as imagens.

    python main.py foto.jpg --saida output/leitura
    python main.py foto.jpg --somente-segmentar --saida output/inspecao

A pasta de saída precisa ser nova: assim os recortes de execuções
diferentes nunca se misturam.
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

from placas.config import FORMATOS
from placas.etapas.e6_normalizacao import preparar_caractere
from placas.etapas.e6_recortes import preparar_recortes
from placas.imagem import ler_imagem
from placas.modelos import Localizacao, Segmentacao
from placas.pipeline import localizar, reconhecer
from placas.saida.exportacao import imagens_das_tentativas
from placas.saida.visualizacao import desenhar_localizacao, desenhar_segmentacao


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OCR individual de caracteres de placas.")
    parser.add_argument("imagem", type=Path)
    parser.add_argument("--saida", type=Path, default=Path("output/leitura"))
    parser.add_argument("--formato", choices=list(FORMATOS), default="livre")
    parser.add_argument("--somente-segmentar", action="store_true",
                        help="Inspeciona etapas sem executar OCR.")
    return parser.parse_args()


def salvar(pasta: Path, nome: str, imagem: np.ndarray) -> None:
    cv2.imwrite(str(pasta / nome), imagem)


def salvar_etapas(pasta: Path, localizacao: Localizacao) -> None:
    """As três imagens que mostram o que o programa enxergou na foto."""
    segmentacao = localizacao.segmentacao
    salvar(pasta, "localizacao.png", desenhar_localizacao(localizacao))
    salvar(pasta, "segmentacao.png", desenhar_segmentacao(segmentacao))
    salvar(pasta, "binaria.png", segmentacao.binaria)


def salvar_entradas(pasta: Path, segmentacao: Segmentacao, somente_segmentar: bool) -> None:
    """Os recortes individuais, exatamente como o OCR os receberia."""
    entradas = ([preparar_caractere(c) for c in segmentacao.caracteres] if somente_segmentar
                else preparar_recortes(segmentacao))
    for i, entrada in enumerate(entradas, 1):
        salvar(pasta, f"caractere_{i:02}.png", entrada)


def salvar_resultado(pasta: Path, segmentacao: Segmentacao, resultado: dict) -> str:
    """O JSON do resultado e uma imagem por tentativa registrada."""
    for nome, imagem in imagens_das_tentativas(segmentacao, resultado).items():
        salvar(pasta, nome, imagem)
    texto = json.dumps(resultado, ensure_ascii=False, indent=2)
    (pasta / "resultado.json").write_text(texto, encoding="utf-8")
    return texto


def main() -> int:
    args = argumentos()
    try:
        localizacao = localizar(ler_imagem(args.imagem.read_bytes()))
        segmentacao = localizacao.segmentacao
        args.saida.mkdir(parents=True, exist_ok=False)
        salvar_etapas(args.saida, localizacao)
        salvar_entradas(args.saida, segmentacao, args.somente_segmentar)
        if args.somente_segmentar:
            print(f"{len(segmentacao.caracteres)} caracteres isolados. Imagens em {args.saida}.")
            return 0
        print(salvar_resultado(args.saida, segmentacao,
                               reconhecer(segmentacao, args.formato)))
        return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
