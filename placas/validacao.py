"""Verificações que protegem o OCR — o portão entre as etapas 5/6 e a etapa 7.

Nenhuma função aqui transforma imagem: todas apenas aceitam ou recusam, com
uma mensagem que explica o motivo. Reunir as três em um arquivo deixa visível
a regra central do projeto: o motor de OCR só recebe um caractere isolado,
com margem branca e geometria conhecida — nunca a placa inteira.
"""
import cv2
import numpy as np

from placas.config import (ALTURA_CARACTERE, ALTURAS_VALIDAS, AREA_MINIMA_COMPONENTE,
                           LARGURA_MAXIMA_CARACTERE, LARGURA_MINIMA_CARACTERE,
                           LARGURA_RELATIVA_COMPONENTE, PROPORCAO_COMPONENTE,
                           TOTAL_CARACTERES)
from placas.modelos import Segmentacao


def _margem_de(imagem: np.ndarray) -> int:
    """Altura total menos a altura fixa do símbolo, dividida entre os dois lados."""
    return (imagem.shape[0] - ALTURA_CARACTERE) // 2


def _tem_borda_branca(imagem: np.ndarray, margem: int) -> bool:
    return bool(np.all(imagem[:margem] == 255) and np.all(imagem[-margem:] == 255)
                and np.all(imagem[:, :margem] == 255) and np.all(imagem[:, -margem:] == 255))


def validar_segmentacao(segmentacao: Segmentacao) -> None:
    """Exige sete recortes na ordem de leitura, sem sobreposição e isolados."""
    caracteres = segmentacao.caracteres
    if len(caracteres) != TOTAL_CARACTERES:
        raise ValueError(f"Foram isolados {len(caracteres)} caracteres; "
                         f"são necessários {TOTAL_CARACTERES}. "
                         "OCR bloqueado. Tente uma foto melhor.")
    altura, largura = segmentacao.binaria.shape
    anterior = -1
    for c in caracteres:
        x, y, w, h = c.caixa
        if (x < anterior or x < 0 or y < 0 or x+w > largura or y+h > altura
                or w > largura * LARGURA_RELATIVA_COMPONENTE[1]
                or w / h > PROPORCAO_COMPONENTE[1] or c.mascara.shape != (h, w)):
            raise ValueError("Recortes inválidos ou sobrepostos; OCR bloqueado.")
        n, _, stats, _ = cv2.connectedComponentsWithStats(c.mascara, 8)
        if n != 2 or stats[1, cv2.CC_STAT_AREA] < AREA_MINIMA_COMPONENTE:
            raise ValueError("Cada recorte deve conter somente um componente isolado.")
        anterior = x + w


def validar_entrada_ocr(imagem: np.ndarray) -> None:
    """Aceita somente um símbolo binário com altura 100 e margem conhecida."""
    if (imagem.ndim != 2 or imagem.dtype != np.uint8
            or imagem.shape[0] not in ALTURAS_VALIDAS):
        raise ValueError("O OCR aceita somente um recorte preparado na etapa 6.")
    margem = _margem_de(imagem)
    largura = imagem.shape[1] - 2 * margem
    if (not LARGURA_MINIMA_CARACTERE <= largura <= LARGURA_MAXIMA_CARACTERE
            or not np.all((imagem == 0) | (imagem == 255))):
        raise ValueError("O OCR aceita somente um recorte preparado na etapa 6.")
    if not _tem_borda_branca(imagem, margem):
        raise ValueError("O recorte deve ter uma margem branca livre de outros objetos.")
    componentes, _ = cv2.connectedComponents(255 - imagem, 8)
    if componentes != 2:
        raise ValueError("O OCR exige exatamente um componente por recorte.")


def validar_entrada_cinza(imagem: np.ndarray, referencia: np.ndarray) -> None:
    """O recorte em cinza só vale acompanhado do componente que o originou."""
    validar_entrada_ocr(referencia)
    if imagem.dtype != np.uint8 or imagem.shape != referencia.shape:
        raise ValueError("Recorte em cinza incompatível com seu componente individual.")
    if not _tem_borda_branca(imagem, _margem_de(imagem)):
        raise ValueError("Recorte em cinza deve ter margem branca livre.")
