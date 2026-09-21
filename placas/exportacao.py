"""Reconstrói os preparos registrados para auditar cada chamada individual de OCR."""
import numpy as np

from placas.modelos import Segmentacao
from placas.preparacao_ocr import gerar_variacoes, preparar_recortes, preparar_cinza


def imagens_das_tentativas(segmentacao: Segmentacao, resultado: dict) -> dict[str, np.ndarray]:
    """Retorna somente imagens das tentativas que constam no resultado."""
    imagens = {}
    cinzas = (preparar_cinza(segmentacao) if any(t['variacao'].startswith('cinza_')
              for l in resultado['leituras'] for t in l['tentativas']) else None)
    for indice, (padrao, leitura) in enumerate(zip(preparar_recortes(segmentacao), resultado["leituras"]), 1):
        variacoes = gerar_variacoes(padrao)
        for tentativa in leitura["tentativas"]:
            nome = tentativa["variacao"]
            sufixo = "_psm13" if tentativa.get("psm", 10) == 13 else ""
            if nome.startswith('cinza_'):
                imagens[f"caractere_{indice:02}_tesseract_{nome}{sufixo}.png"] = cinzas[indice-1][nome][0]
                continue
            imagens[f"caractere_{indice:02}_tesseract_{nome}{sufixo}.png"] = variacoes[nome]
    return imagens
