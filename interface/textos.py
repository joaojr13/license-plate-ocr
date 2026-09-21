"""Os textos didáticos da página, separados do código que monta o layout.

Cada constante é exibida por uma das funções de interface/passos.py. Manter a
prosa aqui deixa passos.py mostrando apenas a estrutura das oito seções, e
permite revisar ou traduzir o texto sem abrir o código da interface.
"""

PREPARACAO = (
    "A orientação da foto é corrigida quando há informação EXIF. Imagens grandes "
    "são reduzidas para, no máximo, 1.400 pixels no maior lado, preservando a proporção. "
    "Depois, a imagem é convertida para cinza e suavizada com um filtro Gaussiano 3×3 "
    "para reduzir pequenos ruídos."
)

BORDAS = (
    "O detector Canny destaca mudanças de intensidade, que podem indicar limites de objetos. "
    "Um fechamento 3×3 conecta pequenas falhas nessas bordas. "
    "Os contornos resultantes geram uma primeira lista de regiões candidatas a placa."
)

BORDAS_OBSERVACAO = (
    "As bordas também aparecem na carroceria e no fundo: ainda não identificamos a placa."
)

MORFOLOGIA_OPERACOES = (
    "O black-hat é a diferença entre o fechamento da imagem em cinza e a própria imagem. "
    "Ele destaca detalhes escuros sobre regiões claras. O top-hat faz a diferença entre "
    "a imagem e sua abertura, destacando detalhes claros sobre regiões escuras, como os "
    "caracteres de uma placa preta. As duas operações são testadas automaticamente. "
    "Otsu transforma cada resposta em uma máscara binária."
)

MORFOLOGIA_MASCARA = (
    "Nessa máscara, o fechamento horizontal (dilatação seguida de erosão) conecta traços "
    "próximos. Em seguida, uma abertura 3×3 (erosão seguida de dilatação) remove pequenos "
    "ruídos. O processo é executado com dois tamanhos de kernel para procurar regiões "
    "em escalas diferentes."
)

MORFOLOGIA_SEM_REGIOES = (
    'Nenhuma região dessa operação passou pelos filtros de tamanho e proporção nessa opção.'
)

MORFOLOGIA_LEGENDA = (
    'Retângulos amarelos: contornos da máscara final desta operação que passaram '
                           'pelos filtros geométricos. Ainda são candidatas, não placas confirmadas. '
                           'Na etapa 4, elas são comparadas com as regiões das outras operações e das bordas. '
                           'Alternar as margens muda apenas esta visualização; as duas opções já foram avaliadas.'
)

MORFOLOGIA_NOTA = (
    "O fechamento não sabe o que é uma placa. Ele gera regiões que serão avaliadas na próxima etapa."
)

LOCALIZACAO_FILTROS = (
    "As regiões vindas das bordas e da morfologia são filtradas pelo tamanho e pelo formato: "
    "os retângulos candidatos precisam ser mais largos que altos, com proporção entre 2 e 6,5 "
    "antes da adição de margens. As candidatas da morfologia são testadas com e sem margem, "
    "pois algumas já envolvem a placa inteira. Cada candidata passa por uma tentativa de segmentação, sem OCR."
)

LOCALIZACAO_PONTUACAO = (
    "A pontuação favorece uma quantidade próxima de sete componentes, alturas semelhantes, "
    "centros alinhados e ocupação horizontal. A candidata com a maior pontuação é escolhida."
)

LOCALIZACAO_CUIDADO = (
    "Uma região com objetos parecidos com letras pode ser escolhida incorretamente. "
    "Por isso, é importante conferir o recorte."
)

LOCALIZACAO_NOTA = (
    'Pontuação geométrica e de segmentação; não é probabilidade. Nenhuma candidata '
                       'é enviada ao OCR nesta etapa.'
)

LOCALIZACAO_AMPLIAR = (
    'A seleção acima serve apenas para inspecionar o recorte; a placa escolhida pelo sistema permanece a mesma.'
)

SEGMENTACAO_ALTERNATIVAS = (
    "Voltamos à imagem recortada e criamos uma nova máscara, pois o fechamento anterior pode "
    "ter unido as letras. São comparadas oito alternativas: Otsu e limiar adaptativo, "
    "cada um com e sem abertura 2×2, procurando tanto caracteres escuros quanto claros. "
    "Em todas as máscaras, os caracteres candidatos ficam brancos sobre fundo preto. "
    "A escolha usa a geometria dos componentes, sem OCR."
)

SEGMENTACAO_COMPONENTES = (
    "Os pixels brancos conectados formam componentes. Filtros de altura, largura e área "
    "tentam eliminar bordas, parafusos e cabeçalhos. Os componentes de uma mesma linha "
    "são ordenados da esquerda para a direita."
)

SEGMENTACAO_NOTA = (
    "Um componente é uma região conectada de pixels; isso, sozinho, não garante que seja uma letra inteira."
)

RECORTES_VALIDACAO = (
    "São exigidos sete recortes válidos, ordenados e não sobrepostos. Cada máscara contém "
    "somente o componente selecionado. A letra é convertida para preto sobre branco, "
    "redimensionada para 100 pixels de altura e recebe uma margem branca de 20 pixels."
)

RECORTES_INCLINACAO = (
    "Antes do OCR, os momentos da máscara estimam a inclinação. Se pelo menos cinco "
    "símbolos apontarem no mesmo sentido, aplicamos pequenas rotações automáticas, "
    "limitadas a 15 graus. A estimativa não usa letras esperadas. O resultado é validado "
    "novamente; as imagens exibidas e exportadas são as mesmas enviadas ao OCR."
)

RECORTES_VARIACOES = (
    "Para leituras incertas, a etapa 6 gera variações do mesmo recorte: margens de 10, "
    "20 e 30 pixels, com e sem leve redução dos traços pretos. São até seis "
    "preparos, incluindo o padrão. Variações que eliminem ou fragmentem o símbolo "
    "são descartadas antes de chegar ao OCR."
)

RECORTES_VALIDOS = (
    "Os sete recortes desta imagem passaram pelas verificações de segmentação."
)

RECORTES_INVALIDOS = (
    "A segmentação desta imagem não passou nas verificações. O OCR está bloqueado."
)

RECORTES_NOTA = (
    "As imagens preparadas aparecem acima, em “Entradas individuais do OCR”. A placa completa não é enviada."
)

OCR_MOTOR = (
    "Tesseract reconhece cada caractere localmente no modo PSM 10. Leituras incertas "
    "recebem novos preparos e, quando necessário, uma tentativa no PSM 13. "
    "Cada chamada recebe apenas um caractere. OpenCV localiza e segmenta a placa."
)

OCR_CONFIANCA = (
    "A leitura inicial exige confiança de pelo menos 60. Recuperações exigem duas "
    "respostas concordantes acima desse limite, sem conflito forte. Caso contrário, "
    "o resultado permanece ‘?’. Não há seleção manual de formato nem uso de outros motores."
)

OCR_CINZA = (
    "Se o binário continuar inconclusivo, o mesmo caractere é recortado da placa em tons "
    "de cinza e testado no PSM 10 com três margens. Duas margens devem concordar com "
    "confiança ≥ 60, sem conflito forte entre as leituras em cinza. Esse consenso pode "
    "resolver o conflito do binário. As respostas anteriores permanecem no histórico."
)

OCR_NOTA = (
    "Confiança é a pontuação do Tesseract, não uma probabilidade calibrada; -1 indica ausência de leitura."
)

OCR_SEM_SEGMENTACAO = (
    "Etapa não executada: a segmentação precisa ser válida antes do reconhecimento."
)

OCR_SEM_MOTOR = (
    "Etapa não executada: o motor selecionado está indisponível neste computador."
)

OCR_PENDENTE = (
    "Etapa pendente: use o botão “Reconhecer caracteres” acima."
)

RESULTADO_ARRAY = (
    "Cada resposta aceita ocupa uma posição na lista de caracteres. Respostas vazias, "
    "com vários símbolos ou fora do alfabeto permitido recebem “?”. Depois, o programa "
    "junta as posições na ordem de leitura e armazena o texto consolidado na lista de placas."
)

RESULTADO_DISPONIVEL = (
    "O resultado desta execução está exibido acima e pode ser baixado com os recortes."
)

RESULTADO_PENDENTE = (
    "Ainda não há um resultado de OCR para esta imagem e este formato. "
    "O array será exibido após o reconhecimento."
)

PASSOS_INTRO = (
    "Acompanhe o que foi feito nesta imagem. Abra cada etapa para ver sua função "
    "e o resultado intermediário usado pelo programa."
)

PASSOS_RESUMO = (
    "Preparação → bordas e morfologia → escolha da região → segmentação → OCR → array"
)


# --- Textos da página principal ---

BOAS_VINDAS = (
    "Envie uma foto frontal de um veículo ou selecione o exemplo sintético na lateral."
)

RESUMO_DO_FLUXO = (
    "**1. Localizar** a placa → **2. Separar** os caracteres → "
    "**3. Reconhecer** um por vez → **4. Concatenar** e exibir."
)

EXEMPLO_SINTETICO = (
    "Exemplo desenhado para demonstrar o fluxo. Não comprova desempenho em fotografias reais."
)

BARRA_LATERAL_NOTA = (
    "Cada chamada ao OCR recebe somente um caractere isolado."
)

RESULTADO_CONFIANCA = (
    "Confiança é a pontuação do motor selecionado, não uma probabilidade calibrada de acerto."
)

RODAPE = (
    "Protótipo didático para uma placa clara ou escura em uma linha. "
    "Inclinação acentuada, reflexos, borrões e letras unidas podem impedir a leitura."
)
