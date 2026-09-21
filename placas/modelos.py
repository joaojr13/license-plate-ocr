"""Dados compartilhados entre as oito etapas; não executa processamento."""
from dataclasses import dataclass, field

import numpy as np

from placas.config import NOME_DO_MOTOR, PSM_CARACTERE_UNICO

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
class CandidataPlaca:
    caixa: Box
    qualidade: float
    quantidade_caracteres: int
    metodo: str


@dataclass
class Localizacao:
    imagem: np.ndarray
    caixa: Box
    segmentacao: Segmentacao
    etapas: dict[str, np.ndarray]
    candidatas: list[CandidataPlaca] = field(default_factory=list)
    total_candidatas: int = 0
    candidatas_morfologia: dict[str, list[Box]] = field(default_factory=dict)


@dataclass
class TentativaOCR:
    variacao: str
    caractere: str
    bruto: str
    confianca: float
    psm: int = PSM_CARACTERE_UNICO
    motor: str = NOME_DO_MOTOR


@dataclass
class Leitura:
    caractere: str
    bruto: str
    confianca: float
    tentativas: list[TentativaOCR] = field(default_factory=list)
    motivo: str = ""
