"""Etapa 1 — redimensionar, converter para cinza e suavizar a imagem BGR.

A leitura de arquivo e a orientação EXIF ficam em imagem.ler_imagem().
"""
import cv2
import numpy as np

from placas.config import (KERNEL_SUAVIZACAO, LADO_MAXIMO_TRABALHO,
                           LADO_MINIMO_ENTRADA)
from placas.modelos import ImagemPreparada


def preparar_imagem(imagem: np.ndarray) -> ImagemPreparada:
    """Entrada: foto BGR. Saída: imagem de trabalho, cinza e suavização."""
    if imagem is None or imagem.ndim != 3 or imagem.shape[2] != 3:
        raise ValueError("Esperada uma imagem colorida BGR.")
    h, w = imagem.shape[:2]
    if min(h, w) < LADO_MINIMO_ENTRADA:
        raise ValueError("Imagem pequena demais.")
    escala = min(1.0, LADO_MAXIMO_TRABALHO / max(h, w))
    trabalho = cv2.resize(imagem, (round(w * escala), round(h * escala)))
    cinza = cv2.cvtColor(trabalho, cv2.COLOR_BGR2GRAY)
    suave = cv2.GaussianBlur(cinza, KERNEL_SUAVIZACAO, 0)
    return ImagemPreparada(trabalho, cinza, suave)
