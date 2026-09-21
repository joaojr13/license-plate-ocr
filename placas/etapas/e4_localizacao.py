"""Etapa 4 — reunir regiões candidatas e escolher a que mais parece uma placa.

A escolha é feita tentando segmentar cada região (etapa 5) e comparando as
pontuações geométricas resultantes. Nenhuma candidata é enviada ao OCR aqui:
o critério é a forma dos componentes, não o que eles significam.
"""
import cv2
import numpy as np

from placas.config import (ALTURA_MINIMA_CANDIDATA, ALTURA_MINIMA_FAIXA_DE_LETRAS,
                           AREA_RELATIVA_CANDIDATA, LARGURA_MINIMA_CANDIDATA,
                           MARGEM_EXTRA_HORIZONTAL, MARGEM_EXTRA_VERTICAL,
                           MAXIMO_CANDIDATAS_EXIBIDAS, MAXIMO_CONTORNOS,
                           MINIMO_COMPONENTES_CANDIDATA, OPERACOES_MORFOLOGIA,
                           PROPORCAO_CANDIDATA, SOBREPOSICAO_MAXIMA_EXIBIDA,
                           TAMANHOS_KERNEL_MORFOLOGIA)
from placas.etapas.e3_morfologia import nome_da_etapa
from placas.etapas.e5_segmentacao import segmentar
from placas.modelos import Box, CandidataPlaca, ImagemPreparada, Localizacao, Segmentacao

# Alguns contornos já abrangem a placa inteira; outros, só a faixa das letras.
MARGENS_DA_CANDIDATA = ((False, "Sem margem extra"), (True, "Com margem extra"))


def nome_da_fonte(operacao: str, tamanho: int, tipo: str) -> str:
    """Rótulo da origem de um grupo de regiões; a página usa o mesmo texto."""
    return f'{operacao} {tamanho} · {tipo}'


# --- 4a · Encontrar retângulos plausíveis em uma máscara ---------------------


def _passa_nos_filtros(w: int, h: int, largura: int, altura: int, expandir: bool) -> bool:
    """Proporção, tamanho mínimo e fração da imagem compatíveis com uma placa."""
    # Uma faixa de letras tem menos altura que a placa com suas margens.
    altura_minima = ALTURA_MINIMA_FAIXA_DE_LETRAS if expandir else ALTURA_MINIMA_CANDIDATA
    if not (PROPORCAO_CANDIDATA[0] <= w / h <= PROPORCAO_CANDIDATA[1]
            and w >= LARGURA_MINIMA_CANDIDATA and h >= altura_minima):
        return False
    area_relativa = w * h / (largura * altura)
    return AREA_RELATIVA_CANDIDATA[0] <= area_relativa <= AREA_RELATIVA_CANDIDATA[1]


def _com_margem_da_placa(caixa: Box, largura: int, altura: int) -> Box:
    """O fechamento localiza a faixa das letras; acrescenta a margem da placa."""
    x, y, w, h = caixa
    dx, dy = round(w * MARGEM_EXTRA_HORIZONTAL), round(h * MARGEM_EXTRA_VERTICAL)
    x1, y1 = max(0, x - dx), max(0, y - dy)
    x2, y2 = min(largura, x + w + dx), min(altura, y + h + dy)
    return x1, y1, x2 - x1, y2 - y1


def _caixas(mascara: np.ndarray, expandir: bool = False) -> list[Box]:
    """Retângulos dos maiores contornos da máscara que passam nos filtros."""
    altura, largura = mascara.shape
    contornos, _ = cv2.findContours(mascara, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    maiores = sorted(contornos, key=cv2.contourArea, reverse=True)[:MAXIMO_CONTORNOS]
    caixas = []
    for contorno in maiores:
        x, y, w, h = cv2.boundingRect(contorno)
        if not _passa_nos_filtros(w, h, largura, altura, expandir):
            continue
        caixas.append(_com_margem_da_placa((x, y, w, h), largura, altura) if expandir
                      else (x, y, w, h))
    return caixas


# --- 4b · Reunir as regiões vindas de todas as fontes ------------------------


def _caixas_por_fonte(morfologia: dict[str, np.ndarray]) -> dict[str, list[Box]]:
    """Regiões agrupadas pela operação e margem que as produziram.

    Preserva a origem antes da união entre operações e remove apenas
    duplicatas exatas, para desenhar as regiões de uma mesma fonte uma vez.
    """
    por_fonte = {}
    for tamanho in TAMANHOS_KERNEL_MORFOLOGIA:
        for operacao in OPERACOES_MORFOLOGIA:
            mascara = morfologia[nome_da_etapa(operacao, tamanho, "Abertura")]
            for expandir, tipo in MARGENS_DA_CANDIDATA:
                caixas = _caixas(mascara, expandir=expandir)
                por_fonte[nome_da_fonte(operacao, tamanho, tipo)] = list(dict.fromkeys(caixas))
    return por_fonte


def _reunir_candidatas(bordas: np.ndarray, por_fonte: dict[str, list[Box]]) -> list[Box]:
    """Bordas primeiro, depois a morfologia; cada caixa é avaliada uma só vez."""
    caixas = _caixas(bordas)
    for regioes in por_fonte.values():
        caixas.extend(regioes)
    return list(dict.fromkeys(caixas))


# --- 4c · Escolher a melhor região, segmentando cada uma ---------------------


def _segmentar_regiao(trabalho: np.ndarray, caixa: Box) -> Segmentacao:
    x, y, w, h = caixa
    return segmentar(trabalho[y:y+h, x:x+w])


def _escolher_melhor(trabalho: np.ndarray, caixas: list[Box],
                     etapas: dict[str, np.ndarray]
                     ) -> tuple[Localizacao | None, list[CandidataPlaca]]:
    """Segmenta cada região como hipótese e fica com a de maior pontuação."""
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


# --- 4d · Reduzir a lista para a galeria da página ---------------------------


def _sobreposicao(a: Box, b: Box) -> float:
    """Área em comum dividida pela área total das duas caixas (IoU)."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    intersecao = max(0, min(ax+aw, bx+bw)-max(ax, bx)) * max(0, min(ay+ah, by+bh)-max(ay, by))
    return intersecao / (aw*ah + bw*bh - intersecao)


def candidatas_para_exibir(candidatas: list[CandidataPlaca], escolhida: Box) -> list[CandidataPlaca]:
    """Reduz sobreposição apenas na visualização; não altera a seleção da placa."""
    ordenadas = sorted(candidatas, key=lambda c: (c.caixa == escolhida, c.qualidade), reverse=True)
    distintas = []
    for candidata in ordenadas:
        if all(_sobreposicao(candidata.caixa, outra.caixa) < SOBREPOSICAO_MAXIMA_EXIBIDA
               for outra in distintas):
            distintas.append(candidata)
        if len(distintas) == MAXIMO_CANDIDATAS_EXIBIDAS:
            break
    return distintas


# --- A etapa 4, em cinco passos ---------------------------------------------


def selecionar_placa(preparada: ImagemPreparada, bordas: np.ndarray,
                     morfologia: dict[str, np.ndarray]) -> Localizacao:
    """Avalia candidatas usando a etapa 5 e devolve a melhor região já segmentada.

    A segmentação é uma hipótese por candidata; não há OCR nessa seleção.
    """
    etapas = {"Cinza": preparada.cinza, "Suavização": preparada.suave, "Bordas": bordas}
    etapas.update(morfologia)
    por_fonte = _caixas_por_fonte(morfologia)
    candidatas = _reunir_candidatas(bordas, por_fonte)
    melhor, avaliadas = _escolher_melhor(preparada.imagem, candidatas, etapas)
    if melhor is None:
        raise ValueError("Não foi encontrada uma região de placa plausível. "
                         "Use uma foto frontal, nítida e com a placa maior na imagem.")
    melhor.candidatas = candidatas_para_exibir(avaliadas, melhor.caixa)
    melhor.total_candidatas = len(avaliadas)
    melhor.candidatas_morfologia = por_fonte
    return melhor
