"""Reconstrói os preparos registrados para auditar cada chamada individual de OCR.

As imagens exportadas são recalculadas a partir da mesma segmentação, e não
guardadas durante o reconhecimento: o que se baixa é exatamente o que foi
enviado ao OCR, pixel a pixel, e o teste de regressão verifica isso.
"""
import io
import json
import zipfile

import cv2
import numpy as np

from placas.etapas.e6_recortes import preparar_cinza, preparar_recortes
from placas.etapas.e6_variacoes import gerar_variacoes
from placas.modelos import Segmentacao


def imagens_das_tentativas(segmentacao: Segmentacao, resultado: dict) -> dict[str, np.ndarray]:
    """Retorna somente imagens das tentativas que constam no resultado."""
    imagens = {}
    cinzas = (preparar_cinza(segmentacao) if any(t['variacao'].startswith('cinza_')
              for l in resultado['leituras'] for t in l['tentativas']) else None)
    for indice, (padrao, leitura) in enumerate(zip(preparar_recortes(segmentacao), resultado["leituras"]), 1):
        variacoes = gerar_variacoes(padrao)
        for tentativa in leitura["tentativas"]:
            nome = tentativa["variacao"]
            sufixo = "_psm13" if tentativa.get("psm", 10) == 13 else ""
            if nome.startswith('cinza_'):
                imagens[f"caractere_{indice:02}_tesseract_{nome}{sufixo}.png"] = (
                    cinzas[indice - 1][nome].imagem)
                continue
            imagens[f"caractere_{indice:02}_tesseract_{nome}{sufixo}.png"] = variacoes[nome]
    return imagens


def montar_pacote_zip(segmentacao: Segmentacao, resultado: dict) -> bytes:
    """Reúne o JSON do resultado e as imagens das tentativas em um único arquivo."""
    pacote = io.BytesIO()
    with zipfile.ZipFile(pacote, "w", zipfile.ZIP_DEFLATED) as zipado:
        zipado.writestr("resultado.json", json.dumps(resultado, ensure_ascii=False, indent=2))
        for nome, imagem in imagens_das_tentativas(segmentacao, resultado).items():
            _, png = cv2.imencode(".png", imagem)
            zipado.writestr(nome, png.tobytes())
    return pacote.getvalue()
