"""Seleciona quais componentes formam a linha principal da placa.

O alinhamento pode ser horizontal ou inclinado. Cada componente propõe linhas
com seus vizinhos; ganha o grupo mais numeroso com alturas semelhantes.
"""

from placas.config import (
    ALTURA_SEMELHANTE,
    DISTANCIA_MINIMA_ENTRE_VIZINHOS,
    INCLINACAO_MAXIMA_DA_LINHA,
    TOLERANCIA_DE_ALINHAMENTO,
)
from placas.modelos import Box, Caractere


def _centro_da_caixa(caixa: Box) -> tuple[float, float]:
    x, y, largura, altura = caixa
    return x + largura / 2, y + altura / 2


def _inclinacoes_candidatas(
    referencia: Caractere, caracteres: list[Caractere],
) -> list[float]:
    """Propõe coeficientes angulares, sempre incluindo a linha horizontal.

    A inclinação é deslocamento vertical / deslocamento horizontal, não graus.
    Vizinhos distantes e de altura parecida reduzem hipóteses geradas por ruído.
    """
    centro_x, centro_y = _centro_da_caixa(referencia.caixa)
    altura_referencia = referencia.caixa[3]
    inclinacoes = [0.0]
    for outra in caracteres:
        x, y, largura, altura = outra.caixa
        deslocamento_x = x + largura / 2 - centro_x
        if (
            abs(deslocamento_x) >= DISTANCIA_MINIMA_ENTRE_VIZINHOS * altura_referencia
            and ALTURA_SEMELHANTE[0] <= altura / altura_referencia <= ALTURA_SEMELHANTE[1]
        ):
            inclinacao = (y + altura / 2 - centro_y) / deslocamento_x
            if abs(inclinacao) <= INCLINACAO_MAXIMA_DA_LINHA:
                inclinacoes.append(inclinacao)
    return inclinacoes


def _componentes_alinhados(
    caracteres: list[Caractere], referencia: Caractere, inclinacao: float,
) -> list[Caractere]:
    """Agrupa centros próximos da reta proposta, mantendo alturas semelhantes."""
    centro_x, centro_y = _centro_da_caixa(referencia.caixa)
    altura_referencia = referencia.caixa[3]
    grupo = []
    for caractere in caracteres:
        x, y = _centro_da_caixa(caractere.caixa)
        desvio = abs(y - centro_y - inclinacao * (x - centro_x))
        if (
            desvio < altura_referencia * TOLERANCIA_DE_ALINHAMENTO
            and ALTURA_SEMELHANTE[0] <= caractere.caixa[3] / altura_referencia
            <= ALTURA_SEMELHANTE[1]
        ):
            grupo.append(caractere)
    return grupo


def selecionar_linha_dominante(caracteres: list[Caractere]) -> list[Caractere]:
    """Devolve o maior grupo alinhado, ordenado da esquerda para a direita.

    Em empate de quantidade vence o grupo de maior altura somada. Assim a linha
    principal tende a superar dizeres menores. Sem componentes, devolve [].
    """
    if not caracteres:
        return []
    linhas = []
    for referencia in caracteres:
        for inclinacao in _inclinacoes_candidatas(referencia, caracteres):
            linhas.append(_componentes_alinhados(caracteres, referencia, inclinacao))
    linha = max(linhas, key=lambda grupo: (len(grupo), sum(c.caixa[3] for c in grupo)))
    return sorted(linha, key=lambda caractere: caractere.caixa[0])
