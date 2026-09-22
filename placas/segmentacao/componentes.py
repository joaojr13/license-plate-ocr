"""Extrai símbolos candidatos de uma máscara, antes de verificar a linha.

Componente conectado é um conjunto de pixels brancos ligados entre si, inclusive
pelas diagonais. Ele ainda pode ser um parafuso ou uma borda, por isso o tamanho,
a proporção e o preenchimento precisam passar por filtros geométricos.
"""

import cv2
import numpy as np

from placas.config import (
    ALTURA_RELATIVA_COMPONENTE,
    LARGURA_RELATIVA_COMPONENTE,
    MARGEM_BORDA_COMPONENTE,
    PREENCHIMENTO_COMPONENTE,
    PROPORCAO_COMPONENTE,
)
from placas.modelos import Caractere


def _tem_geometria_de_caractere(
    largura: int, altura: int, area: int, largura_placa: int, altura_placa: int,
) -> bool:
    """Filtra dizeres pequenos, ruídos e regiões largas com símbolos unidos.

    ``area`` conta pixels brancos; largura × altura inclui também espaços vazios.
    A razão entre eles mede quanto o componente preenche sua caixa.
    """
    return (
        ALTURA_RELATIVA_COMPONENTE[0] <= altura / altura_placa
        <= ALTURA_RELATIVA_COMPONENTE[1]
        and LARGURA_RELATIVA_COMPONENTE[0] <= largura / largura_placa
        <= LARGURA_RELATIVA_COMPONENTE[1]
        and PROPORCAO_COMPONENTE[0] <= largura / altura <= PROPORCAO_COMPONENTE[1]
        and PREENCHIMENTO_COMPONENTE[0] <= area / (largura * altura)
        <= PREENCHIMENTO_COMPONENTE[1]
    )


def _encosta_na_borda(
    x: int, y: int, largura: int, altura: int, largura_placa: int, altura_placa: int,
) -> bool:
    """Indica se a caixa toca o limite da região, sugerindo borda ou corte."""
    margem = MARGEM_BORDA_COMPONENTE
    return (
        x <= margem or y <= margem
        or x + largura >= largura_placa - margem
        or y + altura >= altura_placa - margem
    )


def extrair_componentes_plausiveis(binaria: np.ndarray) -> list[Caractere]:
    """Devolve caixas e máscaras isoladas dos componentes geometricamente válidos.

    A entrada contém branco no primeiro plano e preto no fundo. A máscara de
    saída de cada Caractere guarda somente seu componente, mesmo que a caixa
    envolva pixels pertencentes a outro componente. A lista ainda não está
    agrupada em linha nem ordenada para leitura.
    """
    altura_placa, largura_placa = binaria.shape
    total, rotulos, medidas, _ = cv2.connectedComponentsWithStats(binaria, 8)
    caracteres = []
    for indice in range(1, total):  # O rótulo 0 identifica o fundo.
        x, y, largura, altura, area = map(int, medidas[indice])
        if not _tem_geometria_de_caractere(
            largura, altura, area, largura_placa, altura_placa,
        ):
            continue
        if _encosta_na_borda(x, y, largura, altura, largura_placa, altura_placa):
            continue
        rotulos_no_recorte = rotulos[y:y + altura, x:x + largura]
        mascara = np.uint8(rotulos_no_recorte == indice) * 255
        caracteres.append(Caractere((x, y, largura, altura), mascara))
    return caracteres
