import numpy as np
import pytest
from placas import ocr_easyocr
from placas.modelos import Caractere
from placas.preparacao_ocr import preparar_caractere


def entrada():
    mascara = np.full((40, 15), 255, np.uint8)
    return preparar_caractere(Caractere((0, 0, 15, 40), mascara))


@pytest.mark.parametrize('texto,esperado', [('A','A'),('AB','?'),('','?')])
def test_easyocr_recebe_apenas_recortes(monkeypatch, texto, esperado):
    imagem = entrada()
    chamadas = []
    class Motor:
        def recognize(self, recorte, **kwargs):
            from placas.preparacao_ocr import validar_entrada_ocr
            validar_entrada_ocr(recorte)
            chamadas.append(recorte.copy())
            assert kwargs['paragraph'] is False
            return [(None, texto, .95)]
    monkeypatch.setattr(ocr_easyocr, 'carregar_motor', lambda: Motor())
    leituras = ocr_easyocr.reconhecer_caracteres([imagem]*7)
    assert [l.caractere for l in leituras] == [esperado]*7
    assert len(chamadas) == sum(len(l.tentativas) for l in leituras)
    if esperado == 'A':
        assert len(chamadas) == 7
        for enviada in chamadas:
            np.testing.assert_array_equal(enviada, imagem)


def test_easyocr_bloqueia_entrada_invalida_antes_do_motor(monkeypatch):
    def proibido():
        pytest.fail('Não deveria carregar o OCR')
    monkeypatch.setattr(ocr_easyocr, 'carregar_motor', proibido)
    with pytest.raises(ValueError):
        ocr_easyocr.reconhecer_caracteres([np.zeros((300,600),np.uint8)]*7)


def test_fluxo_usa_somente_tesseract_por_padrao(monkeypatch):
    from examples.gerar_exemplo import criar_veiculo
    from placas.processamento import localizar, reconhecer
    from placas.modelos import Leitura
    from placas import ocr, ocr_easyocr, ocr_hibrido, ocr_google
    def proibido(*args, **kwargs):
        pytest.fail('O fluxo padrão deve chamar somente Tesseract')
    monkeypatch.setattr(ocr_google, 'reconhecer_caracteres', proibido)
    monkeypatch.setattr(ocr_hibrido, 'reconhecer_caracteres', proibido)
    monkeypatch.setattr(ocr_easyocr, 'reconhecer_caracteres', proibido)
    monkeypatch.setattr(ocr, 'reconhecer_caracteres',
                        lambda entradas, formato: [Leitura(c,c,90) for c in 'ABC1D23'])
    resultado = reconhecer(localizar(criar_veiculo()).segmentacao)
    assert resultado['motor'] == 'tesseract'
    assert resultado['texto'] == 'ABC1D23'


def test_margem_ampliada_confirma_sem_substituir_letras(monkeypatch):
    imagem = entrada()
    class Motor:
        def recognize(self, recorte, **kwargs):
            if recorte.shape[0] in (160, 180):
                return [(None, 'W', .75)]
            return [(None, 'H', .4)]
    monkeypatch.setattr(ocr_easyocr, 'carregar_motor', lambda: Motor())
    leituras = ocr_easyocr.reconhecer_caracteres([imagem]*7)
    assert all(l.caractere == 'W' for l in leituras)
    assert all(l.tentativas[-1].variacao == 'margem_40' for l in leituras)


def test_quatro_letras_restringe_alfabeto_por_posicao(monkeypatch):
    permitidos = []
    class Motor:
        def recognize(self, recorte, **kwargs):
            permitidos.append(kwargs['allowlist'])
            return [(None, 'Z' if len(permitidos) <= 4 else '2', .95)]
    monkeypatch.setattr(ocr_easyocr, 'carregar_motor', lambda: Motor())
    leituras = ocr_easyocr.reconhecer_caracteres([entrada()]*7, 'quatro_letras')
    import string
    assert permitidos == [string.ascii_uppercase]*4 + [string.digits]*3
    assert ''.join(l.caractere for l in leituras) == 'ZZZZ222'


def test_validacao_respeita_formato_quatro_letras():
    from placas.resultado import consolidar_resultado
    from placas.modelos import Leitura
    certo = [Leitura(c,c,90) for c in 'WBZL449']
    errado = [Leitura(c,c,90) for c in 'WB2L449']
    assert consolidar_resultado(certo,'quatro_letras')['padrao_valido']
    assert not consolidar_resultado(errado,'quatro_letras')['padrao_valido']
