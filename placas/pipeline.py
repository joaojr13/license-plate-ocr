"""O mapa do fluxo: as oito etapas, na ordem, e quem chama quem.

Leia este arquivo primeiro. Cada chamada leva ao módulo da etapa
correspondente em placas/etapas/, e nenhuma decisão é tomada aqui: este
arquivo só diz a ordem. A interface pode parar depois de localizar(), para
inspecionar os recortes sem executar o OCR.
"""
import numpy as np

from placas.config import NOME_DO_MOTOR
from placas.etapas.e1_preparacao import preparar_imagem
from placas.etapas.e2_bordas import encontrar_bordas
from placas.etapas.e3_morfologia import aplicar_morfologia
from placas.etapas.e4_localizacao import selecionar_placa
from placas.etapas.e6_recortes import preparar_recortes
from placas.etapas.e8_resultado import consolidar_resultado
from placas.modelos import Localizacao, Segmentacao
from placas.reconhecimento.fluxo import reconhecer_entradas


def localizar(imagem: np.ndarray) -> Localizacao:
    """Etapas 1 a 5: da foto até os caracteres separados. Sem acesso ao OCR."""
    preparada = preparar_imagem(imagem)                     # 1 · Preparação
    bordas = encontrar_bordas(preparada.suave)              # 2 · Bordas
    morfologia = aplicar_morfologia(preparada.suave)        # 3 · Morfologia
    return selecionar_placa(preparada, bordas, morfologia)  # 4 · Seleção + 5 · Segmentação


def reconhecer(segmentacao: Segmentacao, formato: str = "livre") -> dict:
    """Etapas 6 a 8: só pode rodar depois que existe uma segmentação válida."""
    entradas = preparar_recortes(segmentacao)                          # 6 · Recortes
    leituras = reconhecer_entradas(entradas, segmentacao, formato)       # 7 · OCR individual
    resultado = consolidar_resultado(leituras, formato)                 # 8 · Arrays e avisos
    resultado["motor"] = NOME_DO_MOTOR
    return resultado
