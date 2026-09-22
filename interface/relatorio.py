"""Apresentação do resultado, das tentativas individuais e dos arquivos para baixar.

As leituras chegam prontas do processamento. Este módulo apenas organiza
essas evidências para a pessoa conferir: não escolhe caracteres nem altera
as regras de confiança.
"""

import streamlit as st

from interface import textos
from placas.modelos import Segmentacao
from placas.saida.exportacao import imagens_das_tentativas, montar_pacote_zip


def mostrar_resultado(segmentacao: Segmentacao, resultado: dict) -> None:
    """Mostra o texto final, as decisões por posição e a opção de exportação."""
    st.subheader("4 · Resultado consolidado")
    st.metric("Texto reconhecido", resultado["texto"])
    st.code(f'caracteres = {resultado["caracteres"]!r}\n'
            f'placas = {resultado["placas"]!r}', language="python")
    for aviso in resultado["avisos"]:
        st.warning(aviso)

    decisoes = []
    for posicao, leitura in enumerate(resultado["leituras"], start=1):
        decisoes.append({
            "Posição": posicao,
            "Caractere": leitura["caractere"],
            "Confiança": leitura["confianca"],
            "Tentativas": len(leitura["tentativas"]),
            "Decisão": leitura["motivo"],
        })
    st.dataframe(decisoes, hide_index=True, width="stretch")
    st.caption(f'{resultado["quantidade_chamadas_ocr"]} chamadas individuais ao OCR. '
               'Confira os candidatos e cada tentativa na etapa 7 do passo a passo.')
    st.caption(textos.RESULTADO_CONFIANCA)
    _mostrar_downloads(segmentacao, resultado)


def mostrar_historico_do_ocr(resultado: dict) -> None:
    """Detalha a decisão por caractere e cada chamada que contribuiu para ela.

    A primeira tabela reúne candidatos por posição. A segunda mantém uma
    linha por chamada, incluindo respostas recusadas e a preparação usada.
    """
    st.success(f'OCR executado: {resultado["quantidade_chamadas_ocr"]} chamadas individuais concluídas.')
    resumo = []
    chamadas = []
    for posicao, leitura in enumerate(resultado["leituras"], start=1):
        candidatos = set()
        for tentativa in leitura["tentativas"]:
            if tentativa["caractere"] != "?":
                candidatos.add(tentativa["caractere"])
            chamadas.append({
                "Posição": posicao,
                "Preparo": tentativa["variacao"],
                "Motor": tentativa.get("motor", "tesseract"),
                "Resposta bruta": tentativa["bruto"],
                "Caractere": tentativa["caractere"],
                "Confiança": tentativa["confianca"],
            })
        resumo.append({
            "Posição": posicao,
            "Caractere aceito": leitura["caractere"],
            "Candidatos observados": ", ".join(sorted(candidatos)) or "Nenhum",
            "Confiança": leitura["confianca"],
            "Decisão": leitura["motivo"],
        })

    st.dataframe(resumo, hide_index=True, width="stretch")
    st.write("**Histórico das chamadas individuais**")
    st.dataframe(chamadas, hide_index=True, width="stretch")
    st.caption(textos.OCR_NOTA)


def _mostrar_downloads(segmentacao: Segmentacao, resultado: dict) -> None:
    """Exibe preparos adicionais e oferece as entradas reais junto do resultado.

    A montagem dos arquivos pertence a ``placas.saida.exportacao``. Aqui
    usamos esse conteúdo para a visualização e para o botão de download.
    """
    imagens = imagens_das_tentativas(segmentacao, resultado)
    adicionais = {
        nome: imagem for nome, imagem in imagens.items()
        if "cinza_" in nome or "escala_" in nome
    }
    if adicionais:
        with st.expander("Recortes em tons de cinza e escalas enviados nas tentativas adicionais"):
            for nome, imagem in adicionais.items():
                st.image(imagem, caption=nome)
    st.download_button("Baixar resultado e recortes",
                       montar_pacote_zip(segmentacao, resultado),
                       "reconhecimento.zip", "application/zip")
