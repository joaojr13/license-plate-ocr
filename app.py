"""Execute: streamlit run app.py."""
import hashlib
import io
import json
from pathlib import Path
import zipfile

import cv2
import streamlit as st

from placas.imagem import ler_imagem
from placas.exportacao import imagens_das_tentativas
from interface.passos import exibir_passos
from placas.ocr import verificar_tesseract
from placas.preparacao_ocr import preparar_caractere, preparar_recortes, validar_segmentacao
from placas.processamento import localizar, reconhecer
from placas.visualizacao import desenhar_localizacao, desenhar_segmentacao

st.set_page_config(page_title="Leitura de placas", page_icon="🚘", layout="wide")
st.title("Reconhecimento de placas veiculares")
st.caption("Visão computacional passo a passo · OpenCV + OCR individual")

with st.sidebar:
    st.header("Imagem de entrada")
    arquivo = st.file_uploader("Foto do veículo", type=["jpg", "jpeg", "png", "webp"])
    demonstracao = st.checkbox("Usar exemplo sintético", value=False)
    formato = "livre"
    st.caption("OCR: Tesseract · processamento local")
    st.info("Cada chamada ao OCR recebe somente um caractere isolado.")
    try:
        versao = verificar_tesseract()
        st.success(f"Tesseract {versao} disponível")
        motor_disponivel = True
    except (RuntimeError, OSError) as exc:
        st.warning(str(exc))
        motor_disponivel = False

if arquivo is not None:
    conteudo = arquivo.getvalue()
elif demonstracao:
    conteudo = (Path(__file__).parent / "examples" / "veiculo_sintetico.png").read_bytes()
    st.info("Exemplo desenhado para demonstrar o fluxo. Não comprova desempenho em fotografias reais.")
else:
    st.write("Envie uma foto frontal de um veículo ou selecione o exemplo sintético na lateral.")
    st.markdown("**1. Localizar** a placa → **2. Separar** os caracteres → "
                "**3. Reconhecer** um por vez → **4. Concatenar** e exibir.")
    st.stop()


@st.cache_data(show_spinner="Localizando a placa e separando os caracteres…", max_entries=5)
def analisar(dados: bytes, versao_segmentacao: str = "candidatas-morfologia-v4"):
    """Executa as etapas 1–5 dos módulos de processamento e guarda o resultado."""
    return localizar(ler_imagem(dados))


try:
    localizacao = analisar(conteudo)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

segmentacao = localizacao.segmentacao
chave = hashlib.sha256(conteudo + formato.encode() + b"tesseract-unico-v1").hexdigest()
if st.session_state.get("chave") != chave:
    st.session_state["chave"] = chave
    st.session_state.pop("resultado", None)

esquerda, direita = st.columns([3, 2])
with esquerda:
    st.subheader("1 · Região localizada")
    st.image(desenhar_localizacao(localizacao), channels="BGR", width="stretch")
with direita:
    st.subheader("2 · Caracteres segmentados")
    st.image(desenhar_segmentacao(segmentacao), channels="BGR", width="stretch")
    st.image(segmentacao.binaria, caption=f"Binarização: {segmentacao.metodo}", width="stretch")
    st.write(f"**{len(segmentacao.caracteres)} recortes** encontrados, ordenados da esquerda para a direita.")

valida = True
try:
    validar_segmentacao(segmentacao)
except ValueError as exc:
    valida = False
    st.warning(str(exc))

st.subheader("3 · Entradas individuais do OCR")
if segmentacao.caracteres:
    entradas = preparar_recortes(segmentacao) if valida else [preparar_caractere(c) for c in segmentacao.caracteres]
    for i, (coluna, entrada) in enumerate(zip(st.columns(len(entradas)), entradas)):
        with coluna:
            st.image(entrada, caption=f"Caractere {i+1}", width="stretch")

if st.button("Reconhecer caracteres", type="primary", disabled=not (valida and motor_disponivel)):
    st.session_state.pop("resultado", None)
    try:
        with st.spinner("Reconhecendo caracteres e conferindo as leituras incertas…"):
            st.session_state["resultado"] = reconhecer(segmentacao, formato)
    except (ValueError, RuntimeError, OSError) as exc:
        st.error(f"Não foi possível concluir o OCR: {exc}")

if "resultado" in st.session_state:
    resultado = st.session_state["resultado"]
    st.subheader("4 · Resultado consolidado")
    st.metric("Texto reconhecido", resultado["texto"])
    st.code(f'caracteres = {resultado["caracteres"]!r}\nplacas = {resultado["placas"]!r}', language="python")
    for aviso in resultado["avisos"]:
        st.warning(aviso)
    st.dataframe([
        {"Posição": i, "Caractere": leitura["caractere"], "Confiança": leitura["confianca"],
         "Tentativas": len(leitura["tentativas"]), "Decisão": leitura["motivo"]}
        for i, leitura in enumerate(resultado["leituras"], 1)
    ], hide_index=True, width="stretch")
    st.caption(f'{resultado["quantidade_chamadas_ocr"]} chamadas individuais ao OCR. '
               'Confira os candidatos e cada tentativa na etapa 7 do passo a passo.')
    st.caption("Confiança é a pontuação do motor selecionado, não uma probabilidade calibrada de acerto.")
    # Exporta cada entrada realmente enviada, incluindo as tentativas adicionais.
    pacote = io.BytesIO()
    imagens_exportadas = imagens_das_tentativas(segmentacao, resultado)
    adicionais = {nome: imagem for nome, imagem in imagens_exportadas.items() if 'cinza_' in nome}
    if adicionais:
        with st.expander("Recortes em tons de cinza enviados nas tentativas adicionais"):
            for nome, imagem in adicionais.items():
                st.image(imagem, caption=nome)
    with zipfile.ZipFile(pacote, "w", zipfile.ZIP_DEFLATED) as zipado:
        zipado.writestr("resultado.json", json.dumps(resultado, ensure_ascii=False, indent=2))
        for nome, imagem in imagens_exportadas.items():
            _, png = cv2.imencode(".png", imagem)
            zipado.writestr(nome, png.tobytes())
    st.download_button("Baixar resultado e recortes", pacote.getvalue(), "reconhecimento.zip", "application/zip")

exibir_passos(localizacao, "Sem formato informado", valida, motor_disponivel,
              st.session_state.get("resultado"))

st.caption("Protótipo didático para uma placa clara ou escura em uma linha. "
           "Inclinação acentuada, reflexos, borrões e letras unidas podem impedir a leitura.")
