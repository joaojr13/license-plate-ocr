"""Etapa 3 — gerar máscaras por black-hat, top-hat, fechamento e abertura."""
import cv2
import numpy as np

from placas.config import (ALTURA_KERNEL_MORFOLOGIA, KERNEL_ABERTURA_MORFOLOGIA,
                           OPERACOES_MORFOLOGIA, TAMANHOS_KERNEL_MORFOLOGIA)

# As três fases intermediárias que a página mostra para cada operação.
FASES = ("Limiarização", "Fechamento", "Abertura")


def nome_da_etapa(operacao: str, tamanho: int, fase: str = "") -> str:
    """Rótulo da imagem intermediária: é a chave do dicionário e a legenda na página.

    Montar esses rótulos em um só lugar evita que a etapa 4 e a interface
    reconstruam a mesma string à mão e se desencontrem em uma mudança.
    """
    return f"{operacao} · {fase} {tamanho}" if fase else f"{operacao} {tamanho}"


def aplicar_morfologia(suave: np.ndarray) -> dict[str, np.ndarray]:
    """Entrada: cinza suavizado. Saída: imagens intermediárias nas duas escalas.

    Este módulo produz máscaras, mas não escolhe qual região é uma placa.
    """
    etapas = {}
    # Duas escalas atendem placas com tamanhos diferentes na fotografia.
    for tamanho in TAMANHOS_KERNEL_MORFOLOGIA:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (tamanho, ALTURA_KERNEL_MORFOLOGIA))
        for nome, operacao in zip(OPERACOES_MORFOLOGIA,
                                  (cv2.MORPH_BLACKHAT, cv2.MORPH_TOPHAT)):
            resposta = cv2.morphologyEx(suave, operacao, kernel)
            _, binaria = cv2.threshold(resposta, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            unida = cv2.morphologyEx(binaria, cv2.MORPH_CLOSE, kernel)
            etapas[nome_da_etapa(nome, tamanho, "Fechamento")] = unida
            unida = cv2.morphologyEx(unida, cv2.MORPH_OPEN,
                                     np.ones(KERNEL_ABERTURA_MORFOLOGIA, np.uint8))
            etapas[nome_da_etapa(nome, tamanho)] = resposta
            etapas[nome_da_etapa(nome, tamanho, "Limiarização")] = binaria
            etapas[nome_da_etapa(nome, tamanho, "Abertura")] = unida
    return etapas
