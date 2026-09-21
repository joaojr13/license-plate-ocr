"""Etapa 7 alternativa: reconhecimento local de um recorte por chamada."""
from functools import lru_cache
from pathlib import Path
import string

from placas.modelos import Leitura, TentativaOCR
from placas.preparacao_ocr import gerar_variacoes, validar_entrada_ocr


@lru_cache(maxsize=1)
def carregar_motor():
    import easyocr
    pasta = Path(__file__).resolve().parents[1] / '.modelos_easyocr'
    return easyocr.Reader(['en'], gpu=False, detector=False,
                          model_storage_directory=str(pasta),
                          user_network_directory=str(pasta / 'user_network'),
                          verbose=False)


def reconhecer_caracteres(entradas, formato='livre'):
    if len(entradas) != 7 or formato not in ('livre', 'antiga', 'mercosul', 'quatro_letras'):
        raise ValueError('São necessários sete recortes e um formato válido.')
    for entrada in entradas:
        validar_entrada_ocr(entrada)
    motor = carregar_motor()
    leituras = []
    for indice, entrada in enumerate(entradas):
        permitidos = string.ascii_uppercase + string.digits
        if formato != 'livre':
            letra = (indice < 4 if formato == 'quatro_letras' else
                     indice < 3 or (formato == 'mercosul' and indice == 4))
            permitidos = string.ascii_uppercase if letra else string.digits
        historico = []
        for nome, imagem in gerar_variacoes(entrada, margem_ampliada=True).items():
            validar_entrada_ocr(imagem)
            # recognize usa a imagem individual inteira como uma única região.
            # Não há detecção de texto nem envio da placa completa.
            resposta = motor.recognize(imagem, allowlist=permitidos,
                                        detail=1, paragraph=False, workers=0)
            bruto = ''.join(str(item[1]).strip().upper() for item in resposta)
            confianca = min((float(item[2]) * 100 for item in resposta), default=-1)
            valor = bruto if len(bruto) == 1 and bruto in permitidos else '?'
            historico.append(TentativaOCR(nome, valor, bruto, confianca, psm=None))
            if nome == 'padrao' and valor != '?' and confianca >= 60:
                break
        fortes = [t for t in historico if t.caractere != '?' and t.confianca >= 60]
        candidatos = {t.caractere for t in fortes}
        aceito = len(candidatos) == 1 and (len(historico) == 1 or len(fortes) >= 2)
        leituras.append(Leitura(fortes[0].caractere if aceito else '?',
                               historico[0].bruto,
                               min(t.confianca for t in fortes) if aceito else -1,
                               historico,
                               'EasyOCR: leitura suficiente.' if aceito else
                               'EasyOCR: evidência insuficiente ou conflitante.'))
    return leituras


def verificar_disponibilidade():
    import importlib.util
    if importlib.util.find_spec("easyocr") is None:
        raise RuntimeError("Instale requirements-easyocr.txt para usar EasyOCR.")
