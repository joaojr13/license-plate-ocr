"""Etapa 5 — binarizar a região, filtrar componentes e ordenar os caracteres.

A etapa 4 reutiliza esta etapa para avaliar cada região candidata, sem OCR.
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


def _componentes(binaria: np.ndarray) -> list[Caractere]:
    altura, largura = binaria.shape
    total, rotulos, stats, _ = cv2.connectedComponentsWithStats(binaria, 8)
    caracteres = []
    for indice in range(1, total):  # 0 é o fundo.
        x, y, w, h, area = map(int, stats[indice])
        # Rejeita borda, cabeçalho, parafusos e regiões largas com letras unidas.
        if not (ALTURA_RELATIVA_COMPONENTE[0] <= h / altura <= ALTURA_RELATIVA_COMPONENTE[1]
                and LARGURA_RELATIVA_COMPONENTE[0] <= w / largura
                <= LARGURA_RELATIVA_COMPONENTE[1]):
            continue
        if not (PROPORCAO_COMPONENTE[0] <= w / h <= PROPORCAO_COMPONENTE[1]
                and PREENCHIMENTO_COMPONENTE[0] <= area / (w * h)
                <= PREENCHIMENTO_COMPONENTE[1]):
            continue
        borda = MARGEM_BORDA_COMPONENTE
        if x <= borda or y <= borda or x + w >= largura - borda or y + h >= altura - borda:
            continue
        mascara = np.uint8(rotulos[y:y+h, x:x+w] == indice) * 255
        caracteres.append(Caractere((x, y, w, h), mascara))
    if not caracteres:
        return []
    # Seleciona a linha dominante, eliminando pequenos dizeres acima da placa.
    linhas = []
    for referencia in caracteres:
        rx, ry, rw, rh = referencia.caixa
        centro_x, centro_y = rx + rw / 2, ry + rh / 2
        inclinacoes = [0.0]
        for outra in caracteres:
            ox, oy, ow, oh = outra.caixa
            dx = ox + ow / 2 - centro_x
            if (abs(dx) >= DISTANCIA_MINIMA_ENTRE_VIZINHOS * rh
                    and ALTURA_SEMELHANTE[0] <= oh / rh <= ALTURA_SEMELHANTE[1]):
                inclinacao = (oy + oh / 2 - centro_y) / dx
                if abs(inclinacao) <= INCLINACAO_MAXIMA_DA_LINHA:
                    inclinacoes.append(inclinacao)
        for inclinacao in inclinacoes:
            grupo = [c for c in caracteres
                     if abs(c.caixa[1] + c.caixa[3] / 2 - centro_y
                            - inclinacao * (c.caixa[0] + c.caixa[2] / 2 - centro_x))
                     < rh * TOLERANCIA_DE_ALINHAMENTO
                     and ALTURA_SEMELHANTE[0] <= c.caixa[3] / rh <= ALTURA_SEMELHANTE[1]]
            linhas.append(grupo)
    linha = max(linhas, key=lambda g: (len(g), sum(c.caixa[3] for c in g)))
    return sorted(linha, key=lambda c: c.caixa[0])


def _qualidade(caracteres: list[Caractere], largura: int) -> float:
    if not caracteres:
        return PONTUACAO_SEM_CARACTERES
    alturas = np.array([c.caixa[3] for c in caracteres])
    centros = np.array([c.caixa[1] + c.caixa[3] / 2 for c in caracteres])
    # Mede desalinhamento em relação à própria linha, inclusive quando inclinada.
    if len(caracteres) >= MINIMO_PARA_AJUSTAR_A_LINHA:
        centros_x = np.array([c.caixa[0] + c.caixa[2] / 2 for c in caracteres])
        coeficientes = np.polyfit(centros_x, centros, 1)
        if abs(coeficientes[0]) <= INCLINACAO_MAXIMA_DA_LINHA:
            centros = centros - np.polyval(coeficientes, centros_x)
    inicio = caracteres[0].caixa[0]
    fim = caracteres[-1].caixa[0] + caracteres[-1].caixa[2]
    return float(PONTUACAO_BASE
                 - PESO_QUANTIDADE * abs(TOTAL_CARACTERES - len(caracteres))
                 - PESO_ALTURA * alturas.std() / alturas.mean()
                 - PESO_ALINHAMENTO * centros.std() / alturas.mean()
                 + PESO_OCUPACAO * (fim - inicio) / largura)


def segmentar(placa: np.ndarray) -> Segmentacao:
    """Testa Otsu/adaptativo nas duas polaridades, sem consultar o OCR."""
    h, w = placa.shape[:2]
    if min(h, w) < LADO_MINIMO_REGIAO:
        raise ValueError("Região pequena demais para segmentar.")
    normalizada = cv2.resize(
        placa, (LARGURA_NORMALIZADA_PLACA, round(LARGURA_NORMALIZADA_PLACA * h / w)))
    cinza = cv2.cvtColor(normalizada, cv2.COLOR_BGR2GRAY)
    suave = cv2.GaussianBlur(cinza, KERNEL_SUAVIZACAO, 0)
    opcoes = []
    for polaridade, base in [("caracteres escuros", suave),
                              ("caracteres claros", 255 - suave)]:
        # Inverter o cinza antes do adaptativo preserva o sentido da constante C.
        # Nas duas alternativas, o caractere fica branco na máscara final.
        _, otsu = cv2.threshold(base, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        adaptativa = cv2.adaptiveThreshold(
            base, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,
            ADAPTATIVO_TAMANHO_DO_BLOCO, ADAPTATIVO_CONSTANTE,
        )
        for nome, binaria in [("Otsu", otsu), ("Adaptativo", adaptativa)]:
            # Abertura pequena é uma alternativa: preserva a opção com traços finos.
            aberta = cv2.morphologyEx(binaria, cv2.MORPH_OPEN,
                                       np.ones(KERNEL_ABERTURA_SEGMENTACAO, np.uint8))
            for sufixo, mascara in [("", binaria), (" + abertura 2×2", aberta)]:
                caracteres = _componentes(mascara)
                opcoes.append(Segmentacao(normalizada, mascara, caracteres,
                                          f"{nome}{sufixo} · {polaridade}",
                                          _qualidade(caracteres,
                                                     LARGURA_NORMALIZADA_PLACA)))
    melhor = max(opcoes, key=lambda s: s.qualidade)
    # A geometria não mede a fidelidade dos traços. Num empate aproximado,
    # prefere Otsu sem abertura: o adaptativo pode apagar detalhes internos.
    # Só desempata entre sete componentes, mesma polaridade e mesmas posições.
    for opcao in opcoes:
        if (len(melhor.caracteres) == len(opcao.caracteres) == TOTAL_CARACTERES
                and opcao.metodo.startswith("Otsu ·")
                and opcao.metodo.split(" · ")[-1] == melhor.metodo.split(" · ")[-1]
                and melhor.qualidade - opcao.qualidade <= TOLERANCIA_DE_DESEMPATE
                and all(abs((a.caixa[0] + a.caixa[2]/2) - (b.caixa[0] + b.caixa[2]/2))
                        <= min(a.caixa[2], b.caixa[2]) * TOLERANCIA_DE_POSICAO_NO_DESEMPATE
                        for a, b in zip(opcao.caracteres, melhor.caracteres))):
            return opcao
    return melhor
