"""Etapa 7a — o adaptador do Tesseract: o único arquivo que fala com o motor.

Aqui ficam apenas a chamada ao OCR e a leitura da resposta. Nenhuma decisão
sobre aceitar ou recusar um caractere acontece neste arquivo — essa política
está em e7_decisao.py. A separação torna óbvio que trocar de motor de OCR
significa reescrever este arquivo, e só ele.
"""
import os
import string

import numpy as np
import pytesseract

from placas.config import (FORMATOS, IDIOMA_OCR, MODO_OEM, PSM_CARACTERE_UNICO,
                           PSM_LINHA_CRUA, TEMPO_LIMITE_OCR)
from placas.modelos import Leitura
from placas.validacao import validar_entrada_cinza, validar_entrada_ocr

ALFABETO = string.ascii_uppercase + string.digits


def alfabeto_por_posicao(indice: int, formato: str) -> str:
    """Na página, o formato livre permite sempre letras e números."""
    if formato == "livre":
        return ALFABETO
    if formato not in FORMATOS:
        raise ValueError("Formato desconhecido.")
    letra = indice < 3 or (formato == "mercosul" and indice == 4)
    return string.ascii_uppercase if letra else string.digits


def verificar_tesseract() -> str:
    caminho = os.environ.get("TESSERACT_CMD")
    if caminho:
        pytesseract.pytesseract.tesseract_cmd = caminho
    try:
        versao = str(pytesseract.get_tesseract_version())
        if "eng" not in pytesseract.get_languages(config=""):
            raise RuntimeError("Instale os dados de idioma 'eng' do Tesseract.")
        return versao
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError("Tesseract não encontrado. Consulte a instalação no README; "
                           "instalar pytesseract pelo pip não instala o motor OCR.") from exc


def reconhecer_caractere(imagem_individual: np.ndarray, permitidos: str = ALFABETO,
                         psm: int = PSM_CARACTERE_UNICO,
                         referencia_binaria: np.ndarray | None = None) -> Leitura:
    """Entrada: um recorte preparado na etapa 6. Saída: uma leitura individual."""
    if referencia_binaria is None:
        validar_entrada_ocr(imagem_individual)
    else:
        validar_entrada_cinza(imagem_individual, referencia_binaria)
    if psm not in (PSM_CARACTERE_UNICO, PSM_LINHA_CRUA):
        raise ValueError("Modo de OCR não suportado.")
    # Mesmo no modo 13, a entrada validada contém somente um caractere.
    dados = pytesseract.image_to_data(
        imagem_individual, lang=IDIOMA_OCR, output_type=pytesseract.Output.DICT,
        config=f"--psm {psm} --oem {MODO_OEM} "
               f"-c tessedit_char_whitelist={permitidos}",
        timeout=TEMPO_LIMITE_OCR,
    )
    tokens = [(str(t).strip().upper(), float(conf))
              for t, conf in zip(dados["text"], dados["conf"]) if str(t).strip()]
    bruto = "".join(t for t, _ in tokens)
    confianca = min((conf for _, conf in tokens), default=-1.0)
    # Nunca corta uma resposta de vários caracteres para fingir um acerto.
    valor = bruto if len(bruto) == 1 and bruto in permitidos else "?"
    return Leitura(valor, bruto, confianca)
