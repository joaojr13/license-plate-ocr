"""Etapa 4 — filtrar regiões candidatas e selecionar a provável placa."""
import cv2
import numpy as np

from placas.modelos import Box, ImagemPreparada, Localizacao
from placas.segmentacao import segmentar


def _caixas(mask: np.ndarray, expandir: bool = False) -> list[Box]:
    altura, largura = mask.shape
    contornos, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    caixas = []
    for contorno in sorted(contornos, key=cv2.contourArea, reverse=True)[:250]:
        x, y, w, h = cv2.boundingRect(contorno)
        # Uma faixa de letras tem menos altura que a placa com suas margens.
        altura_minima = 10 if expandir else 18
        if not (2.0 <= w / h <= 6.5 and w >= 70 and h >= altura_minima):
            continue
        if not 0.0008 <= w * h / (largura * altura) <= 0.60:
            continue
        if expandir:
            # O fechamento localiza a faixa das letras; acrescenta margem da placa.
            dx, dy = round(w * 0.06), round(h * 0.35)
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
    for tamanho in [17, 31]:
        for nome in ["Black-hat", "Top-hat"]:
            mascara = morfologia[f"{nome} · Abertura {tamanho}"]
            # Alguns contornos já abrangem a placa inteira; outros só as letras.
            candidatos.extend(_caixas(mascara))
            candidatos.extend(_caixas(mascara, expandir=True))
    melhor = None
    vistos = set()
    for caixa in candidatos:
        if caixa in vistos:
            continue
        vistos.add(caixa)
        x, y, cw, ch = caixa
        segmentacao = segmentar(trabalho[y:y+ch, x:x+cw])
        if len(segmentacao.caracteres) < 4:
            continue
        if melhor is None or segmentacao.qualidade > melhor.segmentacao.qualidade:
            melhor = Localizacao(trabalho, caixa, segmentacao, etapas)
    if melhor is None:
        raise ValueError("Não foi encontrada uma região de placa plausível. "
                         "Use uma foto frontal, nítida e com a placa maior na imagem.")
    return melhor
