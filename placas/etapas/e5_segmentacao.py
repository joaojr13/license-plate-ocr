"""Etapa 5 — binarizar a região, filtrar componentes e ordenar os caracteres.

A etapa 4 reutiliza esta etapa para avaliar cada região candidata, sem OCR.
O arquivo segue a ordem do raciocínio: gerar as oito binarizações possíveis,
extrair os componentes de cada uma, escolher a linha de caracteres, pontuar
o resultado e ficar com a alternativa de melhor pontuação.
"""
import cv2
import numpy as np

from placas.config import (ADAPTATIVO_CONSTANTE, ADAPTATIVO_TAMANHO_DO_BLOCO,
                           ALTURA_RELATIVA_COMPONENTE, ALTURA_SEMELHANTE,
                           DISTANCIA_MINIMA_ENTRE_VIZINHOS, INCLINACAO_MAXIMA_DA_LINHA,
                           KERNEL_ABERTURA_SEGMENTACAO, KERNEL_SUAVIZACAO,
                           LADO_MINIMO_REGIAO, LARGURA_NORMALIZADA_PLACA,
                           LARGURA_RELATIVA_COMPONENTE, MARGEM_BORDA_COMPONENTE,
                           MINIMO_PARA_AJUSTAR_A_LINHA, PESO_ALINHAMENTO, PESO_ALTURA,
                           PESO_OCUPACAO, PESO_QUANTIDADE, PONTUACAO_BASE,
                           PONTUACAO_SEM_CARACTERES, PREENCHIMENTO_COMPONENTE,
                           PROPORCAO_COMPONENTE, TOLERANCIA_DE_ALINHAMENTO,
                           TOLERANCIA_DE_DESEMPATE, TOLERANCIA_DE_POSICAO_NO_DESEMPATE,
                           TOTAL_CARACTERES)
from placas.modelos import Caractere, Segmentacao

# Rótulos que compõem o nome do método, exibido na página e usado no desempate.
POLARIDADES = ("caracteres escuros", "caracteres claros")
LIMIARIZACOES = ("Otsu", "Adaptativo")
SEM_ABERTURA, COM_ABERTURA = "", " + abertura 2×2"


def nome_do_metodo(limiarizacao: str, abertura: str, polaridade: str) -> str:
    return f"{limiarizacao}{abertura} · {polaridade}"


def _centro(caixa) -> tuple[float, float]:
    x, y, w, h = caixa
    return x + w / 2, y + h / 2


# --- 5a · Quais componentes conectados podem ser um caractere ----------------


def _e_caractere_plausivel(w: int, h: int, area: int, largura: int, altura: int) -> bool:
    """Rejeita borda, cabeçalho, parafusos e regiões largas com letras unidas."""
    return (ALTURA_RELATIVA_COMPONENTE[0] <= h / altura <= ALTURA_RELATIVA_COMPONENTE[1]
            and LARGURA_RELATIVA_COMPONENTE[0] <= w / largura <= LARGURA_RELATIVA_COMPONENTE[1]
            and PROPORCAO_COMPONENTE[0] <= w / h <= PROPORCAO_COMPONENTE[1]
            and PREENCHIMENTO_COMPONENTE[0] <= area / (w * h) <= PREENCHIMENTO_COMPONENTE[1])


def _encosta_na_borda(x: int, y: int, w: int, h: int, largura: int, altura: int) -> bool:
    borda = MARGEM_BORDA_COMPONENTE
    return x <= borda or y <= borda or x + w >= largura - borda or y + h >= altura - borda


def _componentes_plausiveis(binaria: np.ndarray) -> list[Caractere]:
    """Cada região branca conectada que tem tamanho e forma de caractere."""
    altura, largura = binaria.shape
    total, rotulos, stats, _ = cv2.connectedComponentsWithStats(binaria, 8)
    caracteres = []
    for indice in range(1, total):  # 0 é o fundo.
        x, y, w, h, area = map(int, stats[indice])
        if not _e_caractere_plausivel(w, h, area, largura, altura):
            continue
        if _encosta_na_borda(x, y, w, h, largura, altura):
            continue
        mascara = np.uint8(rotulos[y:y+h, x:x+w] == indice) * 255
        caracteres.append(Caractere((x, y, w, h), mascara))
    return caracteres


# --- 5b · Qual desses componentes forma a linha da placa ---------------------


def _inclinacoes_candidatas(referencia: Caractere, caracteres: list[Caractere]) -> list[float]:
    """Ângulos sugeridos por vizinhos distantes e de altura parecida.

    A linha horizontal (0.0) entra sempre. Cada vizinho suficientemente
    afastado propõe a inclinação da reta que o liga à referência, o que
    permite aceitar placas fotografadas de lado.
    """
    centro_x, centro_y = _centro(referencia.caixa)
    rh = referencia.caixa[3]
    inclinacoes = [0.0]
    for outra in caracteres:
        ox, oy, ow, oh = outra.caixa
        dx = ox + ow / 2 - centro_x
        if (abs(dx) >= DISTANCIA_MINIMA_ENTRE_VIZINHOS * rh
                and ALTURA_SEMELHANTE[0] <= oh / rh <= ALTURA_SEMELHANTE[1]):
            inclinacao = (oy + oh / 2 - centro_y) / dx
            if abs(inclinacao) <= INCLINACAO_MAXIMA_DA_LINHA:
                inclinacoes.append(inclinacao)
    return inclinacoes


def _alinhados(caracteres: list[Caractere], referencia: Caractere,
               inclinacao: float) -> list[Caractere]:
    """Componentes próximos da reta que passa pela referência, com altura parecida."""
    centro_x, centro_y = _centro(referencia.caixa)
    rh = referencia.caixa[3]
    grupo = []
    for c in caracteres:
        cx, cy = _centro(c.caixa)
        desvio = abs(cy - centro_y - inclinacao * (cx - centro_x))
        if (desvio < rh * TOLERANCIA_DE_ALINHAMENTO
                and ALTURA_SEMELHANTE[0] <= c.caixa[3] / rh <= ALTURA_SEMELHANTE[1]):
            grupo.append(c)
    return grupo


def _linha_dominante(caracteres: list[Caractere]) -> list[Caractere]:
    """A maior linha possível, eliminando pequenos dizeres acima da placa.

    Testa cada componente como referência e cada inclinação que ele sugere,
    formando um grupo por hipótese. Vence o grupo com mais componentes e,
    em caso de empate, o de maior altura somada.
    """
    linhas = []
    for referencia in caracteres:
        for inclinacao in _inclinacoes_candidatas(referencia, caracteres):
            linhas.append(_alinhados(caracteres, referencia, inclinacao))
    linha = max(linhas, key=lambda g: (len(g), sum(c.caixa[3] for c in g)))
    return sorted(linha, key=lambda c: c.caixa[0])


def _componentes(binaria: np.ndarray) -> list[Caractere]:
    """Os caracteres da linha dominante, ordenados da esquerda para a direita."""
    caracteres = _componentes_plausiveis(binaria)
    if not caracteres:
        return []
    return _linha_dominante(caracteres)


# --- 5c · Quanto essa linha parece a de uma placa ----------------------------


def _desvio_da_propria_linha(caracteres: list[Caractere]) -> np.ndarray:
    """Distância de cada centro até a reta dos centros, inclusive se inclinada."""
    centros = np.array([c.caixa[1] + c.caixa[3] / 2 for c in caracteres])
    if len(caracteres) < MINIMO_PARA_AJUSTAR_A_LINHA:
        return centros
    centros_x = np.array([c.caixa[0] + c.caixa[2] / 2 for c in caracteres])
    coeficientes = np.polyfit(centros_x, centros, 1)
    if abs(coeficientes[0]) > INCLINACAO_MAXIMA_DA_LINHA:
        return centros
    return centros - np.polyval(coeficientes, centros_x)


def _qualidade(caracteres: list[Caractere], largura: int) -> float:
    """Premia sete componentes, alturas iguais, centros alinhados e boa ocupação.

    É uma pontuação geométrica comparável entre candidatas, não uma
    probabilidade de a região ser mesmo uma placa.
    """
    if not caracteres:
        return PONTUACAO_SEM_CARACTERES
    alturas = np.array([c.caixa[3] for c in caracteres])
    centros = _desvio_da_propria_linha(caracteres)
    inicio = caracteres[0].caixa[0]
    fim = caracteres[-1].caixa[0] + caracteres[-1].caixa[2]
    return float(PONTUACAO_BASE
                 - PESO_QUANTIDADE * abs(TOTAL_CARACTERES - len(caracteres))
                 - PESO_ALTURA * alturas.std() / alturas.mean()
                 - PESO_ALINHAMENTO * centros.std() / alturas.mean()
                 + PESO_OCUPACAO * (fim - inicio) / largura)


# --- 5d · As oito binarizações comparadas ------------------------------------


def _binarizar(base: np.ndarray) -> dict[str, np.ndarray]:
    """Otsu (limiar global) e adaptativo (limiar por vizinhança), na mesma base."""
    _, otsu = cv2.threshold(base, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    adaptativa = cv2.adaptiveThreshold(
        base, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,
        ADAPTATIVO_TAMANHO_DO_BLOCO, ADAPTATIVO_CONSTANTE,
    )
    return dict(zip(LIMIARIZACOES, (otsu, adaptativa)))


def _alternativas(normalizada: np.ndarray, suave: np.ndarray) -> list[Segmentacao]:
    """Duas polaridades × dois limiares × com e sem abertura 2×2."""
    opcoes = []
    # Inverter o cinza antes do adaptativo preserva o sentido da constante C.
    # Nas duas polaridades, o caractere fica branco na máscara final.
    for polaridade, base in zip(POLARIDADES, (suave, 255 - suave)):
        for limiarizacao, binaria in _binarizar(base).items():
            # Abertura pequena é uma alternativa: preserva a opção com traços finos.
            aberta = cv2.morphologyEx(binaria, cv2.MORPH_OPEN,
                                      np.ones(KERNEL_ABERTURA_SEGMENTACAO, np.uint8))
            for abertura, mascara in ((SEM_ABERTURA, binaria), (COM_ABERTURA, aberta)):
                caracteres = _componentes(mascara)
                opcoes.append(Segmentacao(
                    normalizada, mascara, caracteres,
                    nome_do_metodo(limiarizacao, abertura, polaridade),
                    _qualidade(caracteres, LARGURA_NORMALIZADA_PLACA)))
    return opcoes


def _mesma_polaridade(a: Segmentacao, b: Segmentacao) -> bool:
    return a.metodo.split(" · ")[-1] == b.metodo.split(" · ")[-1]


def _mesmas_posicoes(a: Segmentacao, b: Segmentacao) -> bool:
    """Os caracteres das duas alternativas estão praticamente nos mesmos lugares."""
    return all(abs((x.caixa[0] + x.caixa[2]/2) - (y.caixa[0] + y.caixa[2]/2))
               <= min(x.caixa[2], y.caixa[2]) * TOLERANCIA_DE_POSICAO_NO_DESEMPATE
               for x, y in zip(a.caracteres, b.caracteres))


def _desempatar_por_otsu(melhor: Segmentacao, opcoes: list[Segmentacao]) -> Segmentacao:
    """Num empate aproximado, prefere Otsu sem abertura.

    A geometria não mede a fidelidade dos traços, e o adaptativo pode apagar
    detalhes internos (o vértice do W, por exemplo). Só desempata entre sete
    componentes, mesma polaridade e mesmas posições.
    """
    otsu_simples = nome_do_metodo(LIMIARIZACOES[0], SEM_ABERTURA, "")
    for opcao in opcoes:
        if (len(melhor.caracteres) == len(opcao.caracteres) == TOTAL_CARACTERES
                and opcao.metodo.startswith(otsu_simples)
                and _mesma_polaridade(opcao, melhor)
                and melhor.qualidade - opcao.qualidade <= TOLERANCIA_DE_DESEMPATE
                and _mesmas_posicoes(opcao, melhor)):
            return opcao
    return melhor


def segmentar(placa: np.ndarray) -> Segmentacao:
    """Testa Otsu/adaptativo nas duas polaridades, sem consultar o OCR."""
    h, w = placa.shape[:2]
    if min(h, w) < LADO_MINIMO_REGIAO:
        raise ValueError("Região pequena demais para segmentar.")
    normalizada = cv2.resize(
        placa, (LARGURA_NORMALIZADA_PLACA, round(LARGURA_NORMALIZADA_PLACA * h / w)))
    cinza = cv2.cvtColor(normalizada, cv2.COLOR_BGR2GRAY)
    suave = cv2.GaussianBlur(cinza, KERNEL_SUAVIZACAO, 0)
    opcoes = _alternativas(normalizada, suave)
    return _desempatar_por_otsu(max(opcoes, key=lambda s: s.qualidade), opcoes)
