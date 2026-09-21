"""O mapa do fluxo: as oito etapas, na ordem, e quem chama quem.

Leia este arquivo primeiro. Cada chamada leva ao módulo da etapa
correspondente em placas/etapas/, e nenhuma decisão é tomada aqui: este
arquivo só diz a ordem. A interface pode parar depois de localizar(), para
inspecionar os recortes sem executar o OCR.
"""
import numpy as np

from placas.config import NOME_DO_MOTOR
from placas.etapas import e7_decisao, e7_motor_ocr
from placas.etapas.e1_preparacao import preparar_imagem
from placas.etapas.e2_bordas import encontrar_bordas
from placas.etapas.e3_morfologia import aplicar_morfologia
from placas.etapas.e4_localizacao import selecionar_placa
from placas.etapas.e6_recortes import preparar_cinza, preparar_recortes
from placas.etapas.e8_resultado import consolidar_resultado
from placas.modelos import Leitura, Localizacao, Segmentacao


def localizar(imagem: np.ndarray) -> Localizacao:
    """Etapas 1 a 5: da foto até os caracteres separados. Sem acesso ao OCR."""
    preparada = preparar_imagem(imagem)                     # 1 · Preparação
    bordas = encontrar_bordas(preparada.suave)              # 2 · Bordas
    morfologia = aplicar_morfologia(preparada.suave)        # 3 · Morfologia
    return selecionar_placa(preparada, bordas, morfologia)  # 4 · Seleção + 5 · Segmentação


def reconhecer(segmentacao: Segmentacao, formato: str = "livre") -> dict:
    """Etapas 6 a 8: só pode rodar depois que existe uma segmentação válida."""
    entradas = preparar_recortes(segmentacao)                       # 6 · Recortes
    leituras = e7_decisao.reconhecer_caracteres(entradas, formato)  # 7 · OCR individual
    leituras = _recuperar_incertas(leituras, segmentacao, formato)  # 7b · Tons de cinza
    leituras = [e7_decisao.recuperar_com_escalas(
        leitura, entrada, e7_motor_ocr.alfabeto_por_posicao(i, formato))
        for i, (leitura, entrada) in enumerate(zip(leituras, entradas))]
    resultado = consolidar_resultado(leituras, formato)             # 8 · Arrays e avisos
    resultado["motor"] = NOME_DO_MOTOR
    return resultado


def _recuperar_incertas(leituras: list[Leitura], segmentacao: Segmentacao,
                        formato: str) -> list[Leitura]:
    """Segunda chance apenas para os '?', usando o recorte em tons de cinza.

    Só recorta a placa de novo se alguma posição ficou sem resposta; quando
    as sete leituras foram aceitas, nenhuma chamada extra ao OCR acontece.
    """
    if not any(leitura.caractere == "?" for leitura in leituras):
        return leituras
    cinzas = preparar_cinza(segmentacao)
    return [e7_decisao.recuperar_com_cinza(
                leitura, cinzas[indice],
                e7_motor_ocr.alfabeto_por_posicao(indice, formato))
            for indice, leitura in enumerate(leituras)]
