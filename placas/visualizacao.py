"""Desenhos de apoio à exibição; não localiza placas nem executa OCR."""
import cv2
import numpy as np

from placas.modelos import Localizacao, Segmentacao


def desenhar_localizacao(resultado: Localizacao) -> np.ndarray:
    marcada = resultado.imagem.copy()
    x, y, w, h = resultado.caixa
    cv2.rectangle(marcada, (x, y), (x+w, y+h), (70, 210, 70), 3)
    return marcada


def desenhar_segmentacao(segmentacao: Segmentacao) -> np.ndarray:
    marcada = segmentacao.placa.copy()
    for indice, c in enumerate(segmentacao.caracteres, start=1):
        x, y, w, h = c.caixa
        cv2.rectangle(marcada, (x, y), (x+w, y+h), (70, 180, 20), 2)
        cv2.putText(marcada, str(indice), (x, max(13, y-5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 70, 230), 1)
    return marcada
