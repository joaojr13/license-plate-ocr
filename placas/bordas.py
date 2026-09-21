"""Etapa 2 — detectar bordas e conectar pequenas falhas."""
import cv2
import numpy as np


def encontrar_bordas(suave: np.ndarray) -> np.ndarray:
    """Entrada: cinza suavizado. Saída: máscara de bordas com fechamento 3×3."""
    bordas = cv2.Canny(suave, 60, 180)
    return cv2.morphologyEx(bordas, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
