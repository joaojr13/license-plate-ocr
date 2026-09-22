"""Entrada e controles da página: receber a foto, inspecionar e pedir o OCR.

``app.py`` organiza o roteiro. As funções daqui desenham os controles e
recortes principais; ``sessao`` cuida da reutilização de resultados e
``relatorio`` apresenta as leituras e os downloads. A página chama cada
módulo diretamente para deixar explícita a responsabilidade de cada bloco.
"""
from pathlib import Path

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from interface import textos
from placas.etapas import e7_motor_ocr
from placas.etapas.e6_normalizacao import preparar_caractere
from placas.etapas.e6_recortes import preparar_recortes
from placas.modelos import Localizacao, Segmentacao
from placas.pipeline import reconhecer
from placas.saida.visualizacao import desenhar_localizacao, desenhar_segmentacao

EXEMPLO = Path(__file__).resolve().parents[1] / "examples" / "veiculo_sintetico.png"


def configurar_pagina() -> None:
    """Define a apresentação geral antes de criar os demais controles."""
    st.set_page_config(page_title="Leitura de placas", page_icon="🚘", layout="wide")
    st.title("Reconhecimento de placas veiculares")
    st.caption("Visão computacional passo a passo · OpenCV + OCR individual")


def barra_lateral() -> tuple[UploadedFile | None, bool, bool]:
    """Devolve o arquivo enviado, se o exemplo foi pedido e se o motor responde."""
    with st.sidebar:
        st.header("Imagem de entrada")
        arquivo = st.file_uploader("Foto do veículo", type=["jpg", "jpeg", "png", "webp"])
        demonstracao = st.checkbox("Usar exemplo sintético", value=False)
        st.caption("OCR: Tesseract · processamento local")
        st.info(textos.BARRA_LATERAL_NOTA)
        try:
            # Chamado pelo módulo, e não por um nome importado: este arquivo é
            # carregado uma vez e fica em cache, então um nome importado ficaria
            # preso à função original e os testes de interface não conseguiriam
            # substituir o motor.
            st.success(f"Tesseract {e7_motor_ocr.verificar_tesseract()} disponível")
            motor_disponivel = True
        except (RuntimeError, OSError) as exc:
            st.warning(str(exc))
            motor_disponivel = False
    return arquivo, demonstracao, motor_disponivel


def obter_imagem(arquivo: UploadedFile | None, demonstracao: bool) -> bytes:
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


def mostrar_regiao_e_segmentacao(localizacao: Localizacao) -> None:
    """Compara a região localizada com a separação dos símbolos já calculada."""
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
    for posicao, (coluna, entrada) in enumerate(zip(st.columns(len(entradas)), entradas), start=1):
        with coluna:
            st.image(entrada, caption=f"Caractere {posicao}", width="stretch")


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
