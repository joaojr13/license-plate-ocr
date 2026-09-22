"""Roteiro didático: uma função de apresentação para cada uma das oito etapas.

Leia ``exibir_passos`` para seguir a ordem completa. Cada etapa combina a
explicação de ``textos`` com imagens já produzidas pelo processamento. As
galerias de regiões ficam em ``candidatas`` e o histórico do OCR em
``relatorio``. Este módulo não executa filtros, escolhe regiões ou chama OCR.
"""
import streamlit as st

from interface import textos
from interface.candidatas import mostrar_comparacao_de_candidatas, mostrar_fontes_morfologicas
from interface.relatorio import mostrar_historico_do_ocr
from placas.modelos import Localizacao, Segmentacao
from placas.saida.visualizacao import desenhar_localizacao, desenhar_segmentacao


def exibir_preparacao(localizacao: Localizacao) -> None:
    """Etapa 1: compara a imagem de trabalho, os tons de cinza e a suavização."""
    with st.expander("1 · Preparar a imagem", expanded=True):
        st.caption("Código desta etapa: placas/etapas/e1_preparacao.py · preparar_imagem()")
        st.write(textos.PREPARACAO)
        original, cinza, suave = st.columns(3)
        original.image(localizacao.imagem, channels="BGR", caption="Imagem usada na localização", width="stretch")
        cinza.image(localizacao.etapas["Cinza"], caption="Tons de cinza", width="stretch")
        suave.image(localizacao.etapas["Suavização"], caption="Suavização Gaussiana", width="stretch")


def exibir_bordas(localizacao: Localizacao) -> None:
    """Etapa 2: mostra bordas conectadas, que ainda podem pertencer a outros objetos."""
    with st.expander("2 · Encontrar bordas"):
        st.caption("Código desta etapa: placas/etapas/e2_bordas.py · encontrar_bordas()")
        st.write(textos.BORDAS)
        st.image(localizacao.etapas["Bordas"], caption="Bordas após Canny e fechamento 3×3", width="stretch")
        st.caption(textos.BORDAS_OBSERVACAO)


def exibir_morfologia(localizacao: Localizacao) -> None:
    """Etapa 3: explica as operações e permite inspecionar suas máscaras e regiões."""
    with st.expander("3 · Aplicar morfologia para gerar outras candidatas"):
        st.caption("Código desta etapa: placas/etapas/e3_morfologia.py · aplicar_morfologia()")
        st.write(textos.MORFOLOGIA_OPERACOES)
        st.write(textos.MORFOLOGIA_MASCARA)
        mostrar_fontes_morfologicas(localizacao)
        st.info(textos.MORFOLOGIA_NOTA)


def exibir_localizacao(localizacao: Localizacao) -> None:
    """Etapa 4: explica a escolha e permite comparar a vencedora às outras candidatas."""
    segmentacao = localizacao.segmentacao
    with st.expander("4 · Escolher e recortar a provável placa"):
        st.caption("Código desta etapa: placas/etapas/e4_localizacao.py · selecionar_placa()")
        st.write(textos.LOCALIZACAO_FILTROS)
        st.write(textos.LOCALIZACAO_PONTUACAO)
        marcada, recorte = st.columns([3, 2])
        marcada.image(desenhar_localizacao(localizacao), channels="BGR", caption="Região selecionada", width="stretch")
        recorte.image(segmentacao.placa, channels="BGR", caption="Recorte normalizado para 600 pixels de largura", width="stretch")
        x, y, largura, altura = localizacao.caixa
        st.caption(f"Nesta imagem de trabalho: x={x}, y={y}, largura={largura}, altura={altura} pixels. "
                   f"Pontuação geométrica: {segmentacao.qualidade:.2f}. Não é uma probabilidade de acerto.")
        st.write(textos.LOCALIZACAO_CUIDADO)
        mostrar_comparacao_de_candidatas(localizacao)


def exibir_segmentacao(segmentacao: Segmentacao) -> None:
    """Etapa 5: relaciona a máscara escolhida aos componentes em ordem de leitura."""
    with st.expander("5 · Binarizar a região e separar os caracteres"):
        st.caption("Código desta etapa: placas/etapas/e5_segmentacao.py · segmentar()")
        st.write(textos.SEGMENTACAO_ALTERNATIVAS)
        st.write(f"**Alternativa selecionada nesta imagem: {segmentacao.metodo}.**")
        st.write(textos.SEGMENTACAO_COMPONENTES)
        mascara, caixas = st.columns(2)
        mascara.image(segmentacao.binaria, caption="Máscara escolhida: objetos brancos sobre fundo preto", width="stretch")
        caixas.image(desenhar_segmentacao(segmentacao), channels="BGR", caption="Componentes selecionados e ordem de leitura", width="stretch")
        st.write(f"**Resultado: {len(segmentacao.caracteres)} componentes selecionados.**")
        st.caption(textos.SEGMENTACAO_NOTA)


def exibir_preparacao_ocr(valida: bool) -> None:
    """Etapa 6: explica os preparos individuais e informa se os recortes são válidos."""
    with st.expander("6 · Validar e preparar cada recorte para o OCR"):
        st.caption("Código desta etapa: placas/etapas/e6_recortes.py · preparar_recortes()")
        st.write(textos.RECORTES_VALIDACAO)
        st.write(textos.RECORTES_INCLINACAO)
        st.write(textos.RECORTES_VARIACOES)
        if valida:
            st.success(textos.RECORTES_VALIDOS)
        else:
            st.warning(textos.RECORTES_INVALIDOS)
        st.caption(textos.RECORTES_NOTA)


def exibir_ocr(valida: bool, motor_disponivel: bool, resultado: dict | None) -> None:
    """Etapa 7: mostra as evidências do OCR ou por que ele ainda não foi executado."""
    with st.expander("7 · Reconhecer uma letra ou número por vez"):
        st.caption("Código desta etapa: placas/etapas/e7_decisao.py · reconhecer_caracteres()")
        st.write(textos.OCR_MOTOR)
        st.write(textos.OCR_CONFIANCA)
        st.write(textos.OCR_CINZA)
        if resultado is not None:
            mostrar_historico_do_ocr(resultado)
        elif not valida:
            st.warning(textos.OCR_SEM_SEGMENTACAO)
        elif not motor_disponivel:
            st.warning(textos.OCR_SEM_MOTOR)
        else:
            st.info(textos.OCR_PENDENTE)


def exibir_resultado(resultado: dict | None) -> None:
    """Etapa 8: mostra como a concatenação preserva a ordem dos caracteres."""
    with st.expander("8 · Concatenar, armazenar no array e exibir"):
        st.caption("Código desta etapa: placas/etapas/e8_resultado.py · consolidar_resultado()")
        st.write(textos.RESULTADO_ARRAY)
        if resultado is not None:
            st.code(f'caracteres = {resultado["caracteres"]!r}\n'
                    f'texto = "".join(caracteres)  # {resultado["texto"]!r}\n'
                    f'placas = [texto]  # {resultado["placas"]!r}', language="python")
            st.write(textos.RESULTADO_DISPONIVEL)
        else:
            st.info(textos.RESULTADO_PENDENTE)


def exibir_passos(localizacao: Localizacao, valida: bool, motor_disponivel: bool,
                  resultado: dict | None = None) -> None:
    """Apresenta as oito etapas na mesma ordem do guia e dos módulos."""
    st.divider()
    st.header("Processo passo a passo")
    st.write(textos.PASSOS_INTRO)
    st.caption(textos.PASSOS_RESUMO)
    exibir_preparacao(localizacao)
    exibir_bordas(localizacao)
    exibir_morfologia(localizacao)
    exibir_localizacao(localizacao)
    exibir_segmentacao(localizacao.segmentacao)
    exibir_preparacao_ocr(valida)
    exibir_ocr(valida, motor_disponivel, resultado)
    exibir_resultado(resultado)
