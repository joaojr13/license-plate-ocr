"""Etapa 6a — transformar a máscara de um componente na imagem que o OCR recebe.

Uma máscara vem da segmentação como pixels brancos em fundo preto, em
qualquer tamanho. O OCR espera sempre o mesmo formato: letra preta sobre
branco, altura fixa e uma margem branca em volta. Esta é a única função que
faz essa conversão, e todas as entradas do OCR passam por ela.
"""
import cv2
import numpy as np

from placas.config import (ALTURA_CARACTERE, LARGURA_MINIMA_CARACTERE, MARGEM_PADRAO,
                           PROPORCAO_COMPONENTE)
from placas.modelos import Caractere


def largura_proporcional(largura: int, altura: int) -> int:
    """Largura que o símbolo terá ao ser levado para a altura padrão."""
    return max(LARGURA_MINIMA_CARACTERE, round(largura * ALTURA_CARACTERE / altura))


def com_margem(letra: np.ndarray, margem: int = MARGEM_PADRAO) -> np.ndarray:
    """Envolve o símbolo em uma borda branca; o OCR precisa desse espaço."""
    return cv2.copyMakeBorder(letra, margem, margem, margem, margem,
                              cv2.BORDER_CONSTANT, value=255)


def sem_margem(entrada: np.ndarray, margem: int = MARGEM_PADRAO) -> np.ndarray:
    """Operação inversa de com_margem(): devolve só o símbolo."""
    return entrada[margem:-margem, margem:-margem]


def normalizar_mascara(mascara: np.ndarray) -> np.ndarray:
    """Letra preta sobre branco, altura 100 px e margem, preservando proporção."""
    if mascara.ndim != 2 or mascara.size == 0:
        raise ValueError("Recorte de caractere inválido.")
    h, w = mascara.shape
    if not PROPORCAO_COMPONENTE[0] <= w / h <= PROPORCAO_COMPONENTE[1]:
        raise ValueError("Recorte largo demais para um caractere isolado.")
    n, _ = cv2.connectedComponents(mascara, 8)
    if n != 2:
        raise ValueError("O OCR exige exatamente um componente por recorte.")
    letra = cv2.resize(255 - mascara, (largura_proporcional(w, h), ALTURA_CARACTERE),
                       interpolation=cv2.INTER_NEAREST)
    return com_margem(letra)


def preparar_caractere(caractere: Caractere) -> np.ndarray:
    """Mesma normalização, partindo de um Caractere vindo da segmentação."""
    return normalizar_mascara(caractere.mascara)
