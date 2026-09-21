"""Etapa 6 — montar as entradas individuais que o OCR vai receber.

Este é o ponto de entrada da etapa 6 e coordena os três arquivos vizinhos:
e6_normalizacao (formato padrão), e6_inclinacao (correção de ângulo) e
placas/validacao.py (as recusas). A etapa 7 só recebe o que sai daqui.
"""
import cv2
import numpy as np

from placas.config import ALTURA_CARACTERE, MARGENS_ALTERNATIVAS
from placas.etapas.e6_inclinacao import corrigir_inclinacao
from placas.etapas.e6_normalizacao import (com_margem, largura_proporcional,
                                           preparar_caractere, sem_margem)
from placas.modelos import EntradaCinza, Segmentacao
from placas.validacao import validar_entrada_cinza, validar_segmentacao


def preparar_recortes(segmentacao: Segmentacao) -> list[np.ndarray]:
    """Valida todos os recortes antes de gerar as sete entradas do OCR."""
    validar_segmentacao(segmentacao)
    return corrigir_inclinacao([preparar_caractere(c) for c in segmentacao.caracteres])


def preparar_cinza(segmentacao: Segmentacao) -> list[dict[str, EntradaCinza]]:
    """Recorta os mesmos boxes validados na placa, preservando tons e proporção.

    A binarização pode apagar detalhes finos; o recorte em cinza conserva o
    que ela perdeu. Devolve, para cada caractere, uma variação por margem —
    imagem e máscara de referência. Nenhuma caixa vem do OCR.
    """
    validar_segmentacao(segmentacao)
    if segmentacao.placa.shape[:2] != segmentacao.binaria.shape:
        raise ValueError("Placa e segmentação devem compartilhar as mesmas coordenadas.")
    cinza = cv2.cvtColor(segmentacao.placa, cv2.COLOR_BGR2GRAY)
    return [_variacoes_em_cinza(cinza, caractere, segmentacao.metodo)
            for caractere in segmentacao.caracteres]


def _variacoes_em_cinza(cinza: np.ndarray, caractere, metodo: str) -> dict[str, EntradaCinza]:
    """Uma entrada por margem, todas do mesmo caractere e já validadas."""
    x, y, w, h = caractere.caixa
    recorte = cinza[y:y+h, x:x+w]
    if "caracteres claros" in metodo:
        # Invertido, o símbolo fica escuro sobre fundo claro nas duas polaridades.
        recorte = 255 - recorte
    letra = cv2.resize(recorte, (largura_proporcional(w, h), ALTURA_CARACTERE),
                       interpolation=cv2.INTER_CUBIC)
    mascara = sem_margem(preparar_caractere(caractere))
    variacoes = {}
    for margem in MARGENS_ALTERNATIVAS:
        entrada = EntradaCinza(com_margem(letra, margem), com_margem(mascara, margem))
        validar_entrada_cinza(entrada.imagem, entrada.referencia)
        variacoes[f'cinza_margem_{margem}'] = entrada
    return variacoes
