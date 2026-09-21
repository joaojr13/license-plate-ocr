"""Coordenação das oito etapas mostradas na página.

Leia este arquivo primeiro; cada chamada leva ao módulo da etapa correspondente.
A interface pode parar após a segmentação para inspecionar os recortes sem OCR.
"""
import numpy as np

from placas.bordas import encontrar_bordas
from placas.localizacao import selecionar_placa
from placas.modelos import Localizacao, Segmentacao
from placas.morfologia import aplicar_morfologia
from placas.preparacao import preparar_imagem
from placas.preparacao_ocr import preparar_recortes, preparar_cinza
from placas.resultado import consolidar_resultado


def localizar(imagem: np.ndarray) -> Localizacao:
    """Executa as etapas 1–5, sem acesso ao motor OCR."""
    preparada = preparar_imagem(imagem)                      # 1 · Preparação
    bordas = encontrar_bordas(preparada.suave)                # 2 · Bordas
    morfologia = aplicar_morfologia(preparada.suave)           # 3 · Morfologia
    return selecionar_placa(preparada, bordas, morfologia)     # 4 · Seleção + 5 · Segmentação


def reconhecer(segmentacao: Segmentacao, formato: str = "livre", motor: str = "tesseract") -> dict:
    """Executa as etapas 6–8 somente depois que existe uma segmentação."""
    entradas = preparar_recortes(segmentacao)                # 6 · Validação e recortes
    if motor == "hibrido":
        from placas import ocr_hibrido
        leituras = ocr_hibrido.reconhecer_caracteres(entradas, formato)
    elif motor == "google":
        from placas import ocr_google
        leituras = ocr_google.reconhecer_caracteres(entradas, formato)
    elif motor == "easyocr":
        from placas import ocr_easyocr
        leituras = ocr_easyocr.reconhecer_caracteres(entradas, formato)
    elif motor == "tesseract":
        from placas import ocr
        leituras = ocr.reconhecer_caracteres(entradas, formato)
        if any(leitura.caractere == '?' for leitura in leituras):
            import string
            cinzas = preparar_cinza(segmentacao)
            for indice, leitura in enumerate(leituras):
                permitidos = ocr.ALFABETO
                if formato != 'livre':
                    letra = indice < 3 or (formato == 'mercosul' and indice == 4)
                    permitidos = string.ascii_uppercase if letra else string.digits
                leituras[indice] = ocr.recuperar_com_cinza(leitura, cinzas[indice], permitidos)
    else:
        raise ValueError("Motor de OCR desconhecido.")
    resultado = consolidar_resultado(leituras, formato)
    resultado["motor"] = motor
    return resultado            # 8 · Arrays e resultado
