from pathlib import Path
import shutil

import cv2
import pytest

from placas.etapas import e7_decisao, e7_motor_ocr
from placas.etapas.e6_escalas import preparar_escalas
from placas.modelos import Leitura

PASTA = Path(__file__).parent / "fixtures" / "recortes_escalas"


@pytest.mark.parametrize("respostas,esperado", [
    ([("A", 91), ("A", 80), ("A", 92), ("A", 84)], "A"),
    ([("A", 91), ("A", 80), ("A", 0), ("A", 0)], "?"),
    ([("A", 91), ("4", 80), ("A", 92), ("A", 84)], "?"),
])
def test_consenso_exige_duas_escalas_sem_conflito(monkeypatch, respostas, esperado):
    respostas = iter(respostas)
    def motor_simulado(*args, **kwargs):
        caractere, confianca = next(respostas)
        return Leitura(caractere, caractere, confianca)
    monkeypatch.setattr(e7_motor_ocr, "reconhecer_caractere", motor_simulado)
    entrada = cv2.imread(str(PASTA / "A.png"), 0)
    leitura = e7_decisao.recuperar_com_escalas(Leitura("?", "", -1), entrada,
                                             e7_motor_ocr.ALFABETO)
    assert leitura.caractere == esperado
    assert len(leitura.tentativas) == 4


def test_escala_adulterada_nao_chega_ao_motor(monkeypatch):
    entrada = cv2.imread(str(PASTA / "A.png"), 0)
    imagem = preparar_escalas(entrada)["escala_30"].copy()
    imagem[0, 0] = 0
    def proibido(*args, **kwargs):
        pytest.fail("Uma imagem adulterada chegou ao OCR")
    monkeypatch.setattr(e7_motor_ocr.pytesseract, "image_to_data", proibido)
    with pytest.raises(ValueError, match="Escala incompatível"):
        e7_motor_ocr.reconhecer_caractere(imagem, referencia_escala=entrada)


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract não instalado")
@pytest.mark.parametrize("arquivo,esperado", [("A.png", "A"), ("9_primeiro.png", "9"),
                                              ("9_ultimo.png", "9")])
def test_regressao_real_dos_recortes(arquivo, esperado):
    entrada = cv2.imread(str(PASTA / arquivo), 0)
    leitura = e7_decisao.recuperar_com_escalas(Leitura("?", "", -1), entrada,
                                             e7_motor_ocr.ALFABETO)
    assert leitura.caractere == esperado
