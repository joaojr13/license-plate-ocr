"""Etapa 7b — roteiro de reconhecimento e recuperação de um caractere.

Aqui se lê a ordem das tentativas: preparo padrão, variações e outro modo.
As recuperações em cinza e em escalas menores são acionadas por reconhecimento/fluxo.py
somente para leituras ainda inconclusivas. Cada representação decide com
suas próprias respostas, mas mantém todas as tentativas no histórico.

As chamadas individuais ficam em reconhecimento/tentativas.py; as regras
que avaliam confiança e consenso ficam em reconhecimento/evidencias.py.
"""
import numpy as np

from placas.config import (CONFIANCA_MINIMA, FORMATOS, PSM_LINHA_CRUA,
                           TOTAL_CARACTERES)
from placas.etapas import e7_motor_ocr
from placas.etapas.e6_variacoes import gerar_variacoes
from placas.etapas.e7_motor_ocr import ALFABETO
from placas.modelos import EntradaCinza, Leitura
from placas.reconhecimento import evidencias, tentativas


def reconhecer_caracteres(entradas: list[np.ndarray], formato: str = "livre") -> list[Leitura]:
    """Recebe sete recortes, reconhece um por vez e preserva a ordem de leitura."""
    if len(entradas) != TOTAL_CARACTERES:
        raise ValueError("O OCR exige sete recortes individuais preparados.")
    if formato not in FORMATOS:
        raise ValueError("Formato desconhecido.")
    e7_motor_ocr.verificar_tesseract()

    leituras = []
    for indice, imagem in enumerate(entradas):
        permitidos = e7_motor_ocr.alfabeto_por_posicao(indice, formato)
        leituras.append(reconhecer_com_tentativas(imagem, permitidos))
    return leituras


def reconhecer_com_tentativas(entrada: np.ndarray, permitidos: str = ALFABETO) -> Leitura:
    """Aceita a leitura padrão forte; nas demais exige concordância sem conflito.

    Pelo menos duas variações devem concordar com confiança >= 60, e nenhuma
    outra resposta com confiança >= 60 pode discordar. A regra é a mesma para
    todos os caracteres; nenhuma posição ou letra esperada desempata respostas.
    """
    primeira = e7_motor_ocr.reconhecer_caractere(entrada, permitidos)
    historico = [tentativas.registrar_resposta("padrao", primeira)]
    if primeira.caractere != "?" and primeira.confianca >= CONFIANCA_MINIMA:
        primeira.tentativas = historico
        primeira.motivo = "Leitura padrão com confiança suficiente."
        return primeira

    variacoes = gerar_variacoes(entrada)
    historico += [tentativas.tentar_preparo_binario(nome, imagem, permitidos)
                  for nome, imagem in variacoes.items() if nome != "padrao"]

    # Só muda o modo se os preparos no modo 10 ainda não resolveram a leitura.
    # Conflitos fortes são preservados; um novo modo não deve escondê-los.
    fortes = evidencias.selecionar_respostas_fortes(historico)
    if evidencias.falta_evidencia_sem_conflito(fortes):
        for nome, imagem in variacoes.items():
            tentativa = tentativas.tentar_preparo_binario(nome, imagem, permitidos,
                                                          PSM_LINHA_CRUA)
            historico.append(tentativa)

    fortes = evidencias.selecionar_respostas_fortes(historico)
    if evidencias.ha_consenso(fortes):
        motivo = (f"Concordância de {len(fortes)} preparos, "
                  "sem conflito de confiança suficiente.")
        return evidencias.construir_leitura_aceita(fortes, historico, motivo)

    if evidencias.ha_conflito(fortes):
        motivo = "Respostas conflitantes com confiança suficiente."
    else:
        motivo = ("Evidência insuficiente: são necessários dois preparos "
                  "concordantes com confiança >= 60.")
    return Leitura("?", primeira.bruto, -1.0, historico, motivo)


def recuperar_com_cinza(leitura: Leitura, variacoes: dict[str, EntradaCinza],
                        permitidos: str = ALFABETO) -> Leitura:
    """Só recupera '?' com consenso entre margens da representação em cinza.

    O consenso desta representação preservada pode resolver conflitos na binária.
    Não mistura pontuações dos dois preparos nem usa a letra esperada: apenas as
    tentativas em cinza votam, embora o histórico guarde todas as respostas.
    """
    if leitura.caractere != "?":
        return leitura
    novas = [tentativas.tentar_preparo_cinza(nome, entrada, permitidos)
             for nome, entrada in variacoes.items()]
    historico = leitura.tentativas + novas
    fortes = evidencias.selecionar_respostas_fortes(novas)
    if evidencias.ha_consenso(fortes):
        motivo = ("Recuperado por concordância entre margens "
                  "em tons de cinza; binário inconclusivo.")
        return evidencias.construir_leitura_aceita(fortes, historico, motivo)
    leitura.tentativas = historico
    leitura.motivo += " Tons de cinza também inconclusivos."
    return leitura


def recuperar_com_escalas(leitura: Leitura, entrada: np.ndarray, permitidos: str) -> Leitura:
    """Última tentativa: consenso independente em duas alturas, sem conflito forte.

    Os votos anteriores continuam no histórico. Como na recuperação em cinza,
    esta representação decide separadamente; não há substituição por posição.
    """
    if leitura.caractere != "?":
        return leitura
    novas = tentativas.tentar_escalas_menores(entrada, permitidos)
    historico = leitura.tentativas + novas
    fortes = evidencias.selecionar_respostas_fortes(novas)
    if evidencias.ha_consenso_em_escalas_distintas(fortes):
        motivo = "Recuperado por concordância entre duas escalas, sem conflito forte."
        return evidencias.construir_leitura_aceita(fortes, historico, motivo)
    leitura.tentativas = historico
    leitura.motivo += " Escalas menores também inconclusivas."
    return leitura
