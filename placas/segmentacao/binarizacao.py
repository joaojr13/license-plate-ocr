"""Prepara a região da placa e produz máscaras para buscar caracteres.

Uma máscara é uma imagem de dois valores: 255 (branco) para possíveis caracteres
e 0 (preto) para o restante. Este módulo não decide quais regiões são letras.
"""

import cv2
import numpy as np

from placas.config import (
    ADAPTATIVO_CONSTANTE,
    ADAPTATIVO_TAMANHO_DO_BLOCO,
    KERNEL_ABERTURA_SEGMENTACAO,
    KERNEL_SUAVIZACAO,
    LADO_MINIMO_REGIAO,
    LARGURA_NORMALIZADA_PLACA,
)

# Os rótulos aparecem na página e identificam as alternativas no desempate.
POLARIDADES = ("caracteres escuros", "caracteres claros")
LIMIARIZACOES = ("Otsu", "Adaptativo")
SEM_ABERTURA, COM_ABERTURA = "", " + abertura 2×2"


def nome_do_metodo(limiarizacao: str, abertura: str, polaridade: str) -> str:
    """Identifica o preparo completo da máscara no resultado e na página."""
    return f"{limiarizacao}{abertura} · {polaridade}"


def preparar_regiao(placa: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Devolve a placa BGR normalizada e seu cinza suavizado para limiarização.

    A largura fixa permite comparar as mesmas regras geométricas entre fotos.
    A altura acompanha a proporção original; o gaussiano reduz ruídos pequenos.
    """
    altura, largura = placa.shape[:2]
    if min(altura, largura) < LADO_MINIMO_REGIAO:
        raise ValueError("Região pequena demais para segmentar.")
    tamanho = (
        LARGURA_NORMALIZADA_PLACA,
        round(LARGURA_NORMALIZADA_PLACA * altura / largura),
    )
    normalizada = cv2.resize(placa, tamanho)
    cinza = cv2.cvtColor(normalizada, cv2.COLOR_BGR2GRAY)
    suave = cv2.GaussianBlur(cinza, KERNEL_SUAVIZACAO, 0)
    return normalizada, suave


def _aplicar_limiares(base: np.ndarray) -> dict[str, np.ndarray]:
    """Cria uma máscara com limiar global (Otsu) e outra com limiares locais."""
    _, otsu = cv2.threshold(base, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    adaptativa = cv2.adaptiveThreshold(
        base, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,
        ADAPTATIVO_TAMANHO_DO_BLOCO, ADAPTATIVO_CONSTANTE,
    )
    return dict(zip(LIMIARIZACOES, (otsu, adaptativa)))


def gerar_mascaras(suave: np.ndarray) -> list[tuple[str, np.ndarray]]:
    """Devolve oito pares (nome, máscara) a partir do cinza suavizado.

    Compara duas polaridades × dois limiares × com/sem abertura. A ordem é
    intencional: empates exatos mantêm a primeira alternativa avaliada.
    """
    alternativas = []
    # Inverter antes do adaptativo preserva o sentido da constante C. Em ambos
    # os casos, os possíveis caracteres ficam brancos na máscara resultante.
    for polaridade, base in zip(POLARIDADES, (suave, 255 - suave)):
        for limiarizacao, binaria in _aplicar_limiares(base).items():
            aberta = cv2.morphologyEx(
                binaria, cv2.MORPH_OPEN, np.ones(KERNEL_ABERTURA_SEGMENTACAO, np.uint8),
            )
            # A abertura remove ruído, mas pode danificar traços finos. Mantemos
            # a opção original para que a comparação decida se ela é necessária.
            for abertura, mascara in ((SEM_ABERTURA, binaria), (COM_ABERTURA, aberta)):
                metodo = nome_do_metodo(limiarizacao, abertura, polaridade)
                alternativas.append((metodo, mascara))
    return alternativas
