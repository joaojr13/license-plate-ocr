"""Exibição didática: uma função de interface para cada etapa do processamento.

Este módulo apenas mostra dados já produzidos. Não executa filtros nem OCR.
"""
import streamlit as st

from placas.saida.visualizacao import (desenhar_candidatas, desenhar_localizacao,
                                       desenhar_regioes_morfologia, desenhar_segmentacao)


def exibir_preparacao(localizacao):
    """Etapa 1 da página."""
    with st.expander("1 · Preparar a imagem", expanded=True):
        st.caption("Código desta etapa: placas/etapas/e1_preparacao.py · preparar_imagem()")
        st.write("A orientação da foto é corrigida quando há informação EXIF. Imagens grandes "
                 "são reduzidas para, no máximo, 1.400 pixels no maior lado, preservando a proporção. "
                 "Depois, a imagem é convertida para cinza e suavizada com um filtro Gaussiano 3×3 "
                 "para reduzir pequenos ruídos.")
        original, cinza, suave = st.columns(3)
        original.image(localizacao.imagem, channels="BGR", caption="Imagem usada na localização", width="stretch")
        cinza.image(localizacao.etapas["Cinza"], caption="Tons de cinza", width="stretch")
        suave.image(localizacao.etapas["Suavização"], caption="Suavização Gaussiana", width="stretch")


def exibir_bordas(localizacao):
    """Etapa 2 da página."""
    with st.expander("2 · Encontrar bordas"):
        st.caption("Código desta etapa: placas/etapas/e2_bordas.py · encontrar_bordas()")
        st.write("O detector Canny destaca mudanças de intensidade, que podem indicar limites de objetos. "
                 "Um fechamento 3×3 conecta pequenas falhas nessas bordas. "
                 "Os contornos resultantes geram uma primeira lista de regiões candidatas a placa.")
        st.image(localizacao.etapas["Bordas"], caption="Bordas após Canny e fechamento 3×3", width="stretch")
        st.caption("As bordas também aparecem na carroceria e no fundo: ainda não identificamos a placa.")


def exibir_morfologia(localizacao):
    """Etapa 3 da página."""
    with st.expander("3 · Aplicar morfologia para gerar outras candidatas"):
        st.caption("Código desta etapa: placas/etapas/e3_morfologia.py · aplicar_morfologia()")
        st.write("O black-hat é a diferença entre o fechamento da imagem em cinza e a própria imagem. "
                 "Ele destaca detalhes escuros sobre regiões claras. O top-hat faz a diferença entre "
                 "a imagem e sua abertura, destacando detalhes claros sobre regiões escuras, como os "
                 "caracteres de uma placa preta. As duas operações são testadas automaticamente. "
                 "Otsu transforma cada resposta em uma máscara binária.")
        st.write("Nessa máscara, o fechamento horizontal (dilatação seguida de erosão) conecta traços "
                 "próximos. Em seguida, uma abertura 3×3 (erosão seguida de dilatação) remove pequenos "
                 "ruídos. O processo é executado com dois tamanhos de kernel para procurar regiões "
                 "em escalas diferentes.")
        combinacoes = [(nome, tamanho) for nome in ["Black-hat", "Top-hat"] for tamanho in [17, 31]]
        for (operacao, tamanho), aba in zip(combinacoes, st.tabs([
            f"{nome} {tamanho}×7" for nome, tamanho in combinacoes
        ])):
            with aba:
                colunas = st.columns(2)
                for i, (nome, legenda) in enumerate([
                    (operacao, "a · Detalhes escuros destacados" if operacao == "Black-hat"
                     else "a · Detalhes claros destacados"),
                    (f"{operacao} · Limiarização", "b · Binarização por Otsu"),
                    (f"{operacao} · Fechamento", "c · Traços conectados pelo fechamento"),
                    (f"{operacao} · Abertura", "d · Máscara após remoção de pequenos ruídos"),
                ]):
                    colunas[i % 2].image(localizacao.etapas[f"{nome} {tamanho}"],
                                        caption=legenda, width="stretch")
                st.markdown(f'**Regiões candidatas geradas por {operacao} {tamanho}×7**')
                tipo = st.radio('Margens das regiões', ['Sem margem extra', 'Com margem extra'],
                                horizontal=True, key=f'margens_{operacao}_{tamanho}')
                caixas = localizacao.candidatas_morfologia.get(f'{operacao} {tamanho} · {tipo}', [])
                st.image(desenhar_regioes_morfologia(localizacao.imagem, caixas),
                         channels='BGR', width='stretch',
                         caption=f'{len(caixas)} regiões candidatas · {operacao} {tamanho}×7 · {tipo.lower()}')
                if not caixas:
                    st.info('Nenhuma região dessa operação passou pelos filtros de tamanho e proporção nessa opção.')
                st.caption('Retângulos amarelos: contornos da máscara final desta operação que passaram '
                           'pelos filtros geométricos. Ainda são candidatas, não placas confirmadas. '
                           'Na etapa 4, elas são comparadas com as regiões das outras operações e das bordas. '
                           'Alternar as margens muda apenas esta visualização; as duas opções já foram avaliadas.')
        st.info("O fechamento não sabe o que é uma placa. Ele gera regiões que serão avaliadas na próxima etapa.")


def exibir_localizacao(localizacao):
    """Etapa 4 da página."""
    segmentacao = localizacao.segmentacao
    with st.expander("4 · Escolher e recortar a provável placa"):
        st.caption("Código desta etapa: placas/etapas/e4_localizacao.py · selecionar_placa()")
        st.write("As regiões vindas das bordas e da morfologia são filtradas pelo tamanho e pelo formato: "
                 "os retângulos candidatos precisam ser mais largos que altos, com proporção entre 2 e 6,5 "
                 "antes da adição de margens. As candidatas da morfologia são testadas com e sem margem, "
                 "pois algumas já envolvem a placa inteira. Cada candidata passa por uma tentativa de segmentação, sem OCR.")
        st.write("A pontuação favorece uma quantidade próxima de sete componentes, alturas semelhantes, "
                 "centros alinhados e ocupação horizontal. A candidata com a maior pontuação é escolhida.")
        marcada, recorte = st.columns([3, 2])
        marcada.image(desenhar_localizacao(localizacao), channels="BGR", caption="Região selecionada", width="stretch")
        recorte.image(segmentacao.placa, channels="BGR", caption="Recorte normalizado para 600 pixels de largura", width="stretch")
        x, y, largura, altura = localizacao.caixa
        st.caption(f"Nesta imagem de trabalho: x={x}, y={y}, largura={largura}, altura={altura} pixels. "
                   f"Pontuação geométrica: {segmentacao.qualidade:.2f}. Não é uma probabilidade de acerto.")
        st.write("Uma região com objetos parecidos com letras pode ser escolhida incorretamente. "
                 "Por isso, é importante conferir o recorte.")
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
            st.caption('Pontuação geométrica e de segmentação; não é probabilidade. Nenhuma candidata '
                       'é enviada ao OCR nesta etapa.')
            numero = st.selectbox('Ampliar candidata', range(1, len(localizacao.candidatas)+1),
                                  format_func=lambda i: f'Candidata {i}', key='candidata_ampliada')
            candidata = localizacao.candidatas[numero-1]
            cx, cy, cw, ch = candidata.caixa
            st.image(localizacao.imagem[cy:cy+ch, cx:cx+cw], channels='BGR', width='stretch',
                     caption=f'Candidata {numero} · x={cx}, y={cy}, largura={cw}, altura={ch}')
            st.caption('A seleção acima serve apenas para inspecionar o recorte; a placa escolhida pelo sistema permanece a mesma.')


def exibir_segmentacao(segmentacao):
    """Etapa 5 da página."""
    with st.expander("5 · Binarizar a região e separar os caracteres"):
        st.caption("Código desta etapa: placas/etapas/e5_segmentacao.py · segmentar()")
        st.write("Voltamos à imagem recortada e criamos uma nova máscara, pois o fechamento anterior pode "
                 "ter unido as letras. São comparadas oito alternativas: Otsu e limiar adaptativo, "
                 "cada um com e sem abertura 2×2, procurando tanto caracteres escuros quanto claros. "
                 "Em todas as máscaras, os caracteres candidatos ficam brancos sobre fundo preto. "
                 "A escolha usa a geometria dos componentes, sem OCR.")
        st.write(f"**Alternativa selecionada nesta imagem: {segmentacao.metodo}.**")
        st.write("Os pixels brancos conectados formam componentes. Filtros de altura, largura e área "
                 "tentam eliminar bordas, parafusos e cabeçalhos. Os componentes de uma mesma linha "
                 "são ordenados da esquerda para a direita.")
        mascara, caixas = st.columns(2)
        mascara.image(segmentacao.binaria, caption="Máscara escolhida: objetos brancos sobre fundo preto", width="stretch")
        caixas.image(desenhar_segmentacao(segmentacao), channels="BGR", caption="Componentes selecionados e ordem de leitura", width="stretch")
        st.write(f"**Resultado: {len(segmentacao.caracteres)} componentes selecionados.**")
        st.caption("Um componente é uma região conectada de pixels; isso, sozinho, não garante que seja uma letra inteira.")


def exibir_preparacao_ocr(valida):
    """Etapa 6 da página."""
    with st.expander("6 · Validar e preparar cada recorte para o OCR"):
        st.caption("Código desta etapa: placas/etapas/e6_recortes.py · preparar_recortes()")
        st.write("São exigidos sete recortes válidos, ordenados e não sobrepostos. Cada máscara contém "
                 "somente o componente selecionado. A letra é convertida para preto sobre branco, "
                 "redimensionada para 100 pixels de altura e recebe uma margem branca de 20 pixels.")
        st.write("Antes do OCR, os momentos da máscara estimam a inclinação. Se pelo menos cinco "
                 "símbolos apontarem no mesmo sentido, aplicamos pequenas rotações automáticas, "
                 "limitadas a 15 graus. A estimativa não usa letras esperadas. O resultado é validado "
                 "novamente; as imagens exibidas e exportadas são as mesmas enviadas ao OCR.")
        st.write("Para leituras incertas, a etapa 6 gera variações do mesmo recorte: margens de 10, "
                 "20 e 30 pixels, com e sem leve redução dos traços pretos. São até seis "
                 "preparos, incluindo o padrão. Variações que eliminem ou fragmentem o símbolo "
                 "são descartadas antes de chegar ao OCR.")
        if valida:
            st.success("Os sete recortes desta imagem passaram pelas verificações de segmentação.")
        else:
            st.warning("A segmentação desta imagem não passou nas verificações. O OCR está bloqueado.")
        st.caption("As imagens preparadas aparecem acima, em “Entradas individuais do OCR”. A placa completa não é enviada.")


def exibir_ocr(formato_label, valida, motor_disponivel, resultado):
    """Etapa 7 da página."""
    with st.expander("7 · Reconhecer uma letra ou número por vez"):
        st.caption("Código desta etapa: placas/etapas/e7_ocr.py · reconhecer_caracteres()")
        st.write("Tesseract reconhece cada caractere localmente no modo PSM 10. Leituras incertas "
                 "recebem novos preparos e, quando necessário, uma tentativa no PSM 13. "
                 "Cada chamada recebe apenas um caractere. OpenCV localiza e segmenta a placa.")
        st.write("A leitura inicial exige confiança de pelo menos 60. Recuperações exigem duas "
                 "respostas concordantes acima desse limite, sem conflito forte. Caso contrário, "
                 "o resultado permanece ‘?’. Não há seleção manual de formato nem uso de outros motores.")
        st.write("Se o binário continuar inconclusivo, o mesmo caractere é recortado da placa em tons "
                 "de cinza e testado no PSM 10 com três margens. Duas margens devem concordar com "
                 "confiança ≥ 60, sem conflito forte entre as leituras em cinza. Esse consenso pode "
                 "resolver o conflito do binário. As respostas anteriores permanecem no histórico.")
        if resultado is not None:
            resultado_etapas = resultado
            st.success(f'OCR executado: {resultado_etapas["quantidade_chamadas_ocr"]} chamadas individuais concluídas.')
            st.dataframe([
                {"Posição": i, "Caractere aceito": leitura["caractere"],
                 "Candidatos observados": ", ".join(sorted({t["caractere"] for t in leitura["tentativas"]
                                                           if t["caractere"] != "?"})) or "Nenhum",
                 "Confiança": leitura["confianca"], "Decisão": leitura["motivo"]}
                for i, leitura in enumerate(resultado_etapas["leituras"], 1)
            ], hide_index=True, width="stretch")
            st.write("**Histórico das chamadas individuais**")
            st.dataframe([
                {"Posição": i, "Preparo": t["variacao"], "Motor": t.get("motor", "tesseract"), "Resposta bruta": t["bruto"],
                 "Caractere": t["caractere"], "Confiança": t["confianca"]}
                for i, leitura in enumerate(resultado_etapas["leituras"], 1)
                for t in leitura["tentativas"]
            ], hide_index=True, width="stretch")
            st.caption("Confiança é a pontuação do Tesseract, não uma probabilidade calibrada; -1 indica ausência de leitura.")
        elif not valida:
            st.warning("Etapa não executada: a segmentação precisa ser válida antes do reconhecimento.")
        elif not motor_disponivel:
            st.warning("Etapa não executada: o motor selecionado está indisponível neste computador.")
        else:
            st.info("Etapa pendente: use o botão “Reconhecer caracteres” acima.")


def exibir_resultado(resultado):
    """Etapa 8 da página."""
    with st.expander("8 · Concatenar, armazenar no array e exibir"):
        st.caption("Código desta etapa: placas/etapas/e8_resultado.py · consolidar_resultado()")
        st.write("Cada resposta aceita ocupa uma posição na lista de caracteres. Respostas vazias, "
                 "com vários símbolos ou fora do alfabeto permitido recebem “?”. Depois, o programa "
                 "junta as posições na ordem de leitura e armazena o texto consolidado na lista de placas.")
        if resultado is not None:
            resultado_etapas = resultado
            st.code(f'caracteres = {resultado_etapas["caracteres"]!r}\n'
                    f'texto = "".join(caracteres)  # {resultado_etapas["texto"]!r}\n'
                    f'placas = [texto]  # {resultado_etapas["placas"]!r}', language="python")
            st.write("O resultado desta execução está exibido acima e pode ser baixado com os recortes.")
        else:
            st.info("Ainda não há um resultado de OCR para esta imagem e este formato. "
                    "O array será exibido após o reconhecimento.")


def exibir_passos(localizacao, formato_label, valida, motor_disponivel, resultado=None):
    """Apresenta as oito etapas na mesma ordem do guia e dos módulos."""
    st.divider()
    st.header("Processo passo a passo")
    st.write("Acompanhe o que foi feito nesta imagem. Abra cada etapa para ver sua função "
             "e o resultado intermediário usado pelo programa.")
    st.caption("Preparação → bordas e morfologia → escolha da região → segmentação → OCR → array")
    exibir_preparacao(localizacao)
    exibir_bordas(localizacao)
    exibir_morfologia(localizacao)
    exibir_localizacao(localizacao)
    exibir_segmentacao(localizacao.segmentacao)
    exibir_preparacao_ocr(valida)
    exibir_ocr(formato_label, valida, motor_disponivel, resultado)
    exibir_resultado(resultado)
