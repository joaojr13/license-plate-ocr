"""Etapa 7a — adaptador: valida a entrada, chama o Tesseract e traduz a resposta.

Este é o único arquivo que chama o motor externo. Uma resposta com vários
símbolos é inválida e vira '?'; uma resposta com um símbolo é devolvida com
sua confiança. Decidir se essa confiança basta é responsabilidade do roteiro
e7_decisao.py, apoiado pelas regras de reconhecimento/evidencias.py.
"""
import os
import string

import numpy as np
import pytesseract

from placas.config import (FORMATOS, IDIOMA_OCR, MODO_OEM, PSM_CARACTERE_UNICO,
                           PSM_LINHA_CRUA, TEMPO_LIMITE_OCR)
from placas.etapas.e6_escalas import preparar_escalas
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
    """Confere executável e idioma; devolve a versão mostrada pela interface."""
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


def _validar_entrada_individual(imagem_individual: np.ndarray,
                               referencia_binaria: np.ndarray | None,
                               referencia_escala: np.ndarray | None) -> None:
    """Escolhe a validação pela origem: máscara, recorte cinza ou escala menor.

    A escala deve ser exatamente uma das imagens produzidas a partir do
    caractere validado. Ter dimensões pequenas, por si só, não autoriza OCR.
    """
    if referencia_escala is not None:
        if referencia_binaria is not None or not any(
            np.array_equal(imagem_individual, imagem)
            for imagem in preparar_escalas(referencia_escala).values()
        ):
            raise ValueError("Escala incompatível com o caractere individual validado.")
    elif referencia_binaria is None:
        validar_entrada_ocr(imagem_individual)
    else:
        validar_entrada_cinza(imagem_individual, referencia_binaria)


def _interpretar_resposta(dados: dict, permitidos: str) -> Leitura:
    """Converte a resposta do motor, preservando o texto bruto para auditoria.

    Ignora registros sem texto e mantém a menor confiança dos registros com
    texto. Nunca corta uma resposta de vários símbolos para fingir um acerto.
    """
    tokens = []
    for texto, confianca in zip(dados["text"], dados["conf"]):
        texto_normalizado = str(texto).strip().upper()
        if texto_normalizado:
            tokens.append((texto_normalizado, float(confianca)))

    bruto = "".join(texto for texto, _ in tokens)
    menor_confianca = min((confianca for _, confianca in tokens), default=-1.0)
    caractere = bruto if len(bruto) == 1 and bruto in permitidos else "?"
    return Leitura(caractere, bruto, menor_confianca)


def reconhecer_caractere(imagem_individual: np.ndarray, permitidos: str = ALFABETO,
                         psm: int = PSM_CARACTERE_UNICO,
                         referencia_binaria: np.ndarray | None = None,
                         referencia_escala: np.ndarray | None = None) -> Leitura:
    """Entrada: um recorte preparado na etapa 6. Saída: uma leitura individual.

    As referências só servem à validação. A única imagem enviada ao Tesseract
    é imagem_individual, inclusive quando o modo de leitura é linha crua.
    """
    _validar_entrada_individual(imagem_individual, referencia_binaria, referencia_escala)
    if psm not in (PSM_CARACTERE_UNICO, PSM_LINHA_CRUA):
        raise ValueError("Modo de OCR não suportado.")
    # Mesmo no modo 13, a entrada validada contém somente um caractere.
    dados = pytesseract.image_to_data(
        imagem_individual, lang=IDIOMA_OCR, output_type=pytesseract.Output.DICT,
        config=f"--psm {psm} --oem {MODO_OEM} "
               f"-c tessedit_char_whitelist={permitidos}",
        timeout=TEMPO_LIMITE_OCR,
    )
    return _interpretar_resposta(dados, permitidos)
