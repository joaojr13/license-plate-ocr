from copy import deepcopy
from pathlib import Path
import shutil

import cv2
import numpy as np
import pytest

from examples.gerar_exemplo import criar_veiculo
from placas.imagem import ler_imagem
from placas.etapas import e7_ocr as ocr
from placas.modelos import Caractere
from placas.etapas.e6_normalizacao import preparar_caractere
from placas.validacao import validar_segmentacao
from placas.pipeline import localizar, reconhecer


@pytest.fixture(scope="module")
def segmentacao():
    return localizar(criar_veiculo()).segmentacao


def test_localiza_e_ordena_caracteres(segmentacao):
    validar_segmentacao(segmentacao)
    xs = [c.caixa[0] for c in segmentacao.caracteres]
    assert len(xs) == 7 and xs == sorted(xs)
    assert all(c.mascara.shape[1] < segmentacao.placa.shape[1] / 6
               for c in segmentacao.caracteres)


@pytest.mark.parametrize("escala", [0.6, 1.3])
def test_localiza_em_outras_escalas(escala):
    original = criar_veiculo("XYZ9876")
    imagem = cv2.resize(original, None, fx=escala, fy=escala)
    validar_segmentacao(localizar(imagem).segmentacao)


def test_rejeita_imagem_sem_placa():
    with pytest.raises(ValueError, match="Não foi encontrada"):
        localizar(np.full((300, 500, 3), 150, np.uint8))


@pytest.mark.parametrize("escala", [0.6, 1.0, 1.3])
def test_placa_escura_sintetica(escala):
    imagem = criar_veiculo()
    # Inverte somente a placa; carro e fundo mantêm as cores originais.
    imagem[385:474, 315:686] = 255 - imagem[385:474, 315:686]
    imagem = cv2.resize(imagem, None, fx=escala, fy=escala)
    resultado = localizar(imagem)
    validar_segmentacao(resultado.segmentacao)
    assert "caracteres claros" in resultado.segmentacao.metodo
    x, y, w, h = resultado.caixa
    assert x <= 500 * escala <= x + w
    assert y <= 440 * escala <= y + h


def test_regressao_foto_placa_preta():
    foto = Path(__file__).parent / "fixtures" / "placa_escura.jpeg"
    resultado = localizar(ler_imagem(foto.read_bytes()))
    segmentacao = resultado.segmentacao
    validar_segmentacao(segmentacao)
    assert "caracteres claros" in segmentacao.metodo
    x, y, w, h = resultado.caixa
    # Região da placa anotada manualmente na fotografia (não usada pelo detector).
    intersecao = max(0, min(x+w, 310) - max(x, 207)) * max(0, min(y+h, 252) - max(y, 218))
    uniao = w*h + 103*34 - intersecao
    assert intersecao / uniao > 0.70  # Não aceitar a carroceria inteira como placa.
    # Cada recorte deve corresponder à posição de uma letra, não a um emblema.
    intervalos_x = [(216, 228), (228, 240), (240, 253), (252, 265),
                    (264, 277), (276, 288), (288, 301)]
    for caractere, (inicio, fim) in zip(segmentacao.caracteres, intervalos_x):
        cx, cy, cw, ch = caractere.caixa
        centro_x = x + (cx + cw/2) * w / segmentacao.placa.shape[1]
        centro_y = y + (cy + ch/2) * h / segmentacao.placa.shape[0]
        assert inicio <= centro_x <= fim
        assert 228 <= centro_y <= 246
        preparada = preparar_caractere(caractere)
        assert preparada[0].min() == 255  # Fundo branco para o OCR, mesmo na placa preta.


def test_rejeita_arquivo_invalido():
    with pytest.raises(ValueError, match="Arquivo inválido"):
        ler_imagem(b"isto nao e uma imagem")


def test_sete_chamadas_com_imagens_individuais(monkeypatch, segmentacao):
    recebidas = []
    valores = iter("ABC1D23")
    monkeypatch.setattr(ocr, "verificar_tesseract", lambda: "teste")

    def motor(imagem, **kwargs):
        recebidas.append(imagem.copy())
        assert "--psm 10" in kwargs["config"]
        return {"text": ["", next(valores)], "conf": [-1, 92]}

    monkeypatch.setattr(ocr.pytesseract, "image_to_data", motor)
    resultado = reconhecer(segmentacao)
    assert resultado["caracteres"] == list("ABC1D23")
    assert resultado["placas"] == ["ABC1D23"]
    assert resultado["texto"] == "ABC1D23"
    assert resultado["padrao_valido"]
    assert len(recebidas) == 7
    for entrada, caractere in zip(recebidas, segmentacao.caracteres):
        np.testing.assert_array_equal(entrada, preparar_caractere(caractere))
        assert entrada.shape[1] < 150


def test_segmentacao_incompleta_nao_chama_ocr(monkeypatch, segmentacao):
    incompleta = deepcopy(segmentacao)
    incompleta.caracteres.pop()
    def proibido(*args, **kwargs):
        pytest.fail("OCR não pode ser chamado para segmentação incompleta")
    monkeypatch.setattr(ocr, "verificar_tesseract", proibido)
    monkeypatch.setattr(ocr.pytesseract, "image_to_data", proibido)
    with pytest.raises(ValueError, match="OCR bloqueado"):
        reconhecer(incompleta)


@pytest.mark.parametrize("bruto", ["", "AB", "@"])
def test_ocr_nao_inventa_leitura(monkeypatch, segmentacao, bruto):
    monkeypatch.setattr(ocr.pytesseract, "image_to_data",
                        lambda *a, **kw: {"text": [bruto], "conf": [30]})
    leitura = ocr.reconhecer_caractere(preparar_caractere(segmentacao.caracteres[0]))
    assert leitura.caractere == "?" and leitura.bruto == bruto


def test_rejeita_placa_completa_como_caractere(segmentacao):
    h, w = segmentacao.binaria.shape
    with pytest.raises(ValueError, match="largo demais"):
        preparar_caractere(Caractere((0, 0, w, h), segmentacao.binaria))


def test_rejeita_dois_componentes_no_mesmo_recorte():
    mascara = np.zeros((100, 60), np.uint8)
    mascara[10:90, 5:15] = 255
    mascara[10:90, 40:50] = 255
    with pytest.raises(ValueError, match="um componente"):
        preparar_caractere(Caractere((0, 0, 60, 100), mascara))


def test_etapa_ocr_rejeita_placa_completa_antes_do_motor(monkeypatch, segmentacao):
    def proibido(*args, **kwargs):
        pytest.fail("O motor não pode receber a imagem da placa completa")
    monkeypatch.setattr(ocr.pytesseract, "image_to_data", proibido)
    with pytest.raises(ValueError, match="recorte preparado"):
        ocr.reconhecer_caractere(segmentacao.binaria)


def test_consolidacao_preserva_posicao_da_falha():
    from placas.modelos import Leitura
    from placas.etapas.e8_resultado import consolidar_resultado
    leituras = [Leitura(c, c, 90) for c in "ABC1D23"]
    leituras[4] = Leitura("?", "", -1)
    resultado = consolidar_resultado(leituras, "mercosul")
    assert resultado["caracteres"] == list("ABC1?23")
    assert resultado["placas"] == ["ABC1?23"]
    assert resultado["quantidade_chamadas_ocr"] == 7
    assert not resultado["padrao_valido"]
    assert any("não reconhecidos" in aviso for aviso in resultado["avisos"])


@pytest.mark.parametrize("formato,posicao4", [("antiga", "0123456789"), ("mercosul", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")])
def test_restricao_por_posicao(monkeypatch, segmentacao, formato, posicao4):
    permitidos = []
    monkeypatch.setattr(ocr, "verificar_tesseract", lambda: "teste")
    def motor(caractere, alfabeto):
        permitidos.append(alfabeto)
        return ocr.Leitura(alfabeto[0], alfabeto[0], 90)
    monkeypatch.setattr(ocr, "reconhecer_caractere", motor)
    reconhecer(segmentacao, formato)
    assert permitidos[:3] == ["ABCDEFGHIJKLMNOPQRSTUVWXYZ"] * 3
    assert permitidos[3] == permitidos[5] == permitidos[6] == "0123456789"
    assert permitidos[4] == posicao4


def test_motor_ausente_tem_mensagem_clara(monkeypatch):
    def ausente():
        raise ocr.pytesseract.TesseractNotFoundError()
    monkeypatch.setattr(ocr.pytesseract, "get_tesseract_version", ausente)
    with pytest.raises(RuntimeError, match="Tesseract não encontrado"):
        ocr.verificar_tesseract()


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Motor Tesseract não instalado")
def test_ocr_real_quando_disponivel(segmentacao):
    resultado = reconhecer(segmentacao, "mercosul")
    assert 7 <= resultado["quantidade_chamadas_ocr"] <= 84
    assert len(resultado["caracteres"]) == 7
    # Este teste verifica a integração; não presume acurácia do motor.


def test_interface_exemplo_sem_motor(monkeypatch):
    from streamlit.testing.v1 import AppTest
    def ausente():
        raise RuntimeError("Tesseract não encontrado")
    monkeypatch.setattr(ocr, "verificar_tesseract", ausente)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
    app.run(timeout=60)
    assert not app.exception
    app.checkbox[0].check().run(timeout=60)
    assert not app.exception
    assert app.button[0].disabled


def test_interface_exibe_resultado_com_tesseract(monkeypatch):
    from streamlit.testing.v1 import AppTest
    letras = iter("ABC1D23")
    from placas.etapas import e7_ocr as ocr
    monkeypatch.setattr(ocr, "verificar_tesseract", lambda: "teste")
    monkeypatch.setattr(ocr.pytesseract, "image_to_data",
                        lambda *a, **kw: {"text": [next(letras)], "conf": [92]})
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
    app.run(timeout=60)
    app.checkbox[0].check().run(timeout=60)
    app.button[0].click().run(timeout=60)
    assert not app.exception
    assert app.metric[0].value == "ABC1D23"
    assert app.session_state["resultado"]["placas"] == ["ABC1D23"]
