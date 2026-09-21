from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from placas import ocr_google
from placas.modelos import Caractere
from placas.preparacao_ocr import preparar_caractere


def entrada():
    mascara = np.full((40, 15), 255, np.uint8)
    mascara[3:37, 5:10] = 0
    return preparar_caractere(Caractere((0, 0, 15, 40), mascara))


def resposta(texto, confianca=0.9):
    simbolo = SimpleNamespace(confidence=confianca)
    palavra = SimpleNamespace(symbols=[simbolo])
    paragrafo = SimpleNamespace(words=[palavra])
    bloco = SimpleNamespace(paragraphs=[paragrafo])
    pagina = SimpleNamespace(blocks=[bloco])
    return SimpleNamespace(
        error=SimpleNamespace(message=""),
        text_annotations=[SimpleNamespace(description=texto)] if texto else [],
        full_text_annotation=SimpleNamespace(pages=[pagina]),
    )


def test_google_envia_sete_recortes_individuais(monkeypatch):
    chamadas = []

    class Cliente:
        def text_detection(self, *, image):
            decodificada = cv2.imdecode(np.frombuffer(image.content, np.uint8), cv2.IMREAD_GRAYSCALE)
            chamadas.append(decodificada)
            return resposta("A")

    monkeypatch.setattr(ocr_google, "verificar_disponibilidade", lambda: None)
    monkeypatch.setattr(ocr_google, "_cliente", lambda: Cliente())
    leituras = ocr_google.reconhecer_caracteres([entrada()] * 7)
    assert [leitura.caractere for leitura in leituras] == ["A"] * 7
    assert len(chamadas) == 7
    for enviada in chamadas:
        np.testing.assert_array_equal(enviada, entrada())


@pytest.mark.parametrize("texto,esperado", [("Z", "Z"), ("22", "?"), ("", "?")])
def test_google_rejeita_respostas_que_nao_sao_um_caractere(monkeypatch, texto, esperado):
    class Cliente:
        def text_detection(self, *, image):
            return resposta(texto)

    monkeypatch.setattr(ocr_google, "verificar_disponibilidade", lambda: None)
    monkeypatch.setattr(ocr_google, "_cliente", lambda: Cliente())
    leitura = ocr_google.reconhecer_caracteres([entrada()] * 7)[0]
    assert leitura.caractere == esperado
