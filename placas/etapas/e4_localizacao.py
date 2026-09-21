"""Etapa 4 — filtrar regiões candidatas e selecionar a provável placa."""
import cv2
import numpy as np

from placas.config import (ALTURA_MINIMA_CANDIDATA, ALTURA_MINIMA_FAIXA_DE_LETRAS,
                           AREA_RELATIVA_CANDIDATA, LARGURA_MINIMA_CANDIDATA,
                           MARGEM_EXTRA_HORIZONTAL, MARGEM_EXTRA_VERTICAL,
                           MAXIMO_CANDIDATAS_EXIBIDAS, MAXIMO_CONTORNOS,
                           MINIMO_COMPONENTES_CANDIDATA, OPERACOES_MORFOLOGIA,
                           PROPORCAO_CANDIDATA, SOBREPOSICAO_MAXIMA_EXIBIDA,
                           TAMANHOS_KERNEL_MORFOLOGIA)
from placas.modelos import Box, CandidataPlaca, ImagemPreparada, Localizacao
from placas.etapas.e5_segmentacao import segmentar


def _sobreposicao(a: Box, b: Box) -> float:
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


def _caixas(mask: np.ndarray, expandir: bool = False) -> list[Box]:
    altura, largura = mask.shape
    contornos, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    caixas = []
    for contorno in sorted(contornos, key=cv2.contourArea, reverse=True)[:MAXIMO_CONTORNOS]:
        x, y, w, h = cv2.boundingRect(contorno)
        # Uma faixa de letras tem menos altura que a placa com suas margens.
        altura_minima = (ALTURA_MINIMA_FAIXA_DE_LETRAS if expandir
                         else ALTURA_MINIMA_CANDIDATA)
        if not (PROPORCAO_CANDIDATA[0] <= w / h <= PROPORCAO_CANDIDATA[1]
                and w >= LARGURA_MINIMA_CANDIDATA and h >= altura_minima):
            continue
        area_relativa = w * h / (largura * altura)
        if not AREA_RELATIVA_CANDIDATA[0] <= area_relativa <= AREA_RELATIVA_CANDIDATA[1]:
            continue
        if expandir:
            # O fechamento localiza a faixa das letras; acrescenta margem da placa.
            dx = round(w * MARGEM_EXTRA_HORIZONTAL)
            dy = round(h * MARGEM_EXTRA_VERTICAL)
            x1, y1 = max(0, x-dx), max(0, y-dy)
            x2, y2 = min(largura, x+w+dx), min(altura, y+h+dy)
            x, y, w, h = x1, y1, x2-x1, y2-y1
        caixas.append((x, y, w, h))
    return caixas


def selecionar_placa(preparada: ImagemPreparada, bordas: np.ndarray,
                     morfologia: dict[str, np.ndarray]) -> Localizacao:
    """Avalia candidatas usando a etapa 5 e devolve a melhor região já segmentada.

    A segmentação é uma hipótese por candidata; não há OCR nessa seleção.
    """
    trabalho = preparada.imagem
    etapas = {"Cinza": preparada.cinza, "Suavização": preparada.suave, "Bordas": bordas}
    etapas.update(morfologia)
    candidatos = _caixas(bordas)
    candidatas_morfologia = {}
    for tamanho in TAMANHOS_KERNEL_MORFOLOGIA:
        for nome in OPERACOES_MORFOLOGIA:
            mascara = morfologia[f"{nome} · Abertura {tamanho}"]
            # Alguns contornos já abrangem a placa inteira; outros só as letras.
            for expandir, tipo in [(False, 'Sem margem extra'), (True, 'Com margem extra')]:
                caixas = _caixas(mascara, expandir=expandir)
                candidatos.extend(caixas)
                # Preserva a origem antes da união entre operações. Remove apenas
                # duplicatas exatas para desenhar as regiões da mesma fonte uma vez.
                candidatas_morfologia[f'{nome} {tamanho} · {tipo}'] = list(dict.fromkeys(caixas))
    melhor = None
    avaliadas = []
    vistos = set()
    for caixa in candidatos:
        if caixa in vistos:
            continue
        vistos.add(caixa)
        x, y, cw, ch = caixa
        segmentacao = segmentar(trabalho[y:y+ch, x:x+cw])
        avaliadas.append(CandidataPlaca(caixa, segmentacao.qualidade,
                                        len(segmentacao.caracteres), segmentacao.metodo))
        if len(segmentacao.caracteres) < MINIMO_COMPONENTES_CANDIDATA:
            continue
        if melhor is None or segmentacao.qualidade > melhor.segmentacao.qualidade:
            melhor = Localizacao(trabalho, caixa, segmentacao, etapas)
    if melhor is None:
        raise ValueError("Não foi encontrada uma região de placa plausível. "
                         "Use uma foto frontal, nítida e com a placa maior na imagem.")
    melhor.candidatas = candidatas_para_exibir(avaliadas, melhor.caixa)
    melhor.total_candidatas = len(avaliadas)
    melhor.candidatas_morfologia = candidatas_morfologia
    return melhor
