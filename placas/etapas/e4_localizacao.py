"""Etapa 4 — comparar as regiões propostas usando seus componentes.

Entrada: fotografia preparada e máscaras das etapas 2 e 3.
Saída: região escolhida, seus caracteres e dados de inspeção.
Esta etapa chama a segmentação para avaliar cada hipótese, sem consultar OCR.
"""
import numpy as np

from placas.config import MINIMO_COMPONENTES_CANDIDATA
from placas.etapas.e5_segmentacao import segmentar
from placas.localizacao.candidatas import agrupar_por_fonte, reunir_candidatas
from placas.modelos import Box, CandidataPlaca, ImagemPreparada, Localizacao, Segmentacao
from placas.saida.galeria import candidatas_para_exibir


# --- 4c · Escolher a melhor região, segmentando cada uma ---------------------


def _segmentar_regiao(trabalho: np.ndarray, caixa: Box) -> Segmentacao:
    """Recorta a fotografia por linhas (y) e colunas (x) e chama a etapa 5."""
    x, y, largura, altura = caixa
    recorte = trabalho[y:y + altura, x:x + largura]
    return segmentar(recorte)


def _escolher_melhor(trabalho: np.ndarray, caixas: list[Box],
                     etapas: dict[str, np.ndarray]
                     ) -> tuple[Localizacao | None, list[CandidataPlaca]]:
    """Segmenta cada região como hipótese e fica com a de maior pontuação.

    Quatro componentes permitem disputar a localização. Sete são exigidos
    depois, antes do OCR. Em empate, preserva a primeira candidata encontrada.
    """
    melhor = None
    avaliadas = []
    for caixa in caixas:
        segmentacao = _segmentar_regiao(trabalho, caixa)
        avaliadas.append(CandidataPlaca(caixa, segmentacao.qualidade,
                                        len(segmentacao.caracteres), segmentacao.metodo))
        if len(segmentacao.caracteres) < MINIMO_COMPONENTES_CANDIDATA:
            continue
        if melhor is None or segmentacao.qualidade > melhor.segmentacao.qualidade:
            melhor = Localizacao(trabalho, caixa, segmentacao, etapas)
    return melhor, avaliadas


def selecionar_placa(preparada: ImagemPreparada, bordas: np.ndarray,
                     morfologia: dict[str, np.ndarray]) -> Localizacao:
    """Avalia candidatas usando a etapa 5 e devolve a melhor região já segmentada.

    A segmentação é uma hipótese por candidata; não há OCR nessa seleção.
    """
    etapas = {"Cinza": preparada.cinza, "Suavização": preparada.suave, "Bordas": bordas}
    etapas.update(morfologia)
    por_fonte = agrupar_por_fonte(morfologia)
    candidatas = reunir_candidatas(bordas, por_fonte)
    melhor, avaliadas = _escolher_melhor(preparada.imagem, candidatas, etapas)
    if melhor is None:
        raise ValueError("Não foi encontrada uma região de placa plausível. "
                         "Use uma foto frontal, nítida e com a placa maior na imagem.")
    melhor.candidatas = candidatas_para_exibir(avaliadas, melhor.caixa)
    melhor.total_candidatas = len(avaliadas)
    melhor.candidatas_morfologia = por_fonte
    return melhor
