"""Etapa 7 — OCR individual com novas tentativas somente nas leituras incertas."""
import os
import string

import numpy as np
import pytesseract

from placas.config import (CONFIANCA_MINIMA, FORMATOS, IDIOMA_OCR,
                           MINIMO_DE_CONCORDANCIAS, MODO_OEM, PSM_CARACTERE_UNICO,
                           PSM_LINHA_CRUA, TEMPO_LIMITE_OCR, TOTAL_CARACTERES)
from placas.modelos import Leitura, TentativaOCR
from placas.etapas.e6_recortes import (gerar_variacoes, validar_entrada_cinza,
                                       validar_entrada_ocr)

ALFABETO = string.ascii_uppercase + string.digits


def alfabeto_por_posicao(indice: int, formato: str) -> str:
    """Na página, o formato livre permite sempre letras e números."""
    if formato == 'livre':
        return ALFABETO
    if formato not in FORMATOS:
        raise ValueError('Formato desconhecido.')
    letra = indice < 3 or (formato == 'mercosul' and indice == 4)
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


def recuperar_com_cinza(leitura: Leitura, variacoes: dict, permitidos: str = ALFABETO) -> Leitura:
    """Só recupera '?' com consenso entre margens da representação em cinza.

    O consenso desta representação preservada pode resolver conflitos na binária.
    Não mistura pontuações dos dois preparos nem usa a letra esperada.
    """
    if leitura.caractere != '?':
        return leitura
    novas = []
    for nome, (imagem, referencia) in variacoes.items():
        resposta = reconhecer_caractere(imagem, permitidos, referencia_binaria=referencia)
        novas.append(TentativaOCR(nome, resposta.caractere, resposta.bruto, resposta.confianca))
    historico = leitura.tentativas + novas
    fortes = [t for t in novas if t.caractere != '?' and t.confianca >= CONFIANCA_MINIMA]
    if (len(fortes) >= MINIMO_DE_CONCORDANCIAS
            and len({t.caractere for t in fortes}) == 1):
        return Leitura(fortes[0].caractere, fortes[0].bruto, min(t.confianca for t in fortes),
                       historico, 'Recuperado por concordância entre margens em tons de cinza; binário inconclusivo.')
    leitura.tentativas = historico
    leitura.motivo += ' Tons de cinza também inconclusivos.'
    return leitura


def reconhecer_com_tentativas(entrada: np.ndarray, permitidos: str = ALFABETO) -> Leitura:
    """Aceita a leitura padrão forte; nas demais exige concordância sem conflito.

    Pelo menos duas variações devem concordar com confiança >= 60, e nenhuma
    outra resposta com confiança >= 60 pode discordar. A regra é a mesma para
    todos os caracteres; nenhuma posição ou letra esperada desempata respostas.
    """
    primeira = reconhecer_caractere(entrada, permitidos)
    historico = [TentativaOCR("padrao", primeira.caractere, primeira.bruto, primeira.confianca)]
    if primeira.caractere != "?" and primeira.confianca >= CONFIANCA_MINIMA:
        primeira.tentativas = historico
        primeira.motivo = "Leitura padrão com confiança suficiente."
        return primeira

    variacoes = gerar_variacoes(entrada)
    for nome, imagem in variacoes.items():
        if nome == "padrao":
            continue
        leitura = reconhecer_caractere(imagem, permitidos)
        historico.append(TentativaOCR(nome, leitura.caractere, leitura.bruto, leitura.confianca))

    fortes = [t for t in historico if t.caractere != "?" and t.confianca >= CONFIANCA_MINIMA]
    candidatos = {t.caractere for t in fortes}
    # Só muda o modo se os preparos no modo 10 ainda não resolveram a leitura.
    # Conflitos fortes são preservados; um novo modo não deve escondê-los.
    if len(candidatos) <= 1 and len(fortes) < MINIMO_DE_CONCORDANCIAS:
        for nome, imagem in variacoes.items():
            leitura = reconhecer_caractere(imagem, permitidos, psm=PSM_LINHA_CRUA)
            historico.append(TentativaOCR(nome, leitura.caractere, leitura.bruto,
                                          leitura.confianca, psm=PSM_LINHA_CRUA))
        fortes = [t for t in historico if t.caractere != "?" and t.confianca >= CONFIANCA_MINIMA]
        candidatos = {t.caractere for t in fortes}
    if len(candidatos) == 1 and len(fortes) >= MINIMO_DE_CONCORDANCIAS:
        escolhida = fortes[0]
        return Leitura(escolhida.caractere, escolhida.bruto, min(t.confianca for t in fortes),
                       historico, f"Concordância de {len(fortes)} preparos, sem conflito de confiança suficiente.")
    motivo = ("Respostas conflitantes com confiança suficiente." if len(candidatos) > 1
              else "Evidência insuficiente: são necessários dois preparos concordantes com confiança >= 60.")
    return Leitura("?", primeira.bruto, -1.0, historico, motivo)


def reconhecer_caracteres(entradas: list[np.ndarray], formato: str = "livre") -> list[Leitura]:
    """Entrada: sete recortes da etapa 6. Saída: leituras, ainda sem concatenar."""
    if len(entradas) != TOTAL_CARACTERES:
        raise ValueError("O OCR exige sete recortes individuais preparados.")
    if formato not in FORMATOS:
        raise ValueError("Formato desconhecido.")
    verificar_tesseract()
    leituras = []
    for indice, imagem_individual in enumerate(entradas):
        permitidos = alfabeto_por_posicao(indice, formato)
        leituras.append(reconhecer_com_tentativas(imagem_individual, permitidos))
    return leituras
