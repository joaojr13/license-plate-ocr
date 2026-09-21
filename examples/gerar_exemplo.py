"""Imagem sintética, não uma fotografia nem uma evidência de acurácia real."""
from pathlib import Path

import cv2
import numpy as np


def criar_veiculo(texto: str = "ABC1D23") -> np.ndarray:
    imagem = np.full((600, 1000, 3), (205, 210, 216), np.uint8)
    cv2.rectangle(imagem, (0, 465), (1000, 600), (85, 85, 85), -1)
    cv2.rectangle(imagem, (200, 390), (295, 535), (25, 25, 25), -1)
    cv2.rectangle(imagem, (705, 390), (800, 535), (25, 25, 25), -1)
    cv2.fillConvexPoly(imagem, np.array([[200, 290], [300, 140], [700, 140], [800, 290]]), (115, 70, 40))
    cv2.fillConvexPoly(imagem, np.array([[290, 265], [335, 165], [665, 165], [710, 265]]), (180, 165, 140))
    cv2.rectangle(imagem, (165, 275), (835, 490), (160, 100, 45), -1)
    cv2.rectangle(imagem, (195, 305), (310, 350), (225, 230, 235), -1)
    cv2.rectangle(imagem, (690, 305), (805, 350), (225, 230, 235), -1)
    cv2.rectangle(imagem, (310, 380), (690, 478), (20, 20, 20), -1)
    cv2.rectangle(imagem, (315, 385), (685, 473), (246, 246, 246), -1)
    cv2.rectangle(imagem, (315, 385), (685, 402), (165, 60, 15), -1)
    for i, letra in enumerate(texto):
        cv2.putText(imagem, letra, (329 + i * 49, 460), cv2.FONT_HERSHEY_SIMPLEX,
                    1.5, (12, 12, 12), 3, cv2.LINE_AA)
    return imagem


if __name__ == "__main__":
    cv2.imwrite(str(Path(__file__).with_name("veiculo_sintetico.png")), criar_veiculo())
