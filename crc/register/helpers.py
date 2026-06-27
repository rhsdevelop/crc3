import datetime
from pathlib import Path

from django.conf import settings
from reportlab.pdfgen import canvas


S205_PAGE_WIDTH = 842
S205_PAGE_HEIGHT = 595
S205_IMAGE_WIDTH = 2480
S205_IMAGE_HEIGHT = 1754
OBSERVACOES_SERVICO_CONTINUO = ['tempo indeterminado', 'continuamente']


def _x(pixel):
    return pixel * S205_PAGE_WIDTH / S205_IMAGE_WIDTH


def _y(pixel):
    return S205_PAGE_HEIGHT - (pixel * S205_PAGE_HEIGHT / S205_IMAGE_HEIGHT)


def _draw_fit_text(icanvas, text, x, y, max_width, font='Times-Roman', size=12, min_size=8, centered=False):
    text = text or ''
    current_size = size
    while current_size > min_size and icanvas.stringWidth(text, font, current_size) > max_width:
        current_size -= 0.5
    icanvas.setFont(font, current_size)
    if centered:
        icanvas.drawCentredString(x, y, text)
    else:
        icanvas.drawString(x, y, text)


def gerar_peticao_pioneiro_auxiliar(arquivo, pioneiro, comissao=None, data_peticao=None):
    data_peticao = data_peticao or datetime.date.today()
    publicador = pioneiro.publicador
    membros = [
        '' if not comissao or not comissao.coordenador else comissao.coordenador,
        '' if not comissao or not comissao.superintendente_servico else comissao.superintendente_servico,
        '' if not comissao or not comissao.secretario else comissao.secretario,
    ]

    template = Path(settings.BASE_DIR) / 'static' / 'img' / 'S-205b_T_page-0001.jpg'
    icanvas = canvas.Canvas(arquivo, pageCompression=0)
    icanvas.setPageSize((S205_PAGE_WIDTH, S205_PAGE_HEIGHT))
    icanvas.drawImage(str(template), 0, 0, width=S205_PAGE_WIDTH, height=S205_PAGE_HEIGHT, preserveAspectRatio=False)
    icanvas.setFillColorRGB(0, 0, 0)

    mes_servico = pioneiro.mes.strftime('%m/%Y')
    observacao = (pioneiro.observacao or '').strip()
    servico_continuo = getattr(pioneiro, 'tempo_indeterminado', False) or observacao.lower() in OBSERVACOES_SERVICO_CONTINUO
    if observacao and not servico_continuo:
        mes_servico = '%s     %s' % (mes_servico, pioneiro.observacao)

    _draw_fit_text(
        icanvas,
        mes_servico,
        _x(600),
        _y(512),
        _x(1760),
        size=14,
    )
    if servico_continuo:
        _draw_fit_text(icanvas, 'X', _x(221), _y(565), _x(40), font='Times-Bold', size=16, centered=True)

    _draw_fit_text(
        icanvas,
        data_peticao.strftime('%d/%m/%Y'),
        _x(320),
        _y(817),
        _x(560),
        size=14,
    )

    nome = publicador.nome
    _draw_fit_text(icanvas, nome, _x(1650), _y(812), _x(1180), size=14, centered=True)
    _draw_fit_text(icanvas, nome, _x(1650), _y(963), _x(1180), size=14, centered=True)

    linhas_comissao = [1308, 1425, 1544]
    for membro, linha_y in zip(membros, linhas_comissao):
        _draw_fit_text(icanvas, membro, _x(1990), _y(linha_y), _x(600), size=12, centered=True)

    icanvas.save()
    return arquivo
