from pathlib import Path
import shutil
import cv2
import pytest

from placas.pipeline import localizar, reconhecer
from placas.validacao import validar_segmentacao


@pytest.fixture(scope="module")
def localizacao():
    caminho = Path(__file__).parent / "fixtures" / "placa_inclinada_wrv.png"
    return localizar(cv2.imread(str(caminho)))


def test_linha_inclinada_inclui_os_sete_caracteres(localizacao):
    seg = localizacao.segmentacao
    validar_segmentacao(seg)
    assert len(seg.caracteres) == 7
    x, y, w, h = localizacao.caixa
    # Região anotada manualmente inclui a placa inteira, não apenas quatro letras.
    assert 295 <= x <= 320 and 375 <= y <= 400
    assert x + w >= 449 and y + h >= 458
    assert seg.caracteres[-1].caixa[1] > seg.caracteres[0].caixa[1]


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract não instalado")
def test_ocr_real_linha_inclinada(localizacao):
    assert reconhecer(localizacao.segmentacao)["texto"] == "WRV2021"
