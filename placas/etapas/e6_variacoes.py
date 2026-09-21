"""Etapa 6d — gerar preparos alternativos do MESMO caractere.

Quando a primeira leitura é incerta, o OCR recebe novas versões do mesmo
símbolo: margens diferentes e um traço levemente mais fino. Nenhuma placa é
acessada aqui — a entrada é um recorte que já passou pela etapa 6.
"""
import cv2
import numpy as np

from placas.config import (ALTURA_PADRAO_DA_ENTRADA, KERNEL_AFINAMENTO, MARGEM_PADRAO,
                           MARGENS_ALTERNATIVAS)
from placas.etapas.e6_normalizacao import com_margem, sem_margem
from placas.validacao import validar_entrada_ocr


def _afinar(imagem: np.ndarray) -> np.ndarray:
    """Dilatar o fundo branco reduz levemente a espessura do traço preto."""
    return cv2.dilate(imagem, np.ones(KERNEL_AFINAMENTO, np.uint8))


def gerar_variacoes(entrada: np.ndarray) -> dict[str, np.ndarray]:
    """Até seis preparos do MESMO caractere; nenhuma placa é acessada aqui.

    Base: altura 100 e margem 20. Outras margens: 10 e 30. A dilatação
    do fundo branco com kernel 2×2 reduz levemente os traços pretos.
    Variações que fragmentem ou eliminem o caractere não são enviadas ao OCR.
    """
    validar_entrada_ocr(entrada)
    if entrada.shape[0] != ALTURA_PADRAO_DA_ENTRADA:
        raise ValueError("As variações devem partir do recorte padrão com margem 20.")
    letra = sem_margem(entrada)
    candidatas = {"padrao": entrada}
    for afinar in (False, True):
        for margem in MARGENS_ALTERNATIVAS:
            if not afinar and margem == MARGEM_PADRAO:
                continue  # A margem padrão sem afinamento já é "padrao".
            imagem = com_margem(letra, margem)
            if afinar:
                imagem = _afinar(imagem)
            nome = f"margem_{margem}" + ("_traco_fino" if afinar else "")
            try:
                validar_entrada_ocr(imagem)
            except ValueError:
                continue  # Um preparo que destrói o símbolo não chega ao OCR.
            if not any(np.array_equal(imagem, existente) for existente in candidatas.values()):
                candidatas[nome] = imagem
    return candidatas
