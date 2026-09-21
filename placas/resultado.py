"""Etapa 8 — concatenar as leituras, formar os arrays e os avisos."""
from dataclasses import asdict
import re

from placas.modelos import Leitura


def consolidar_resultado(leituras: list[Leitura], formato: str = "livre") -> dict:
    """Entrada: leituras ordenadas. Saída: texto, arrays e dados para exibição."""
    caracteres = [leitura.caractere for leitura in leituras]
    texto = "".join(caracteres)
    padroes = {
        "antiga": r"[A-Z]{3}[0-9]{4}",
        "mercosul": r"[A-Z]{3}[0-9][A-Z][0-9]{2}",
        "quatro_letras": r"[A-Z]{4}[0-9]{3}",
        "livre": r"(?:[A-Z]{3}(?:[0-9]{4}|[0-9][A-Z][0-9]{2})|[A-Z]{4}[0-9]{3})",
    }
    padrao_valido = bool(re.fullmatch(padroes[formato], texto))
    avisos = []
    if "?" in texto:
        avisos.append("Há caracteres não reconhecidos, representados por '?'.")
    if any(leitura.confianca < 60 for leitura in leituras):
        avisos.append("Há leituras com confiança baixa. Confira os recortes visualmente.")
    if not padrao_valido:
        avisos.append("O texto não corresponde aos padrões de automóvel previstos neste projeto.")
    return {
        "caracteres": caracteres,
        "texto": texto,
        "placas": [texto],  # Vetor com o resultado concatenado, conforme o enunciado.
        "leituras": [asdict(leitura) for leitura in leituras],
        "formato": formato,
        "padrao_valido": padrao_valido,
        "avisos": avisos,
        "quantidade_chamadas_ocr": sum(len(l.tentativas) or 1 for l in leituras),
    }
