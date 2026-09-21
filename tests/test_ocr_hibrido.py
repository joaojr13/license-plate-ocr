import numpy as np

from placas import ocr_hibrido
from placas.modelos import Leitura, TentativaOCR


def leitura(valor, motor):
    return Leitura(valor, valor if valor != "?" else "", 90 if valor != "?" else -1,
                   [TentativaOCR("padrao", valor, valor if valor != "?" else "", 90, motor=motor)])


def test_easyocr_aceito_nao_chama_outros_motores(monkeypatch):
    entradas = [np.full((140, 30), 255, np.uint8)] * 7
    from placas import ocr_easyocr, ocr, ocr_google
    monkeypatch.setattr(ocr_easyocr, "reconhecer_caracteres",
                        lambda entradas, formato: [leitura("A", "easyocr") for _ in entradas])
    monkeypatch.setattr(ocr, "verificar_tesseract", lambda: (_ for _ in ()).throw(AssertionError()))
    monkeypatch.setattr(ocr_google, "verificar_disponibilidade", lambda: (_ for _ in ()).throw(AssertionError()))
    saida = ocr_hibrido.reconhecer_caracteres(entradas)
    assert [item.caractere for item in saida] == ["A"] * 7
    assert all(item.tentativas[0].motor == "easyocr" for item in saida)


def test_falha_easyocr_usa_tesseract_no_mesmo_recorte(monkeypatch):
    entradas = [np.full((140, 30), 255, np.uint8)] * 7
    from placas import ocr_easyocr, ocr, ocr_google
    monkeypatch.setattr(ocr_easyocr, "reconhecer_caracteres",
                        lambda entradas, formato: [leitura("?", "easyocr")] + [leitura("A", "easyocr") for _ in range(6)])
    monkeypatch.setattr(ocr, "verificar_tesseract", lambda: "teste")
    recebidas = []
    def tesseract(entrada):
        recebidas.append(entrada)
        return leitura("Z", "tesseract")
    monkeypatch.setattr(ocr, "reconhecer_com_tentativas", tesseract)
    monkeypatch.setattr(ocr_google, "verificar_disponibilidade", lambda: (_ for _ in ()).throw(AssertionError()))
    saida = ocr_hibrido.reconhecer_caracteres(entradas)
    assert saida[0].caractere == "Z"
    assert recebidas == [entradas[0]]
    assert [t.motor for t in saida[0].tentativas] == ["easyocr", "tesseract"]


def test_falhas_locais_usam_google_com_entrada_individual(monkeypatch):
    entradas = [np.full((140, 30), 255, np.uint8)] * 7
    from placas import ocr_easyocr, ocr, ocr_google
    monkeypatch.setattr(ocr_easyocr, "reconhecer_caracteres",
                        lambda entradas, formato: [leitura("?", "easyocr") for _ in entradas])
    monkeypatch.setattr(ocr, "verificar_tesseract", lambda: "teste")
    monkeypatch.setattr(ocr, "reconhecer_com_tentativas", lambda entrada: leitura("?", "tesseract"))
    monkeypatch.setattr(ocr_google, "verificar_disponibilidade", lambda: None)
    cliente = object()
    monkeypatch.setattr(ocr_google, "_cliente", lambda: cliente)
    recebidas = []
    def google(entrada, recebido):
        recebidas.append((entrada, recebido))
        return leitura("Z", "google")
    monkeypatch.setattr(ocr_google, "reconhecer_caractere", google)
    saida = ocr_hibrido.reconhecer_caracteres(entradas)
    assert [item.caractere for item in saida] == ["Z"] * 7
    assert recebidas == [(entrada, cliente) for entrada in entradas]
    assert all([t.motor for t in item.tentativas] == ["easyocr", "tesseract", "google"] for item in saida)
