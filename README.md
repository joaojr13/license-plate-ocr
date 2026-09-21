> Configuração atual: página e linha de comando usam somente Tesseract por padrão, localmente, sem fallback para EasyOCR ou Google. As seções sobre outros motores documentam experimentos anteriores.

# Reconhecimento de placas veiculares

A seleção da linha de caracteres considera também inclinações de até aproximadamente 19°.
O alinhamento é medido em relação à linha estimada, evitando descartar os caracteres mais baixos
numa placa inclinada. Isso não equivale a uma correção completa de perspectiva.

Se as tentativas binárias forem inconclusivas, o Tesseract recebe três versões em tons de cinza
do mesmo caractere, com margens de 10, 20 e 30 pixels. Dois resultados em cinza devem concordar
com pontuação ≥ 60, sem conflito forte entre eles. Esse consenso tem precedência sobre o binário
inconclusivo; não mistura votos de representações diferentes. São até três chamadas adicionais
por caractere. Leituras já aceitas não são reavaliadas. A exportação inclui todos os preparos usados.

A etapa 6 estima a inclinação pelos momentos dos sete recortes. Quando pelo menos cinco símbolos
indicam inclinação no mesmo sentido e a mediana está entre 3° e 15°, corrige cada símbolo elegível
em passos de 5°, com espaço adicional para evitar cortes. O resultado volta a ser normalizado e
validado. Essa heurística depende do desenho das letras e não garante correção em toda fotografia.
O histórico e a exportação usam as imagens corrigidas efetivamente enviadas ao OCR.

Aplicação didática em Python que localiza uma placa na fotografia, isola seus caracteres e executa **OCR de um único caractere por chamada**, com tentativas adicionais nas leituras incertas. Apresenta os resultados em tela e em arrays. Aceita imagens JPEG, PNG e WebP. A interface mostra as etapas intermediárias para que o grupo possa explicar e inspecionar o processamento.

## Executar

Requer Python 3.10 ou superior e o **programa Tesseract**, com o idioma `eng`. `pytesseract` é apenas a ponte Python para esse programa. O processamento é local; as fotos não são enviadas a um serviço externo.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Instale também o motor OCR:

- macOS com Homebrew: `brew install tesseract`.
- Ubuntu/Debian: `sudo apt install tesseract-ocr tesseract-ocr-eng`.
- Windows: instale o Tesseract conforme as [instruções oficiais](https://tesseract-ocr.github.io/tessdoc/Installation.html) e acrescente o executável ao PATH. Opcionalmente, configure `TESSERACT_CMD` com o caminho completo do executável.

Se o Homebrew indicar licença pendente do Xcode, o responsável pelo computador deve revisar e resolver a licença usando `sudo xcodebuild -license`, antes de instalar o Tesseract. Esse problema depende da configuração do computador.

```bash
tesseract --version
streamlit run app.py
```

Abra o endereço local exibido pelo Streamlit. Envie uma foto ou marque **Usar exemplo sintético**, confira os recortes e clique em **Reconhecer caracteres**. O botão fica desabilitado sem o motor ou quando a segmentação é inconsistente. É possível visualizar a localização e os recortes mesmo sem o Tesseract.

A seção **Processo passo a passo** explica oito etapas usando os resultados da imagem enviada: preparação, bordas, morfologia, escolha da região, segmentação, preparação dos recortes, OCR e formação do array. As imagens de fechamento e abertura são mostradas separadamente. As etapas de reconhecimento e consolidação ficam identificadas como pendentes até o OCR ser executado.

Neste ambiente, as dependências Python foram instaladas em `.venv`. Portanto, também é possível iniciar diretamente com:

```bash
.venv/bin/streamlit run app.py
```

## Uso pelo terminal

```bash
python main.py caminho/veiculo.jpg --saida output/minha-leitura
python main.py examples/veiculo_sintetico.png --somente-segmentar --saida output/inspecao
python main.py caminho/veiculo.jpg --formato mercosul --saida output/mercosul
```

Use uma pasta de saída nova a cada execução, para não misturar arquivos antigos. O modo normal grava as etapas, os recortes e `resultado.json`. `--somente-segmentar` grava somente as imagens; não simula resultados de OCR.

## Como os requisitos são atendidos

| Requisito | Implementação |
|---|---|
| Localizar e isolar a placa | `localizar()` coordena as etapas 1–5; `selecionar_placa()` em `placas/localizacao.py` escolhe a região |
| Separar caracteres | `segmentar()` em `placas/segmentacao.py`: binarização, componentes conexos, filtros e ordenação por x |
| OCR individual | `reconhecer_caractere()` em `placas/ocr.py`: uma imagem individual, `--psm 10` |
| Concatenar e armazenar | `consolidar_resultado()` em `placas/resultado.py`: `caracteres`, `texto` e `placas` |
| Exibir | `app.py` mostra etapas, recortes, vetor, texto e pontuações; `main.py` imprime o JSON |

Exemplo **ilustrativo**, não uma leitura real já validada pelo OCR:

```python
caracteres = ['A', 'B', 'C', '1', 'D', '2', '3']
texto = ''.join(caracteres)  # 'ABC1D23'
placas = [texto]            # ['ABC1D23']
```

A exportação da interface contém o JSON e todas as imagens efetivamente enviadas ao OCR, incluindo as tentativas adicionais. O nome de cada arquivo identifica a posição do caractere e o preparo utilizado. A imagem da placa completa é usada apenas no processamento e na visualização. Não existe uma chamada alternativa de OCR da placa inteira.

## Tentativas automáticas para leituras incertas

A etapa 7 aceita a primeira leitura quando há exatamente um caractere permitido e confiança de pelo menos **60**. Caso contrário, a etapa 6 gera um conjunto fixo de variações do mesmo recorte: margens brancas de **10, 20 e 30 pixels**, com e sem leve redução da espessura dos traços pretos. A altura do símbolo permanece em 100 pixels.

São no máximo **12 chamadas por caractere**, incluindo a padrão, ou **84 chamadas por placa**. Quando todas as primeiras leituras são suficientes, continuam sendo apenas sete chamadas. Preparos idênticos ou que eliminam/fragmentam o símbolo são descartados.

Para recuperar uma leitura incerta, **pelo menos dois preparos devem concordar com confiança ≥ 60**, e nenhuma resposta diferente pode atingir esse limite. Uma única resposta, mesmo com pontuação alta, não basta. Empates, conflitos e evidência insuficiente produzem `?`. Respostas abaixo do limite aparecem no histórico, mas não contam como confirmação. A confiança exibida de uma recuperação é a menor pontuação entre seus apoiadores fortes.

O limite 60 é uma heurística, não uma probabilidade de acerto. Variações correlacionadas podem repetir um erro. Uma leitura padrão errada com confiança alta ainda pode ser aceita; por isso a avaliação em fotos novas continua necessária. Nenhuma regra conhece a letra esperada ou completa caracteres ausentes a partir do formato da placa.

A página mostra a decisão por posição. Na **etapa 7**, aparecem os candidatos e o histórico de cada tentativa, com resposta bruta e confiança. O JSON guarda esses dados em `leituras[].tentativas` e o total real em `quantidade_chamadas_ocr`. O ZIP inclui somente os preparos realmente enviados.

## Fluxo de processamento

1. Corrige a orientação EXIF da foto e converte RGB para BGR.
2. Reduz fotos grandes, preservando a proporção. Produz cinza e suavização Gaussiana.
3. Obtém candidatos usando Canny e, em duas escalas, black-hat (detalhes escuros), top-hat (detalhes claros) e fechamento horizontal.
4. Filtra caixas por tamanho e proporção. Candidatas morfológicas são testadas com e sem margem. Testa a segmentação de cada candidata, **sem OCR**.
5. Normaliza cada candidata para 600 pixels de largura e testa Otsu/adaptativo, com e sem abertura pequena, nas duas polaridades. Os caracteres sempre ficam brancos nas máscaras, mesmo quando a placa original é preta.
6. Extrai componentes conexos, filtra por altura, largura e ocupação, seleciona uma linha e ordena por x.
7. Escolhe o candidato pela quantidade de componentes próxima de sete, alinhamento, uniformidade e ocupação horizontal.
8. Exige sete recortes válidos e não sobrepostos; cada máscara contém um único componente. O recorte guarda somente o componente selecionado, eliminando pixels de outros rótulos.
9. Inverte cada recorte, normaliza a altura e adiciona margem branca. Executa Tesseract individualmente.
10. Mantém respostas inválidas como `?`, concatena, armazena em listas, exibe e permite exportação.

Os modos **Antiga** e **Mercosul** restringem o alfabeto por posição segundo os formatos adotados pelo projeto (`ABC1234` e `ABC1D23`). **Livre** aceita letras/números em qualquer posição. A aplicação não troca automaticamente `O` por `0` nem inventa caracteres para completar uma placa. Formato válido não comprova que o conteúdo foi lido corretamente.

## Estrutura

Comece por **`placas/processamento.py`**, que apenas coordena as etapas. Os filtros e as regras ficam nos módulos correspondentes às oito etapas da página:

| Etapa da página | Módulo | Função principal | Entrada → saída |
|---|---|---|---|
| 1 · Preparar a imagem | `placas/preparacao.py` | `preparar_imagem()` | Foto BGR → imagem de trabalho, cinza e suavizada |
| 2 · Encontrar bordas | `placas/bordas.py` | `encontrar_bordas()` | Cinza suavizado → máscara de bordas |
| 3 · Aplicar morfologia | `placas/morfologia.py` | `aplicar_morfologia()` | Cinza suavizado → máscaras nas duas escalas e polaridades |
| 4 · Escolher e recortar a placa | `placas/localizacao.py` | `selecionar_placa()` | Imagem preparada e máscaras → candidata selecionada |
| 5 · Binarizar e separar caracteres | `placas/segmentacao.py` | `segmentar()` | Região candidata → máscara e caracteres ordenados |
| 6 · Validar e preparar recortes | `placas/preparacao_ocr.py` | `preparar_recortes()` / `gerar_variacoes()` | Segmentação → recortes padrão e variações individuais quando necessárias |
| 7 · Reconhecer caracteres | `placas/ocr.py` | `reconhecer_caracteres()` / `reconhecer_com_tentativas()` | Sete recortes → sete decisões com histórico de chamadas |
| 8 · Consolidar o resultado | `placas/resultado.py` | `consolidar_resultado()` | Leituras → texto, arrays e avisos para exibição |

**Ligação entre as etapas 4 e 5:** para escolher a placa, a etapa 4 chama a etapa 5 em cada candidata e compara as pontuações. A segmentação da candidata vencedora é reaproveitada. A ordem da página é didática; o código explicita essa avaliação interna e não repete desnecessariamente a segmentação após a seleção.

As etapas 1–5 funcionam sem Tesseract. A função `reconhecer()` do coordenador chama, em ordem, preparação dos recortes (6), OCR individual (7) e consolidação (8). A etapa 7 recebe apenas as imagens individuais já preparadas, sem acesso à fotografia ou à placa completa.

Arquivos de apoio:

```text
app.py                      Entrada da interface e interação com o usuário
main.py                     Entrada pelo terminal
interface/passos.py         Uma função de exibição para cada uma das oito etapas
placas/processamento.py     Coordena o fluxo das etapas
placas/imagem.py             Leitura de arquivo e orientação EXIF
placas/modelos.py            Estruturas de dados trocadas entre etapas
placas/visualizacao.py       Desenha caixas e números sobre as imagens
placas/exportacao.py         Reconstrói os preparos registrados para download e auditoria
examples/                   Exemplo sintético e seu gerador
tests/test_fluxo.py          Regressões e verificação do OCR individual
tests/test_tentativas_ocr.py  Concordância, abstenção de resposta e auditoria das tentativas
docs/GUIA_APRESENTACAO.md    Explicações e exercícios para o grupo
docs/VALIDACAO.md            Evidências e limites da validação
```

## Testes

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Os testes substituem o Tesseract por uma função controlada para verificar **quais imagens são enviadas**, quantas chamadas ocorrem, a ordem e a concatenação. Esses testes não medem acurácia de OCR. Há um teste de integração com o motor real, executado somente quando o Tesseract está disponível.

## Limites e avaliação real

O escopo é uma placa clara com caracteres escuros ou uma placa escura com caracteres claros, em uma linha, aproximadamente frontal, por imagem. A seleção é heurística: sete componentes não garantem que a região seja uma placa nem que cada componente corresponda semanticamente a uma letra. Letras unidas ou fragmentadas podem causar rejeição ou erro. O programa não resolve placas de moto em duas linhas, forte perspectiva, placas muito pequenas, oclusão, baixo contraste e múltiplas placas. Não há correção de perspectiva.

O exemplo sintético serve para demonstrar o fluxo. A foto de placa preta fornecida pelo usuário (`tests/fixtures/placa_escura.jpeg`, originalmente `images-2.jpeg`) foi usada para verificar localização e segmentação e prevenir regressões. **Não foi medida acurácia de OCR em fotos reais.** Antes da apresentação, testem outras fotografias e registrem os acertos e as falhas, separando imagens de ajuste e de avaliação. O guia propõe um roteiro para isso.

## Materiais de apoio

- PDF fornecido `aula_03_b_Operacoes_Morfologicas.pdf`: erosão (p. 11), dilatação (p. 14), abertura/fechamento (p. 17) e componentes conexos (p. 23).
- PDF fornecido `Livro-Introdução-a-Visão-Computacional-com-Python-e-OpenCV.pdf`: recortes (p. 15), cores (p. 20), binarização (pp. 35–37), bordas (pp. 38–40) e contagem de objetos (pp. 42–45).
- PDF fornecido do notebook de Lucas Lattari: exemplos de morfologia, black-hat e regiões de caracteres (pp. 4–13). [Notebook original](https://github.com/lucaslattari/Python_OpenCV4/blob/master/13_morphological_operators.ipynb).
- [OpenCV: operações morfológicas](https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html).
- [Tesseract: qualidade, margens e modos de segmentação](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html).

Os PDFs foram tratados como referência conceitual. As atividades e instruções contidas neles não foram incorporadas como novos requisitos.


Se as variações no PSM 10 não produzirem concordância suficiente e não houver conflito forte, o OCR repete os mesmos recortes no PSM 13. Cada entrada continua contendo apenas um caractere. A decisão considera todas as respostas fortes dos dois modos; respostas múltiplas são rejeitadas. O histórico registra o modo e os arquivos das chamadas alternativas recebem o sufixo `_psm13`.


## EasyOCR opcional

Instale com `.venv/bin/python -m pip install -r requirements-easyocr.txt` e selecione EasyOCR em “Motor de OCR” na página. O primeiro uso baixa o modelo inglês para `.modelos_easyocr/`; depois o reconhecimento é local em CPU. O módulo `placas/ocr_easyocr.py` implementa a etapa 7, sem detector: cada chamada a `recognize` recebe apenas um recorte validado. O motor é carregado uma vez por processo. Usa os mesmos preparos e a regra heurística de confiança 60, com até sete chamadas por caractere. Respostas múltiplas e conflitos são rejeitados. As pontuações dos motores não são comparáveis nem probabilidades calibradas. O JSON exportado identifica o motor; EasyOCR não usa PSM.

Comparação inicial no formato livre: os recortes enviados deram QEL3C98 nos dois motores; a placa escura deu LZN6A99 no Tesseract e L2N6A99 no EasyOCR; o exemplo sintético deu ?BC1D23 no Tesseract e 00C2023 no EasyOCR. Portanto, EasyOCR permanece uma opção experimental e Tesseract continua como padrão. Esses três casos não medem a precisão geral.

EasyOCR inclui margem branca adicional de 40 pixels para leituras incertas. A proporção é preservada e conflitos fortes continuam rejeitados.


Formato opcional “4 letras + 3 números” (`quatro_letras`): restringe o alfabeto enviado ao EasyOCR por posição, sem substituir caracteres após o reconhecimento. Na foto paraguaia, o modo Livre continua retornando WB2L449; com o formato selecionado, retorna WBZL449. As sete variações livres do Z retornaram 2, portanto o ajuste utiliza informação explícita do formato, não uma melhoria geral da distinção visual Z/2. Cada chamada continua recebendo somente um caractere.
## Google Cloud Vision

A aplicação usa a Google Cloud Vision como OCR padrão. Cada uma das sete chamadas envia somente um PNG do caractere já segmentado; a foto e a placa completa não são enviadas à API. Não há escolha de formato da placa para influenciar a resposta.

Antes de executar a página, configure credenciais locais com:

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project SEU_ID_DO_PROJETO
```

A conta deve ter a Cloud Vision API ativada e faturamento vinculado ao projeto. A chave ou credencial não é armazenada neste repositório. Quando a API não disponibiliza confiança para o símbolo, a aplicação registra `-1`; essa ausência não é interpretada como erro de leitura.
