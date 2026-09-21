"""Etapa 7 — OCR na Google Cloud Vision, um recorte por chamada."""
import string

import cv2

from placas.modelos import Leitura, TentativaOCR
from placas.preparacao_ocr import validar_entrada_ocr

ALFABETO = string.ascii_uppercase + string.digits


def verificar_disponibilidade() -> None:
    """Confere biblioteca e credenciais locais sem guardar chaves no projeto."""
    try:
        from google.auth.exceptions import DefaultCredentialsError
        import google.auth
        from google.cloud import vision

        credenciais, projeto = google.auth.default()
        if not (projeto or getattr(credenciais, "quota_project_id", None)):
            raise RuntimeError(
                "Defina o projeto de cotas: 'gcloud auth application-default set-quota-project SEU_PROJETO'."
            )
        vision.ImageAnnotatorClient()
    except ImportError as exc:
        raise RuntimeError("Instale google-cloud-vision para usar a Google Vision.") from exc
    except DefaultCredentialsError as exc:
        raise RuntimeError(
            "Google Vision não autenticada. Execute 'gcloud auth application-default login'."
        ) from exc


def _cliente():
    from google.cloud import vision
    return vision.ImageAnnotatorClient()


def _confianca_da_resposta(resposta) -> float:
    """A API pode não fornecer confiança; nesse caso, registra -1."""
    try:
        simbolos = resposta.full_text_annotation.pages[0].blocks[0].paragraphs[0].words[0].symbols
        valores = [float(simbolo.confidence) * 100 for simbolo in simbolos]
        return min(valores) if valores else -1.0
    except (AttributeError, IndexError, TypeError):
        return -1.0


def reconhecer_caractere(imagem, cliente, permitidos: str = ALFABETO) -> Leitura:
    """Envia exatamente uma imagem de caractere já validada à API externa."""
    validar_entrada_ocr(imagem)
    from google.cloud import vision

    ok, png = cv2.imencode(".png", imagem)
    if not ok:
        raise RuntimeError("Não foi possível converter o recorte para PNG.")
    resposta = cliente.text_detection(image=vision.Image(content=png.tobytes()))
    if resposta.error.message:
        raise RuntimeError(f"Google Vision: {resposta.error.message}")
    bruto = resposta.text_annotations[0].description.strip().upper() if resposta.text_annotations else ""
    valor = bruto if len(bruto) == 1 and bruto in permitidos else "?"
    return Leitura(valor, bruto, _confianca_da_resposta(resposta))


def reconhecer_caracteres(entradas: list, formato: str = "livre") -> list[Leitura]:
    """Faz sete chamadas: uma para cada recorte, sem usar formato da placa."""
    if len(entradas) != 7:
        raise ValueError("O OCR exige sete recortes individuais preparados.")
    verificar_disponibilidade()
    cliente = _cliente()
    leituras = []
    for entrada in entradas:
        leitura = reconhecer_caractere(entrada, cliente)
        leitura.tentativas = [TentativaOCR("padrao", leitura.caractere, leitura.bruto,
                                           leitura.confianca, psm=None)]
        leitura.motivo = "Google Vision: uma chamada para o recorte individual."
        leituras.append(leitura)
    return leituras
