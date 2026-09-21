from pathlib import Path
import cv2
from placas.processamento import localizar
from placas.preparacao_ocr import preparar_caractere, validar_entrada_ocr


def test_preserva_detalhe_interno_no_desempate_de_segmentacao():
    caminho = Path(__file__).parent / 'fixtures' / 'placa_paraguai.jpg'
    seg = localizar(cv2.imread(str(caminho))).segmentacao
    assert len(seg.caracteres) == 7
    assert seg.metodo == 'Otsu · caracteres escuros'
    recorte = preparar_caractere(seg.caracteres[0])
    validar_entrada_ocr(recorte)
    # O vértice central do W deve sobreviver na metade inferior do símbolo.
    letra = recorte[20:-20,20:-20]
    centro = letra[50:70, letra.shape[1]//2-2:letra.shape[1]//2+3]
    assert (centro == 0).mean() > 0.5
