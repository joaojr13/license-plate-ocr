"""Etapa 6 — validar a segmentação e preparar somente recortes individuais."""
import cv2
import numpy as np

from placas.config import (ALTURA_CARACTERE, ALTURA_PADRAO_DA_ENTRADA, ALTURAS_VALIDAS,
                           ANGULO_MAXIMO_CORRIGIVEL, ANGULO_MINIMO_CORRIGIVEL,
                           AREA_MINIMA_COMPONENTE, KERNEL_AFINAMENTO,
                           LARGURA_MAXIMA_CARACTERE, LARGURA_MINIMA_CARACTERE,
                           LARGURA_RELATIVA_COMPONENTE, MARGEM_PADRAO,
                           MARGEM_PARA_ROTACIONAR, MARGENS_ALTERNATIVAS,
                           MINIMO_DE_SIMBOLOS_INCLINADOS, PASSO_DO_ANGULO,
                           PROPORCAO_COMPONENTE, TOTAL_CARACTERES)
from placas.modelos import Caractere, Segmentacao


def validar_segmentacao(segmentacao: Segmentacao) -> None:
    caracteres = segmentacao.caracteres
    if len(caracteres) != TOTAL_CARACTERES:
        raise ValueError(f"Foram isolados {len(caracteres)} caracteres; "
                         f"são necessários {TOTAL_CARACTERES}. "
                         "OCR bloqueado. Tente uma foto melhor.")
    altura, largura = segmentacao.binaria.shape
    anterior = -1
    for c in caracteres:
        x, y, w, h = c.caixa
        if (x < anterior or x < 0 or y < 0 or x+w > largura or y+h > altura
                or w > largura * LARGURA_RELATIVA_COMPONENTE[1]
                or w / h > PROPORCAO_COMPONENTE[1] or c.mascara.shape != (h, w)):
            raise ValueError("Recortes inválidos ou sobrepostos; OCR bloqueado.")
        n, _, stats, _ = cv2.connectedComponentsWithStats(c.mascara, 8)
        if n != 2 or stats[1, cv2.CC_STAT_AREA] < AREA_MINIMA_COMPONENTE:
            raise ValueError("Cada recorte deve conter somente um componente isolado.")
        anterior = x + w


def preparar_caractere(caractere: Caractere) -> np.ndarray:
    """Letra preta sobre branco, altura 100 px e margem, preservando proporção."""
    mascara = caractere.mascara
    if mascara.ndim != 2 or mascara.size == 0:
        raise ValueError("Recorte de caractere inválido.")
    h, w = mascara.shape
    if not PROPORCAO_COMPONENTE[0] <= w / h <= PROPORCAO_COMPONENTE[1]:
        raise ValueError("Recorte largo demais para um caractere isolado.")
    n, _ = cv2.connectedComponents(mascara, 8)
    if n != 2:
        raise ValueError("O OCR exige exatamente um componente por recorte.")
    largura = max(LARGURA_MINIMA_CARACTERE, round(w * ALTURA_CARACTERE / h))
    letra = cv2.resize(255 - mascara, (largura, ALTURA_CARACTERE),
                       interpolation=cv2.INTER_NEAREST)
    return cv2.copyMakeBorder(letra, MARGEM_PADRAO, MARGEM_PADRAO, MARGEM_PADRAO, MARGEM_PADRAO,
                              cv2.BORDER_CONSTANT, value=255)


def preparar_recortes(segmentacao: Segmentacao) -> list[np.ndarray]:
    """Valida todos os recortes antes de gerar as sete entradas do OCR."""
    validar_segmentacao(segmentacao)
    return corrigir_inclinacao([preparar_caractere(c) for c in segmentacao.caracteres])


def preparar_cinza(segmentacao: Segmentacao) -> list[dict[str, tuple[np.ndarray, np.ndarray]]]:
    """Recorta os mesmos boxes validados na placa, preservando tons e proporção.

    Retorna imagem e máscara de referência individual; não recebe caixas do OCR.
    A referência documenta o componente segmentado e valida a geometria do envio.
    """
    validar_segmentacao(segmentacao)
    if segmentacao.placa.shape[:2] != segmentacao.binaria.shape:
        raise ValueError('Placa e segmentação devem compartilhar as mesmas coordenadas.')
    cinza = cv2.cvtColor(segmentacao.placa, cv2.COLOR_BGR2GRAY)
    saida = []
    for caractere in segmentacao.caracteres:
        x, y, w, h = caractere.caixa
        recorte = cinza[y:y+h, x:x+w]
        if 'caracteres claros' in segmentacao.metodo:
            recorte = 255 - recorte
        largura = max(LARGURA_MINIMA_CARACTERE, round(w * ALTURA_CARACTERE / h))
        letra = cv2.resize(recorte, (largura, ALTURA_CARACTERE),
                           interpolation=cv2.INTER_CUBIC)
        mascara = preparar_caractere(caractere)[MARGEM_PADRAO:-MARGEM_PADRAO, MARGEM_PADRAO:-MARGEM_PADRAO]
        variacoes = {}
        for margem in MARGENS_ALTERNATIVAS:
            imagem = cv2.copyMakeBorder(letra, margem, margem, margem, margem,
                                       cv2.BORDER_CONSTANT, value=255)
            referencia = cv2.copyMakeBorder(mascara, margem, margem, margem, margem,
                                           cv2.BORDER_CONSTANT, value=255)
            validar_entrada_cinza(imagem, referencia)
            variacoes[f'cinza_margem_{margem}'] = (imagem, referencia)
        saida.append(variacoes)
    return saida


def validar_entrada_cinza(imagem: np.ndarray, referencia: np.ndarray) -> None:
    validar_entrada_ocr(referencia)
    if imagem.dtype != np.uint8 or imagem.shape != referencia.shape:
        raise ValueError('Recorte em cinza incompatível com seu componente individual.')
    margem = (imagem.shape[0] - ALTURA_CARACTERE) // 2
    if not (np.all(imagem[:margem] == 255) and np.all(imagem[-margem:] == 255)
            and np.all(imagem[:, :margem] == 255) and np.all(imagem[:, -margem:] == 255)):
        raise ValueError('Recorte em cinza deve ter margem branca livre.')


def corrigir_inclinacao(entradas: list[np.ndarray]) -> list[np.ndarray]:
    """Estima a inclinação pelos momentos dos recortes, sem consultar o OCR.

    Exige pelo menos cinco símbolos inclinados no mesmo sentido. Os momentos
    também dependem do desenho da letra; por isso limitamos a correção a 15°.
    Arredondar a 5° evita interpretar pequenas diferenças como ângulos precisos.
    """
    angulos = []
    for entrada in entradas:
        validar_entrada_ocr(entrada)
        momentos = cv2.moments(255 - entrada)
        inclinacao = momentos['mu11'] / momentos['mu02'] if momentos['mu02'] else 0
        angulos.append(float(-np.degrees(np.arctan(inclinacao))))
    mediana = float(np.median(angulos))
    no_mesmo_sentido = sum(a * mediana > 0 and abs(a) >= ANGULO_MINIMO_CORRIGIVEL
                           for a in angulos)
    if (len(entradas) != TOTAL_CARACTERES
            or not ANGULO_MINIMO_CORRIGIVEL <= abs(mediana) <= ANGULO_MAXIMO_CORRIGIVEL
            or no_mesmo_sentido < MINIMO_DE_SIMBOLOS_INCLINADOS):
        return entradas
    corrigidas = []
    for entrada, angulo in zip(entradas, angulos):
        if (not ANGULO_MINIMO_CORRIGIVEL <= abs(angulo) <= ANGULO_MAXIMO_CORRIGIVEL
                or angulo * mediana <= 0):
            corrigidas.append(entrada)
            continue
        angulo = round(angulo / PASSO_DO_ANGULO) * PASSO_DO_ANGULO
        ampliada = cv2.copyMakeBorder(
            entrada, MARGEM_PARA_ROTACIONAR, MARGEM_PARA_ROTACIONAR,
            MARGEM_PARA_ROTACIONAR, MARGEM_PARA_ROTACIONAR,
            cv2.BORDER_CONSTANT, value=255)
        h, w = ampliada.shape
        matriz = cv2.getRotationMatrix2D((w / 2, h / 2), angulo, 1)
        rotacionada = cv2.warpAffine(ampliada, matriz, (w, h),
                                    flags=cv2.INTER_NEAREST, borderValue=255)
        y, x = np.where(rotacionada == 0)
        mascara = 255 - rotacionada[y.min():y.max()+1, x.min():x.max()+1]
        try:
            corrigida = preparar_caractere(Caractere((0, 0, mascara.shape[1], mascara.shape[0]), mascara))
            validar_entrada_ocr(corrigida)
        except ValueError:
            corrigida = entrada
        corrigidas.append(corrigida)
    return corrigidas


def validar_entrada_ocr(imagem: np.ndarray) -> None:
    """Aceita somente um símbolo binário com altura 100 e margem conhecida."""
    if (imagem.ndim != 2 or imagem.dtype != np.uint8
            or imagem.shape[0] not in ALTURAS_VALIDAS):
        raise ValueError("O OCR aceita somente um recorte preparado na etapa 6.")
    margem = (imagem.shape[0] - ALTURA_CARACTERE) // 2
    largura = imagem.shape[1] - 2 * margem
    if (not LARGURA_MINIMA_CARACTERE <= largura <= LARGURA_MAXIMA_CARACTERE
            or not np.all((imagem == 0) | (imagem == 255))):
        raise ValueError("O OCR aceita somente um recorte preparado na etapa 6.")
    if not (np.all(imagem[:margem] == 255) and np.all(imagem[-margem:] == 255)
            and np.all(imagem[:, :margem] == 255) and np.all(imagem[:, -margem:] == 255)):
        raise ValueError("O recorte deve ter uma margem branca livre de outros objetos.")
    componentes, _ = cv2.connectedComponents(255 - imagem, 8)
    if componentes != 2:
        raise ValueError("O OCR exige exatamente um componente por recorte.")


def gerar_variacoes(entrada: np.ndarray) -> dict[str, np.ndarray]:
    """Até seis preparos do MESMO caractere; nenhuma placa é acessada aqui.

    Base: altura 100 e margem 20. Outras margens: 10 e 30. A dilatação
    do fundo branco com kernel 2×2 reduz levemente os traços pretos.
    Variações que fragmentem ou eliminem o caractere não são enviadas ao OCR.
    """
    validar_entrada_ocr(entrada)
    if entrada.shape[0] != ALTURA_PADRAO_DA_ENTRADA:
        raise ValueError("As variações devem partir do recorte padrão com margem 20.")
    letra = entrada[MARGEM_PADRAO:-MARGEM_PADRAO, MARGEM_PADRAO:-MARGEM_PADRAO]
    candidatas = {"padrao": entrada}
    for afinar in (False, True):
        for margem in MARGENS_ALTERNATIVAS:
            if not afinar and margem == MARGEM_PADRAO:
                continue
            imagem = cv2.copyMakeBorder(letra, margem, margem, margem, margem,
                                       cv2.BORDER_CONSTANT, value=255)
            if afinar:
                imagem = cv2.dilate(imagem, np.ones(KERNEL_AFINAMENTO, np.uint8))
            nome = f"margem_{margem}" + ("_traco_fino" if afinar else "")
            try:
                validar_entrada_ocr(imagem)
            except ValueError:
                continue
            if not any(np.array_equal(imagem, existente) for existente in candidatas.values()):
                candidatas[nome] = imagem
    return candidatas
