import datetime
import json
import os
from calendar import monthrange
from io import BytesIO, StringIO
from zipfile import ZipFile

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Avg, Case, Count, Sum, When
from django.db.models.functions import TruncMonth
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.template import loader

from .forms import AddReunioesForm, FindReunioesForm
from .helpers import imprime_cartao_resumo
from .models import Reunioes, TIPO_REUNIAO
from register.models import CongUser


@login_required
@permission_required('meetings.add_reunioes')
def add_reunioes(request):
    if request.GET and 'data' in request.GET and request.GET['data']:
        try:
            date_initial = datetime.datetime.strptime(request.GET['data'], '%Y-%m-%d')
            if date_initial.weekday() in [5, 6]:
                CHOICES = '1'
            else:
                CHOICES = '0'
        except:
            CHOICES = '0'
        json_string = json.dumps(CHOICES)
        return HttpResponse(json_string)
    crc_user = None
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            #form.fields['publicador'].queryset = Publicadores.objects.filter(cong_id=crc_user.first().cong_id, situacao=1).order_by('nome')
            pass
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    if request.POST:
        request_post = request.POST.copy()
        # Testar se tem relatório lançado.
        if crc_user:
            cong_id = crc_user.first().cong_id
        else:
            cong_id = request_post['cong_id']
        reunioes = Reunioes.objects.filter(
            data=request_post['data'],
            cong_id=cong_id
        )
        if reunioes:
            reunioes.update(
                tipo = request_post['tipo'],
                assistencia = request_post['assistencia'],
                observacao = request_post['observacao'],
                assign_user_id=request.user.id,
            )
            messages.success(request, 'Registro já existia e foi atualizado com sucesso.')
        else:
            new_item = {
                'data': request_post['data'],
                'tipo': request_post['tipo'],
                'assistencia': request_post['assistencia'],
                'observacao': request_post['observacao'],
                'cong_id': cong_id,
                'create_user_id': request.user.id,
                'assign_user_id': request.user.id,
            }
            Reunioes.objects.create(**new_item)
            messages.success(request, 'Registro adicionado com sucesso.')
        return redirect('/meetings/reunioes/add')
    form = AddReunioesForm()
    if not request.user.is_staff:
        form.fields['cong'].widget = forms.HiddenInput()
    #form.fields['tipo'].disabled = True
    date_initial = datetime.date.today() - datetime.timedelta(days=1)
    form.fields['data'].initial = str(date_initial)
    if date_initial.weekday() in [5, 6]:
        form.fields['tipo'].initial = 1
    else:
        form.fields['tipo'].initial = 0

    template = loader.get_template('reunioes/add.html')
    context = {
        'title': 'Digitar Assistência de Reunião',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('meetings.view_reunioes')
def list_reunioes(request):
    filter_search = {}
    form = FindReunioesForm()
    if request.GET:
        request_get = request.GET.copy()
        form.fields['mes_inicio'].initial = request_get['mes_inicio']
        form.fields['mes_fim'].initial = request_get['mes_fim']
        form.fields['tipo'].initial = request_get['tipo']
        form.fields['somente_resumo'].initial = False if not 'somente_resumo' in request_get else True
    else:
        form.fields['mes_inicio'].initial = str(datetime.date.today().replace(day=1))[0:7]
        form.fields['mes_fim'].initial = str(datetime.date.today().replace(day=1))[0:7]
        filter_search['data__gte'] = (datetime.date.today().replace(day=1))
        filter_search['data__lte'] = (datetime.date.today().replace(day=monthrange(datetime.date.today().year, datetime.date.today().month)[1]))
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            filter_search['cong_id'] = crc_user.first().cong_id
            #form.fields['grupo'].queryset = Grupos.objects.filter(cong_id=crc_user.first().cong_id).order_by('grupo')
            #form.fields['publicador'].queryset = Publicadores.objects.filter(cong_id=crc_user.first().cong_id).order_by('nome')
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    for key, value in request.GET.items():
        if key in ['tipo'] and value:
            filter_search[key] = value
        elif key in ['mes_inicio'] and value:
            filter_search['data__gte'] = value + '-01'
        elif key in ['mes_fim'] and value:
            filter_search['data__lte'] = value + '-' + str(monthrange(datetime.date.today().year, datetime.date.today().month)[1])
    list_reunioes = Reunioes.objects.filter(**filter_search).order_by('-data')
    resumo = False
    if 'somente_resumo' in request.GET and request.GET['somente_resumo']:
        data = list_reunioes.annotate(mes=TruncMonth('data')).values('mes', 'tipo').annotate(eventos=Count('id'), total=Sum('assistencia'), media=Avg('assistencia')).order_by('-mes', 'tipo')
        tr = {
            0: 'Meio de Semana',
            1: 'Fim de Semana',
            2: 'Outro Evento'
        }
        list_reunioes = []
        for item in data:
            new_item = item.copy()
            new_item['tipo'] = tr[new_item['tipo']]
            list_reunioes.append(new_item)
        resumo = True
    template = loader.get_template('reunioes/list.html')
    context = {
        'title': 'Assistência às Reuniões',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'resumo': resumo,
        'list_reunioes': list_reunioes,
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('meetings.view_reunioes')
def printcard_reunioes(request):
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            pass
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    hoje = datetime.date.today()
    ano_servico = hoje.year if hoje.month >= 9 else hoje.year - 1
    meses_intervalo = [datetime.date(ano_servico, 9, 1), (hoje.replace(day=1) - datetime.timedelta(days=1))]
    if 'mes_inicio' in request.GET and request.GET['mes_inicio']:
        meses_intervalo[0] = datetime.datetime.strptime(request.GET['mes_inicio'] + '-01', '%Y-%m-%d')
    if 'mes_fim' in request.GET and request.GET['mes_fim']:
        meses_intervalo[1] = datetime.datetime.strptime(request.GET['mes_fim'] + '-' + str(monthrange(datetime.date.today().year, datetime.date.today().month)[1]), '%Y-%m-%d')
    arquivo = BytesIO()
    resp = imprime_cartao_resumo(arquivo, meses_intervalo, crc_user.first().cong_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Cartão Reuniões.pdf"'
    pdf = arquivo.getvalue()
    arquivo.close()
    response.write(pdf)
    return response
