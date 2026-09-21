"""Localização, segmentação e reconhecimento individual de caracteres.

O caminho de leitura do projeto:

  placas/config.py     todos os parâmetros numéricos, agrupados por etapa
  placas/pipeline.py   o mapa do fluxo: quem chama quem, na ordem
  placas/etapas/       uma etapa por arquivo, de e1_preparacao a e8_resultado
  placas/validacao.py  as recusas que protegem o OCR
  placas/saida/        desenho das marcações e exportação dos recortes

Uso mínimo:

    from placas import localizar, reconhecer

    localizacao = localizar(imagem_bgr)
    resultado = reconhecer(localizacao.segmentacao)
"""
from placas.pipeline import localizar, reconhecer

__all__ = ["localizar", "reconhecer"]
