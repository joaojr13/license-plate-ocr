"""Reduz somente um recorte já validado, preservando proporção e níveis de cinza."""
import cv2

from placas.config import (ALTURA_PADRAO_DA_ENTRADA, ALTURAS_RECUPERACAO,
                           MARGEM_PADRAO, MARGEM_RECUPERACAO)
from placas.validacao import validar_entrada_ocr


def preparar_escalas(entrada):
    validar_entrada_ocr(entrada)
    if entrada.shape[0] != ALTURA_PADRAO_DA_ENTRADA:
        raise ValueError("As escalas exigem a entrada padrão de altura 140.")
    letra = entrada[MARGEM_PADRAO:-MARGEM_PADRAO, MARGEM_PADRAO:-MARGEM_PADRAO]
    return {
        f"escala_{altura}": cv2.copyMakeBorder(
            cv2.resize(letra, (max(1, round(letra.shape[1] * altura / letra.shape[0])), altura),
                       interpolation=cv2.INTER_AREA),
            MARGEM_RECUPERACAO, MARGEM_RECUPERACAO,
            MARGEM_RECUPERACAO, MARGEM_RECUPERACAO, cv2.BORDER_CONSTANT, value=255)
        for altura in ALTURAS_RECUPERACAO
    }
