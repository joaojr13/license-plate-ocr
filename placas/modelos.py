"""Vocabulário de dados do algoritmo; estas classes não executam processamento.

Uma dataclass reúne campos relacionados sem esconder lógica. Imagens são
matrizes NumPy: imagem[y, x] acessa uma linha e uma coluna. Caixa é uma tupla
(x, y, largura, altura), medida em pixels na imagem indicada pelo contexto.
"""
from dataclasses import dataclass, field

import numpy as np

from placas.config import NOME_DO_MOTOR, PSM_CARACTERE_UNICO

Box = tuple[int, int, int, int]  # x, y, largura, altura


@dataclass
class ImagemPreparada:
    """Etapa 1: a mesma foto colorida, em cinza e suavizada, na escala de trabalho."""
    imagem: np.ndarray
    cinza: np.ndarray
    suave: np.ndarray


@dataclass
class Caractere:
    """Componente candidato a símbolo, ainda sem letra atribuída pelo OCR.

    caixa usa coordenadas da placa normalizada; mascara contém apenas esse
    componente dentro da caixa (branco 255 sobre fundo preto 0).
    """
    caixa: Box
    mascara: np.ndarray  # Somente este componente: branco em fundo preto.


@dataclass
class Segmentacao:
    """Uma hipótese da etapa 5: placa normalizada, máscara e linha de componentes.

    qualidade é uma pontuação geométrica, não confiança do OCR. Uma hipótese
    pode ter menos de sete caracteres e, nesse caso, não está pronta para OCR.
    """
    placa: np.ndarray
    binaria: np.ndarray
    caracteres: list[Caractere]
    metodo: str
    qualidade: float


@dataclass
class CandidataPlaca:
    """Resumo para comparar regiões; caixa está nas coordenadas da fotografia."""
    caixa: Box
    qualidade: float
    quantidade_caracteres: int
    metodo: str


@dataclass
class Localizacao:
    """Resultado das etapas 1–5, incluindo evidências para explicar a escolha.

    caixa está em imagem (foto de trabalho). Os caracteres, por sua vez, estão
    em segmentacao.placa (recorte redimensionado): são coordenadas diferentes.
    etapas guarda imagens intermediárias apenas para inspeção.
    """
    imagem: np.ndarray
    caixa: Box
    segmentacao: Segmentacao
    etapas: dict[str, np.ndarray]
    candidatas: list[CandidataPlaca] = field(default_factory=list)
    total_candidatas: int = 0
    candidatas_morfologia: dict[str, list[Box]] = field(default_factory=dict)


@dataclass
class EntradaCinza:
    """Recorte em tons de cinza acompanhado do componente que o originou.

    A referência é a máscara binária do mesmo caractere. Ela não vai ao OCR:
    serve para provar que o recorte em cinza tem a mesma geometria validada.
    """
    imagem: np.ndarray
    referencia: np.ndarray


@dataclass
class TentativaOCR:
    """Resposta de uma chamada: preparo usado, texto bruto, interpretação e confiança.

    caractere é '?' quando a resposta não é um único símbolo permitido;
    bruto preserva o que o motor retornou, mesmo quando a leitura foi recusada.
    """
    variacao: str
    caractere: str
    bruto: str
    confianca: float
    psm: int = PSM_CARACTERE_UNICO
    motor: str = NOME_DO_MOTOR


@dataclass
class Leitura:
    """Decisão para uma posição da placa, com as tentativas e o motivo de aceitação.

    O símbolo pode continuar '?'. A confiança é uma pontuação do Tesseract,
    não uma porcentagem de certeza, e não deve ser confundida com qualidade.
    """
    caractere: str
    bruto: str
    confianca: float
    tentativas: list[TentativaOCR] = field(default_factory=list)
    motivo: str = ""
