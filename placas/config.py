"""Todos os parâmetros numéricos do processamento, agrupados por etapa.

Este arquivo não executa nada. Ele é a resposta única para "quais números o
sistema usa": cada etapa importa daqui em vez de repetir literais no meio da
lógica. Alterar um valor aqui muda o comportamento de todas as etapas que o
utilizam, o que torna os ajustes visíveis e reversíveis.
"""

# --- Regra geral do projeto -------------------------------------------------
TOTAL_CARACTERES = 7           # A placa esperada tem sete símbolos em uma linha.

# --- Leitura do arquivo -----------------------------------------------------
LIMITE_DE_PIXELS = 25_000_000  # Fotos maiores que 25 megapixels são recusadas.

# --- Etapa 1 · preparação ---------------------------------------------------
LADO_MINIMO_ENTRADA = 30       # Menor lado aceito na foto original, em pixels.
LADO_MAXIMO_TRABALHO = 1400    # Maior lado da imagem de trabalho; acima disso, reduz.
KERNEL_SUAVIZACAO = (3, 3)     # Gaussiano que reduz ruído antes de detectar bordas.

# --- Etapa 2 · bordas -------------------------------------------------------
CANNY_LIMIAR_INFERIOR = 60
CANNY_LIMIAR_SUPERIOR = 180
KERNEL_FECHAMENTO_BORDAS = (3, 3)  # Conecta pequenas falhas deixadas pelo Canny.

# --- Etapa 3 · morfologia ---------------------------------------------------
TAMANHOS_KERNEL_MORFOLOGIA = (17, 31)  # Duas escalas: placas pequenas e grandes.
ALTURA_KERNEL_MORFOLOGIA = 7           # O kernel é horizontal: tamanho × 7.
OPERACOES_MORFOLOGIA = ("Black-hat", "Top-hat")
KERNEL_ABERTURA_MORFOLOGIA = (3, 3)    # Remove ruído depois do fechamento.

# --- Etapa 4 · localização --------------------------------------------------
MAXIMO_CONTORNOS = 250                    # Maiores contornos avaliados por máscara.
PROPORCAO_CANDIDATA = (2.0, 6.5)          # largura / altura aceita para uma placa.
LARGURA_MINIMA_CANDIDATA = 70             # Em pixels da imagem de trabalho.
ALTURA_MINIMA_CANDIDATA = 18              # Região que já inclui as margens da placa.
ALTURA_MINIMA_FAIXA_DE_LETRAS = 10        # Região que contém apenas os caracteres.
AREA_RELATIVA_CANDIDATA = (0.0008, 0.60)  # Fração da área total da imagem.
MARGEM_EXTRA_HORIZONTAL = 0.06            # Acréscimo que transforma faixa em placa.
MARGEM_EXTRA_VERTICAL = 0.35
MINIMO_COMPONENTES_CANDIDATA = 4          # Abaixo disso a região não disputa a escolha.
MAXIMO_CANDIDATAS_EXIBIDAS = 5            # Afeta apenas a galeria da página.
SOBREPOSICAO_MAXIMA_EXIBIDA = 0.5         # Agrupa regiões repetidas na galeria.

# --- Etapa 5 · segmentação --------------------------------------------------
LADO_MINIMO_REGIAO = 10                # Menor lado de uma região segmentável.
LARGURA_NORMALIZADA_PLACA = 600        # A região é redimensionada para esta largura.
ADAPTATIVO_TAMANHO_DO_BLOCO = 31
ADAPTATIVO_CONSTANTE = 9
KERNEL_ABERTURA_SEGMENTACAO = (2, 2)   # Alternativa que preserva traços finos.

ALTURA_RELATIVA_COMPONENTE = (0.30, 0.88)    # Descarta bordas e cabeçalhos.
LARGURA_RELATIVA_COMPONENTE = (0.012, 0.16)  # Descarta parafusos e letras unidas.
PROPORCAO_COMPONENTE = (0.08, 1.05)          # largura / altura de um caractere.
PREENCHIMENTO_COMPONENTE = (0.10, 0.95)      # área / (largura × altura).
MARGEM_BORDA_COMPONENTE = 1                  # Componentes encostados na borda saem.

DISTANCIA_MINIMA_ENTRE_VIZINHOS = 2    # Em múltiplos da altura da referência.
ALTURA_SEMELHANTE = (0.65, 1.45)       # Faixa aceita entre as alturas de dois símbolos.
INCLINACAO_MAXIMA_DA_LINHA = 0.35      # Coeficiente angular máximo da linha de letras.
TOLERANCIA_DE_ALINHAMENTO = 0.22       # Desvio aceito, em múltiplos da altura.
MINIMO_PARA_AJUSTAR_A_LINHA = 3        # Pontos necessários para estimar a reta.

PONTUACAO_SEM_CARACTERES = -100.0      # Região vazia nunca vence a comparação.
PONTUACAO_BASE = 20
PESO_QUANTIDADE = 5                    # Penaliza afastar-se de TOTAL_CARACTERES.
PESO_ALTURA = 4                        # Penaliza alturas desiguais.
PESO_ALINHAMENTO = 4                   # Penaliza centros fora da linha.
PESO_OCUPACAO = 2                      # Premia ocupar a largura da região.
TOLERANCIA_DE_DESEMPATE = 0.05                # Diferença tratada como empate.
TOLERANCIA_DE_POSICAO_NO_DESEMPATE = 0.25     # Em múltiplos da largura do caractere.

# --- Etapa 6 · preparação individual ----------------------------------------
ALTURA_CARACTERE = 100                 # Altura padrão do símbolo enviado ao OCR.
LARGURA_MINIMA_CARACTERE = 8           # Evita recortes degenerados ao redimensionar.
LARGURA_MAXIMA_CARACTERE = 105
MARGEM_PADRAO = 20                     # Margem branca do preparo padrão.
MARGENS_ALTERNATIVAS = (10, 20, 30)    # Margens testadas nas novas tentativas.
ALTURAS_VALIDAS = tuple(ALTURA_CARACTERE + 2 * m for m in MARGENS_ALTERNATIVAS)
ALTURA_PADRAO_DA_ENTRADA = ALTURA_CARACTERE + 2 * MARGEM_PADRAO
AREA_MINIMA_COMPONENTE = 8             # Em pixels; abaixo disso o recorte é recusado.
KERNEL_AFINAMENTO = (2, 2)             # Dilata o branco, afinando o traço preto.

ANGULO_MINIMO_CORRIGIVEL = 3           # Abaixo disso é ruído do desenho da letra.
ANGULO_MAXIMO_CORRIGIVEL = 15          # Acima disso não é mais inclinação de fonte.
PASSO_DO_ANGULO = 5                    # Arredonda para não fingir precisão de ângulo.
MINIMO_DE_SIMBOLOS_INCLINADOS = 5      # Exigidos no mesmo sentido para corrigir.
MARGEM_PARA_ROTACIONAR = 40            # Espaço extra para o símbolo não ser cortado.

# --- Etapa 7 · OCR ----------------------------------------------------------
NOME_DO_MOTOR = "tesseract"
IDIOMA_OCR = "eng"
MODO_OEM = 3                   # Motor LSTM padrão do Tesseract.
PSM_CARACTERE_UNICO = 10       # Interpreta a imagem como um único caractere.
PSM_LINHA_CRUA = 13            # Alternativa quando o PSM 10 não resolve.
TEMPO_LIMITE_OCR = 10          # Segundos por chamada ao motor.
CONFIANCA_MINIMA = 60.0        # Heurística, não uma probabilidade calibrada.
MINIMO_DE_CONCORDANCIAS = 2    # Preparos que precisam concordar para aceitar.

# --- Etapa 8 · resultado ----------------------------------------------------
FORMATOS = ("livre", "antiga", "mercosul")
PADROES_DE_PLACA = {
    "antiga": r"[A-Z]{3}[0-9]{4}",
    "mercosul": r"[A-Z]{3}[0-9][A-Z][0-9]{2}",
    "livre": r"(?:[A-Z]{3}(?:[0-9]{4}|[0-9][A-Z][0-9]{2})|[A-Z]{4}[0-9]{3})",
}
