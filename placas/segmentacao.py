"""Etapa 5 — binarizar a região, filtrar componentes e ordenar os caracteres.

A etapa 4 reutiliza esta etapa para avaliar cada região candidata, sem OCR.
"""
import cv2
import numpy as np

from placas.modelos import Caractere, Segmentacao


def _componentes(binaria: np.ndarray) -> list[Caractere]:
    altura, largura = binaria.shape
    total, rotulos, stats, _ = cv2.connectedComponentsWithStats(binaria, 8)
    caracteres = []
    for indice in range(1, total):  # 0 é o fundo.
        x, y, w, h, area = map(int, stats[indice])
        # Rejeita borda, cabeçalho, parafusos e regiões largas com letras unidas.
        if not (0.30 <= h / altura <= 0.88 and 0.012 <= w / largura <= 0.16):
            continue
        if not (0.08 <= w / h <= 1.05 and 0.10 <= area / (w * h) <= 0.95):
            continue
        if x <= 1 or y <= 1 or x + w >= largura - 1 or y + h >= altura - 1:
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
            if abs(dx) >= 2 * rh and 0.65 <= oh / rh <= 1.45:
                inclinacao = (oy + oh / 2 - centro_y) / dx
                if abs(inclinacao) <= 0.35:
                    inclinacoes.append(inclinacao)
        for inclinacao in inclinacoes:
            grupo = [c for c in caracteres
                     if abs(c.caixa[1] + c.caixa[3] / 2 - centro_y
                            - inclinacao * (c.caixa[0] + c.caixa[2] / 2 - centro_x)) < rh * 0.22
                     and 0.65 <= c.caixa[3] / rh <= 1.45]
            linhas.append(grupo)
    linha = max(linhas, key=lambda g: (len(g), sum(c.caixa[3] for c in g)))
    return sorted(linha, key=lambda c: c.caixa[0])


def _qualidade(caracteres: list[Caractere], largura: int) -> float:
    if not caracteres:
        return -100.0
    alturas = np.array([c.caixa[3] for c in caracteres])
    centros = np.array([c.caixa[1] + c.caixa[3] / 2 for c in caracteres])
    # Mede desalinhamento em relação à própria linha, inclusive quando inclinada.
    if len(caracteres) >= 3:
        centros_x = np.array([c.caixa[0] + c.caixa[2] / 2 for c in caracteres])
        coeficientes = np.polyfit(centros_x, centros, 1)
        if abs(coeficientes[0]) <= 0.35:
            centros = centros - np.polyval(coeficientes, centros_x)
    inicio = caracteres[0].caixa[0]
    fim = caracteres[-1].caixa[0] + caracteres[-1].caixa[2]
    return float(20 - 5 * abs(7 - len(caracteres))
                 - 4 * alturas.std() / alturas.mean()
                 - 4 * centros.std() / alturas.mean()
                 + 2 * (fim - inicio) / largura)


def segmentar(placa: np.ndarray) -> Segmentacao:
    """Testa Otsu/adaptativo nas duas polaridades, sem consultar o OCR."""
    h, w = placa.shape[:2]
    if min(h, w) < 10:
        raise ValueError("Região pequena demais para segmentar.")
    normalizada = cv2.resize(placa, (600, round(600 * h / w)))
    cinza = cv2.cvtColor(normalizada, cv2.COLOR_BGR2GRAY)
    suave = cv2.GaussianBlur(cinza, (3, 3), 0)
    opcoes = []
    for polaridade, base in [("caracteres escuros", suave),
                              ("caracteres claros", 255 - suave)]:
        # Inverter o cinza antes do adaptativo preserva o sentido da constante C.
        # Nas duas alternativas, o caractere fica branco na máscara final.
        _, otsu = cv2.threshold(base, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        adaptativa = cv2.adaptiveThreshold(
            base, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 9
        )
        for nome, binaria in [("Otsu", otsu), ("Adaptativo", adaptativa)]:
            # Abertura pequena é uma alternativa: preserva a opção com traços finos.
            aberta = cv2.morphologyEx(binaria, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
            for sufixo, mascara in [("", binaria), (" + abertura 2×2", aberta)]:
                caracteres = _componentes(mascara)
                opcoes.append(Segmentacao(normalizada, mascara, caracteres,
                                          f"{nome}{sufixo} · {polaridade}",
                                          _qualidade(caracteres, 600)))
    melhor = max(opcoes, key=lambda s: s.qualidade)
    # A geometria não mede a fidelidade dos traços. Num empate aproximado,
    # prefere Otsu sem abertura: o adaptativo pode apagar detalhes internos.
    # Só desempata entre sete componentes, mesma polaridade e mesmas posições.
    for opcao in opcoes:
        if (len(melhor.caracteres) == len(opcao.caracteres) == 7
                and opcao.metodo.startswith("Otsu ·")
                and opcao.metodo.split(" · ")[-1] == melhor.metodo.split(" · ")[-1]
                and melhor.qualidade - opcao.qualidade <= 0.05
                and all(abs((a.caixa[0] + a.caixa[2]/2) - (b.caixa[0] + b.caixa[2]/2))
                        <= min(a.caixa[2], b.caixa[2]) * 0.25
                        for a, b in zip(opcao.caracteres, melhor.caracteres))):
            return opcao
    return melhor
