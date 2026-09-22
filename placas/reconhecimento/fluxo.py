"""Coordena as três representações usadas no reconhecimento individual.

A preparação binária já foi feita pela etapa 6. Primeiro reconhecemos esses
recortes; para os '?' tentamos tons de cinza e, por último, escalas menores.
As regras de aceitação pertencem à etapa 7, não a este coordenador.
"""
import numpy as np

from placas.etapas import e7_decisao, e7_motor_ocr
from placas.etapas.e6_recortes import preparar_cinza
from placas.modelos import Leitura, Segmentacao


def _recuperar_em_cinza(leituras: list[Leitura], segmentacao: Segmentacao,
                        formato: str) -> list[Leitura]:
    """Só prepara as imagens em cinza se alguma leitura continuar incerta."""
    if not any(leitura.caractere == "?" for leitura in leituras):
        return leituras
    recortes_em_cinza = preparar_cinza(segmentacao)
    recuperadas = []
    for indice, leitura in enumerate(leituras):
        permitidos = e7_motor_ocr.alfabeto_por_posicao(indice, formato)
        recuperada = e7_decisao.recuperar_com_cinza(
            leitura, recortes_em_cinza[indice], permitidos)
        recuperadas.append(recuperada)
    return recuperadas


def _recuperar_em_escalas(leituras: list[Leitura], entradas: list[np.ndarray],
                          formato: str) -> list[Leitura]:
    """Reutiliza o recorte individual padrão; leituras aceitas passam sem novas chamadas."""
    recuperadas = []
    for indice, (leitura, entrada) in enumerate(zip(leituras, entradas)):
        permitidos = e7_motor_ocr.alfabeto_por_posicao(indice, formato)
        recuperada = e7_decisao.recuperar_com_escalas(leitura, entrada, permitidos)
        recuperadas.append(recuperada)
    return recuperadas


def reconhecer_entradas(entradas: list[np.ndarray], segmentacao: Segmentacao,
                         formato: str) -> list[Leitura]:
    """Devolve sete leituras na ordem original, cada uma com seu histórico.

    A segmentação serve apenas para preparar os recortes em cinza. Nenhuma
    fotografia ou placa completa é passada ao adaptador do Tesseract.
    """
    leituras = e7_decisao.reconhecer_caracteres(entradas, formato)
    leituras = _recuperar_em_cinza(leituras, segmentacao, formato)
    return _recuperar_em_escalas(leituras, entradas, formato)
