"""Responsabilidades internas da etapa 5, sem OCR nem interface.

``binarizacao`` prepara a região e gera as oito máscaras.
``componentes`` identifica regiões conectadas com tamanho plausível de símbolo.
``alinhamento`` seleciona a linha dominante e ordena seus componentes.
``avaliacao`` pontua a geometria e desempata as alternativas.

A entrada principal continua em ``placas.etapas.e5_segmentacao.segmentar``.
"""
