import json
import datetime

from register.models import Cong, CongUser, Drive, Grupos, Publicadores, Pioneiros, TIPO
from .forms import AddRelatoriosForm, FindRelatoriosForm
from .models import Relatorios

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
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