# Validação e pendências

## Ambiente e escopo

Verificação inicial em 19/09/2026 e integração real verificada em 20/09/2026, com Python 3.12, OpenCV 4.14, NumPy 2.5, pytesseract 0.3.13 e Streamlit 1.64. As dependências Python estão no ambiente local `.venv`; a lista exata está em `requirements-lock.txt`.

O motor estava ausente na verificação inicial. Após a instalação realizada pelo usuário, a aplicação encontrou **Tesseract 5.5.3**, com o idioma `eng`. Não foi necessário alterar o caminho do executável nem o código de reconhecimento.

## Evidências obtidas

- Resultado de `python -m pytest -q` após as tentativas automáticas: **35 testes aprovados, nenhum ignorado**, incluindo a integração com o motor real. Esses testes verificam execução, restrições e estrutura; não garantem acerto de todos os caracteres. Na verificação inicial, `pip check` não encontrou conflitos de dependências.
- A aplicação foi iniciada em `http://127.0.0.1:8501` e conferida visualmente no navegador, incluindo a imagem localizada e os sete recortes do exemplo.
- O exemplo sintético foi localizado automaticamente e produziu sete recortes individuais em ordem. A imagem de segmentação foi inspecionada visualmente.
- A localização/segmentação também foi verificada em versões sintéticas redimensionadas e com outro texto.
- A foto `images-2.jpeg` fornecida pelo usuário foi incluída como caso de regressão local em `tests/fixtures/placa_escura.jpeg`. A versão anterior não encontrava uma região plausível; a versão corrigida selecionou a caixa `(210, 215, 97, 35)` e sete recortes com `Otsu · caracteres claros`. A localização e os recortes foram inspecionados visualmente. O teste verifica a sobreposição com a região anotada e a posição de cada caractere, sem codificar essas coordenadas no detector.
- Placas escuras sintéticas também foram verificadas em três escalas. O OCR individual e as placas claras continuam cobertos pelos testes anteriores.
- Uma imagem uniforme sem placa foi rejeitada.
- Um arquivo que não é imagem foi rejeitado com mensagem compreensível.
- O teste que intercepta o OCR conferiu sete chamadas, modo `--psm 10`, os pixels de cada imagem enviada e os arrays resultantes.
- Segmentação com seis caracteres, uma placa completa tratada como caractere e uma máscara com dois componentes foram rejeitadas antes da chamada de OCR.
- Respostas vazias, com vários caracteres ou fora do alfabeto permitido viraram `?`.
- As restrições de letras/números por posição foram verificadas para os dois formatos.
- A interface foi exercitada com motor ausente e com respostas controladas: exibição do resultado, botão desabilitado sem motor e limpeza de resultados ao mudar o formato.
- A refatoração foi comparada com uma referência obtida antes da mudança em três imagens (placa clara sintética, placa escura sintética e a foto fornecida). Caixas, métodos escolhidos, pontuações, máscaras, recortes e todas as imagens intermediárias permaneceram idênticos, pixel a pixel.
- O terminal também foi executado após a refatoração com a foto de placa preta em modo de segmentação: sete caracteres isolados. Os testes do OCR continuam verificando as sete imagens efetivamente entregues ao motor controlado; foram adicionadas verificações da rejeição de uma placa inteira na entrada da etapa 7 e da preservação de `?` na consolidação da etapa 8.

## Leituras reais em 20/09/2026, antes das tentativas automáticas

Cada execução abaixo fez sete chamadas individuais, no modo `--psm 10`. Nenhuma imagem de placa completa foi enviada ao motor. Os resultados completos foram salvos localmente em `output/validacao-tesseract/leituras.json`.

| Imagem | Texto esperado (inspeção humana/gerador) | Formato livre | Formato Mercosul |
|---|---|---|---|
| Exemplo sintético | `ABC1D23` | `?BC?D23` | `?BC?D23` |
| Foto da placa preta | `LZN6A99` | `LZ?6A99` | `LZ?6A?9` |

Os símbolos `?` correspondem a respostas vazias do OCR. A integração funciona, mas nenhuma dessas leituras ficou inteiramente correta. Restringir o alfabeto por posição não garantiu melhora: nesta foto, o modo Mercosul também deixou um dos dígitos sem resposta. Os textos esperados não foram inseridos nas respostas do programa.

## Comparação com tentativas automáticas

Comparação executada com Tesseract 5.5.3. O arquivo `output/validacao-tentativas/comparacao.json` contém os históricos completos. Os textos esperados são usados somente para avaliar, nunca como entrada do reconhecimento.

| Caso | Leitura padrão | Com tentativas | Chamadas com tentativas |
|---|---|---|---|
| Foto preta, livre | `LZ?6A99` | `LZN6A99` | 12 |
| Foto preta, Mercosul | `LZ?6A?9` | `LZN6A99` | 17 |
| Arquivo sintético da interface, livre | `?BC?D23` | `?BC1D23` | 17 |
| Sintética `ABC1D23` gerada em memória, livre | `A?C1D23` | `A?C1D23` | 12 |
| Sintética `XYZ9876` gerada em memória, livre | `XYZ?876` | `XYZ?876` | 12 |

O PNG de exemplo já salvo e a imagem produzida novamente pelo gerador não são a mesma entrada pixel a pixel; por isso seus resultados são registrados separadamente. Nos casos comparados, as posições previamente corretas foram preservadas. Permaneceram respostas incertas: no arquivo de exemplo, o A teve uma leitura com confiança 83 e outra 59, insuficientes pela regra de duas confirmações ≥ 60. O limite não foi reduzido para forçar esse acerto.

As tentativas ficaram limitadas a seis por caractere e só ocorreram após resposta inválida ou confiança < 60. Os novos testes verificam conflitos mesmo quando a maior pontuação favorece um candidato, evidência insuficiente, respostas fora do alfabeto, descarte de variações destrutivas, contagem de chamadas, histórico na interface e correspondência pixel a pixel das imagens exportadas com as imagens enviadas ao motor controlado.

## O que não foi validado

- Acurácia geral do Tesseract: há apenas as leituras exploratórias acima, sem conjunto independente de avaliação. Respostas controladas dos testes não contam como reconhecimento real.
- Generalização em fotografias reais: uma única foto de placa preta foi usada para ajuste e regressão; isso não constitui avaliação independente de acurácia.
- Uso com forte perspectiva, placa de moto ou múltiplas placas.

## Próxima verificação necessária

1. Investigar os caracteres sem resposta, avaliando o preparo dos recortes e o reconhecimento individual, sem completar resultados a partir do texto esperado.
2. Usar outras fotos reais para avaliação independente, comparando as etapas com as regiões esperadas e registrando o acerto completo e por caractere conforme o guia de apresentação.

Não foi declarada nenhuma porcentagem de acerto.


## Modo alternativo de OCR

Após acrescentar o PSM 13 para leituras ainda sem evidência suficiente no PSM 10, os sete recortes enviados em `reconhecimento` produziram `QEL3C98`, em 29 chamadas individuais. Q e 8 exigiram 12 chamadas cada; os demais exigiram uma. A confiança mínima dos apoiadores foi 90 para Q e 84 para 8. A validação foi feita sobre os recortes exportados, sem a foto original. Os 39 testes passaram, incluindo preservação dos pixels no modo alternativo, exportação, conflitos e rejeição de respostas múltiplas. O limite atual é de 84 chamadas por placa.


EasyOCR integrado como motor opcional. 43 testes passaram, incluindo validação antes do motor, entradas individuais e rejeição de respostas múltiplas. Comparação real dos três casos registrada em `output/comparacao-easyocr.json`: não houve melhora geral nessa amostra; manter Tesseract como padrão.


## Preservação do W na placa paraguaia

A binarização adaptativa apagava o vértice central do primeiro caractere. Otsu e adaptativo tinham notas geométricas 21,476 e 21,498: diferença insuficiente para justificar a perda de traços. A etapa 5 agora prefere Otsu sem abertura em empates de até 0,05 ponto, somente com sete componentes, mesma polaridade e centros correspondentes. Esse limite é heurístico e precisa ser avaliado em mais fotos. Nenhuma letra esperada é usada para selecionar o recorte.

Nesta foto, Tesseract passou de ?BLL449 para WB?L449; EasyOCR passou de HB2L449 para ?B2L449. A placa completa ainda não foi reconhecida corretamente. O formato brasileiro não se aplica a esta placa: usar Livre.


## EasyOCR: margem adicional para leituras incertas

Adicionada margem branca de 40 pixels sem alterar os traços nem a proporção. Na placa paraguaia, margens 30 e 40 concordam em W acima do limiar 60: resultado passou de ?B2L449 para WB2L449. A confusão Z/2 continua. Nos exemplos de placa escura e sintético os resultados permaneceram L2N6A99 e 00C2023. Não houve troca automática de H por W. São até sete chamadas por caractere (49 por placa); a primeira leitura forte continua encerrando as tentativas.


Formato opcional “4 letras + 3 números” (`quatro_letras`): restringe o alfabeto enviado ao EasyOCR por posição, sem substituir caracteres após o reconhecimento. Na foto paraguaia, o modo Livre continua retornando WB2L449; com o formato selecionado, retorna WBZL449. As sete variações livres do Z retornaram 2, portanto o ajuste utiliza informação explícita do formato, não uma melhoria geral da distinção visual Z/2. Cada chamada continua recebendo somente um caractere.
## Google Cloud Vision

O fluxo padrão usa `placas/ocr_google.py`. Os testes interceptam o cliente oficial da API e verificam sete chamadas, cada uma contendo somente o PNG de um recorte validado, além da rejeição de respostas vazias ou com mais de um caractere. Nenhuma credencial, imagem de placa completa ou chamada externa é usada durante os testes automatizados.
## Correção automática de inclinação — 21/09/2026

Os sete recortes fornecidos em reconhecimento-3 passaram de TE?3A42 para TEP3A12
com o Tesseract após a correção geométrica por momentos, sem usar rótulos esperados na decisão.
Mantidos os resultados de controle: LZN6A99 na placa escura, WB?L449 na paraguaia,
e ?BC1D23 no exemplo sintético. A validação do novo caso usa os recortes exportados;
a imagem original do veículo não foi fornecida para testar a localização completa.
## Recuperação em tons de cinza — 21/09/2026

Confirmada igualdade pixel a pixel do terceiro recorte enviado em reconhecimento-4 com o gerado
da foto placa_paraguai.jpg. Em PSM 10, suas margens 10/20/30 em cinza retornaram Z com pontuações
88/90/87. O fluxo completo em modo livre passou de WB?L449 para WBZL449 (31 chamadas).
A placa escura manteve LZN6A99 (12 chamadas); o exemplo sintético passou de ?BC1D23 para
ABC1D23 (26 chamadas). A integração mantém o OCR individual, sem letras esperadas ou escolha
manual de formato. Os testes verificam consenso, conflitos, respostas múltiplas, bloqueio da
placa completa e correspondência pixel a pixel dos preparos exportados com as entradas do OCR.
## Segmentação de linha inclinada — WRV2021

Na imagem fornecida do Honda WR-V, o filtro de linha horizontal encontrava quatro caracteres
e bloqueava o OCR. A etapa 5 passou a testar inclinações estimadas entre pares de componentes
com alturas semelhantes (inclinação máxima 0,35), e a pontuar o desvio em relação à própria linha.
Resultado: sete componentes isolados e WRV2021 no Tesseract. A foto de teste contém um retângulo
verde já desenhado pelo usuário; não foi fornecida a versão sem essa anotação.
