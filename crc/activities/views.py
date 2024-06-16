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
    if request.POST:
        form = AddRelatoriosForm(request.POST)
        item = form.save(commit=False)
        item.create_user = request.user
        item.assign_user = request.user
        item.save()
        messages.success(request, 'Registro adicionado com sucesso.')
        return redirect('/relatorios/list')
    form = AddRelatoriosForm()
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
            filter_search['id'] = crc_user.first().cong_id
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