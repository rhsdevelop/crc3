import json
import datetime

from register.models import Cong, CongUser, Drive, Grupos, Publicadores, Pioneiros, TIPO
from .forms import AddRelatoriosForm, FindRelatoriosForm, FindResumoForm
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
        CHOICES = [[publicador.tipo, publicador.get_tipo_display()]]
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
    form = FindRelatoriosForm(request.GET)
    form.fields['publicador'].required = False
    form.fields['grupo'].required = False
    filter_search = {}
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
        if key in ['publicador', 'grupo'] and value:
            filter_search['%s__icontains' % key] = value
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
    form = FindResumoForm(request.GET)
    filter_search = {}
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
    list_relatorios = Relatorios.objects.filter(**filter_search)
    list_resumo = []
    if list_relatorios:
        list_relatorios = Relatorios.objects.filter(**filter_search).values('mes', 'tipo').annotate(membros=Count('id'), horas=Sum('horas'), estudos=Sum('estudos'))
        tipos = {x[0]: x[1] for x in TIPO}
        for i in list_relatorios:
            new_item = i.copy()
            new_item['tipo'] = tipos[new_item['tipo']]
            list_resumo.append(new_item)
    template = loader.get_template('resumo/list.html')
    context = {
        'title': 'Relatórios de Campo - Resumo',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'list_resumo': list_resumo,
        'form': form,
    }
    return HttpResponse(template.render(context, request))