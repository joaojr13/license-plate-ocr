"""Etapa 6f — criar alturas menores do mesmo caractere para recuperação.

O Tesseract pode responder de forma diferente ao tamanho do símbolo. Primeiro
retiramos a margem da entrada padrão; depois reduzimos o símbolo e colocamos
uma nova margem branca. A interpolação por área pode introduzir tons de cinza
nas bordas, por isso estas entradas mantêm a referência ao recorte binário.
"""
import cv2
import numpy as np

from placas.config import (ALTURA_PADRAO_DA_ENTRADA, ALTURAS_RECUPERACAO,
                           MARGEM_RECUPERACAO)
from placas.etapas.e6_normalizacao import com_margem, sem_margem
from placas.validacao import validar_entrada_ocr


def preparar_escalas(entrada: np.ndarray) -> dict[str, np.ndarray]:
    """Devolve imagens nomeadas por altura, partindo apenas da entrada padrão.

    A proporção largura/altura é preservada. O nome de cada escala é usado no
    histórico para verificar se respostas fortes vieram de alturas diferentes.
    """
    validar_entrada_ocr(entrada)
    if entrada.shape[0] != ALTURA_PADRAO_DA_ENTRADA:
        raise ValueError(f"As escalas exigem a entrada padrão de altura {ALTURA_PADRAO_DA_ENTRADA}.")

    simbolo = sem_margem(entrada)
    altura_original, largura_original = simbolo.shape
    escalas = {}
    for altura in ALTURAS_RECUPERACAO:
        largura = max(1, round(largura_original * altura / altura_original))
        simbolo_reduzido = cv2.resize(simbolo, (largura, altura), interpolation=cv2.INTER_AREA)
        escalas[f"escala_{altura}"] = com_margem(simbolo_reduzido, MARGEM_RECUPERACAO)
    return escalas
