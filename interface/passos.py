"""Exibição didática: uma função de interface para cada etapa do processamento.

Este módulo apenas mostra dados já produzidos. Não executa filtros nem OCR.
"""
import streamlit as st

from interface import textos
from placas.etapas.e3_morfologia import FASES, nome_da_etapa
from placas.etapas.e4_localizacao import nome_da_fonte
from placas.saida.visualizacao import (desenhar_candidatas, desenhar_localizacao,
                                       desenhar_regioes_morfologia, desenhar_segmentacao)


def exibir_preparacao(localizacao):
    """Etapa 1 da página."""
    with st.expander("1 · Preparar a imagem", expanded=True):
        st.caption("Código desta etapa: placas/etapas/e1_preparacao.py · preparar_imagem()")
        st.write(textos.PREPARACAO)
        original, cinza, suave = st.columns(3)
        original.image(localizacao.imagem, channels="BGR", caption="Imagem usada na localização", width="stretch")
        cinza.image(localizacao.etapas["Cinza"], caption="Tons de cinza", width="stretch")
        suave.image(localizacao.etapas["Suavização"], caption="Suavização Gaussiana", width="stretch")


def exibir_bordas(localizacao):
    """Etapa 2 da página."""
    with st.expander("2 · Encontrar bordas"):
        st.caption("Código desta etapa: placas/etapas/e2_bordas.py · encontrar_bordas()")
        st.write(textos.BORDAS)
        st.image(localizacao.etapas["Bordas"], caption="Bordas após Canny e fechamento 3×3", width="stretch")
        st.caption(textos.BORDAS_OBSERVACAO)


def exibir_morfologia(localizacao):
    """Etapa 3 da página."""
    with st.expander("3 · Aplicar morfologia para gerar outras candidatas"):
        st.caption("Código desta etapa: placas/etapas/e3_morfologia.py · aplicar_morfologia()")
        st.write(textos.MORFOLOGIA_OPERACOES)
        st.write(textos.MORFOLOGIA_MASCARA)
        combinacoes = [(nome, tamanho) for nome in ["Black-hat", "Top-hat"] for tamanho in [17, 31]]
        for (operacao, tamanho), aba in zip(combinacoes, st.tabs([
            f"{nome} {tamanho}×7" for nome, tamanho in combinacoes
        ])):
            with aba:
                colunas = st.columns(2)
                legendas = [
                    "a · Detalhes escuros destacados" if operacao == "Black-hat"
                    else "a · Detalhes claros destacados",
                    "b · Binarização por Otsu",
                    "c · Traços conectados pelo fechamento",
                    "d · Máscara após remoção de pequenos ruídos",
                ]
                for i, (fase, legenda) in enumerate(zip(("",) + FASES, legendas)):
                    colunas[i % 2].image(
                        localizacao.etapas[nome_da_etapa(operacao, tamanho, fase)],
                        caption=legenda, width="stretch")
                st.markdown(f'**Regiões candidatas geradas por {operacao} {tamanho}×7**')
                tipo = st.radio('Margens das regiões', ['Sem margem extra', 'Com margem extra'],
                                horizontal=True, key=f'margens_{operacao}_{tamanho}')
                caixas = localizacao.candidatas_morfologia.get(
                    nome_da_fonte(operacao, tamanho, tipo), [])
                st.image(desenhar_regioes_morfologia(localizacao.imagem, caixas),
                         channels='BGR', width='stretch',
                         caption=f'{len(caixas)} regiões candidatas · {operacao} {tamanho}×7 · {tipo.lower()}')
                if not caixas:
                    st.info(textos.MORFOLOGIA_SEM_REGIOES)
                st.caption(textos.MORFOLOGIA_LEGENDA)
        st.info(textos.MORFOLOGIA_NOTA)


def exibir_localizacao(localizacao):
    """Etapa 4 da página."""
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
        if localizacao.candidatas:
            st.markdown('**Recortes comparados na escolha da placa**')
            st.caption(f'{localizacao.total_candidatas} regiões avaliadas; abaixo estão até cinco '
                       'candidatas distintas. Regiões muito sobrepostas foram agrupadas apenas '
                       'para exibição. A pontuação não é uma probabilidade.')
            for inicio in range(0, len(localizacao.candidatas), 3):
                colunas = st.columns(3)
                for deslocamento, candidata in enumerate(localizacao.candidatas[inicio:inicio+3]):
                    numero = inicio + deslocamento + 1
                    cx, cy, cw, ch = candidata.caixa
                    with colunas[deslocamento]:
                        with st.container(border=True):
                            st.markdown(f'**Candidata {numero}**')
                            st.image(localizacao.imagem[cy:cy+ch, cx:cx+cw],
                                     channels='BGR', width='stretch',
                                     caption=f'Recorte da candidata {numero}')
                            if candidata.caixa == localizacao.caixa:
                                st.success('Escolhida pelo sistema')
                            elif candidata.quantidade_caracteres < 4:
                                st.caption('Descartada: menos de 4 componentes')
                            else:
                                st.caption('Não escolhida')
                            st.write(f'Pontuação: **{candidata.qualidade:.2f}** · '
                                     f'Componentes: **{candidata.quantidade_caracteres}**')
                            st.caption(f'Binarização: {candidata.metodo}')
        if localizacao.candidatas and st.checkbox('Ver regiões candidatas', key='ver_candidatas'):
            st.image(desenhar_candidatas(localizacao), channels='BGR', width='stretch',
                     caption='Verde: região escolhida · Amarelo: outras regiões avaliadas')
            st.caption(f'{localizacao.total_candidatas} regiões avaliadas. Exibindo até cinco distintas, '
                       'ordenadas por pontuação, com a escolhida em primeiro lugar. Regiões muito '
                       'sobrepostas foram agrupadas apenas nesta visualização.')
            st.dataframe([
                {'Candidata': i, 'Pontuação': round(c.qualidade, 2),
                 'Caracteres encontrados': c.quantidade_caracteres,
                 'Situação': ('Escolhida' if c.caixa == localizacao.caixa else
                              'Descartada: menos de 4 caracteres' if c.quantidade_caracteres < 4 else
                              'Outra candidata'), 'Binarização': c.metodo}
                for i, c in enumerate(localizacao.candidatas, 1)
            ], hide_index=True, width='stretch')
            st.caption(textos.LOCALIZACAO_NOTA)
            numero = st.selectbox('Ampliar candidata', range(1, len(localizacao.candidatas)+1),
                                  format_func=lambda i: f'Candidata {i}', key='candidata_ampliada')
            candidata = localizacao.candidatas[numero-1]
            cx, cy, cw, ch = candidata.caixa
            st.image(localizacao.imagem[cy:cy+ch, cx:cx+cw], channels='BGR', width='stretch',
                     caption=f'Candidata {numero} · x={cx}, y={cy}, largura={cw}, altura={ch}')
            st.caption(textos.LOCALIZACAO_AMPLIAR)


def exibir_segmentacao(segmentacao):
    """Etapa 5 da página."""
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


def exibir_preparacao_ocr(valida):
    """Etapa 6 da página."""
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


def exibir_ocr(valida, motor_disponivel, resultado):
    """Etapa 7 da página."""
    with st.expander("7 · Reconhecer uma letra ou número por vez"):
        st.caption("Código desta etapa: placas/etapas/e7_decisao.py · reconhecer_caracteres()")
        st.write(textos.OCR_MOTOR)
        st.write(textos.OCR_CONFIANCA)
        st.write(textos.OCR_CINZA)
        if resultado is not None:
            st.success(f'OCR executado: {resultado["quantidade_chamadas_ocr"]} chamadas individuais concluídas.')
            st.dataframe([
                {"Posição": i, "Caractere aceito": leitura["caractere"],
                 "Candidatos observados": ", ".join(sorted({t["caractere"] for t in leitura["tentativas"]
                                                           if t["caractere"] != "?"})) or "Nenhum",
                 "Confiança": leitura["confianca"], "Decisão": leitura["motivo"]}
                for i, leitura in enumerate(resultado["leituras"], 1)
            ], hide_index=True, width="stretch")
            st.write("**Histórico das chamadas individuais**")
            st.dataframe([
                {"Posição": i, "Preparo": t["variacao"], "Motor": t.get("motor", "tesseract"), "Resposta bruta": t["bruto"],
                 "Caractere": t["caractere"], "Confiança": t["confianca"]}
                for i, leitura in enumerate(resultado["leituras"], 1)
                for t in leitura["tentativas"]
            ], hide_index=True, width="stretch")
            st.caption(textos.OCR_NOTA)
        elif not valida:
            st.warning(textos.OCR_SEM_SEGMENTACAO)
        elif not motor_disponivel:
            st.warning(textos.OCR_SEM_MOTOR)
        else:
            st.info(textos.OCR_PENDENTE)


def exibir_resultado(resultado):
    """Etapa 8 da página."""
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


def exibir_passos(localizacao, valida, motor_disponivel, resultado=None):
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
