import datetime
from html import escape
from io import BytesIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import ProgramacaoCampo


AZUL = colors.HexColor('#174a72')
LINHA = colors.HexColor('#cbd5e1')


def gerar_pdf_programacao_campo(cong, semana):
    fim = semana + datetime.timedelta(days=6)
    itens = list(ProgramacaoCampo.objects.filter(
        cong=cong, data__range=(semana, fim)
    ).select_related('dirigente', 'grupo', 'territorio', 'local'))
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=11 * mm,
        rightMargin=11 * mm,
        topMargin=12 * mm,
        bottomMargin=14 * mm,
        title='Programação do Serviço de Campo',
        author='CRC-3',
    )
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle(
        'CampoTitulo', parent=estilos['Title'], fontName='Helvetica-Bold',
        fontSize=17, leading=20, textColor=colors.HexColor('#0b69b7'),
        alignment=TA_CENTER, spaceAfter=4,
    )
    subtitulo = ParagraphStyle(
        'CampoSubtitulo', parent=estilos['Normal'], fontSize=9.5,
        leading=12, alignment=TA_CENTER, textColor=colors.HexColor('#334155'),
    )
    cabecalho = ParagraphStyle(
        'CampoCabecalho', parent=estilos['Normal'], fontName='Helvetica-Bold',
        fontSize=7.5, leading=9, textColor=colors.white, alignment=TA_CENTER,
    )
    celula = ParagraphStyle(
        'CampoCelula', parent=estilos['Normal'], fontSize=7.2, leading=9,
        textColor=colors.HexColor('#17202a'), alignment=TA_LEFT,
    )
    elementos = [
        Paragraph('Programação do Serviço de Campo', titulo),
        Paragraph(escape(str(cong)), subtitulo),
        Paragraph(
            'Semana de %s a %s' % (
                semana.strftime('%d/%m/%Y'), fim.strftime('%d/%m/%Y')
            ),
            subtitulo,
        ),
        Spacer(1, 5 * mm),
    ]
    if not itens:
        vazio = ParagraphStyle(
            'CampoVazio', parent=estilos['Normal'], fontSize=11,
            alignment=TA_CENTER, textColor=colors.HexColor('#475569'),
            spaceBefore=18 * mm,
        )
        elementos.append(Paragraph(
            'Nenhuma saída programada para esta semana', vazio
        ))
    else:
        dados = [[Paragraph(valor, cabecalho) for valor in [
            'Data', 'Horário', 'Local / grupo', 'Dirigente', 'Atividade', 'Situação'
        ]]]
        for item in itens:
            local = escape(item.local_nome)
            if item.grupo_nome:
                local += '<br/><font color="#475569">%s</font>' % escape(item.grupo_nome)
            dados.append([
                Paragraph(item.data.strftime('%d/%m/%Y'), celula),
                Paragraph(item.horario.strftime('%H:%M'), celula),
                Paragraph(local, celula),
                Paragraph(escape(item.dirigente_exibicao), celula),
                Paragraph(escape(item.atividade_exibicao), celula),
                Paragraph(escape(item.get_status_display()), celula),
            ])
        larguras = [25 * mm, 19 * mm, 62 * mm, 55 * mm, 57 * mm, 31 * mm]
        tabela = Table(dados, colWidths=larguras, repeatRows=1, hAlign='CENTER')
        estilo = [
            ('BACKGROUND', (0, 0), (-1, 0), AZUL),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.35, LINHA),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]
        for indice in range(1, len(dados)):
            estilo.append((
                'BACKGROUND', (0, indice), (-1, indice),
                colors.white if indice % 2 else colors.HexColor('#f3f7fa'),
            ))
        tabela.setStyle(TableStyle(estilo))
        elementos.append(tabela)

    agora = timezone.now()
    if timezone.is_aware(agora):
        agora = timezone.localtime(agora)
    gerado_em = agora.strftime('%d/%m/%Y às %H:%M')

    def rodape(canvas, documento):
        canvas.saveState()
        largura, _ = landscape(A4)
        canvas.setStrokeColor(LINHA)
        canvas.line(doc.leftMargin, 9 * mm, largura - doc.rightMargin, 9 * mm)
        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.setFont('Helvetica', 7)
        canvas.drawString(doc.leftMargin, 5.5 * mm, 'Gerado em %s' % gerado_em)
        canvas.drawRightString(
            largura - doc.rightMargin, 5.5 * mm, 'Página %s' % documento.page
        )
        canvas.restoreState()

    doc.build(elementos, onFirstPage=rodape, onLaterPages=rodape)
    buffer.seek(0)
    return buffer
