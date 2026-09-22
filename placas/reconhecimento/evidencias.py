"""Regras de aceitação do OCR, sem acessar imagens ou chamar o Tesseract.

Uma resposta forte contém um símbolo e atinge a confiança mínima. Consenso
significa respostas fortes suficientes que concordam entre si. Duas respostas
fortes diferentes constituem conflito, mesmo que uma seja mais frequente.

Estas funções só consultam as tentativas recebidas; não alteram o histórico.
Não usam posição, formato de placa ou um caractere esperado para desempatar.
"""
from placas.config import CONFIANCA_MINIMA, MINIMO_DE_CONCORDANCIAS
from placas.modelos import Leitura, TentativaOCR


def selecionar_respostas_fortes(tentativas: list[TentativaOCR]) -> list[TentativaOCR]:
    """Ignora respostas desconhecidas e pontuações abaixo do limite configurado."""
    return [tentativa for tentativa in tentativas
            if tentativa.caractere != "?" and tentativa.confianca >= CONFIANCA_MINIMA]


def _caracteres_distintos(tentativas: list[TentativaOCR]) -> set[str]:
    return {tentativa.caractere for tentativa in tentativas}


def ha_consenso(respostas_fortes: list[TentativaOCR]) -> bool:
    """Exige a quantidade mínima de apoiadores e somente um caractere proposto."""
    return (len(respostas_fortes) >= MINIMO_DE_CONCORDANCIAS
            and len(_caracteres_distintos(respostas_fortes)) == 1)


def ha_conflito(respostas_fortes: list[TentativaOCR]) -> bool:
    """Uma resposta forte diferente basta para impedir a aceitação por consenso."""
    return len(_caracteres_distintos(respostas_fortes)) > 1


def falta_evidencia_sem_conflito(respostas_fortes: list[TentativaOCR]) -> bool:
    """Autoriza experimentar outro modo de leitura, sem esconder um conflito."""
    return (not ha_conflito(respostas_fortes)
            and len(respostas_fortes) < MINIMO_DE_CONCORDANCIAS)


def ha_consenso_em_escalas_distintas(respostas_fortes: list[TentativaOCR]) -> bool:
    """Dois modos na mesma altura não contam como duas escalas concordantes."""
    escalas_com_apoio = {tentativa.variacao for tentativa in respostas_fortes}
    return ha_consenso(respostas_fortes) and len(escalas_com_apoio) >= 2


def construir_leitura_aceita(respostas_fortes: list[TentativaOCR],
                            historico: list[TentativaOCR], motivo: str) -> Leitura:
    """Registra a menor confiança dos apoiadores, após o consenso ser verificado.

    O histórico inclui também respostas fracas e conflitantes de preparos
    anteriores: elas continuam visíveis para auditoria, sem votar novamente.
    """
    primeira_resposta = respostas_fortes[0]
    menor_confianca = min(tentativa.confianca for tentativa in respostas_fortes)
    return Leitura(primeira_resposta.caractere, primeira_resposta.bruto,
                   menor_confianca, historico, motivo)
