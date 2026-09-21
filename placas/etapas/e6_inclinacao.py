"""Etapa 6b — corrigir a inclinação da fonte antes de enviar ao OCR.

Fotos de placas costumam ter letras levemente inclinadas. A correção é
heurística e deliberadamente conservadora: só age quando a maioria dos
símbolos concorda com o mesmo sentido, e nunca consulta a letra esperada.
"""
import cv2
import numpy as np

from placas.config import (ANGULO_MAXIMO_CORRIGIVEL, ANGULO_MINIMO_CORRIGIVEL,
                           MARGEM_PARA_ROTACIONAR, MINIMO_DE_SIMBOLOS_INCLINADOS,
                           PASSO_DO_ANGULO, TOTAL_CARACTERES)
from placas.etapas.e6_normalizacao import normalizar_mascara
from placas.validacao import validar_entrada_ocr


def _angulo_do_simbolo(entrada: np.ndarray) -> float:
    """Inclinação estimada pelos momentos da imagem, em graus."""
    momentos = cv2.moments(255 - entrada)
    inclinacao = momentos["mu11"] / momentos["mu02"] if momentos["mu02"] else 0
    return float(-np.degrees(np.arctan(inclinacao)))


def _corrigivel(angulo: float) -> bool:
    """Abaixo do mínimo é ruído do desenho; acima do máximo não é inclinação."""
    return ANGULO_MINIMO_CORRIGIVEL <= abs(angulo) <= ANGULO_MAXIMO_CORRIGIVEL


def _vale_a_pena_corrigir(entradas: list[np.ndarray], angulos: list[float],
                          mediana: float) -> bool:
    """Exige sete símbolos e uma maioria inclinada para o mesmo lado."""
    no_mesmo_sentido = sum(a * mediana > 0 and abs(a) >= ANGULO_MINIMO_CORRIGIVEL
                           for a in angulos)
    return (len(entradas) == TOTAL_CARACTERES and _corrigivel(mediana)
            and no_mesmo_sentido >= MINIMO_DE_SIMBOLOS_INCLINADOS)


def _mascara_girada(entrada: np.ndarray, angulo: float) -> np.ndarray:
    """Gira o símbolo com folga e recorta de volta a área que contém tinta."""
    ampliada = cv2.copyMakeBorder(
        entrada, MARGEM_PARA_ROTACIONAR, MARGEM_PARA_ROTACIONAR,
        MARGEM_PARA_ROTACIONAR, MARGEM_PARA_ROTACIONAR,
        cv2.BORDER_CONSTANT, value=255)
    h, w = ampliada.shape
    matriz = cv2.getRotationMatrix2D((w / 2, h / 2), angulo, 1)
    rotacionada = cv2.warpAffine(ampliada, matriz, (w, h),
                                 flags=cv2.INTER_NEAREST, borderValue=255)
    y, x = np.where(rotacionada == 0)
    return 255 - rotacionada[y.min():y.max()+1, x.min():x.max()+1]


def corrigir_inclinacao(entradas: list[np.ndarray]) -> list[np.ndarray]:
    """Estima a inclinação pelos momentos dos recortes, sem consultar o OCR.

    Exige pelo menos cinco símbolos inclinados no mesmo sentido. Os momentos
    também dependem do desenho da letra; por isso limitamos a correção a 15°.
    Arredondar a 5° evita interpretar pequenas diferenças como ângulos precisos.
    Uma rotação que invalide o símbolo é descartada: fica a entrada original.
    """
    angulos = []
    for entrada in entradas:
        validar_entrada_ocr(entrada)
        angulos.append(_angulo_do_simbolo(entrada))
    mediana = float(np.median(angulos))
    if not _vale_a_pena_corrigir(entradas, angulos, mediana):
        return entradas
    corrigidas = []
    for entrada, angulo in zip(entradas, angulos):
        if not _corrigivel(angulo) or angulo * mediana <= 0:
            corrigidas.append(entrada)
            continue
        mascara = _mascara_girada(entrada, round(angulo / PASSO_DO_ANGULO) * PASSO_DO_ANGULO)
        try:
            corrigida = normalizar_mascara(mascara)
            validar_entrada_ocr(corrigida)
        except ValueError:
            corrigida = entrada
        corrigidas.append(corrigida)
    return corrigidas
