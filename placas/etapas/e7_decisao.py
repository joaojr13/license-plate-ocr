"""Etapa 7b — as regras que decidem se uma leitura é aceita ou vira '?'.

Nenhuma função aqui conversa com o Tesseract: todas as chamadas passam pelo
adaptador e7_motor_ocr. O que este arquivo contém é a política — quantas
respostas precisam concordar, o que conta como conflito e quando desistir.
Ela é a mesma para todos os caracteres: nenhuma posição, letra esperada ou
formato de placa é usado para desempatar uma resposta.
"""
import numpy as np

from placas.config import (CONFIANCA_MINIMA, FORMATOS, MINIMO_DE_CONCORDANCIAS,
                           PSM_CARACTERE_UNICO, PSM_LINHA_CRUA, TOTAL_CARACTERES)
from placas.etapas import e7_motor_ocr
from placas.etapas.e6_variacoes import gerar_variacoes
from placas.etapas.e7_motor_ocr import ALFABETO
from placas.modelos import EntradaCinza, Leitura, TentativaOCR

# --- Vocabulário da decisão: quatro perguntas puras sobre um histórico -------


def _fortes(tentativas: list[TentativaOCR]) -> list[TentativaOCR]:
    """Tentativas com resposta única e confiança suficiente para pesar."""
    return [t for t in tentativas
            if t.caractere != "?" and t.confianca >= CONFIANCA_MINIMA]


def _respostas(fortes: list[TentativaOCR]) -> set[str]:
    return {t.caractere for t in fortes}


def _ha_consenso(fortes: list[TentativaOCR]) -> bool:
    """Duas ou mais respostas fortes, todas iguais: é o que autoriza aceitar."""
    return (len(fortes) >= MINIMO_DE_CONCORDANCIAS
            and len(_respostas(fortes)) == 1)


def _ha_conflito(fortes: list[TentativaOCR]) -> bool:
    """Respostas fortes que discordam entre si: o sistema se abstém."""
    return len(_respostas(fortes)) > 1


def _falta_evidencia_sem_conflito(fortes: list[TentativaOCR]) -> bool:
    """Ainda não há duas concordâncias, mas também não há conflito forte."""
    return (len(_respostas(fortes)) <= 1
            and len(fortes) < MINIMO_DE_CONCORDANCIAS)


def _aceitar(fortes: list[TentativaOCR], historico: list[TentativaOCR],
             motivo: str) -> Leitura:
    """A confiança registrada é a MENOR entre os apoiadores, não a maior."""
    escolhida = fortes[0]
    return Leitura(escolhida.caractere, escolhida.bruto,
                   min(t.confianca for t in fortes), historico, motivo)


# --- Chamadas ao motor, sempre com um caractere por vez ----------------------


def _tentar(nome: str, imagem: np.ndarray, permitidos: str,
            psm: int = PSM_CARACTERE_UNICO) -> TentativaOCR:
    leitura = e7_motor_ocr.reconhecer_caractere(imagem, permitidos, psm=psm)
    return TentativaOCR(nome, leitura.caractere, leitura.bruto, leitura.confianca, psm=psm)


def _tentar_em_cinza(nome: str, entrada: EntradaCinza, permitidos: str) -> TentativaOCR:
    leitura = e7_motor_ocr.reconhecer_caractere(
        entrada.imagem, permitidos, referencia_binaria=entrada.referencia)
    return TentativaOCR(nome, leitura.caractere, leitura.bruto, leitura.confianca)


# --- As três decisões --------------------------------------------------------


def reconhecer_com_tentativas(entrada: np.ndarray, permitidos: str = ALFABETO) -> Leitura:
    """Aceita a leitura padrão forte; nas demais exige concordância sem conflito.

    Pelo menos duas variações devem concordar com confiança >= 60, e nenhuma
    outra resposta com confiança >= 60 pode discordar. A regra é a mesma para
    todos os caracteres; nenhuma posição ou letra esperada desempata respostas.
    """
    primeira = e7_motor_ocr.reconhecer_caractere(entrada, permitidos)
    historico = [TentativaOCR("padrao", primeira.caractere, primeira.bruto, primeira.confianca)]
    if primeira.caractere != "?" and primeira.confianca >= CONFIANCA_MINIMA:
        primeira.tentativas = historico
        primeira.motivo = "Leitura padrão com confiança suficiente."
        return primeira

    variacoes = gerar_variacoes(entrada)
    historico += [_tentar(nome, imagem, permitidos)
                  for nome, imagem in variacoes.items() if nome != "padrao"]

    # Só muda o modo se os preparos no modo 10 ainda não resolveram a leitura.
    # Conflitos fortes são preservados; um novo modo não deve escondê-los.
    if _falta_evidencia_sem_conflito(_fortes(historico)):
        historico += [_tentar(nome, imagem, permitidos, PSM_LINHA_CRUA)
                      for nome, imagem in variacoes.items()]

    fortes = _fortes(historico)
    if _ha_consenso(fortes):
        return _aceitar(fortes, historico,
                        f"Concordância de {len(fortes)} preparos, "
                        "sem conflito de confiança suficiente.")
    motivo = ("Respostas conflitantes com confiança suficiente." if _ha_conflito(fortes)
              else "Evidência insuficiente: são necessários dois preparos "
                   "concordantes com confiança >= 60.")
    return Leitura("?", primeira.bruto, -1.0, historico, motivo)


def recuperar_com_cinza(leitura: Leitura, variacoes: dict[str, EntradaCinza],
                        permitidos: str = ALFABETO) -> Leitura:
    """Só recupera '?' com consenso entre margens da representação em cinza.

    O consenso desta representação preservada pode resolver conflitos na binária.
    Não mistura pontuações dos dois preparos nem usa a letra esperada: apenas as
    tentativas em cinza votam, embora o histórico guarde todas as respostas.
    """
    if leitura.caractere != '?':
        return leitura
    novas = [_tentar_em_cinza(nome, entrada, permitidos)
             for nome, entrada in variacoes.items()]
    historico = leitura.tentativas + novas
    fortes = _fortes(novas)
    if _ha_consenso(fortes):
        return _aceitar(fortes, historico, 'Recuperado por concordância entre margens '
                                           'em tons de cinza; binário inconclusivo.')
    leitura.tentativas = historico
    leitura.motivo += ' Tons de cinza também inconclusivos.'
    return leitura


def reconhecer_caracteres(entradas: list[np.ndarray], formato: str = "livre") -> list[Leitura]:
    """Entrada: sete recortes da etapa 6. Saída: leituras, ainda sem concatenar."""
    if len(entradas) != TOTAL_CARACTERES:
        raise ValueError("O OCR exige sete recortes individuais preparados.")
    if formato not in FORMATOS:
        raise ValueError("Formato desconhecido.")
    e7_motor_ocr.verificar_tesseract()
    return [reconhecer_com_tentativas(imagem,
                                      e7_motor_ocr.alfabeto_por_posicao(indice, formato))
            for indice, imagem in enumerate(entradas)]
