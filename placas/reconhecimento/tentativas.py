"""Executa chamadas individuais ao adaptador e registra o preparo utilizado.

Este módulo não decide se o resultado está correto ou se deve ser aceito.
Cada chamada recebe somente uma versão de um caractere já isolado. As
referências enviadas ao adaptador servem para validar sua origem; elas não
são enviadas ao Tesseract.
"""
import numpy as np

from placas.config import PSM_CARACTERE_UNICO, PSM_LINHA_CRUA
from placas.etapas import e7_motor_ocr
from placas.etapas.e6_escalas import preparar_escalas
from placas.modelos import EntradaCinza, Leitura, TentativaOCR


def registrar_resposta(nome: str, leitura: Leitura,
                       psm: int = PSM_CARACTERE_UNICO) -> TentativaOCR:
    """Relaciona uma resposta ao nome do preparo e ao modo usado na chamada."""
    return TentativaOCR(nome, leitura.caractere, leitura.bruto, leitura.confianca, psm=psm)


def tentar_preparo_binario(nome: str, imagem: np.ndarray, permitidos: str,
                          psm: int = PSM_CARACTERE_UNICO) -> TentativaOCR:
    """Envia uma máscara individual; o adaptador valida o recorte antes do OCR."""
    leitura = e7_motor_ocr.reconhecer_caractere(imagem, permitidos, psm=psm)
    return registrar_resposta(nome, leitura, psm)


def tentar_preparo_cinza(nome: str, entrada: EntradaCinza,
                        permitidos: str) -> TentativaOCR:
    """A máscara de referência comprova a geometria do recorte em tons de cinza."""
    leitura = e7_motor_ocr.reconhecer_caractere(
        entrada.imagem, permitidos, referencia_binaria=entrada.referencia)
    return registrar_resposta(nome, leitura)


def tentar_escalas_menores(entrada: np.ndarray, permitidos: str) -> list[TentativaOCR]:
    """Testa cada altura nos dois modos, preservando a ordem no histórico."""
    tentativas = []
    for nome, imagem in preparar_escalas(entrada).items():
        for psm in (PSM_CARACTERE_UNICO, PSM_LINHA_CRUA):
            leitura = e7_motor_ocr.reconhecer_caractere(
                imagem, permitidos, psm=psm, referencia_escala=entrada)
            tentativas.append(registrar_resposta(nome, leitura, psm))
    return tentativas
