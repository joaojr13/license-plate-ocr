"""Compara a geometria das linhas e escolhe a alternativa de segmentação.

A pontuação mede quantidade, uniformidade, alinhamento e ocupação horizontal.
Ela é uma heurística, não uma probabilidade nem uma leitura dos caracteres.
"""

import numpy as np

from placas.config import (
    INCLINACAO_MAXIMA_DA_LINHA,
    MINIMO_PARA_AJUSTAR_A_LINHA,
    PESO_ALINHAMENTO,
    PESO_ALTURA,
    PESO_OCUPACAO,
    PESO_QUANTIDADE,
    PONTUACAO_BASE,
    PONTUACAO_SEM_CARACTERES,
    TOLERANCIA_DE_DESEMPATE,
    TOLERANCIA_DE_POSICAO_NO_DESEMPATE,
    TOTAL_CARACTERES,
)
from placas.modelos import Caractere, Segmentacao
from placas.segmentacao.binarizacao import LIMIARIZACOES, SEM_ABERTURA, nome_do_metodo


def _desvios_da_linha(caracteres: list[Caractere]) -> np.ndarray:
    """Mede as diferenças verticais entre centros e a reta ajustada a eles.

    Subtrair a tendência da reta evita penalizar uma placa inteira inclinada.
    Sem pontos suficientes, ou com inclinação excessiva, conserva os centros
    originais para avaliar sua dispersão vertical.
    """
    centros_y = np.array([c.caixa[1] + c.caixa[3] / 2 for c in caracteres])
    if len(caracteres) < MINIMO_PARA_AJUSTAR_A_LINHA:
        return centros_y
    centros_x = np.array([c.caixa[0] + c.caixa[2] / 2 for c in caracteres])
    coeficientes = np.polyfit(centros_x, centros_y, 1)
    if abs(coeficientes[0]) > INCLINACAO_MAXIMA_DA_LINHA:
        return centros_y
    return centros_y - np.polyval(coeficientes, centros_x)


def pontuar_linha(caracteres: list[Caractere], largura_placa: int) -> float:
    """Pontua uma lista já ordenada, premiando sete componentes e boa geometria.

    As dispersões são divididas pela altura média para comparar diferentes
    tamanhos. ``largura_placa`` normaliza a ocupação horizontal da linha.
    Uma lista vazia recebe a pontuação reservada às regiões sem caracteres.
    """
    if not caracteres:
        return PONTUACAO_SEM_CARACTERES
    alturas = np.array([c.caixa[3] for c in caracteres])
    desvios = _desvios_da_linha(caracteres)
    inicio = caracteres[0].caixa[0]
    fim = caracteres[-1].caixa[0] + caracteres[-1].caixa[2]

    # std() mede dispersão; mean() fornece a altura média usada como referência.
    penalidade_quantidade = PESO_QUANTIDADE * abs(TOTAL_CARACTERES - len(caracteres))
    penalidade_altura = PESO_ALTURA * alturas.std() / alturas.mean()
    penalidade_alinhamento = PESO_ALINHAMENTO * desvios.std() / alturas.mean()
    bonus_ocupacao = PESO_OCUPACAO * (fim - inicio) / largura_placa
    return float(
        PONTUACAO_BASE - penalidade_quantidade - penalidade_altura
        - penalidade_alinhamento + bonus_ocupacao
    )


def _mesma_polaridade(a: Segmentacao, b: Segmentacao) -> bool:
    return a.metodo.split(" · ")[-1] == b.metodo.split(" · ")[-1]


def _mesmas_posicoes(a: Segmentacao, b: Segmentacao) -> bool:
    """Compara os centros horizontais de duas listas com a mesma quantidade."""
    return all(
        abs((x.caixa[0] + x.caixa[2] / 2) - (y.caixa[0] + y.caixa[2] / 2))
        <= min(x.caixa[2], y.caixa[2]) * TOLERANCIA_DE_POSICAO_NO_DESEMPATE
        for x, y in zip(a.caracteres, b.caracteres)
    )


def escolher_melhor_segmentacao(alternativas: list[Segmentacao]) -> Segmentacao:
    """Escolhe a maior pontuação; num empate aproximado, prefere Otsu sem abertura.

    Recebe uma lista não vazia na ordem de geração das máscaras. O desempate
    compara somente sete componentes, mesma polaridade e mesmas posições.
    Isso preserva traços que o adaptativo pode apagar sem mudar muito a geometria.
    """
    melhor = max(alternativas, key=lambda segmentacao: segmentacao.qualidade)
    otsu_simples = nome_do_metodo(LIMIARIZACOES[0], SEM_ABERTURA, "")
    for alternativa in alternativas:
        if (
            len(melhor.caracteres) == len(alternativa.caracteres) == TOTAL_CARACTERES
            and alternativa.metodo.startswith(otsu_simples)
            and _mesma_polaridade(alternativa, melhor)
            and melhor.qualidade - alternativa.qualidade <= TOLERANCIA_DE_DESEMPATE
            and _mesmas_posicoes(alternativa, melhor)
        ):
            return alternativa
    return melhor
