from pathlib import Path
import shutil
import cv2
import numpy as np
import pytest

from placas.etapas import e7_decisao, e7_motor_ocr
from placas.modelos import Leitura, TentativaOCR
from placas.pipeline import localizar, reconhecer
from placas.etapas.e6_recortes import preparar_cinza
from placas.validacao import validar_entrada_cinza
from placas.saida.exportacao import imagens_das_tentativas


@pytest.fixture
def segmentacao():
    return localizar(cv2.imread(str(Path(__file__).parent/'fixtures'/'placa_paraguai.jpg'))).segmentacao


@pytest.mark.parametrize('respostas,esperado', [
    ([('Z',88),('Z',90),('Z',87)], 'Z'),
    ([('Z',88),('L',90),('Z',87)], '?'),
    ([('Z',88),('Z',30),('Z',20)], '?'),
    ([('ZZ',88),('ZZ',90),('ZZ',87)], '?'),
])
def test_cinza_consenso_e_exportacao(monkeypatch, segmentacao, respostas, esperado):
    variacoes = preparar_cinza(segmentacao)[2]
    respostas = iter(respostas)
    enviadas = []
    def motor(imagem, **kwargs):
        enviadas.append(imagem.copy())
        texto, conf = next(respostas)
        return {'text':[texto], 'conf':[conf]}
    monkeypatch.setattr(e7_motor_ocr.pytesseract, 'image_to_data', motor)
    anterior = Leitura('?', 'L', -1, [TentativaOCR('padrao','L','L',74)])
    leitura = e7_decisao.recuperar_com_cinza(anterior, variacoes)
    assert leitura.caractere == esperado
    assert len(leitura.tentativas) == 4
    from dataclasses import asdict
    vazia = asdict(Leitura('A','A',90))
    resultado = {'leituras':[vazia, vazia, asdict(leitura)]}
    exportadas = imagens_das_tentativas(segmentacao, resultado)
    adicionais = [im for nome,im in exportadas.items() if 'cinza_' in nome]
    assert len(adicionais) == len(enviadas) == 3
    for enviada, exportada in zip(enviadas, adicionais):
        np.testing.assert_array_equal(enviada, exportada)


def test_cinza_rejeita_placa_completa(segmentacao):
    entrada = preparar_cinza(segmentacao)[2]['cinza_margem_20']
    validar_entrada_cinza(entrada.imagem, entrada.referencia)
    with pytest.raises(ValueError):
        validar_entrada_cinza(segmentacao.placa, entrada.referencia)


def test_leitura_aceita_nao_dispara_cinza(monkeypatch):
    def proibido(*a, **kw):
        pytest.fail('Não deve chamar OCR')
    monkeypatch.setattr(e7_motor_ocr, 'reconhecer_caractere', proibido)
    leitura = Leitura('2','2',90)
    assert e7_decisao.recuperar_com_cinza(leitura, {}) is leitura


@pytest.mark.skipif(shutil.which('tesseract') is None, reason='Tesseract não instalado')
def test_regressao_real_z_sem_restricao_de_formato(segmentacao):
    resultado = reconhecer(segmentacao)
    assert resultado['texto'] == 'WBZL449'
    assert resultado['formato'] == 'livre'
    assert any(t['variacao'].startswith('cinza_') for t in resultado['leituras'][2]['tentativas'])
