"""Reutilização de análises e validade dos resultados guardados pela página.

O Streamlit executa a página novamente quando o usuário altera um controle.
O cache evita repetir a localização da mesma foto; o estado da sessão mantém
o resultado do OCR entre essas execuções. São mecanismos diferentes: trocar
a imagem deve descartar o resultado anterior, mesmo que haja análises no cache.
"""

import hashlib

import streamlit as st

from placas.imagem import ler_imagem
from placas.modelos import Localizacao
from placas.pipeline import localizar

# Alterar estas versões quando as regras do processamento forem modificadas
# impede que a página reutilize respostas produzidas pelo algoritmo anterior.
VERSAO_DA_SEGMENTACAO = "candidatas-morfologia-v4"
VERSAO_DO_OCR = b"tesseract-escalas-v2"


@st.cache_data(show_spinner="Localizando a placa e separando os caracteres…", max_entries=5)
def _localizar_em_cache(
    dados: bytes, versao_segmentacao: str = VERSAO_DA_SEGMENTACAO
) -> Localizacao:
    """Converte o arquivo e executa as etapas 1–5 uma vez por entrada e versão.

    ``versao_segmentacao`` participa da chave do cache mesmo sem ser usada
    no corpo da função. O cache considera os argumentos recebidos.
    """
    return localizar(ler_imagem(dados))


def localizar_placa(conteudo: bytes) -> Localizacao:
    """Obtém a análise; uma foto sem placa plausível interrompe a página."""
    try:
        return _localizar_em_cache(conteudo)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()


def esquecer_resultado_de_outra_imagem(conteudo: bytes, formato: str) -> None:
    """Descarta o OCR anterior quando a foto, o formato ou as regras mudam.

    O resumo SHA-256 identifica a entrada sem guardar outra cópia da foto na
    sessão. Ele serve para comparação; não participa do reconhecimento.
    """
    chave = hashlib.sha256(conteudo + formato.encode() + VERSAO_DO_OCR).hexdigest()
    if st.session_state.get("chave") != chave:
        st.session_state["chave"] = chave
        st.session_state.pop("resultado", None)
