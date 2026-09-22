"""Inspeção visual das regiões já avaliadas pelo algoritmo de localização.

Uma candidata é um retângulo que pode conter a placa. Os filtros, a pontuação
e a escolha desse retângulo pertencem ao processamento; aqui apenas mostramos
seus resultados. Alterar uma opção na galeria nunca muda a região escolhida.
"""

import streamlit as st

from interface import textos
from placas.etapas.e3_morfologia import FASES, nome_da_etapa
from placas.localizacao.candidatas import nome_da_fonte
from placas.modelos import CandidataPlaca, Localizacao
from placas.saida.visualizacao import desenhar_candidatas, desenhar_regioes_morfologia


def mostrar_fontes_morfologicas(localizacao: Localizacao) -> None:
    """Mostra a transformação das máscaras e as caixas geradas por cada fonte.

    Cada aba representa uma operação (Black-hat ou Top-hat) e uma largura de
    kernel. O controle de margens consulta caixas já guardadas na análise.
    """
    combinacoes = [(nome, tamanho) for nome in ["Black-hat", "Top-hat"] for tamanho in [17, 31]]
    titulos = [f"{nome} {tamanho}×7" for nome, tamanho in combinacoes]
    for (operacao, tamanho), aba in zip(combinacoes, st.tabs(titulos)):
        with aba:
            colunas = st.columns(2)
            legendas = [
                "a · Detalhes escuros destacados" if operacao == "Black-hat"
                else "a · Detalhes claros destacados",
                "b · Binarização por Otsu",
                "c · Traços conectados pelo fechamento",
                "d · Máscara após remoção de pequenos ruídos",
            ]
            for indice, (fase, legenda) in enumerate(zip(("",) + FASES, legendas)):
                colunas[indice % 2].image(
                    localizacao.etapas[nome_da_etapa(operacao, tamanho, fase)],
                    caption=legenda, width="stretch")

            st.markdown(f'**Regiões candidatas geradas por {operacao} {tamanho}×7**')
            tipo_margem = st.radio(
                "Margens das regiões", ["Sem margem extra", "Com margem extra"],
                horizontal=True, key=f'margens_{operacao}_{tamanho}')
            fonte = nome_da_fonte(operacao, tamanho, tipo_margem)
            caixas = localizacao.candidatas_morfologia.get(fonte, [])
            st.image(desenhar_regioes_morfologia(localizacao.imagem, caixas),
                     channels="BGR", width="stretch",
                     caption=f'{len(caixas)} regiões candidatas · {operacao} {tamanho}×7 · {tipo_margem.lower()}')
            if not caixas:
                st.info(textos.MORFOLOGIA_SEM_REGIOES)
            st.caption(textos.MORFOLOGIA_LEGENDA)


def mostrar_comparacao_de_candidatas(localizacao: Localizacao) -> None:
    """Compara recortes, pontuações e quantidades de componentes encontrados.

    O algoritmo já entrega até cinco candidatas distintas para exibir. Os
    cartões mostram essa lista na mesma ordem, com a escolhida primeiro.
    """
    if not localizacao.candidatas:
        return
    st.markdown("**Recortes comparados na escolha da placa**")
    st.caption(f'{localizacao.total_candidatas} regiões avaliadas; abaixo estão até cinco '
               'candidatas distintas. Regiões muito sobrepostas foram agrupadas apenas '
               'para exibição. A pontuação não é uma probabilidade.')
    for inicio in range(0, len(localizacao.candidatas), 3):
        colunas = st.columns(3)
        candidatas_da_linha = localizacao.candidatas[inicio:inicio + 3]
        for deslocamento, candidata in enumerate(candidatas_da_linha):
            numero = inicio + deslocamento + 1
            with colunas[deslocamento]:
                _mostrar_cartao(localizacao, candidata, numero)

    if st.checkbox("Ver regiões candidatas", key="ver_candidatas"):
        _mostrar_comparacao_detalhada(localizacao)


def _mostrar_cartao(localizacao: Localizacao, candidata: CandidataPlaca, numero: int) -> None:
    """Apresenta uma candidata com os mesmos critérios usados na comparação."""
    x, y, largura, altura = candidata.caixa
    recorte = localizacao.imagem[y:y + altura, x:x + largura]
    with st.container(border=True):
        st.markdown(f'**Candidata {numero}**')
        st.image(recorte, channels="BGR", width="stretch",
                 caption=f'Recorte da candidata {numero}')
        if candidata.caixa == localizacao.caixa:
            st.success("Escolhida pelo sistema")
        elif candidata.quantidade_caracteres < 4:
            st.caption("Descartada: menos de 4 componentes")
        else:
            st.caption("Não escolhida")
        st.write(f'Pontuação: **{candidata.qualidade:.2f}** · '
                 f'Componentes: **{candidata.quantidade_caracteres}**')
        st.caption(f'Binarização: {candidata.metodo}')


def _mostrar_comparacao_detalhada(localizacao: Localizacao) -> None:
    """Marca as regiões na foto e permite ampliar um recorte para inspeção."""
    st.image(desenhar_candidatas(localizacao), channels="BGR", width="stretch",
             caption="Verde: região escolhida · Amarelo: outras regiões avaliadas")
    st.caption(f'{localizacao.total_candidatas} regiões avaliadas. Exibindo até cinco distintas, '
               'ordenadas por pontuação, com a escolhida em primeiro lugar. Regiões muito '
               'sobrepostas foram agrupadas apenas nesta visualização.')
    comparacao = []
    for numero, candidata in enumerate(localizacao.candidatas, start=1):
        if candidata.caixa == localizacao.caixa:
            situacao = "Escolhida"
        elif candidata.quantidade_caracteres < 4:
            situacao = "Descartada: menos de 4 caracteres"
        else:
            situacao = "Outra candidata"
        comparacao.append({
            "Candidata": numero,
            "Pontuação": round(candidata.qualidade, 2),
            "Caracteres encontrados": candidata.quantidade_caracteres,
            "Situação": situacao,
            "Binarização": candidata.metodo,
        })
    st.dataframe(comparacao, hide_index=True, width="stretch")
    st.caption(textos.LOCALIZACAO_NOTA)
    numero = st.selectbox(
        "Ampliar candidata", range(1, len(localizacao.candidatas) + 1),
        format_func=lambda indice: f'Candidata {indice}', key="candidata_ampliada")
    candidata = localizacao.candidatas[numero - 1]
    x, y, largura, altura = candidata.caixa
    recorte = localizacao.imagem[y:y + altura, x:x + largura]
    st.image(recorte, channels="BGR", width="stretch",
             caption=f'Candidata {numero} · x={x}, y={y}, largura={largura}, altura={altura}')
    st.caption(textos.LOCALIZACAO_AMPLIAR)
