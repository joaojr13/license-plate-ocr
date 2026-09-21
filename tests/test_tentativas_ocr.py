from pathlib import Path

import numpy as np
import pytest

from examples.gerar_exemplo import criar_veiculo
from placas.etapas import e7_ocr as ocr
from placas.saida.exportacao import imagens_das_tentativas
from placas.etapas.e6_recortes import gerar_variacoes, preparar_caractere, validar_entrada_ocr
from placas.pipeline import localizar, reconhecer


@pytest.fixture(scope="module")
def segmentacao():
    return localizar(criar_veiculo()).segmentacao


def motor_controlado(monkeypatch, respostas):
    valores = iter(respostas)
    chamadas = []
    def motor(imagem, **kwargs):
        chamadas.append(imagem.copy())
        assert any(f"--psm {modo}" in kwargs["config"] for modo in (10, 13))
        bruto, confianca = next(valores, ("", -1))
        return {"text": [bruto], "conf": [confianca]}
    monkeypatch.setattr(ocr.pytesseract, "image_to_data", motor)
    return chamadas


def test_primeira_leitura_forte_nao_dispara_novas_tentativas(monkeypatch, segmentacao):
    chamadas = motor_controlado(monkeypatch, [("A", 90)])
    leitura = ocr.reconhecer_com_tentativas(preparar_caractere(segmentacao.caracteres[0]))
    assert leitura.caractere == "A"
    assert len(chamadas) == len(leitura.tentativas) == 1


@pytest.mark.parametrize("respostas,esperado", [
    ([("", -1), ("A", 82), ("A", 85), ("", -1), ("", -1), ("", -1)], "A"),
    ([("A", 40), ("A", 82), ("A", 85), ("B", 30), ("", -1), ("", -1)], "A"),
    ([("", -1), ("A", 82), ("A", 85), ("B", 99), ("A", 90), ("A", 91)], "?"),
    ([("", -1), ("A", 99), ("", -1), ("", -1), ("", -1), ("", -1)], "?"),
    ([("A", 20), ("A", 30), ("A", 40), ("A", 50), ("A", 59), ("A", 59)], "?"),
    ([("", -1), ("A", 83), ("", -1), ("", -1), ("", -1), ("A", 59)], "?"),
])
def test_concordancia_e_abstencao(monkeypatch, segmentacao, respostas, esperado):
    entrada = preparar_caractere(segmentacao.caracteres[0])
    chamadas = motor_controlado(monkeypatch, respostas)
    leitura = ocr.reconhecer_com_tentativas(entrada)
    assert leitura.caractere == esperado
    assert len(chamadas) == len(leitura.tentativas)
    assert len(chamadas) in (6, 12)
    # Todas as chamadas recebem variações somente do primeiro caractere.
    for imagem, preparada in zip(chamadas, gerar_variacoes(entrada).values()):
        np.testing.assert_array_equal(imagem, preparada)
        validar_entrada_ocr(imagem)
    if esperado != "?":
        assert leitura.confianca == 82  # Menor pontuação dos apoiadores fortes, não a maior.
    else:
        assert leitura.confianca == -1


def test_alfabeto_restrito_nao_preenche_resposta_ausente(monkeypatch, segmentacao):
    chamadas = motor_controlado(monkeypatch, [("A", 99)] * 6)
    leitura = ocr.reconhecer_com_tentativas(preparar_caractere(segmentacao.caracteres[0]), "0123456789")
    assert leitura.caractere == "?"
    assert len(chamadas) == 12
    assert all(t.caractere == "?" for t in leitura.tentativas)


def test_descarta_afinamento_que_elimina_simbolo():
    entrada = np.full((140, 48), 255, np.uint8)
    entrada[20:120, 24] = 0
    variacoes = gerar_variacoes(entrada)
    assert set(variacoes) == {"padrao", "margem_10", "margem_30"}
    for imagem in variacoes.values():
        validar_entrada_ocr(imagem)


def test_contagem_e_exportacao_correspondem_as_chamadas(monkeypatch, segmentacao):
    # Só o primeiro caractere falha inicialmente; os demais mantêm sua primeira leitura.
    respostas = [("", -1), ("A", 82), ("A", 85), ("", -1), ("", -1), ("", -1)]
    respostas += [(c, 90) for c in "BC1D23"]
    chamadas = motor_controlado(monkeypatch, respostas)
    monkeypatch.setattr(ocr, "verificar_tesseract", lambda: "teste")
    resultado = reconhecer(segmentacao)
    assert resultado["texto"] == "ABC1D23"
    assert resultado["quantidade_chamadas_ocr"] == len(chamadas) == 12
    assert [len(l["tentativas"]) for l in resultado["leituras"]] == [6, 1, 1, 1, 1, 1, 1]
    exportadas = imagens_das_tentativas(segmentacao, resultado)
    assert len(exportadas) == len(chamadas)
    for exportada, enviada in zip(exportadas.values(), chamadas):
        np.testing.assert_array_equal(exportada, enviada)


def test_interface_mostra_historico_das_tentativas(monkeypatch):
    from streamlit.testing.v1 import AppTest
    from placas.etapas import e7_ocr as ocr
    from placas.modelos import Leitura
    monkeypatch.setattr(ocr, "verificar_tesseract", lambda: "teste")
    monkeypatch.setattr(ocr, "reconhecer_caracteres",
                        lambda entradas, formato: [Leitura(c, c, 90) for c in "ABC1D23"])
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
    app.run(timeout=60)
    app.checkbox[0].check().run(timeout=60)
    app.button[0].click().run(timeout=60)
    assert not app.exception
    assert app.metric[0].value == "ABC1D23"
    assert any("7 chamadas individuais" in c.value for c in app.caption)
    assert any("Histórico das chamadas individuais" in m.value for m in app.markdown)
    assert any(len(t.value) == 7 for t in app.dataframe)


@pytest.mark.parametrize("alternativas,esperado", [
    ([("Q", 91)] * 6, "Q"),
    ([("Q", 91), ("8", 95)] + [("", -1)] * 4, "?"),
    ([("Q", 91)] + [("", -1)] * 5, "?"),
    ([("QQ", 95)] * 6, "?"),
])
def test_modo_alternativo_preserva_recortes_e_validacao(monkeypatch, segmentacao, alternativas, esperado):
    entrada = preparar_caractere(segmentacao.caracteres[0])
    chamadas = motor_controlado(monkeypatch, [("", -1)] * 6 + alternativas)
    leitura = ocr.reconhecer_com_tentativas(entrada)
    assert leitura.caractere == esperado
    assert [t.psm for t in leitura.tentativas] == [10] * 6 + [13] * 6
    for primeira, alternativa in zip(chamadas[:6], chamadas[6:]):
        np.testing.assert_array_equal(primeira, alternativa)
    from dataclasses import asdict
    exportadas = imagens_das_tentativas(segmentacao, {"leituras": [asdict(leitura)]})
    assert len(exportadas) == 12
    for enviada, exportada in zip(chamadas, exportadas.values()):
        np.testing.assert_array_equal(enviada, exportada)
