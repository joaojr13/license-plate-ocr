# Validação da versão Tesseract

Execute `.venv/bin/python -m pytest -q`. Os testes incluem segmentação, preservação da restrição
de um caractere por chamada, consenso/conflitos, exportação e interface. Testes de OCR real exigem
o executável Tesseract e dados `eng`; são pulados quando o executável não está instalado.

## Casos de referência

| Entrada | Resultado validado antes da refatoração |
|---|---|
| Placa escura | LZN6A99 |
| Placa paraguaia | WBZL449 |
| Placa inclinada Honda WR-V | WRV2021 |
| Exemplo sintético salvo | ABC1D23 |
| Sete recortes inclinados enviados pelo usuário | TEP3A12 |

A placa paraguaia é recuperada usando tons de cinza sem seleção de formato. A foto do Honda já
contém um retângulo verde desenhado no arquivo fornecido; o teste cobre essa versão. O caso
TEP3A12 foi validado a partir dos recortes exportados, não da foto original do veículo.

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
