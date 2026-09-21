"""Etapa 3 — gerar máscaras por black-hat, top-hat, fechamento e abertura."""
import cv2
import numpy as np


def aplicar_morfologia(suave: np.ndarray) -> dict[str, np.ndarray]:
    """Entrada: cinza suavizado. Saída: imagens intermediárias nas duas escalas.

    Este módulo produz máscaras, mas não escolhe qual região é uma placa.
    """
    etapas = {}
    # Duas escalas atendem placas com tamanhos diferentes na fotografia.
    for tamanho in [17, 31]:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (tamanho, 7))
        for nome, operacao in [("Black-hat", cv2.MORPH_BLACKHAT),
                               ("Top-hat", cv2.MORPH_TOPHAT)]:
            resposta = cv2.morphologyEx(suave, operacao, kernel)
            _, binaria = cv2.threshold(resposta, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            unida = cv2.morphologyEx(binaria, cv2.MORPH_CLOSE, kernel)
            etapas[f"{nome} · Fechamento {tamanho}"] = unida
            unida = cv2.morphologyEx(unida, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
            etapas[f"{nome} {tamanho}"] = resposta
            etapas[f"{nome} · Limiarização {tamanho}"] = binaria
            etapas[f"{nome} · Abertura {tamanho}"] = unida
    return etapas
