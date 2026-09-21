"""Coordenação das oito etapas mostradas na página.

Leia este arquivo primeiro; cada chamada leva ao módulo da etapa correspondente.
A interface pode parar após a segmentação para inspecionar os recortes sem OCR.
"""
import numpy as np

from placas.config import NOME_DO_MOTOR
from placas.etapas import e7_ocr as ocr
from placas.etapas.e1_preparacao import preparar_imagem
from placas.etapas.e2_bordas import encontrar_bordas
from placas.etapas.e3_morfologia import aplicar_morfologia
from placas.etapas.e4_localizacao import selecionar_placa
from placas.etapas.e6_recortes import preparar_cinza, preparar_recortes
from placas.etapas.e8_resultado import consolidar_resultado
from placas.modelos import Localizacao, Segmentacao


def localizar(imagem: np.ndarray) -> Localizacao:
    """Executa as etapas 1–5, sem acesso ao motor OCR."""
    preparada = preparar_imagem(imagem)                      # 1 · Preparação
    bordas = encontrar_bordas(preparada.suave)                # 2 · Bordas
    morfologia = aplicar_morfologia(preparada.suave)           # 3 · Morfologia
    return selecionar_placa(preparada, bordas, morfologia)     # 4 · Seleção + 5 · Segmentação


def reconhecer(segmentacao: Segmentacao, formato: str = "livre") -> dict:
    """Executa as etapas 6–8 somente depois que existe uma segmentação."""
    entradas = preparar_recortes(segmentacao)                # 6 · Validação e recortes
    leituras = ocr.reconhecer_caracteres(entradas, formato)    # 7 · OCR individual
    if any(leitura.caractere == '?' for leitura in leituras):
        cinzas = preparar_cinza(segmentacao)
        for indice, leitura in enumerate(leituras):
            leituras[indice] = ocr.recuperar_com_cinza(
                leitura, cinzas[indice], ocr.alfabeto_por_posicao(indice, formato))
    resultado = consolidar_resultado(leituras, formato)
    resultado["motor"] = NOME_DO_MOTOR
    return resultado            # 8 · Arrays e resultado
