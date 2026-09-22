# Validação da versão Tesseract

Execute `.venv/bin/python -m pytest -q`. Os testes incluem segmentação, preservação da restrição
de um caractere por chamada, consenso/conflitos, exportação e interface. Testes de OCR real exigem
o executável Tesseract e dados `eng`; são pulados quando o executável não está instalado.

Os resultados de referência abaixo foram verificados antes e depois da reorganização do código
em `placas/etapas/`, comparando o texto reconhecido, as caixas, o método de binarização, a
pontuação, as mensagens de erro e o hash de cada imagem intermediária e exportada.

## Casos de referência

| Entrada | Resultado validado antes da refatoração |
|---|---|
| Placa escura | LZN6A99 |
| Placa paraguaia | WBZL449 |
| Placa inclinada Honda WR-V | WRV2021 |
| Exemplo sintético salvo | ABC1D23 |
| Sete recortes inclinados enviados pelo usuário | TEP3A12 |
| Placa em perspectiva (testee12.jpg) | ABC1D34 |
| Fiat vermelho (foto enviada pelo WhatsApp) | NUJ9549 |

A placa paraguaia é recuperada usando tons de cinza sem seleção de formato. A foto do Honda já
contém um retângulo verde desenhado no arquivo fornecido; o teste cobre essa versão. O caso
TEP3A12 foi validado a partir dos recortes exportados, não da foto original do veículo.

## Refatoração por responsabilidade — 22/09/2026

Na branch `refatoracao-responsabilidades-didaticas`, a suíte existente passou com **59 testes**.
Além disso, uma execução da versão anterior (commit `b8952a5`) foi comparada à nova versão
em seis imagens completas: escura, paraguaia, Honda, sintética, testee12 e Fiat.
Foram idênticos os retângulos escolhidos, candidatas, máscaras, caixas dos caracteres,
pontuações, texto, histórico de tentativas e pixels das imagens exportadas.

A comparação foi feita no mesmo ambiente local com Tesseract 5.5.3. As duas novas fotos
completas vieram de Downloads; os três recortes de regressão A/9 continuam versionados em
`tests/fixtures/recortes_escalas/`. Essa comparação não comprova equivalência entre sistemas
operacionais ou modelos de idioma diferentes.

## O que os testes demonstram

- A placa inteira e máscaras inválidas são bloqueadas antes do OCR.
- As chamadas usam somente recortes individuais; respostas múltiplas são rejeitadas.
- Recuperações exigem concordância suficiente e tratam conflitos.
- Os pixels exportados correspondem às imagens usadas nas tentativas testadas.
- Rotação automática preserva os componentes e recupera P/1 no caso de regressão.
- A segmentação aceita a linha inclinada e preserva sete caracteres no Honda.
- A recuperação em cinza identifica Z e registra as novas chamadas.
- A interface exibe candidatos, recortes, histórico e resultados.

As comparações são pequenas e não fornecem estimativa de precisão geral. O limiar de confiança
não é calibrado como probabilidade. A versão atual contém somente Tesseract e não faz chamadas
a serviços externos. Instalações antigas de outros motores no ambiente virtual não são usadas.
