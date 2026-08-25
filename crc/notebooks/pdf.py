import os
import threading
from io import BytesIO

import reportlab
from PIL import Image, ImageOps
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import EmbeddedType1Face, Font
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .services import MESES_PORTUGUES, dias_mes, meses_ano_servico


LARGURA_PAGINA, ALTURA_PAGINA = landscape(A4)
MEIO_PAGINA = LARGURA_PAGINA / 2
COR_TEXTO = colors.HexColor('#17202a')
COR_LINHAS = colors.HexColor('#49515b')
COR_CABECALHO = colors.HexColor('#f1f3f5')
COR_FIM_SEMANA = colors.HexColor('#e9ecef')
MARGEM_ESQUERDA = 15
LARGURA_ESQUERDA = MEIO_PAGINA - 30
MARGEM_DIREITA = MEIO_PAGINA + 32
LARGURA_DIREITA = LARGURA_PAGINA - MARGEM_DIREITA - 17

EVENTOS_MES = [
    'Assembléia de Circuito',
    'Celebração',
    'Congresso Regional',
    'Escola de Pioneiros',
    'Reunião Especial',
    'Visita do Sup. de Circuito',
]

VERSICULO_ABERTURA = [
    'Como são lindos, sobre os montes,',
    'os pés daquele que traz boas novas,',
    'Do proclamador de paz,',
    'Daquele que traz boas novas de algo melhor,',
    'Do proclamador de salvação,',
    'Daquele que diz a Sião: “Seu Deus tornou-se Rei!”',
]

_FONT_LOCK = threading.Lock()
_FONTES = None


def registrar_fontes():
    global _FONTES
    if _FONTES:
        return _FONTES

    with _FONT_LOCK:
        if _FONTES:
            return _FONTES

        pasta_fontes = os.path.join(os.path.dirname(reportlab.__file__), 'fonts')
        fontes = {
            'normal': 'Helvetica',
            'negrito': 'Helvetica-Bold',
            'italico': 'Times-Italic',
            'caligrafica': 'Times-Italic',
        }
        arquivos = [
            ('normal', 'CadernoVera', 'Vera.ttf'),
            ('negrito', 'CadernoVeraNegrito', 'VeraBd.ttf'),
            ('italico', 'CadernoVeraItalico', 'VeraIt.ttf'),
        ]

        for chave, nome, arquivo in arquivos:
            caminho = os.path.join(pasta_fontes, arquivo)
            if os.path.isfile(caminho):
                if nome not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont(nome, caminho))
                fontes[chave] = nome

        afm = os.path.join(pasta_fontes, 'callig15.afm')
        pfb = os.path.join(pasta_fontes, 'callig15.pfb')
        if os.path.isfile(afm) and os.path.isfile(pfb):
            nome = 'CadernoCaligrafia'
            if nome not in pdfmetrics.getRegisteredFontNames():
                face = EmbeddedType1Face(afm, pfb)
                pdfmetrics.registerTypeFace(face)
                pdfmetrics.registerFont(Font(nome, face.name, 'WinAnsiEncoding'))
            fontes['caligrafica'] = nome

        _FONTES = fontes
        return _FONTES


def _texto_ajustado(pdf, texto, x, y, largura, fonte, tamanho, minimo=7, centro=False):
    def largura_renderizada(tamanho_fonte):
        largura_texto = pdfmetrics.stringWidth(texto, fonte, tamanho_fonte)
        espaco_nativo = pdfmetrics.stringWidth(' ', fonte, tamanho_fonte)
        espaco_palavras = tamanho_fonte * 0.22 if not espaco_nativo else 0
        largura_texto += texto.count(' ') * espaco_palavras
        return largura_texto, espaco_palavras

    largura_texto, espaco_palavras = largura_renderizada(tamanho)
    while tamanho > minimo and largura_texto > largura:
        tamanho -= 0.3
        largura_texto, espaco_palavras = largura_renderizada(tamanho)

    pdf.setFont(fonte, tamanho)
    posicao_x = x + (largura - largura_texto) / 2 if centro else x
    if espaco_palavras:
        pdf.drawString(posicao_x, y, texto, wordSpace=espaco_palavras)
        return
    pdf.drawString(posicao_x, y, texto)


def _imagem_capa(configuracao, largura, altura):
    with configuracao.imagem.open('rb') as arquivo:
        with Image.open(arquivo) as original:
            imagem = ImageOps.exif_transpose(original)
            if imagem.mode in ('RGBA', 'LA') or (
                imagem.mode == 'P' and 'transparency' in imagem.info
            ):
                rgba = imagem.convert('RGBA')
                fundo = Image.new('RGBA', rgba.size, 'white')
                fundo.alpha_composite(rgba)
                imagem = fundo.convert('RGB')
            else:
                imagem = imagem.convert('RGB')
            tamanho = (max(1, round(largura * 3)), max(1, round(altura * 3)))
            imagem = ImageOps.fit(
                imagem,
                tamanho,
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
            return ImageReader(imagem)


def _desenhar_capa(pdf, publicador, configuracao, imagem, fontes):
    x = MEIO_PAGINA + 28
    largura = LARGURA_PAGINA - x - 18
    titulo_y = ALTURA_PAGINA - 83

    pdf.setFillColor(COR_TEXTO)
    _texto_ajustado(
        pdf,
        'CADERNO DE ATIVIDADE DE PREGAÇÃO',
        x,
        titulo_y,
        largura,
        fontes['negrito'],
        17,
        minimo=12,
        centro=True,
    )
    pdf.setStrokeColor(COR_LINHAS)
    pdf.setLineWidth(0.8)
    pdf.line(x, titulo_y - 10, x + largura, titulo_y - 10)

    imagem_x = x + 17
    imagem_largura = largura - 34
    imagem_altura = 146
    imagem_y = 230
    pdf.drawImage(
        imagem,
        imagem_x,
        imagem_y,
        width=imagem_largura,
        height=imagem_altura,
        preserveAspectRatio=False,
        mask='auto',
    )
    pdf.setLineWidth(0.9)
    pdf.rect(imagem_x - 1, imagem_y - 1, imagem_largura + 2, imagem_altura + 2)

    _texto_ajustado(
        pdf,
        'Ano de Serviço: %s' % configuracao.ano_servico_exibicao,
        x,
        178,
        largura,
        fontes['negrito'],
        22,
        minimo=15,
        centro=True,
    )

    etiqueta = 'Pioneiro Regular:'
    pdf.setFont(fontes['negrito'], 10)
    pdf.drawString(x, 91, etiqueta)
    nome_x = x + pdfmetrics.stringWidth(etiqueta, fontes['negrito'], 10) + 8
    largura_nome = x + largura - nome_x
    _texto_ajustado(
        pdf,
        publicador.nome,
        nome_x,
        89,
        largura_nome,
        fontes['caligrafica'],
        18,
        minimo=10,
    )
    pdf.setLineWidth(0.45)
    pdf.line(nome_x, 85, x + largura, 85)


def gerar_pdf_capas(configuracao, publicadores):
    fontes = registrar_fontes()
    arquivo = BytesIO()
    pdf = canvas.Canvas(arquivo, pagesize=landscape(A4), pageCompression=0)
    pdf.setTitle('Capas dos cadernos de pioneiros regulares')
    pdf.setAuthor('CRC-3')

    largura_imagem = LARGURA_PAGINA - (MEIO_PAGINA + 28) - 18 - 34
    imagem = _imagem_capa(configuracao, largura_imagem, 146)
    for publicador in publicadores:
        _desenhar_capa(pdf, publicador, configuracao, imagem, fontes)
        pdf.showPage()

    pdf.save()
    arquivo.seek(0)
    return arquivo


def _desenhar_informacoes(pdf, fontes):
    x = MARGEM_ESQUERDA
    largura = LARGURA_ESQUERDA
    pdf.setFillColor(COR_TEXTO)
    pdf.setStrokeColor(COR_LINHAS)

    pdf.setFont(fontes['negrito'], 11)
    pdf.drawCentredString(x + largura / 2, ALTURA_PAGINA - 28, 'INFORMAÇÕES IMPORTANTES')

    cabecalho_y = ALTURA_PAGINA - 76
    pdf.setFont(fontes['negrito'], 8.6)
    pdf.drawCentredString(x + 30, cabecalho_y, 'DATA')
    pdf.drawCentredString(
        x + 220,
        cabecalho_y,
        'TEMA DO DISCURSO NO FINAL DE SEMANA',
    )
    pdf.setLineWidth(0.45)
    primeira_linha = cabecalho_y - 18
    for indice in range(5):
        y = primeira_linha - indice * 15
        pdf.line(x, y, x + largura, y)

    eventos_y = ALTURA_PAGINA - 183
    pdf.setFont(fontes['negrito'], 9.2)
    pdf.drawCentredString(x + largura / 2, eventos_y, 'EVENTOS ESPECIAIS DO MÊS')
    pdf.setFont(fontes['normal'], 8.5)
    for indice, evento in enumerate(EVENTOS_MES):
        y = eventos_y - 20 - indice * 15
        pdf.rect(x + 4, y - 1, 7, 7, fill=0, stroke=1)
        pdf.drawString(x + 15, y, evento)
        pdf.line(x + 160, y - 2, x + largura, y - 2)

    anotacoes_y = ALTURA_PAGINA - 303
    pdf.setFont(fontes['negrito'], 10)
    pdf.drawCentredString(x + largura / 2, anotacoes_y, 'ANOTAÇÕES')
    y = anotacoes_y - 21
    while y >= 38:
        pdf.line(x, y, x + largura, y)
        y -= 15


def _desenhar_abertura(pdf, fontes):
    x = MARGEM_DIREITA
    largura = LARGURA_DIREITA
    pdf.setFillColor(COR_TEXTO)
    _texto_ajustado(
        pdf,
        'Atividade do pioneiro',
        x,
        ALTURA_PAGINA - 137,
        largura,
        fontes['negrito'],
        22,
        minimo=16,
        centro=True,
    )
    pdf.setLineWidth(0.8)
    pdf.line(x, ALTURA_PAGINA - 145, x + largura, ALTURA_PAGINA - 145)

    y = ALTURA_PAGINA - 215
    for linha in VERSICULO_ABERTURA:
        _texto_ajustado(
            pdf,
            linha,
            x,
            y,
            largura,
            fontes['caligrafica'],
            21,
            minimo=14,
            centro=True,
        )
        y -= 32

    _texto_ajustado(
        pdf,
        'Isaías 52:7',
        x + largura * 0.56,
        y - 18,
        largura * 0.42,
        fontes['caligrafica'],
        27,
        minimo=18,
        centro=True,
    )


def _colunas_relatorio():
    proporcoes = [28, 29, 45, 48, 47, 43, 66, 49]
    total = sum(proporcoes)
    return [LARGURA_DIREITA * valor / total for valor in proporcoes]


def _desenhar_mes(pdf, data, meta_horas, fontes):
    x = MARGEM_DIREITA
    largura = LARGURA_DIREITA
    pdf.setFillColor(COR_TEXTO)

    _texto_ajustado(
        pdf,
        'RELATÓRIO DE SERVIÇO DE CAMPO',
        x,
        ALTURA_PAGINA - 28,
        largura,
        fontes['negrito'],
        11,
        minimo=9,
        centro=True,
    )

    identificacao_y = ALTURA_PAGINA - 54
    pdf.setFont(fontes['normal'], 9.5)
    pdf.drawString(x + largura * 0.46, identificacao_y, 'Mês:')
    mes_x = x + largura * 0.54
    mes_largura = largura * 0.22
    _texto_ajustado(
        pdf,
        MESES_PORTUGUES[data.month - 1],
        mes_x,
        identificacao_y,
        mes_largura,
        fontes['normal'],
        9.5,
        minimo=7.5,
        centro=True,
    )
    pdf.line(mes_x, identificacao_y - 3, mes_x + mes_largura, identificacao_y - 3)
    ano_x = x + largura * 0.78
    pdf.setFont(fontes['normal'], 9.5)
    pdf.drawString(ano_x, identificacao_y, 'Ano:')
    valor_ano_x = x + largura * 0.88
    pdf.drawCentredString(valor_ano_x + largura * 0.055, identificacao_y, str(data.year))
    pdf.line(valor_ano_x, identificacao_y - 3, x + largura, identificacao_y - 3)

    topo = ALTURA_PAGINA - 68
    altura_cabecalho = 16
    altura_linha = 14.1
    colunas = _colunas_relatorio()
    limites = [x]
    for coluna in colunas:
        limites.append(limites[-1] + coluna)

    pdf.setFillColor(COR_CABECALHO)
    pdf.rect(x, topo - altura_cabecalho, largura, altura_cabecalho, fill=1, stroke=0)

    dias = list(dias_mes(data, meta_horas))
    for indice, item in enumerate(dias):
        if item['fim_semana']:
            y = topo - altura_cabecalho - (indice + 1) * altura_linha
            pdf.setFillColor(COR_FIM_SEMANA)
            pdf.rect(x, y, largura, altura_linha, fill=1, stroke=0)

    pdf.setStrokeColor(COR_LINHAS)
    pdf.setLineWidth(0.38)
    base = topo - altura_cabecalho - 31 * altura_linha
    for limite in limites:
        pdf.line(limite, base, limite, topo)
    pdf.line(x, topo, x + largura, topo)
    for indice in range(32):
        y = topo - altura_cabecalho - indice * altura_linha
        pdf.line(x, y, x + largura, y)

    pdf.setFillColor(COR_TEXTO)
    cabecalhos = ['', 'Dia', 'Meta', 'Soma', 'Hora', 'Vídeos', 'Publicações', 'Revisitas']
    for indice, cabecalho in enumerate(cabecalhos):
        _texto_ajustado(
            pdf,
            cabecalho,
            limites[indice] + 2,
            topo - 11,
            colunas[indice] - 4,
            fontes['negrito'],
            7.2,
            minimo=6,
            centro=True,
        )

    for indice, item in enumerate(dias):
        y = topo - altura_cabecalho - (indice + 1) * altura_linha + 4.2
        valores = [item['dia_semana'], str(item['dia']), item['meta']]
        for coluna, valor in enumerate(valores):
            fonte = fontes['negrito'] if coluna == 1 else fontes['normal']
            pdf.setFont(fonte, 8)
            pdf.drawCentredString(limites[coluna] + colunas[coluna] / 2, y, valor)

    rodape_y = base - 24
    pdf.setFont(fontes['normal'], 8.8)
    texto = 'Estudos Bíblicos dirigidos:'
    texto_largura = pdfmetrics.stringWidth(texto, fontes['normal'], 8.8)
    pdf.drawString(x + largura - texto_largura - 93, rodape_y, texto)
    pdf.line(x + largura - 83, rodape_y - 3, x + largura, rodape_y - 3)


def gerar_pdf_miolo(ano_servico, meta_horas=50):
    fontes = registrar_fontes()
    arquivo = BytesIO()
    pdf = canvas.Canvas(arquivo, pagesize=landscape(A4), pageCompression=0)
    pdf.setTitle('Caderno de atividade anual dos pioneiros regulares')
    pdf.setAuthor('CRC-3')

    _desenhar_informacoes(pdf, fontes)
    _desenhar_abertura(pdf, fontes)
    pdf.showPage()

    for data in meses_ano_servico(ano_servico):
        _desenhar_informacoes(pdf, fontes)
        _desenhar_mes(pdf, data, meta_horas, fontes)
        pdf.showPage()

    pdf.save()
    arquivo.seek(0)
    return arquivo
