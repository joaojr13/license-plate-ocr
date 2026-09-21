"""Etapa 7 — cadeia de OCR por caractere: EasyOCR, Tesseract e Google Vision."""
from placas import ocr, ocr_easyocr, ocr_google
from placas.modelos import Leitura, TentativaOCR


def _marcar_motor(leitura: Leitura, motor: str) -> Leitura:
    for tentativa in leitura.tentativas:
        tentativa.motor = motor
    return leitura


def verificar_disponibilidade() -> None:
    """Só o motor principal bloqueia a execução; os outros são tentativas extras."""
    ocr_easyocr.verificar_disponibilidade()


def reconhecer_caracteres(entradas: list, formato: str = "livre") -> list[Leitura]:
    """Tenta o mesmo recorte em ordem, somente quando o motor anterior falhar."""
    leituras_easy = ocr_easyocr.reconhecer_caracteres(entradas, formato)
    pendentes = [i for i, leitura in enumerate(leituras_easy) if leitura.caractere == "?"]
    for leitura in leituras_easy:
        _marcar_motor(leitura, "easyocr")
    if not pendentes:
        return leituras_easy

    try:
        ocr.verificar_tesseract()
        tesseract_disponivel = True
    except RuntimeError:
        tesseract_disponivel = False

    google_disponivel = False
    mensagem_google = ""
    if tesseract_disponivel:
        for indice in pendentes[:]:
            leitura_tesseract = _marcar_motor(ocr.reconhecer_com_tentativas(entradas[indice]), "tesseract")
            leituras_easy[indice].tentativas.extend(leitura_tesseract.tentativas)
            if leitura_tesseract.caractere != "?":
                leitura_tesseract.tentativas = leituras_easy[indice].tentativas
                leitura_tesseract.motivo = "Tesseract aceito após falha do EasyOCR."
                leituras_easy[indice] = leitura_tesseract
                pendentes.remove(indice)

    if pendentes:
        try:
            ocr_google.verificar_disponibilidade()
            cliente = ocr_google._cliente()
            google_disponivel = True
        except RuntimeError as exc:
            mensagem_google = str(exc)
        if google_disponivel:
            for indice in pendentes:
                leitura_google = ocr_google.reconhecer_caractere(entradas[indice], cliente)
                tentativa = TentativaOCR("padrao", leitura_google.caractere, leitura_google.bruto,
                                         leitura_google.confianca, psm=None, motor="google")
                historico = leituras_easy[indice].tentativas + [tentativa]
                leitura_google.tentativas = historico
                leitura_google.motivo = ("Google Vision aceito após falha dos dois motores locais."
                                         if leitura_google.caractere != "?" else
                                         "Nenhum dos três motores produziu uma leitura válida.")
                leituras_easy[indice] = leitura_google
        elif mensagem_google:
            for indice in pendentes:
                leituras_easy[indice].motivo += f" Google Vision não usada: {mensagem_google}"

    return leituras_easy
