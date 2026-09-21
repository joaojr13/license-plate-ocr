# Guia para explicar o projeto

Comece por `placas/pipeline.py`: ele tem duas funções, `localizar()` e `reconhecer()`, e cada
linha delas leva ao arquivo da etapa correspondente em `placas/etapas/`, numerado de e1 a e8.
O código usa OpenCV para localizar/segmentar e somente Tesseract para reconhecer caracteres.

Três arquivos ajudam a responder perguntas durante a apresentação:

- `placas/config.py` — todos os números citados aqui (limiares, tamanhos, margens, ângulos),
  agrupados por etapa. Se perguntarem "de onde vem esse 60?", a resposta está nesse arquivo.
- `placas/validacao.py` — as três recusas que impedem a placa inteira de chegar ao OCR.
- `placas/etapas/e7_motor_ocr.py` — o único arquivo do projeto que importa `pytesseract`.

## 1. Preparação

A leitura trata orientação EXIF e converte para BGR. Imagens maiores são reduzidas para até
1.400 pixels no maior lado; depois convertemos para cinza e suavizamos com Gaussiano 3×3.

## 2. Bordas

Canny destaca mudanças de intensidade. Fechamento 3×3 conecta falhas. Os contornos geram
candidatas, mas também aparecem em objetos que não são placas.

## 3. Morfologia

Black-hat é fechamento menos a imagem e destaca detalhes escuros. Top-hat é imagem menos abertura
e destaca detalhes claros. Usamos ambos com kernels 17×7 e 31×7. Após Otsu, fechamento horizontal
conecta traços e abertura remove ruídos. A página mostra as máscaras e os retângulos de cada fonte.

## 4. Localização

Filtramos retângulos pelo tamanho e proporção. Testamos candidatas com e sem margens. Cada região
é segmentada sem OCR. A pontuação favorece sete componentes, alturas semelhantes, alinhamento e
ocupação horizontal. Escolhemos a maior pontuação entre regiões com pelo menos quatro componentes.
A galeria exibe até cinco candidatas distintas, incluindo a escolhida. Pontuação não é probabilidade.

## 5. Segmentação

Otsu escolhe um limiar global; o adaptativo usa a vizinhança local. Testamos ambos com caracteres
claros/escuros e com/sem abertura 2×2. Componentes conectados são filtrados pelo tamanho, forma e
preenchimento. A seleção considera linhas inclinadas, até inclinação 0,35. As caixas são ordenadas
da esquerda para a direita. Em empate aproximado, Otsu sem abertura pode preservar melhor os traços.

## 6. Preparação individual

Validamos sete componentes isolados e caixas não sobrepostas. Normalizamos o símbolo para altura
100, preservando a proporção, preto no branco e margem 20. Quando a maioria indica inclinação
semelhante, os momentos da máscara orientam pequenas rotações. A correção é heurística.
As variações binárias usam margens 10/20/30 e afinamento leve. Os tons de cinza vêm dos mesmos
boxes individuais, preservando detalhes que a binarização pode eliminar.

## 7. OCR

`reconhecer_caractere`, em `placas/etapas/e7_motor_ocr.py`, é o único ponto que chama
`pytesseract.image_to_data`. As regras que decidem aceitar ou recusar a resposta estão
separadas, em `placas/etapas/e7_decisao.py`, e nunca conversam com o motor.
PSM 10 indica símbolo único; PSM 13 é alternativa de interpretação. Ambos recebem somente
um caractere. O modo, sozinho, não garante o cumprimento da restrição: os recortes são validados antes.

A primeira resposta forte é aceita. Se for incerta, exigimos concordância entre preparos. Se o
binário permanecer inconclusivo, avaliamos separadamente o consenso de três margens em cinza.
Uma resposta com vários símbolos não é truncada; torna-se `?`. Não há substituição fixa de Z/2 ou W/H.
Se o cinza falhar, há quatro chamadas extras: alturas 30 e 50, cada uma em PSM 10 e 13.
A redução por área preserva proporção e produz níveis de cinza nas bordas. Exigimos consenso
forte entre as duas alturas, sem conflito forte nas novas tentativas. O OCR é sensível à escala:
um símbolo maior não é necessariamente mais fácil de reconhecer. Não criamos detalhes novos.
Confiança ≥ 60 é uma heurística, e não 60% de certeza. A maior pontuação isolada não comprova acerto.

## 8. Resultado

```python
caracteres = ['W', 'B', 'Z', 'L', '4', '4', '9']
texto = ''.join(caracteres)
placas = [texto]
```

Exibimos histórico, avisos e imagens realmente usadas. O ZIP permite auditar cada chamada.

## Perguntas para ensaiar

1. Qual é a diferença entre localizar, segmentar e reconhecer?
2. Por que o fechamento gera candidatas, mas não identifica placas sozinho?
3. Qual a diferença entre Otsu e limiar adaptativo?
4. Por que exigimos sete recortes antes do OCR?
5. Como demonstrar que a placa inteira nunca chega ao Tesseract?
6. Como a inclinação fez o sistema descartar caracteres no exemplo WRV2021?
7. Por que preservar tons de cinza ajudou o Z?
8. Por que dois preparos podem concordar e mesmo assim estar errados?

Apresentem também limitações: baixa resolução, reflexos, caracteres unidos, duas linhas e erros
aceitos com confiança alta. Os exemplos de teste não representam uma taxa geral de acerto.
