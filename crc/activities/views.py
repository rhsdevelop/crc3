import csv
import datetime
import json
import os
from io import BytesIO, StringIO
from zipfile import ZipFile, ZIP_DEFLATED

from register.models import Cong, CongUser, Drive, Grupos, Publicadores, Pioneiros, TIPO
from .forms import AddRelatoriosForm, FindRelatoriosForm, FindResumoForm, FindResumoPioneirosRegularesForm, FindCartoesForm
from .helpers import imprime_cartao, imprime_cartao_resumo
from .models import Relatorios

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Avg, Case, Count, IntegerField, Q, Sum, Value, When
from django.db.models.functions import Coalesce
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.template import loader


def periodo_ano_servico(data=None):
    data = data or datetime.date.today()
    ano_servico = data.year if data.month >= 9 else data.year - 1
    return '%s-09' % ano_servico, '%s-08' % (ano_servico + 1)


def primeiro_dia_mes(mes, padrao):
    try:
        return datetime.datetime.strptime(mes + '-01', '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return datetime.datetime.strptime(padrao + '-01', '%Y-%m-%d').date()


@login_required
@permission_required('activities.add_relatorios')
def add_relatorios(request):
    if request.GET and 'publicador' in request.GET and request.GET['publicador']:
        publicador = Publicadores.objects.get(id=request.GET['publicador'])
        if publicador.tipo == 2:
            CHOICES = [[publicador.tipo, publicador.get_tipo_display()]]
        else:
            pioneiro = Pioneiros.objects.filter(publicador=publicador, mes=request.GET['mes'] + '-01')
            if pioneiro:
                CHOICES = [[1, 'Pioneiro Auxiliar']]
            else:
                CHOICES = [[0, 'Publicador']]
        json_string = json.dumps(CHOICES)
        return HttpResponse(json_string)
    if request.POST:
        request_post = request.POST.copy()
        # Testar se tem relatório lançado.
        relatorio = Relatorios.objects.filter(
            publicador_id=request_post['publicador'],
            mes=request_post['mes'] + '-01',
        )
        if relatorio:
            relatorio.update(
                horas=0 if not 'horas' in request_post else request_post['horas'],
                estudos=request_post['estudos'],
                observacao=request_post['observacao'],
                tipo=3 if not 'presente' in request_post else request_post['tipo'],
                atv_local=True if 'atv_local' in request_post and request_post['atv_local'] == 'on' else False,
                assign_user_id=request.user.id,
            )
            messages.success(request, 'Registro já existia e foi atualizado com sucesso.')
        else:
            new_item = {
                'publicador_id': request_post['publicador'],
                'mes': request_post['mes'] + '-01',
                'publicacoes': 0,
                'videos': 0,
                'horas': 0 if not 'horas' in request_post else request_post['horas'],
                'revisitas': 0,
                'estudos': request_post['estudos'],
                'observacao': request_post['observacao'],
                'tipo': 3 if not 'presente' in request_post else request_post['tipo'],
                'atv_local': True if 'atv_local' in request_post and request_post['atv_local'] == 'on' else False,
                'create_user_id': request.user.id,
                'assign_user_id': request.user.id,
            }
            Relatorios.objects.create(**new_item)
            messages.success(request, 'Registro adicionado com sucesso.')
        return redirect('/activities/relatorios/add')
    form = AddRelatoriosForm()
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            form.fields['publicador'].queryset = Publicadores.objects.filter(cong_id=crc_user.first().cong_id, situacao=1).order_by('nome')
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    #form.fields['tipo'].disabled = True
    form.fields['mes'].initial = str(datetime.date.today().replace(day=1) - datetime.timedelta(days=1))[0:7]
    template = loader.get_template('relatorios/add.html')
    context = {
        'title': 'Digitar Relatório de Campo',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('activities.view_relatorios')
def list_relatorios(request):
    filter_search = {}
    form = FindRelatoriosForm()
    filter_fields = ['publicador', 'grupo', 'tipo', 'privilegio', 'mes_inicio', 'mes_fim']
    if any(key in request.GET for key in filter_fields):
        request_get = request.GET.copy()
        for field in filter_fields:
            form.fields[field].initial = request_get.get(field)
    else:
        form.fields['mes_inicio'].initial = str(datetime.date.today().replace(day=1) - datetime.timedelta(days=1))[0:7]
        form.fields['mes_fim'].initial = str(datetime.date.today().replace(day=1) - datetime.timedelta(days=1))[0:7]
        filter_search['mes__gte'] = (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        filter_search['mes__lte'] = (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
    form.fields['publicador'].required = False
    form.fields['grupo'].required = False
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            filter_search['publicador__cong_id'] = crc_user.first().cong_id
            form.fields['grupo'].queryset = Grupos.objects.filter(cong_id=crc_user.first().cong_id).order_by('grupo')
            form.fields['publicador'].queryset = Publicadores.objects.filter(cong_id=crc_user.first().cong_id).order_by('nome')
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    for key, value in request.GET.items():
        if key in ['publicador', 'tipo'] and value:
            filter_search[key] = value
        elif key in ['grupo', 'privilegio'] and value:
            filter_search['publicador__%s' % key] = value
        elif key in ['mes_inicio'] and value:
            filter_search['mes__gte'] = value + '-01'
        elif key in ['mes_fim'] and value:
            filter_search['mes__lte'] = value + '-01'
    list_relatorios = Relatorios.objects.filter(**filter_search).select_related('publicador')
    if request.GET.get('export') == 'csv':
        return sheet_relatorios(list_relatorios)
    spreadsheet_query = request.GET.copy()
    spreadsheet_query['export'] = 'csv'
    template = loader.get_template('relatorios/list.html')
    context = {
        'title': 'Relatórios de Campo',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'list_relatorios': list_relatorios,
        'form': form,
        'spreadsheet_url': '?%s' % spreadsheet_query.urlencode(),
    }
    return HttpResponse(template.render(context, request))


def sheet_relatorios(list_relatorios):
    io_report = StringIO()
    writerio = csv.writer(io_report, delimiter=';')
    writerio.writerow(['Publicador', 'Mês', 'Horas', 'Estudos', 'Observação', 'Tipo', 'Atividade local?'])
    for relatorio in list_relatorios:
        writerio.writerow([
            relatorio.publicador,
            relatorio.mes.strftime('%m-%Y'),
            relatorio.horas,
            relatorio.estudos,
            '' if not relatorio.observacao else relatorio.observacao,
            relatorio.get_tipo_display(),
            'Sim' if relatorio.atv_local else 'Não',
        ])
    response = HttpResponse(io_report.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=relatorios.csv'
    return response


@login_required
@permission_required('activities.view_relatorios')
def list_resumo(request):
    filter_search = {'atv_local': True}
    form = FindResumoForm()
    if request.GET:
        request_get = request.GET.copy()
        form.fields['mes_inicio'].initial = request_get['mes_inicio']
        form.fields['mes_fim'].initial = request_get['mes_fim']
        form.fields['grupo'].initial = request_get['grupo']
        if not 'somente_ativos' in request_get:
            form.fields['somente_ativos'].initial = False
    else:
        form.fields['mes_inicio'].initial = str(datetime.date.today().replace(day=1) - datetime.timedelta(days=1))[0:7]
        form.fields['mes_fim'].initial = str(datetime.date.today().replace(day=1) - datetime.timedelta(days=1))[0:7]
        filter_search['mes__gte'] = (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        filter_search['mes__lte'] = (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            filter_search['publicador__cong_id'] = crc_user.first().cong_id
            form.fields['grupo'].queryset = Grupos.objects.filter(cong_id=crc_user.first().cong_id).order_by('grupo')
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    for key, value in request.GET.items():
        if key in ['publicador', 'grupo'] and value:
            filter_search['publicador__%s' % key] = value
        elif key in ['mes_inicio'] and value:
            filter_search['mes__gte'] = value + '-01'
        elif key in ['mes_fim'] and value:
            filter_search['mes__lte'] = value + '-01'
        if key in ['somente_ativos'] and value:
            filter_search['publicador__situacao'] = 1
    list_relatorios = Relatorios.objects.filter(**filter_search)
    list_resumo = []
    if list_relatorios:
        list_relatorios = Relatorios.objects.filter(**filter_search).values('mes', 'tipo').annotate(membros=Count('id'), horas=Sum('horas'), estudos=Sum('estudos')).order_by('-mes', 'tipo')
        tipos = {x[0]: x[1] for x in TIPO}
        ultimo_mes = list_relatorios[0]['mes']
        soma = {'membros': 0, 'horas': 0, 'estudos': 0}
        for i in list_relatorios:
            new_item = i.copy()
            if new_item['mes'] != ultimo_mes:
                list_resumo.append({'mes': ultimo_mes, 'tipo': 'TOTAL', 'membros': soma['membros'], 'horas': soma['horas'], 'estudos': soma['estudos']})
                soma = {'membros': 0, 'horas': 0, 'estudos': 0}
                ultimo_mes = new_item['mes']
            new_item['tipo'] = tipos[new_item['tipo']]
            soma['membros'] += i['membros']
            soma['horas'] += i['horas']
            soma['estudos'] += i['estudos']
            list_resumo.append(new_item)
        list_resumo.append({'mes': ultimo_mes, 'tipo': 'TOTAL', 'membros': soma['membros'], 'horas': soma['horas'], 'estudos': soma['estudos']})
        ultimo_mes = new_item['mes']
    template = loader.get_template('resumo/list.html')
    context = {
        'title': 'Relatórios de Campo - Resumo',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'list_resumo': list_resumo,
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('activities.view_relatorios')
def resumo_pioneiros_regulares(request):
    mes_inicio_padrao, mes_fim_padrao = periodo_ano_servico()
    mes_inicio = request.GET.get('mes_inicio') or mes_inicio_padrao
    mes_fim = request.GET.get('mes_fim') or mes_fim_padrao
    inicio = primeiro_dia_mes(mes_inicio, mes_inicio_padrao)
    fim = primeiro_dia_mes(mes_fim, mes_fim_padrao)

    form = FindResumoPioneirosRegularesForm(initial={
        'congregacao': request.GET.get('congregacao'),
        'grupo': request.GET.get('grupo'),
        'publicador': request.GET.get('publicador'),
        'mes_inicio': mes_inicio,
        'mes_fim': mes_fim,
    })
    filter_search = {'tipo': 2, 'situacao': 1}
    if request.user.is_staff:
        if request.GET.get('congregacao'):
            filter_search['cong_id'] = request.GET['congregacao']
            form.fields['grupo'].queryset = Grupos.objects.filter(cong_id=request.GET['congregacao']).order_by('grupo')
    else:
        crc_user = CongUser.objects.filter(user=request.user).first()
        if not crc_user:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
        filter_search['cong_id'] = crc_user.cong_id
        form.fields['grupo'].queryset = Grupos.objects.filter(cong_id=crc_user.cong_id).order_by('grupo')

    if request.GET.get('grupo'):
        filter_search['grupo_id'] = request.GET['grupo']
    if request.GET.get('publicador'):
        filter_search['nome__icontains'] = request.GET['publicador']

    list_pioneiros = Publicadores.objects.filter(**filter_search).select_related('grupo', 'cong').annotate(
        total_horas=Coalesce(
            Sum('relatorios__horas', filter=Q(relatorios__mes__gte=inicio, relatorios__mes__lte=fim)),
            Value(0),
            output_field=IntegerField(),
        )
    ).order_by('nome')
    template = loader.get_template('resumo_pioneiros_regulares/list.html')
    context = {
        'title': 'Resumo de Pioneiros Regulares',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'list_pioneiros': list_pioneiros,
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('activities.view_relatorios')
def generate_cartoes(request, publicadores_id):
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            publicadores = Publicadores.objects.get(id=publicadores_id, cong_id=crc_user.first().cong_id)
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    else:
        publicadores = Publicadores.objects.get(id=publicadores_id)
    meses_intervalo = datetime.date(2024, 5, 1), datetime.date(2024, 5, 1)
    arquivo = BytesIO()
    resp = imprime_cartao(arquivo, meses_intervalo, publicadores_id)
    messages.success(request, 'Cartão gerado com sucesso.')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Cartão-%s.pdf"' % publicadores.nome
    pdf = arquivo.getvalue()
    arquivo.close()
    response.write(pdf)
    return response




@login_required
@permission_required('activities.view_relatorios')
def list_cartoes(request):
    form = FindCartoesForm()
    form.fields['publicador'].required = False
    form.fields['grupo'].required = False
    filter_search = {}
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            filter_search['cong_id'] = crc_user.first().cong_id
            form.fields['grupo'].queryset = Grupos.objects.filter(cong_id=crc_user.first().cong_id).order_by('grupo')
            form.fields['publicador'].queryset = Publicadores.objects.filter(cong_id=crc_user.first().cong_id).order_by('nome')
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    if request.GET:
        request_get = request.GET.copy()
        form.fields['mes_inicio'].initial = request_get['mes_inicio']
        form.fields['mes_fim'].initial = request_get['mes_fim']
        form.fields['grupo'].initial = request_get['grupo']
        form.fields['publicador'].initial = request_get['publicador']
        hoje = datetime.date.today()
        ano_servico = hoje.year if hoje.month >= 9 else hoje.year - 1
        meses_intervalo = [datetime.date(ano_servico, 9, 1), (hoje.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)]
        somente_resumo = False
        publicador_id = None
        grupo_id = None
        if 'somente_resumo' in request.GET and request.GET['somente_resumo']:
            somente_resumo = True
        if 'publicador' in request.GET and request.GET['publicador']:
            publicador_id = request.GET['publicador']
        if 'grupo' in request.GET and request.GET['grupo']:
            grupo_id = request.GET['grupo']
        if 'mes_inicio' in request.GET and request.GET['mes_inicio']:
            meses_intervalo[0] = datetime.datetime.strptime(request.GET['mes_inicio'] + '-01', '%Y-%m-%d')
        if 'mes_fim' in request.GET and request.GET['mes_fim']:
            meses_intervalo[1] = datetime.datetime.strptime(request.GET['mes_fim'] + '-01', '%Y-%m-%d')
        arquivo = BytesIO()
        if somente_resumo:
            filter_search = {
                'mes__gte': meses_intervalo[0],
                'mes__lte': meses_intervalo[1],
                'publicador__situacao': 1,
                'atv_local': True,
                'tipo__in': [0, 1, 2]
            }
            crc_user = CongUser.objects.filter(user=request.user)
            if crc_user:
                filter_search['publicador__cong_id'] = crc_user.first().cong_id
            else:
                messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
                return redirect('/')
            if grupo_id: filter_search['publicador__grupo_id'] = grupo_id
            resp = imprime_cartao_resumo(arquivo, meses_intervalo, filter_search)
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="Cartão-Resumo.pdf"'
            pdf = arquivo.getvalue()
            arquivo.close()
            response.write(pdf)
            return response
        elif publicador_id:
            publicadores = Publicadores.objects.get(id=publicador_id)
            resp = imprime_cartao(arquivo, meses_intervalo, publicador_id)
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="Cartão-%s.pdf"' % publicadores.nome
            pdf = arquivo.getvalue()
            arquivo.close()
            response.write(pdf)
            return response
        elif grupo_id:
            grupos = Grupos.objects.get(pk=grupo_id)
            publicadores = Publicadores.objects.filter(grupo_id=grupo_id, situacao=1).order_by('nome')
            file_list = []
            for pub in publicadores:
                filename = 'Cartão-%s.pdf' % pub.nome
                try:
                    resp = imprime_cartao(filename, meses_intervalo, pub.id)
                    file_list.append(filename)
                except:
                    pass
            zip_pub = ZipFile(arquivo, mode='w', compression=ZIP_DEFLATED, allowZip64=True)
            #zip_pub = ZipFile(grupos.grupo + '.zip', mode='w')
            for i in file_list:
                try:
                    zip_pub.write(i)
                    os.remove(i)
                except:
                    pass
            zip_name = grupos.grupo + '.zip'
            zip_pub.close()
            return_response = HttpResponse(content_type='application/force-download')
            return_response['Content-Disposition'] = 'attachment; filename="%s"' % zip_name
            pub_arq = arquivo.getvalue()
            return_response.write(pub_arq)
            arquivo.close()
            return return_response
        else:
            messages.error(request, 'Selecione um publicador ou um grupo de serviço.')
    list_cartoes = Publicadores.objects.filter(**filter_search)
    template = loader.get_template('cartoes/list.html')
    context = {
        'title': 'Registro de Publicador de Congregação',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'list_cartoes': list_cartoes,
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('activities.view_relatorios')
def relatorios_pendentes(request):
    filter_search = {'situacao': 1}
    form = FindResumoForm()
    if request.GET:
        request_get = request.GET.copy()
        form.fields['grupo'].initial = request_get['grupo']
    else:
        pass
    crc_user = None
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            filter_search['cong_id'] = crc_user.first().cong_id
            form.fields['grupo'].queryset = Grupos.objects.filter(cong_id=crc_user.first().cong_id).order_by('grupo')
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    for key, value in request.GET.items():
        if key in ['grupo'] and value:
            filter_search[key] = value
    filter_relatorios = {'mes': (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).replace(day=1)}
    if crc_user: filter_relatorios['publicador__cong_id'] = crc_user.first().cong_id
    relatorios = Relatorios.objects.filter(**filter_relatorios)
    relatorios_entregues = [x.publicador_id for x in relatorios]
    list_publicadores = Publicadores.objects.filter(**filter_search).exclude(id__in=relatorios_entregues)
    template = loader.get_template('pendentes/list.html')
    context = {
        'title': 'Relatórios de Campo - Pendentes de entregar',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'list_publicadores': list_publicadores,
        'form': form,
        'mes': datetime.datetime.strftime((datetime.date.today().replace(day=1) - datetime.timedelta(days=1)), '%m/%Y')
    }
    return HttpResponse(template.render(context, request))
