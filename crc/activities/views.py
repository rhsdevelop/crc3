import datetime
import json
import os
from io import BytesIO, StringIO
from zipfile import ZipFile

from register.models import Cong, CongUser, Drive, Grupos, Publicadores, Pioneiros, TIPO
from .forms import AddRelatoriosForm, FindRelatoriosForm, FindResumoForm, FindCartoesForm
from .helpers import imprime_cartao, imprime_cartao_resumo
from .models import Relatorios

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Avg, Case, Count, Sum, When
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.template import loader


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
                atv_local=True if request_post['atv_local'] == 'on' else False,
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
                'atv_local': True if request_post['atv_local'] == 'on' else False,
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
    if request.GET:
        request_get = request.GET.copy()
        form.fields['mes_inicio'].initial = request_get['mes_inicio']
        form.fields['mes_fim'].initial = request_get['mes_fim']
        form.fields['publicador'].initial = request_get['publicador']
        form.fields['grupo'].initial = request_get['grupo']
        form.fields['tipo'].initial = request_get['tipo']
        form.fields['privilegio'].initial = request_get['privilegio']
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
    list_relatorios = Relatorios.objects.filter(**filter_search)
    template = loader.get_template('relatorios/list.html')
    context = {
        'title': 'Relatórios de Campo',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'list_relatorios': list_relatorios,
        'form': form,
    }
    return HttpResponse(template.render(context, request))


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
        list_relatorios = Relatorios.objects.filter(**filter_search).values('mes', 'tipo').annotate(membros=Count('id'), horas=Sum('horas'), estudos=Sum('estudos')).order_by('tipo', 'mes')
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
                except:
                    pass
                file_list.append(filename)
            zip_pub = ZipFile(arquivo, mode='w')
            #zip_pub = ZipFile(grupos.grupo + '.zip', mode='w')
            for i in file_list:
                zip_pub.write(i)
                os.remove(i)
            zip_name = grupos.grupo + '.zip'
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
