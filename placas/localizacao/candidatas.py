"""Transforma máscaras em retângulos plausíveis, sem segmentar ou reconhecer.

As caixas estão nas coordenadas da fotografia preparada. Os filtros de
tamanho e proporção reduzem a busca; não comprovam que a região seja placa.
"""
import cv2
import numpy as np

from placas.config import (ALTURA_MINIMA_CANDIDATA, ALTURA_MINIMA_FAIXA_DE_LETRAS,
                           AREA_RELATIVA_CANDIDATA, LARGURA_MINIMA_CANDIDATA,
                           MARGEM_EXTRA_HORIZONTAL, MARGEM_EXTRA_VERTICAL,
                           MAXIMO_CONTORNOS, OPERACOES_MORFOLOGIA, PROPORCAO_CANDIDATA,
                           TAMANHOS_KERNEL_MORFOLOGIA)
from placas.etapas.e3_morfologia import nome_da_etapa
from placas.modelos import Box

# Alguns contornos já abrangem a placa inteira; outros, só a faixa das letras.
MARGENS_DA_CANDIDATA = ((False, "Sem margem extra"), (True, "Com margem extra"))


def nome_da_fonte(operacao: str, tamanho: int, tipo: str) -> str:
    """Rótulo da origem de um grupo de regiões; a página usa o mesmo texto."""
    return f'{operacao} {tamanho} · {tipo}'


# --- 4a · Encontrar retângulos plausíveis em uma máscara ---------------------


def _passa_nos_filtros(largura: int, altura: int, largura_foto: int,
                       altura_foto: int, expandir: bool) -> bool:
    """Proporção, tamanho mínimo e fração da imagem compatíveis com uma placa."""
    # Uma faixa de letras tem menos altura que a placa com suas margens.
    altura_minima = ALTURA_MINIMA_FAIXA_DE_LETRAS if expandir else ALTURA_MINIMA_CANDIDATA
    if not (PROPORCAO_CANDIDATA[0] <= largura / altura <= PROPORCAO_CANDIDATA[1]
            and largura >= LARGURA_MINIMA_CANDIDATA and altura >= altura_minima):
        return False
    area_relativa = largura * altura / (largura_foto * altura_foto)
    return AREA_RELATIVA_CANDIDATA[0] <= area_relativa <= AREA_RELATIVA_CANDIDATA[1]


def _com_margem_da_placa(caixa: Box, largura_foto: int, altura_foto: int) -> Box:
    """Acrescenta margem à possível faixa das letras, sem sair da fotografia."""
    x, y, largura, altura = caixa
    margem_x = round(largura * MARGEM_EXTRA_HORIZONTAL)
    margem_y = round(altura * MARGEM_EXTRA_VERTICAL)
    esquerda, topo = max(0, x - margem_x), max(0, y - margem_y)
    direita = min(largura_foto, x + largura + margem_x)
    base = min(altura_foto, y + altura + margem_y)
    return esquerda, topo, direita - esquerda, base - topo


def encontrar_caixas(mascara: np.ndarray, expandir: bool = False) -> list[Box]:
    """Retângulos dos maiores contornos da máscara que passam nos filtros."""
    altura_foto, largura_foto = mascara.shape
    contornos, _ = cv2.findContours(mascara, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    maiores = sorted(contornos, key=cv2.contourArea, reverse=True)[:MAXIMO_CONTORNOS]
    caixas = []
    for contorno in maiores:
        x, y, largura, altura = cv2.boundingRect(contorno)
        if not _passa_nos_filtros(largura, altura, largura_foto, altura_foto, expandir):
            continue
        caixa = (x, y, largura, altura)
        if expandir:
            caixa = _com_margem_da_placa(caixa, largura_foto, altura_foto)
        caixas.append(caixa)
    return caixas


# --- 4b · Reunir as regiões vindas de todas as fontes ------------------------


def agrupar_por_fonte(morfologia: dict[str, np.ndarray]) -> dict[str, list[Box]]:
    """Regiões agrupadas pela operação e margem que as produziram.

    Preserva a origem antes da união entre operações e remove apenas
    duplicatas exatas, para desenhar as regiões de uma mesma fonte uma vez.
    """
    por_fonte = {}
    for tamanho in TAMANHOS_KERNEL_MORFOLOGIA:
        for operacao in OPERACOES_MORFOLOGIA:
            mascara = morfologia[nome_da_etapa(operacao, tamanho, "Abertura")]
            for expandir, tipo in MARGENS_DA_CANDIDATA:
                caixas = encontrar_caixas(mascara, expandir=expandir)
                # Elimina caixas idênticas mantendo a ordem em que foram encontradas.
                por_fonte[nome_da_fonte(operacao, tamanho, tipo)] = list(dict.fromkeys(caixas))
    return por_fonte


def reunir_candidatas(bordas: np.ndarray, por_fonte: dict[str, list[Box]]) -> list[Box]:
    """Bordas primeiro, depois a morfologia; cada caixa é avaliada uma só vez."""
    caixas = encontrar_caixas(bordas)
    for regioes in por_fonte.values():
        caixas.extend(regioes)
    return list(dict.fromkeys(caixas))
