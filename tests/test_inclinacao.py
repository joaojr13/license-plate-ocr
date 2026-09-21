from pathlib import Path
import shutil

import cv2
import numpy as np
import pytest

from placas.etapas.e6_recortes import corrigir_inclinacao, validar_entrada_ocr
from placas.etapas.e7_ocr import reconhecer_caracteres


def recortes():
    pasta = Path(__file__).parent / 'fixtures' / 'recortes_inclinados'
    return [cv2.imread(str(p), cv2.IMREAD_GRAYSCALE) for p in sorted(pasta.glob('*.png'))]


def test_correcao_preserva_sete_simbolos_individuais():
    entradas = recortes()
    assert len(entradas) == 7
    corrigidas = corrigir_inclinacao(entradas)
    assert any(not np.array_equal(a, b) for a, b in zip(entradas, corrigidas))
    for imagem in corrigidas:
        validar_entrada_ocr(imagem)


def test_sem_inclinacao_comum_nao_altera_simbolos():
    entrada = np.full((140, 80), 255, np.uint8)
    entrada[20:120, 35:45] = 0
    for corrigida in corrigir_inclinacao([entrada] * 7):
        np.testing.assert_array_equal(corrigida, entrada)


@pytest.mark.skipif(shutil.which('tesseract') is None, reason='Tesseract não instalado')
def test_regressao_real_p_e_um():
    leituras = reconhecer_caracteres(corrigir_inclinacao(recortes()))
    assert ''.join(l.caractere for l in leituras) == 'TEP3A12'
