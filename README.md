# Reconhecimento de placas veiculares

Aplicação didática em Python, OpenCV e Tesseract. Localiza a placa, segmenta sete caracteres,
reconhece cada um individualmente e concatena os resultados. Aceita JPEG, PNG e WebP.
O processamento é local: a placa inteira nunca é enviada ao OCR.

## Instalação e execução

Use Python 3.10 ou superior. Instale também o programa Tesseract e os dados de idioma `eng`:
no macOS, `brew install tesseract`; no Ubuntu/Debian, `sudo apt install tesseract-ocr tesseract-ocr-eng`.
No Windows, siga as [instruções do Tesseract](https://tesseract-ocr.github.io/tessdoc/Installation.html).
Se necessário, a variável `TESSERACT_CMD` pode indicar o caminho do executável.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

`pytesseract` é a biblioteca que chama o programa Tesseract; não instala esse programa.
As versões fixadas do ambiente de referência estão em `requirements-lock.txt`.

## Como o código está organizado

```
app.py                      a página, em uma tela: cada linha é uma etapa
main.py                     a mesma leitura pelo terminal
placas/
  config.py                 todos os parâmetros numéricos, agrupados por etapa
  pipeline.py               o mapa do fluxo: quem chama quem, na ordem
  modelos.py                as estruturas de dados compartilhadas
  imagem.py                 leitura do arquivo e orientação EXIF
  validacao.py              as recusas que protegem o OCR
  etapas/                   uma etapa por arquivo, de e1 a e8
  saida/                    desenho das marcações e exportação dos recortes
interface/
  componentes.py            os blocos visuais da página principal
  passos.py                 a estrutura das oito seções do passo a passo
  textos.py                 os textos didáticos, fora do código
```

Comece por `placas/pipeline.py`: ele tem duas funções, `localizar()` e `reconhecer()`,
e cada linha delas leva ao arquivo da etapa correspondente.

## Oito etapas da página

| Etapa | Responsabilidade | Arquivo |
|---|---|---|
| 1 | Redimensionar, converter para cinza e suavizar | `placas/etapas/e1_preparacao.py` |
| 2 | Detectar e conectar bordas | `placas/etapas/e2_bordas.py` |
| 3 | Black-hat/top-hat, limiarização, fechamento e abertura | `placas/etapas/e3_morfologia.py` |
| 4 | Avaliar regiões e escolher a melhor candidata | `placas/etapas/e4_localizacao.py` |
| 5 | Separar componentes e encontrar a linha de caracteres | `placas/etapas/e5_segmentacao.py` |
| 6 | Validar recortes, normalizar e corrigir inclinação | `placas/etapas/e6_recortes.py` |
| 7 | Reconhecer cada caractere pelo Tesseract | `placas/etapas/e7_decisao.py` |
| 8 | Concatenar, formar arrays e emitir avisos | `placas/etapas/e8_resultado.py` |

A etapa 6 se apoia em três arquivos vizinhos: `e6_normalizacao.py` põe o símbolo no formato
padrão, `e6_inclinacao.py` corrige o ângulo e `e6_variacoes.py` gera os preparos alternativos.
A etapa 7 é dividida em dois: `e7_motor_ocr.py` é o único arquivo que fala com o Tesseract, e
`e7_decisao.py` contém as regras que aceitam ou recusam uma leitura, sem chamar o motor.

`placas/saida/visualizacao.py` desenha as marcações e `placas/saida/exportacao.py` reconstrói
as entradas do OCR para o download.

Na etapa 3, cada aba mostra as regiões originadas por aquela operação e kernel, com ou sem margem.
Na etapa 4, uma galeria mostra até cinco candidatas distintas com recorte, pontuação e número de
componentes. Inspecionar uma candidata não altera a escolha automática. A pontuação é geométrica,
não uma probabilidade. A seleção de região não usa OCR.

## Como o reconhecimento decide

- São exigidos sete recortes válidos, sem sobreposição e com um componente selecionado por máscara.
- A preparação pode corrigir inclinação quando pelo menos cinco símbolos apontam no mesmo sentido.
  Usa momentos da imagem, mediana entre 3° e 15° e rotações em passos de 5°, sem consultar letras esperadas.
- O Tesseract começa no PSM 10. Uma resposta única e permitida com confiança ≥ 60 é aceita.
- Caso contrário, testa margens 10/20/30, com e sem afinamento. Pode usar PSM 13 se ainda houver
  evidência insuficiente e nenhum conflito forte. A entrada continua sendo um único caractere.
- A recuperação binária exige pelo menos duas respostas fortes concordantes, sem resposta forte diferente.
- Se continuar inconclusiva, usa o recorte em tons de cinza com três margens no PSM 10. Duas margens
  precisam concordar com confiança ≥ 60 e sem conflito forte entre as leituras em cinza. Esse consenso
  pode resolver conflitos do binário, preservando todas as respostas no histórico.
- Sem evidência suficiente, mantém `?`. São até 15 chamadas por caractere, 105 por placa; com primeiras
  leituras aceitas, são apenas sete. Preparos inválidos ou duplicados são descartados.

Pontuações não são probabilidades calibradas. Uma leitura errada com pontuação alta ainda pode ser
aceita, e preparos correlacionados podem repetir um erro. A página usa formato livre e não troca
caracteres com base na posição. Os dados exportados identificam o motor como `tesseract`.

## Terminal e exportação

```bash
python main.py foto.webp --saida output/minha-leitura
python main.py foto.webp --somente-segmentar --saida output/inspecao
```

A pasta de saída deve ser nova. O CLI mantém `--formato antiga` e `--formato mercosul` como opções
explícitas para restringir o alfabeto; o padrão é `livre`. A página não solicita formato.
O botão **Baixar resultado e recortes** exporta o JSON e as imagens individuais efetivamente usadas,
incluindo margens, modos e tons de cinza. O resultado contém `caracteres`, `texto`, `placas`, histórico e avisos.

## Verificação e apresentação

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Todos os limiares e tamanhos citados acima estão em `placas/config.py`, com um comentário
de uma linha cada: é lá que se ajusta o comportamento, não no meio da lógica.
Para conferir o estilo do código: `python -m pip install ruff && ruff check .`

Consulte [o guia da apresentação](docs/GUIA_APRESENTACAO.md) e [a validação](docs/VALIDACAO.md).
O protótipo espera sete caracteres em uma linha. Reflexos, desfoque, perspectiva acentuada e
caracteres unidos podem impedir a leitura. A correção de inclinação não é uma retificação completa
de perspectiva. O exemplo sintético demonstra o fluxo, mas não comprova precisão em fotografias.
