"""Leitura compartilhada pela interface e pelo terminal."""
from io import BytesIO

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from placas.config import LIMITE_DE_PIXELS


def ler_imagem(conteudo: bytes) -> np.ndarray:
    try:
        with Image.open(BytesIO(conteudo)) as imagem:
            if imagem.width * imagem.height > LIMITE_DE_PIXELS:
                raise ValueError("Use uma imagem com até 25 megapixels.")
            rgb = np.array(ImageOps.exif_transpose(imagem).convert("RGB"))
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Arquivo inválido. Envie uma imagem PNG, JPEG ou WebP legível.") from exc
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
