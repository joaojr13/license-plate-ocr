"""Etapa 5 — separar a região da placa em uma linha de caracteres.

Esta etapa coordena quatro responsabilidades do pacote ``placas.segmentacao``:
produzir máscaras, extrair componentes, encontrar a linha e avaliar alternativas.
Recebe um recorte BGR e devolve uma Segmentacao, inclusive quando faltam letras.
A etapa 4 usa a mesma função para pontuar candidatas, sempre sem consultar OCR.
"""

import numpy as np

from placas.config import LARGURA_NORMALIZADA_PLACA
from placas.modelos import Segmentacao
from placas.segmentacao.alinhamento import selecionar_linha_dominante
from placas.segmentacao.avaliacao import escolher_melhor_segmentacao, pontuar_linha
from placas.segmentacao.binarizacao import gerar_mascaras, preparar_regiao
from placas.segmentacao.componentes import extrair_componentes_plausiveis


def segmentar(placa: np.ndarray) -> Segmentacao:
    """Compara oito máscaras e devolve a melhor linha, ordenada para leitura.

    ``placa`` é uma imagem colorida (BGR), ainda sem normalização. Cada máscara
    representa os possíveis caracteres em branco sobre fundo preto. A escolha
    usa geometria, não o conteúdo das letras; sete componentes não são garantidos.
    Regiões pequenas demais são recusadas antes do processamento.
    """
    normalizada, suave = preparar_regiao(placa)
    alternativas = []

    for metodo, mascara in gerar_mascaras(suave):
        componentes = extrair_componentes_plausiveis(mascara)
        caracteres = selecionar_linha_dominante(componentes)
        qualidade = pontuar_linha(caracteres, LARGURA_NORMALIZADA_PLACA)
        alternativas.append(Segmentacao(normalizada, mascara, caracteres, metodo, qualidade))

    return escolher_melhor_segmentacao(alternativas)
