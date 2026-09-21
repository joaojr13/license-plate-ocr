"""Etapa 2 — detectar bordas e conectar pequenas falhas."""
import cv2
import numpy as np

from placas.config import (CANNY_LIMIAR_INFERIOR, CANNY_LIMIAR_SUPERIOR,
                           KERNEL_FECHAMENTO_BORDAS)


def encontrar_bordas(suave: np.ndarray) -> np.ndarray:
    """Entrada: cinza suavizado. Saída: máscara de bordas com fechamento 3×3."""
    bordas = cv2.Canny(suave, CANNY_LIMIAR_INFERIOR, CANNY_LIMIAR_SUPERIOR)
    return cv2.morphologyEx(bordas, cv2.MORPH_CLOSE,
                            np.ones(KERNEL_FECHAMENTO_BORDAS, np.uint8))
