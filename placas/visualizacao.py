"""Desenhos de apoio à exibição; não localiza placas nem executa OCR."""
import cv2
import numpy as np

from placas.modelos import Box, Localizacao, Segmentacao


def desenhar_localizacao(resultado: Localizacao) -> np.ndarray:
    marcada = resultado.imagem.copy()
    x, y, w, h = resultado.caixa
    cv2.rectangle(marcada, (x, y), (x+w, y+h), (70, 210, 70), 3)
    return marcada


def desenhar_candidatas(resultado: Localizacao) -> np.ndarray:
    marcada = resultado.imagem.copy()
    # Desenha a escolhida por último para manter seu contorno visível.
    for indice, candidata in reversed(list(enumerate(resultado.candidatas, start=1))):
        x, y, w, h = candidata.caixa
        escolhida = candidata.caixa == resultado.caixa
        cor = (70, 210, 70) if escolhida else (0, 215, 255)
        cv2.rectangle(marcada, (x, y), (x+w, y+h), cor, 3 if escolhida else 2)
        legenda = f'{indice}' + (' - escolhida' if escolhida else '')
        posicao = (x, max(18, y-6))
        cv2.putText(marcada, legenda, posicao, cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,0,0), 4)
        cv2.putText(marcada, legenda, posicao, cv2.FONT_HERSHEY_SIMPLEX, 0.55, cor, 1)
    return marcada


def desenhar_segmentacao(segmentacao: Segmentacao) -> np.ndarray:
    marcada = segmentacao.placa.copy()
    for indice, c in enumerate(segmentacao.caracteres, start=1):
        x, y, w, h = c.caixa
        cv2.rectangle(marcada, (x, y), (x+w, y+h), (70, 180, 20), 2)
        cv2.putText(marcada, str(indice), (x, max(13, y-5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 70, 230), 1)
    return marcada


def desenhar_regioes_morfologia(imagem: np.ndarray, caixas: list[Box]) -> np.ndarray:
    """Mostra todas as regiões daquela fonte, antes da escolha da placa."""
    marcada = imagem.copy()
    for indice, (x, y, w, h) in enumerate(caixas, 1):
        cv2.rectangle(marcada, (x, y), (x+w, y+h), (0, 215, 255), 2)
        posicao = (x, max(18, y-6))
        cv2.putText(marcada, str(indice), posicao, cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (0, 0, 0), 4)
        cv2.putText(marcada, str(indice), posicao, cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (0, 215, 255), 1)
    return marcada
