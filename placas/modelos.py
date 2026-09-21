"""Dados compartilhados entre as oito etapas; não executa processamento."""
from dataclasses import dataclass, field

import numpy as np

Box = tuple[int, int, int, int]  # x, y, largura, altura


@dataclass
class ImagemPreparada:
    imagem: np.ndarray
    cinza: np.ndarray
    suave: np.ndarray


@dataclass
class Caractere:
    caixa: Box
    mascara: np.ndarray  # Somente este componente: branco em fundo preto.


@dataclass
class Segmentacao:
    placa: np.ndarray
    binaria: np.ndarray
    caracteres: list[Caractere]
    metodo: str
    qualidade: float


@dataclass
class Localizacao:
    imagem: np.ndarray
    caixa: Box
    segmentacao: Segmentacao
    etapas: dict[str, np.ndarray]


@dataclass
class TentativaOCR:
    variacao: str
    caractere: str
    bruto: str
    confianca: float
    psm: int | None = 10
    motor: str = "tesseract"


@dataclass
class Leitura:
    caractere: str
    bruto: str
    confianca: float
    tentativas: list[TentativaOCR] = field(default_factory=list)
    motivo: str = ""
