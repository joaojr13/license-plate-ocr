"""Alternativa à interface: python main.py foto.jpg --saida output/leitura."""
import argparse
import json
from pathlib import Path
import sys

import cv2

from placas.imagem import ler_imagem
from placas.exportacao import imagens_das_tentativas
from placas.preparacao_ocr import preparar_caractere, preparar_recortes
from placas.processamento import localizar, reconhecer
from placas.visualizacao import desenhar_localizacao, desenhar_segmentacao


def main() -> int:
    parser = argparse.ArgumentParser(description="OCR individual de caracteres de placas.")
    parser.add_argument("imagem", type=Path)
    parser.add_argument("--saida", type=Path, default=Path("output/leitura"))
    parser.add_argument("--formato", choices=["livre", "antiga", "mercosul"], default="livre")
    parser.add_argument("--somente-segmentar", action="store_true", help="Inspeciona etapas sem executar OCR.")
    args = parser.parse_args()
    try:
        localizacao = localizar(ler_imagem(args.imagem.read_bytes()))
        segmentacao = localizacao.segmentacao
        # Uma pasta nova evita misturar recortes de execuções diferentes.
        args.saida.mkdir(parents=True, exist_ok=False)
        cv2.imwrite(str(args.saida / "localizacao.png"), desenhar_localizacao(localizacao))
        cv2.imwrite(str(args.saida / "segmentacao.png"), desenhar_segmentacao(segmentacao))
        cv2.imwrite(str(args.saida / "binaria.png"), segmentacao.binaria)
        entradas = ([preparar_caractere(c) for c in segmentacao.caracteres] if args.somente_segmentar
                    else preparar_recortes(segmentacao))
        for i, entrada in enumerate(entradas, 1):
            cv2.imwrite(str(args.saida / f"caractere_{i:02}.png"), entrada)
        if args.somente_segmentar:
            print(f"{len(segmentacao.caracteres)} caracteres isolados. Imagens em {args.saida}.")
            return 0
        resultado = reconhecer(segmentacao, args.formato)
        for nome, imagem in imagens_das_tentativas(segmentacao, resultado).items():
            cv2.imwrite(str(args.saida / nome), imagem)
        texto = json.dumps(resultado, ensure_ascii=False, indent=2)
        (args.saida / "resultado.json").write_text(texto, encoding="utf-8")
        print(texto)
        return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
