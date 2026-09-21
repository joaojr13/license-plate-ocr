"""Os blocos visuais da página principal, na ordem em que aparecem.

app.py fica com o roteiro — entrada, localização, segmentação, OCR, resultado
— e cada bloco desenhado mora em uma função daqui. A ordem em que as funções
são chamadas é a ordem dos elementos na tela.
"""
import hashlib
from pathlib import Path

import streamlit as st

from interface import textos
from placas.etapas.e6_normalizacao import preparar_caractere
from placas.etapas.e6_recortes import preparar_recortes
from placas.etapas.e7_motor_ocr import verificar_tesseract
from placas.imagem import ler_imagem
from placas.modelos import Localizacao, Segmentacao
from placas.pipeline import localizar, reconhecer
from placas.saida.exportacao import imagens_das_tentativas, montar_pacote_zip
from placas.saida.visualizacao import desenhar_localizacao, desenhar_segmentacao

EXEMPLO = Path(__file__).resolve().parents[1] / "examples" / "veiculo_sintetico.png"
# Muda quando a segmentação muda, para invalidar o cache de execuções antigas.
VERSAO_DA_SEGMENTACAO = "candidatas-morfologia-v4"
VERSAO_DO_OCR = b"tesseract-unico-v1"


def configurar_pagina() -> None:
    st.set_page_config(page_title="Leitura de placas", page_icon="🚘", layout="wide")
    st.title("Reconhecimento de placas veiculares")
    st.caption("Visão computacional passo a passo · OpenCV + OCR individual")


def barra_lateral() -> tuple[object, bool, bool]:
    """Devolve o arquivo enviado, se o exemplo foi pedido e se o motor responde."""
    with st.sidebar:
        st.header("Imagem de entrada")
        arquivo = st.file_uploader("Foto do veículo", type=["jpg", "jpeg", "png", "webp"])
        demonstracao = st.checkbox("Usar exemplo sintético", value=False)
        st.caption("OCR: Tesseract · processamento local")
        st.info(textos.BARRA_LATERAL_NOTA)
        try:
            st.success(f"Tesseract {verificar_tesseract()} disponível")
            motor_disponivel = True
        except (RuntimeError, OSError) as exc:
            st.warning(str(exc))
            motor_disponivel = False
    return arquivo, demonstracao, motor_disponivel


def obter_imagem(arquivo, demonstracao: bool) -> bytes:
    """Sem foto nem exemplo, apresenta o fluxo e interrompe a página."""
    if arquivo is not None:
        return arquivo.getvalue()
    if demonstracao:
        conteudo = EXEMPLO.read_bytes()
        st.info(textos.EXEMPLO_SINTETICO)
        return conteudo
    st.write(textos.BOAS_VINDAS)
    st.markdown(textos.RESUMO_DO_FLUXO)
    st.stop()


@st.cache_data(show_spinner="Localizando a placa e separando os caracteres…", max_entries=5)
def _localizar_em_cache(dados: bytes, versao_segmentacao: str = VERSAO_DA_SEGMENTACAO):
    """Executa as etapas 1–5 dos módulos de processamento e guarda o resultado."""
    return localizar(ler_imagem(dados))


def localizar_placa(conteudo: bytes) -> Localizacao:
    """Etapas 1–5. Uma imagem sem placa plausível interrompe a página."""
    try:
        return _localizar_em_cache(conteudo)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()


def esquecer_resultado_de_outra_imagem(conteudo: bytes, formato: str) -> None:
    """O resultado guardado só vale para a mesma imagem, formato e versão do OCR."""
    chave = hashlib.sha256(conteudo + formato.encode() + VERSAO_DO_OCR).hexdigest()
    if st.session_state.get("chave") != chave:
        st.session_state["chave"] = chave
        st.session_state.pop("resultado", None)


def mostrar_regiao_e_segmentacao(localizacao: Localizacao) -> None:
    segmentacao = localizacao.segmentacao
    esquerda, direita = st.columns([3, 2])
    with esquerda:
        st.subheader("1 · Região localizada")
        st.image(desenhar_localizacao(localizacao), channels="BGR", width="stretch")
    with direita:
        st.subheader("2 · Caracteres segmentados")
        st.image(desenhar_segmentacao(segmentacao), channels="BGR", width="stretch")
        st.image(segmentacao.binaria, caption=f"Binarização: {segmentacao.metodo}",
                 width="stretch")
        st.write(f"**{len(segmentacao.caracteres)} recortes** encontrados, "
                 "ordenados da esquerda para a direita.")


def mostrar_entradas_do_ocr(segmentacao: Segmentacao, valida: bool) -> None:
    """Exibe exatamente as imagens que seriam enviadas ao motor.

    Quando a segmentação não passou nas verificações, mostra os recortes sem a
    correção de inclinação — o suficiente para inspecionar, sem chamar o OCR.
    """
    st.subheader("3 · Entradas individuais do OCR")
    if not segmentacao.caracteres:
        return
    entradas = (preparar_recortes(segmentacao) if valida
                else [preparar_caractere(c) for c in segmentacao.caracteres])
    for i, (coluna, entrada) in enumerate(zip(st.columns(len(entradas)), entradas)):
        with coluna:
            st.image(entrada, caption=f"Caractere {i+1}", width="stretch")


def botao_de_reconhecimento(segmentacao: Segmentacao, formato: str, habilitado: bool) -> None:
    """Guarda o resultado na sessão para sobreviver ao próximo redesenho da página."""
    if not st.button("Reconhecer caracteres", type="primary", disabled=not habilitado):
        return
    st.session_state.pop("resultado", None)
    try:
        with st.spinner("Reconhecendo caracteres e conferindo as leituras incertas…"):
            st.session_state["resultado"] = reconhecer(segmentacao, formato)
    except (ValueError, RuntimeError, OSError) as exc:
        st.error(f"Não foi possível concluir o OCR: {exc}")


def mostrar_resultado(segmentacao: Segmentacao, resultado: dict) -> None:
    st.subheader("4 · Resultado consolidado")
    st.metric("Texto reconhecido", resultado["texto"])
    st.code(f'caracteres = {resultado["caracteres"]!r}\n'
            f'placas = {resultado["placas"]!r}', language="python")
    for aviso in resultado["avisos"]:
        st.warning(aviso)
    st.dataframe([
        {"Posição": i, "Caractere": leitura["caractere"], "Confiança": leitura["confianca"],
         "Tentativas": len(leitura["tentativas"]), "Decisão": leitura["motivo"]}
        for i, leitura in enumerate(resultado["leituras"], 1)
    ], hide_index=True, width="stretch")
    st.caption(f'{resultado["quantidade_chamadas_ocr"]} chamadas individuais ao OCR. '
               'Confira os candidatos e cada tentativa na etapa 7 do passo a passo.')
    st.caption(textos.RESULTADO_CONFIANCA)
    _mostrar_downloads(segmentacao, resultado)


def _mostrar_downloads(segmentacao: Segmentacao, resultado: dict) -> None:
    """Exporta cada entrada realmente enviada, incluindo as tentativas adicionais."""
    imagens = imagens_das_tentativas(segmentacao, resultado)
    adicionais = {nome: imagem for nome, imagem in imagens.items() if 'cinza_' in nome}
    if adicionais:
        with st.expander("Recortes em tons de cinza enviados nas tentativas adicionais"):
            for nome, imagem in adicionais.items():
                st.image(imagem, caption=nome)
    st.download_button("Baixar resultado e recortes",
                       montar_pacote_zip(segmentacao, resultado),
                       "reconhecimento.zip", "application/zip")
