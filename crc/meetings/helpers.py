import datetime
from calendar import monthrange

from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncMonth

from .models import Reunioes


def adiciona_meses(data, meses):
    mes = data.month - 1 + meses
    ano = data.year + mes // 12
    mes = mes % 12 + 1
    return datetime.date(ano, mes, 1)


def dias_reuniao_no_mes(mes, dia_semana):
    ultimo_dia = monthrange(mes.year, mes.month)[1]
    return [
        datetime.date(mes.year, mes.month, dia).day
        for dia in range(1, ultimo_dia + 1)
        if datetime.date(mes.year, mes.month, dia).weekday() == dia_semana
    ]


def dias_meio_semana_por_coluna(dias_meio_semana, dias_fim_semana):
    inicio = 0
    if dias_meio_semana and dias_fim_semana and dias_meio_semana[0] > dias_fim_semana[0]:
        inicio = 1
    return [
        (coluna + inicio, dia)
        for coluna, dia in enumerate(dias_meio_semana)
        if coluna + inicio < 5
    ]


def imprime_s3_reunioes(arquivo, congregacao, mes_inicial, dia_meio_semana, dia_fim_semana):
    pagina_largura = 595
    pagina_altura = 842
    template = settings.BASE_DIR / "static/img/S-3_T_template.jpg"
    meses = [adiciona_meses(mes_inicial, i) for i in range(3)]
    blocos = [
        {'congregacao_y': 697, 'mes_y': 697, 'meio_y': 646, 'fim_y': 606},
        {'congregacao_y': 448, 'mes_y': 448, 'meio_y': 397, 'fim_y': 357},
        {'congregacao_y': 199, 'mes_y': 199, 'meio_y': 148, 'fim_y': 108},
    ]
    semana_x = [207, 244, 281, 318, 355]
    congregacao_x = 231
    mes_x = 385

    icanvas = canvas.Canvas(arquivo)
    icanvas.setPageSize((pagina_largura, pagina_altura))
    icanvas.drawImage(str(template), 0, 0, width=pagina_largura, height=pagina_altura, preserveAspectRatio=False)
    icanvas.setFillColorRGB(0, 0, 0)

    for index, mes in enumerate(meses):
        bloco = blocos[index]
        icanvas.setFont('Times-Roman', 14)
        icanvas.drawString(congregacao_x, bloco['congregacao_y'], congregacao)
        icanvas.drawString(mes_x, bloco['mes_y'], mes.strftime('%m/%Y'))
        icanvas.setFont('Times-Bold', 9)
        dias_meio = dias_reuniao_no_mes(mes, dia_meio_semana)
        dias_fim = dias_reuniao_no_mes(mes, dia_fim_semana)
        for semana, dia in dias_meio_semana_por_coluna(dias_meio, dias_fim):
            icanvas.drawCentredString(semana_x[semana], bloco['meio_y'] + 4, str(dia))
        for semana, dia in enumerate(dias_fim[:5]):
            icanvas.drawCentredString(semana_x[semana], bloco['fim_y'] + 4, str(dia))

    icanvas.save()
    return arquivo


def imprime_cartao_resumo(arquivo, meses_intervalo, cong_id, formulario=True, cabecalho=True, dados=True, exibir_soma=True):
    service_year = meses_intervalo[0].year - (1 if meses_intervalo[0].month <= 8 else 0)
    service_year = str(service_year) + '/' + str(service_year + 1)
    # inicializa o pdf
    titulo = 'Reunioes'
    icanvas = canvas.Canvas(arquivo)
    # icanvas.setPageSize((450, 300))
    icanvas.setPageSize((595, 842))
    icanvas.setLineWidth(.3)
    icanvas.setFont('Times-Roman', 14)
    qt = 100
    ct = 75
    par = 0
    logo = "static/img/S-88_T.png"
    logo2 = "static/img/S-88_T.jpg"
    # anexa o plano de fundo; modelo do cartão
    try:
        icanvas.drawImage(logo, 0, 0, width=595, height=842, preserveAspectRatio=False)
    except:
        icanvas.drawImage(logo2, 0, 0, width=595, height=842, preserveAspectRatio=False)
    # abre os novos cartões para atualizar os dados
    for cart in [1, 0]:
        data = Reunioes.objects.filter(data__range=meses_intervalo, cong_id=cong_id, tipo=cart).annotate(mes=TruncMonth('data')).values('mes').annotate(eventos=Count('id'), total=Sum('assistencia'), media=Avg('assistencia'))
        if par == 2:
            icanvas.save()
            icanvas.setLineWidth(.3)
            icanvas.setFont('Times-Roman', 14)
            qt = 100
            ct = 75
            par = 0
        '''
        # anexa o plano de fundo; modelo do cartão ANTIGO
        try:
            icanvas.drawImage(logo, 0 + ct, 0 + qt, width=450, height=300, preserveAspectRatio=False)
        except:
            icanvas.drawImage(logo2, 0 + ct, 0 + qt, width=450, height=300, preserveAspectRatio=False)
        '''
        # preenche o cabeçalho
        #icanvas.drawString(65 + ct, 303 + qt, cart)         # Preenche o nome da reunião

        soma = {'Eventos': 0, 'Total': 0, 'Media': 0}
        lin = 0
        count = 0
        first = True
        icanvas.setFont('Times-Roman', 12)
        icanvas.drawString(-42 + ct + lin, 268 + qt, service_year)
        icanvas.setFont('Times-Roman', 14)
        for item in data:
            print(item)
            if item['mes'].month == 9 and not first:
                if exibir_soma:
                    icanvas.setFont('Times-Bold', 14)
                    if exibir_soma and soma['Eventos']:
                        icanvas.drawString(182 + ct + lin, 249 - 238 + qt, str(int(soma['Media'] / count)))
                service_year = item['mes'].year
                service_year = str(service_year) + '/' + str(service_year + 1)
                lin = lin + 282
                icanvas.setFont('Times-Roman', 12)
                icanvas.drawString(-42 + ct + lin, 268 + qt, service_year)
                icanvas.setFont('Times-Roman', 14)
                soma = {'Eventos': 0, 'Total': 0, 'Media': 0}
                count = 0

            col = (item['mes'].month - 9 if item['mes'].month > 8 else item['mes'].month + 3) * 19.8
            icanvas.drawString(50 + ct + lin, 249 - col + qt, str(item['eventos']))
            icanvas.drawString(115 + ct + lin, 249 - col + qt, str(item['total']))
            icanvas.drawString(182 + ct + lin, 249 - col + qt, str(int(item['media'])))
            soma['Eventos'] += item['eventos']
            soma['Total'] += item['total']
            soma['Media']  += item['media']
            count += 1
            first = False
        if exibir_soma:
            icanvas.setFont('Times-Bold', 14)
            if exibir_soma and soma['Eventos']:
                icanvas.drawString(182 + ct + lin, 249 - 238 + qt, str(int(soma['Media'] / count)))
            icanvas.setFont('Times-Roman', 14)
        qt += 350
        par += 1
    icanvas.save()
    if icanvas:
        try:
            icanvas.save()
            return arquivo
        except Exception as err:
            return err
    else:
        return None
