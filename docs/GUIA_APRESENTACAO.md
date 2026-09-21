# Entender e apresentar o projeto

O objetivo deste guia é ajudar o grupo a explicar o código e experimentar alterações. Leiam as funções, acompanhem as imagens intermediárias e reproduzam as experiências. Decorar o texto não substitui entender os resultados.

## Como acompanhar o código pelas oito etapas

Abra `placas/processamento.py`: ele coordena o fluxo sem misturar filtros com interface. Siga as chamadas para `preparacao.py` (1), `bordas.py` (2), `morfologia.py` (3) e `localizacao.py` (4). A seleção em `localizacao.py` chama `segmentacao.py` (5) para cada região candidata. Depois da inspeção visual, `reconhecer()` chama `preparacao_ocr.py` (6), `ocr.py` (7) e `resultado.py` (8).

Cada etapa da página indica o arquivo e a função correspondentes. A exibição está separada em `interface/passos.py`, com uma função para cada etapa. Ela recebe resultados já calculados; não aplica filtros nem executa OCR. As estruturas `ImagemPreparada`, `Localizacao`, `Segmentacao`, `Caractere` e `Leitura`, em `placas/modelos.py`, registram o que passa de uma etapa para outra.

As etapas 4 e 5 não são independentes: precisamos tentar segmentar uma candidata para avaliar se ela parece uma placa. Ao escolher a melhor, reaproveitamos sua segmentação. Expliquem essa relação quando mostrarem o fluxo.

## Roteiro de demonstração

1. Expliquem o problema e a proibição de OCR da placa completa.
2. Enviem uma fotografia e mostrem a região que o algoritmo selecionou.
3. Abram as etapas: cinza, bordas, black-hat/top-hat e fechamento.
4. Mostrem a binarização da placa e expliquem por que ela é diferente da máscara usada para localização.
5. Contem e inspecionem os sete recortes, da esquerda para a direita.
6. Executem o OCR. Mostrem as leituras individuais, a lista de caracteres e a lista com o texto concatenado.
7. Mostrem um caso que falha e expliquem se a falha está na localização, segmentação ou reconhecimento.

## Por que duas máscaras?

Para **localizar**, queremos que traços próximos formem uma região horizontal. O fechamento ajuda a ligar esses elementos. Para **segmentar**, queremos letras separadas. Por isso a segunda etapa volta à imagem da região e faz outra binarização; usar a máscara fortemente fechada como entrada da segmentação uniria letras.

## Operações que precisam ser compreendidas

Na segmentação, os objetos são brancos (255) e o fundo é preto (0). Essa convenção importa: erosão reduz as regiões brancas e dilatação as expande. Se a polaridade mudar, a interpretação visual também muda.

| Operação | Ideia | Uso e risco |
|---|---|---|
| Cinza | Uma intensidade por pixel | Simplifica os filtros; descarta informação de cor |
| Gaussiano | Média ponderada de vizinhos | Reduz ruído; pode apagar traços muito finos |
| Canny | Busca mudanças fortes de intensidade | Propõe contornos; carro e fundo também produzem bordas |
| Erosão | Mantém regiões onde o kernel cabe | Remove pequenas regiões e afina os objetos |
| Dilatação | Expande regiões conforme o kernel | Conecta fragmentos; pode juntar caracteres |
| Abertura | Erosão seguida de dilatação | Remove ruído pequeno; pode remover parte de uma letra |
| Fechamento | Dilatação seguida de erosão | Une traços na localização; pode fechar espaços indevidos |
| Black-hat | Fechamento menos imagem | Destaca detalhes escuros menores que o kernel sobre um fundo claro |
| Top-hat | Imagem menos abertura | Destaca detalhes claros menores que o kernel sobre um fundo escuro |
| Otsu | Escolhe limiar minimizando variância dentro das duas classes | Funciona melhor quando fundo e objeto são separáveis por intensidade |
| Adaptativo | Calcula limiar a partir de vizinhanças | Pode ajudar sob iluminação desigual; pode criar ruído |

O kernel define a vizinhança. O fechamento usa uma forma horizontal porque a placa procurada contém uma linha de caracteres. O tamanho do kernel depende da escala da placa na fotografia; duas escalas são testadas, mas isso não cobre todos os cenários.

Para placas pretas, a hipótese de caracteres escuros não funciona. Por isso, a localização testa também top-hat, e a segmentação testa tanto o cinza original quanto seu inverso. A escolha continua sendo geométrica, sem OCR. Em ambas as alternativas, os componentes ficam brancos sobre fundo preto na máscara e são convertidos em caracteres pretos sobre branco antes do OCR. A imagem da placa completa nunca é enviada ao motor.

## Como as letras são separadas?

`connectedComponentsWithStats` atribui um rótulo a cada conjunto de pixels brancos conectado por vizinhança de oito. O rótulo zero representa o fundo. Para cada objeto, obtemos posição, largura, altura e área.

Os filtros rejeitam componentes baixos (como textos de cabeçalho), grandes demais (como a borda) e largos demais (como grupos de caracteres unidos). Depois escolhemos um grupo com centros e alturas compatíveis e ordenamos as caixas pelo eixo x. Sem essa ordenação, a ordem dos rótulos não oferece a garantia de leitura que precisamos.

`imagem[y:y+h, x:x+w]` usa primeiro linhas (y), depois colunas (x). Confundir essa ordem é um erro frequente. No código, o recorte de OCR é uma máscara do rótulo escolhido: outros componentes que eventualmente entrem na caixa não são copiados.

Uma letra inteira costuma corresponder a um componente, mas isso é uma hipótese. Letras quebradas podem gerar vários; letras coladas podem gerar um único componente. Os filtros reduzem esses casos sem oferecer uma garantia universal.

## Como a região da placa é escolhida?

A localização não sabe ainda quais letras estão escritas. Ela cria candidatos com contornos e morfologia. A segmentação de cada candidato recebe uma pontuação geométrica: quantidade próxima de sete, alturas semelhantes, centros alinhados e ocupação horizontal. Não há consulta ao OCR para escolher a região.

É possível selecionar uma região errada contendo sete objetos parecidos. Essa é uma limitação de heurísticas geométricas. Para comprovar desempenho, é necessário avaliar fotos diversas com a localização correta marcada manualmente.

## Como provar o OCR individual?

No módulo `placas/ocr.py`, existe somente um ponto de chamada a `pytesseract.image_to_data`. A função `reconhecer_caractere()` recebe uma imagem individual já preparada pela etapa 6 e usa `--psm 10`, modo de caractere único. A função `reconhecer_caracteres()` percorre os sete recortes; `reconhecer_com_tentativas()` executa a primeira leitura e, somente quando necessário, testa variações daquele mesmo caractere. A preparação está em `placas/preparacao_ocr.py`; a concatenação fica em `placas/resultado.py`.

O teste `test_sete_chamadas_com_imagens_individuais` intercepta as chamadas e verifica os pixels de cada entrada contra o recorte esperado. Os testes também tentam passar uma placa completa e dois componentes na mesma máscara, que devem ser rejeitados. A exportação ZIP permite inspecionar as imagens enviadas. O modo `--psm 10`, sozinho, não substituiria a obrigação de recortar previamente.

## Como explicar as tentativas adicionais?

Primeiro usamos a margem padrão de 20 pixels. Se o OCR não devolver um único caractere permitido ou tiver confiança menor que 60, geramos margens de 10, 20 e 30 pixels com e sem leve redução dos traços. Como o fundo do recorte é branco, uma dilatação do branco com kernel 2×2 reduz os traços pretos. Isso não é uma operação de esqueletização.

São até 12 chamadas por símbolo, contando a primeira. Para aceitar uma recuperação, pelo menos duas respostas devem concordar com confiança ≥ 60 e não pode haver uma resposta diferente também acima desse limite. A maior pontuação isolada não decide o resultado. Se a evidência for insuficiente ou conflitante, mantemos `?` e mostramos as tentativas para conferência.

O limite 60 não significa 60% de chance de acerto. Os preparos são variações da mesma imagem e podem cometer o mesmo erro. Uma resposta errada com confiança alta já na primeira chamada também pode passar. A regra reduz algumas falhas, mas não substitui avaliação com imagens diferentes das usadas no ajuste.

O total de chamadas agora varia entre 7 e 84 por placa. A restrição do trabalho continua atendida: **cada chamada recebe somente um caractere**, mesmo quando o mesmo caractere é tentado novamente. O histórico e o ZIP registram as chamadas reais, não somente as sete imagens padrão.

## Arrays e concatenação

Uma lista Python funciona como o vetor solicitado pelo enunciado. `caracteres` mantém cada resposta individual em ordem. `"".join(caracteres)` forma uma string, sem separadores. `placas = [texto]` guarda o resultado consolidado em um vetor. Essas duas listas deixam explícitas tanto as respostas individuais quanto a consolidação.

Se o OCR não reconhece um caractere, a posição fica com `?`. Isso preserva a posição do erro. Remover o resultado vazio deslocaria as letras seguintes e esconderia a falha. Respostas de vários caracteres são recusadas, não truncadas.

## Perguntas para praticar

1. Por que aplicar fechamento na localização pode ajudar e na segmentação pode atrapalhar?
2. O que muda quando o kernel cresce? Mostrem uma imagem intermediária para explicar.
3. Por que a área do componente é diferente da área de sua caixa?
4. O que pode acontecer com a letra B se usarmos apenas contornos e contarmos também seus buracos?
5. Como o código rejeita cabeçalhos e bordas? Em quais casos isso pode falhar?
6. Por que ordenar por x funciona para uma linha e não resolve placas em duas linhas?
7. Em qual linha conceitual a imagem individual chega ao OCR? Qual variável armazena o array final?
8. O que `--psm 10` informa ao Tesseract? Por que ele não resolve uma segmentação errada?
9. Por que uma pontuação de confiança 90 não deve ser chamada de 90% de probabilidade de acerto?
10. Como distinguir um erro de localização de um erro de OCR?

## Experiências antes da apresentação

- Alterem o tamanho da abertura e observem ruídos removidos e traços perdidos. Restaurem o parâmetro depois de registrar a observação.
- Comparem Otsu e adaptativo numa foto com sombra. Inspecionem a quantidade e o formato dos componentes.
- Reduzam a resolução da mesma foto e identifiquem a partir de quando a segmentação falha.
- Desliguem a restrição de formato e comparem caracteres ambíguos, como O/0, I/1 e B/8.
- Usem uma foto sem placa para observar a mensagem de falha.

## Como medir resultados reais

Separem fotografias de ajuste e de avaliação. Registrem para cada imagem: texto esperado, localização correta, sete caracteres corretamente isolados, texto lido, tempo e tipo de erro. Mantenham os casos difíceis na contagem.

- Taxa de localização: regiões corretas / total de fotos.
- Taxa de segmentação: placas com sete caracteres corretamente separados / total de fotos.
- Acerto completo: placas inteiramente corretas / total de fotos.
- Acerto por caractere: posições corretas / total de posições esperadas; contem falhas anteriores como erros na avaliação de ponta a ponta.

Apresentem o número de fotos junto das taxas. Resultados em uma imagem sintética não estimam desempenho no mundo real. Escolham exemplos de falha para justificar melhorias futuras, como retificação de perspectiva ou um detector treinado.


Se as variações no PSM 10 não produzirem concordância suficiente e não houver conflito forte, o OCR repete os mesmos recortes no PSM 13. Cada entrada continua contendo apenas um caractere. A decisão considera todas as respostas fortes dos dois modos; respostas múltiplas são rejeitadas. O histórico registra o modo e os arquivos das chamadas alternativas recebem o sufixo `_psm13`.
