import datetime

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncMonth

from .models import Reunioes


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
