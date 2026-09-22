"""Agrupa regiões parecidas apenas para exibição; não altera a escolha da placa."""
from placas.config import MAXIMO_CANDIDATAS_EXIBIDAS, SOBREPOSICAO_MAXIMA_EXIBIDA
from placas.modelos import Box, CandidataPlaca


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
