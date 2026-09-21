"""A página, em uma tela: cada linha é uma etapa do fluxo.

Execute com: streamlit run app.py

Os blocos visuais estão em interface/componentes.py e o passo a passo em
interface/passos.py. O processamento em si nunca é chamado daqui direto:
tudo passa por placas/pipeline.py.
"""
import streamlit as st

from interface import componentes, textos
from interface.passos import exibir_passos
from placas.validacao import validar_segmentacao

# A página usa alfabeto livre; o CLI aceita 'antiga' e 'mercosul' (main.py).
FORMATO = "livre"


def segmentacao_valida(segmentacao) -> bool:
    """Avisa na tela quando os recortes não podem ir ao OCR, sem interromper."""
    try:
        validar_segmentacao(segmentacao)
        return True
    except ValueError as exc:
        st.warning(str(exc))
        return False


componentes.configurar_pagina()
arquivo, demonstracao, motor_disponivel = componentes.barra_lateral()
conteudo = componentes.obter_imagem(arquivo, demonstracao)

localizacao = componentes.localizar_placa(conteudo)          # Etapas 1–5.
segmentacao = localizacao.segmentacao
componentes.esquecer_resultado_de_outra_imagem(conteudo, FORMATO)

componentes.mostrar_regiao_e_segmentacao(localizacao)
valida = segmentacao_valida(segmentacao)
componentes.mostrar_entradas_do_ocr(segmentacao, valida)

componentes.botao_de_reconhecimento(                          # Etapas 6–8.
    segmentacao, FORMATO, habilitado=valida and motor_disponivel)

resultado = st.session_state.get("resultado")
if resultado is not None:
    componentes.mostrar_resultado(segmentacao, resultado)

exibir_passos(localizacao, valida, motor_disponivel, resultado)
st.caption(textos.RODAPE)
