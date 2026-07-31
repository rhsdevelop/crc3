from html import escape
from io import BytesIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .services import montar_grade_testemunho_publico


AZUL = colors.HexColor('#0b69b7')
AZUL_ESCURO = colors.HexColor('#174a72')
LINHA = colors.HexColor('#c8d2dc')


def gerar_pdf_testemunho_publico(cong, semana, carrinho=None):
    grade = montar_grade_testemunho_publico(cong, semana, carrinho=carrinho)
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=12 * mm,
        bottomMargin=14 * mm,
        title='Testemunho Público',
        author='CRC-3',
        pageCompression=0,
    )
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle(
        'TituloTP', parent=estilos['Title'], fontName='Helvetica-Bold',
        fontSize=17, leading=20, textColor=AZUL, alignment=TA_CENTER,
        spaceAfter=4,
    )
    subtitulo = ParagraphStyle(
        'SubtituloTP', parent=estilos['Normal'], fontSize=9.5, leading=12,
        alignment=TA_CENTER, textColor=colors.HexColor('#334155'),
    )
    cabecalho = ParagraphStyle(
        'CabecalhoTP', parent=estilos['Normal'], fontName='Helvetica-Bold',
        fontSize=7.2, leading=8.5, textColor=colors.white, alignment=TA_CENTER,
    )
    horario = ParagraphStyle(
        'HorarioTP', parent=estilos['Normal'], fontName='Helvetica-Bold',
        fontSize=7.2, leading=8.5, textColor=AZUL_ESCURO, alignment=TA_LEFT,
    )
    celula = ParagraphStyle(
        'CelulaTP', parent=estilos['Normal'], fontSize=6.8, leading=8.4,
        textColor=colors.HexColor('#17202a'), alignment=TA_LEFT,
    )

    filtro = str(carrinho) if carrinho else 'Todos os carrinhos'
    elementos = [
        Paragraph('Testemunho Público', titulo),
        Paragraph(escape(str(cong)), subtitulo),
        Paragraph(
            'Semana de %s a %s &nbsp;&nbsp;|&nbsp;&nbsp; %s' % (
                semana.strftime('%d/%m/%Y'),
                grade['fim_semana'].strftime('%d/%m/%Y'),
                escape(filtro),
            ),
            subtitulo,
        ),
        Spacer(1, 5 * mm),
    ]

    if not grade['designacoes']:
        vazio = ParagraphStyle(
            'VazioTP', parent=estilos['Normal'], fontSize=11, leading=14,
            alignment=TA_CENTER, textColor=colors.HexColor('#475569'),
            spaceBefore=18 * mm,
        )
        elementos.append(Paragraph(
            'Nenhuma designação programada para esta semana', vazio
        ))
    else:
        dados = [[Paragraph('Horário', cabecalho)] + [
            Paragraph(
                '%s<br/><font size="6.5">%s</font>' % (
                    escape(dia['nome']), dia['data'].strftime('%d/%m')
                ),
                cabecalho,
            )
            for dia in grade['dias']
        ]]
        for linha in grade['linhas']:
            linha_pdf = [Paragraph(escape(linha['rotulo']), horario)]
            for item in linha['celulas']:
                blocos = []
                for designacao in item['designacoes']:
                    blocos.append(
                        '<b>%s</b><br/><font color="#475569">%s</font>' % (
                            escape(designacao.nomes_resumidos),
                            escape(str(designacao.local)),
                        )
                    )
                linha_pdf.append(Paragraph('<br/><br/>'.join(blocos), celula))
            dados.append(linha_pdf)

        largura_horario = 28 * mm
        largura_dia = (doc.width - largura_horario) / 7
        tabela = Table(
            dados,
            colWidths=[largura_horario] + [largura_dia] * 7,
            repeatRows=1,
            hAlign='CENTER',
        )
        estilo_tabela = [
            ('BACKGROUND', (0, 0), (-1, 0), AZUL_ESCURO),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.35, LINHA),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]
        for indice in range(1, len(dados)):
            cor = colors.white if indice % 2 else colors.HexColor('#f3f7fa')
            estilo_tabela.append(('BACKGROUND', (0, indice), (-1, indice), cor))
        tabela.setStyle(TableStyle(estilo_tabela))
        elementos.append(tabela)

    agora = timezone.now()
    if timezone.is_aware(agora):
        agora = timezone.localtime(agora)
    gerado_em = agora.strftime('%d/%m/%Y às %H:%M')

    def desenhar_rodape(canvas, documento):
        canvas.saveState()
        canvas.setStrokeColor(LINHA)
        canvas.setLineWidth(0.4)
        canvas.line(doc.leftMargin, 9 * mm, landscape(A4)[0] - doc.rightMargin, 9 * mm)
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawString(doc.leftMargin, 5.5 * mm, 'Gerado em %s' % gerado_em)
        canvas.drawRightString(
            landscape(A4)[0] - doc.rightMargin,
            5.5 * mm,
            'Página %s' % documento.page,
        )
        canvas.restoreState()

    doc.build(
        elementos,
        onFirstPage=desenhar_rodape,
        onLaterPages=desenhar_rodape,
    )
    buffer.seek(0)
    return buffer
