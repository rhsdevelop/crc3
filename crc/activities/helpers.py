import datetime

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.db.models import Sum, Count

from .models import Relatorios

def imprime_cartao(arquivo, meses_intervalo, publicador_id, formulario=True, cabecalho=True, dados=True, soma=True):
    def renderiza_cabeçalho():
        icanvas.drawString(58 + ct, 196 + qt, publicador)         # Nome
        if sexo == 1:
            icanvas.drawString(488 + ct, 179 + qt, 'x')   # Sexo
        elif sexo == 0:
            icanvas.drawString(386 + ct, 179 + qt, 'x')   # Sexo
        if privilegio == 2:
            icanvas.drawString(19 + ct, 146 + qt, 'x')       # Privilégio
        elif privilegio == 1:
            icanvas.drawString(86 + ct, 146 + qt, 'x')   # Privilégio
        if tipo == 2:
            icanvas.drawString(212 + ct, 146 + qt, 'x')     # Pioneiro Regular
        icanvas.drawString(135 + ct, 179 + qt, '' if not nascimento else datetime.datetime.strftime(nascimento, '%d/%m/%Y'))
        icanvas.drawString(118 + ct, 162 + qt, '' if not batismo else datetime.datetime.strftime(batismo, '%d/%m/%Y'))
        if esperanca == 0:
            icanvas.drawString(386 + ct, 162 + qt, 'x')   # Esperança
        elif esperanca == 1:
            icanvas.drawString(488 + ct, 162 + qt, 'x')   # Esperança
        icanvas.drawString(40, 650, service_year)

    data = Relatorios.objects.filter(mes__range=meses_intervalo, publicador_id=publicador_id)
    # inicializa o pdf
    icanvas = None
    first = True
    if data:
        icanvas = canvas.Canvas(arquivo, pagesize=letter)
        pub = data[0].publicador
        publicador = pub.nome
        sexo = pub.sexo
        privilegio = pub.privilegio
        tipo = pub.tipo
        nascimento = pub.nascimento
        batismo = pub.batismo
        esperanca = pub.esperanca
    else:
        return None
    icanvas.setPageSize((595, 842)) # para uso com arquivo model.png que era o modelo anterior.
    icanvas.setLineWidth(.3)
    icanvas.setFont('Times-Roman', 12)
    # Anexa o plano de fundo; modelo do cartão
    if formulario:
        logo = "static/img/S-21_T.png"
        logo2 = "static/img/S-21_T.jpg"
        try:
            icanvas.drawImage(logo, 0, 0, width=595, height=842, preserveAspectRatio=False)
        except:
            icanvas.drawImage(logo2, 0, 0, width=595, height=842, preserveAspectRatio=False)
    qt = 570
    ct = 0

    # PRIMEIRO ANO DE SERVIÇO
    # Preenche cabeçalho e primeiro ano de serviço.
    if cabecalho:
        service_year = meses_intervalo[0].year - (1 if meses_intervalo[0].month <= 8 else 0)
        service_year = str(service_year) + '/' + str(service_year + 1)
        renderiza_cabeçalho()

    soma = {'Horas': 0, 'Estudos': 0}

    first = True
    # Preenche dados dos relatórios mensais.
    for item in data:
        if item.mes.month == 9 and not first:
            # Preenche a soma no cartão concluído.
            if soma:
                icanvas.setFont('Times-Bold', 12)
                icanvas.drawString(340, 388, str(soma['Horas']))
                soma = {'Horas': 0, 'Estudos': 0}
            # ANOS DE SERVIÇO POSTERIORES
            # Preenche cabeçalho e primeiro ano de serviço.
            icanvas.showPage()
            icanvas.setPageSize((595, 842)) # para uso com arquivo model.png que era o modelo anterior.
            icanvas.setLineWidth(.3)
            icanvas.setFont('Times-Roman', 12)
            if formulario:
                logo = "static/img/S-21_T.png"
                logo2 = "static/img/S-21_T.jpg"
                try:
                    icanvas.drawImage(logo, 0, 0, width=595, height=842, preserveAspectRatio=False)
                except:
                    icanvas.drawImage(logo2, 0, 0, width=595, height=842, preserveAspectRatio=False)
            if cabecalho:
                service_year = item.mes.year
                service_year = str(service_year) + '/' + str(service_year + 1)
                renderiza_cabeçalho()
        if dados:
            col = (item.mes.month - 9 if item.mes.month > 8 else item.mes.month + 3) * 19.8
            try:
                if item.tipo != 3:
                    icanvas.drawString(133, 628 - col, 'x')
                icanvas.drawString(203, 628 - col, str(item.estudos))
                if item.tipo == 1:
                    icanvas.drawString(275, 628 - col, 'x')
                if item.tipo in [1, 2]:
                    icanvas.drawString(340, 628 - col, str(item.horas))
                soma['Horas'] = soma['Horas'] + int(item.horas)
                soma['Estudos'] = soma['Estudos'] + int(item.estudos)
                icanvas.drawString(390, 628 - col, item.observacao)
            except:
                pass
        first = False
    if soma:
        icanvas.setFont('Times-Bold', 12)
        icanvas.drawString(340, 388, str(soma['Horas']))
        soma = {'Horas': 0, 'Estudos': 0}
    if icanvas:
        try:
            icanvas.save()
            return arquivo
        except Exception as err:
            return err
    else:
        return None


def imprime_cartao_resumo(arquivo, meses_intervalo, filter_search, formulario=True, cabecalho=True, dados=True, soma=True):
    def renderiza_cabeçalho():
        icanvas.drawString(58 + ct, 196 + qt, publicador)         # Nome
        if sexo == 1:
            icanvas.drawString(488 + ct, 179 + qt, 'x')   # Sexo
        elif sexo == 0:
            icanvas.drawString(386 + ct, 179 + qt, 'x')   # Sexo
        if privilegio == 2:
            icanvas.drawString(19 + ct, 146 + qt, 'x')       # Privilégio
        elif privilegio == 1:
            icanvas.drawString(86 + ct, 146 + qt, 'x')   # Privilégio
        if tipo == 2:
            icanvas.drawString(212 + ct, 146 + qt, 'x')     # Pioneiro Regular
        icanvas.drawString(135 + ct, 179 + qt, '' if not nascimento else datetime.datetime.strftime(nascimento, '%d/%m/%Y'))
        icanvas.drawString(118 + ct, 162 + qt, '' if not batismo else datetime.datetime.strftime(batismo, '%d/%m/%Y'))
        if esperanca == 0:
            icanvas.drawString(386 + ct, 162 + qt, 'x')   # Esperança
        elif esperanca == 1:
            icanvas.drawString(488 + ct, 162 + qt, 'x')   # Esperança
        icanvas.drawString(40, 650, service_year)

    tipo_data = Relatorios.objects.filter(**filter_search).values('tipo', 'mes').annotate(membros=Count('id'), horas=Sum('horas'), estudos=Sum('estudos'))
    # inicializa o pdf
    icanvas = None
    if not tipo_data:
        return None
    else:
        tipo_list = [
            'Resumo de atividade dos Publicadores',
            'Resumo de atividade dos Pioneiros Auxiliares',
            'Resumo de atividade dos Pioneiros Regulares'
        ]
        icanvas = canvas.Canvas(arquivo, pagesize=letter)
        del filter_search['tipo__in']
        for tipo_id in range(0, 3):
            filter_search['tipo'] = tipo_id
            data = Relatorios.objects.filter(**filter_search).values('tipo', 'mes').annotate(membros=Count('id'), horas=Sum('horas'), estudos=Sum('estudos'))
            first = True
            if data:
                publicador = tipo_list[tipo_id]
                sexo = None
                privilegio = None
                tipo = tipo_id
                nascimento = None
                batismo = None
                esperanca = None
            if tipo_id != 0: icanvas.showPage()
            icanvas.setPageSize((595, 842)) # para uso com arquivo model.png que era o modelo anterior.
            icanvas.setLineWidth(.3)
            icanvas.setFont('Times-Roman', 12)
            # Anexa o plano de fundo; modelo do cartão
            if formulario:
                logo = "static/img/S-21_T.png"
                logo2 = "static/img/S-21_T.jpg"
                try:
                    icanvas.drawImage(logo, 0, 0, width=595, height=842, preserveAspectRatio=False)
                except:
                    icanvas.drawImage(logo2, 0, 0, width=595, height=842, preserveAspectRatio=False)
            qt = 570
            ct = 0

            # PRIMEIRO ANO DE SERVIÇO
            # Preenche cabeçalho e primeiro ano de serviço.
            if cabecalho:
                service_year = meses_intervalo[0].year - (1 if meses_intervalo[0].month <= 8 else 0)
                service_year = str(service_year) + '/' + str(service_year + 1)
                renderiza_cabeçalho()

            soma = {'Horas': 0, 'Estudos': 0}

            first = True
            # Preenche dados dos relatórios mensais.
            for item in data:
                if item['mes'].month == 9 and not first:
                    # Preenche a soma no cartão concluído.
                    if soma:
                        icanvas.setFont('Times-Bold', 12)
                        icanvas.drawString(340, 388, str(soma['Horas']))
                        soma = {'Horas': 0, 'Estudos': 0}
                    # ANOS DE SERVIÇO POSTERIORES
                    # Preenche cabeçalho e primeiro ano de serviço.
                    icanvas.showPage()
                    icanvas.setPageSize((595, 842)) # para uso com arquivo model.png que era o modelo anterior.
                    icanvas.setLineWidth(.3)
                    icanvas.setFont('Times-Roman', 12)
                    if formulario:
                        logo = "static/img/S-21_T.png"
                        logo2 = "static/img/S-21_T.jpg"
                        try:
                            icanvas.drawImage(logo, 0, 0, width=595, height=842, preserveAspectRatio=False)
                        except:
                            icanvas.drawImage(logo2, 0, 0, width=595, height=842, preserveAspectRatio=False)
                    if cabecalho:
                        service_year = item['mes'].year
                        service_year = str(service_year) + '/' + str(service_year + 1)
                        renderiza_cabeçalho()
                if dados:
                    col = (item['mes'].month - 9 if item['mes'].month > 8 else item['mes'].month + 3) * 19.8
                    try:
                        if item['tipo'] != 3:
                            icanvas.drawString(133, 628 - col, 'x')
                        icanvas.drawString(203, 628 - col, str(item['estudos']))
                        if item['tipo'] == 1:
                            icanvas.drawString(275, 628 - col, 'x')
                        if item['tipo'] in [1, 2]:
                            icanvas.drawString(340, 628 - col, str(item['horas']))
                        icanvas.drawString(390, 628 - col, str(item['membros']) + ' publicador%s.' % 'es' if item['membros'] != 1 else '')
                        soma['Horas'] = soma['Horas'] + int(item['horas'])
                        soma['Estudos'] = soma['Estudos'] + int(item['estudos'])
                    except:
                        pass
                first = False
            if soma:
                icanvas.setFont('Times-Bold', 12)
                icanvas.drawString(340, 388, str(soma['Horas']))
                soma = {'Horas': 0, 'Estudos': 0}
    if icanvas:
        try:
            icanvas.save()
            return arquivo
        except Exception as err:
            return err
    else:
        return None
