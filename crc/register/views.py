from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.template import loader

from .forms import (AddCongForm, FindCongForm, AddGruposForm, FindGruposForm,
                    AddCongUserForm, FindCongUserForm,
                    AddPublicadoresForm, FindPublicadoresForm, AddPioneirosForm,
                    FindPioneirosForm)
from .models import Cong, CongUser, Drive, Grupos, Publicadores, Reunioes, Relatorios, Pioneiros, Faltas

# Create your views here.


@login_required
def index(request):
    template = loader.get_template('index.html')
    context = {
        'title': 'CRC - Controle de Registros de Congregação - V.3.0',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('register.add_cong')
def add_cong(request):
    if request.POST:
        form = AddCongForm(request.POST)
        item = form.save(commit=False)
        item.create_user = request.user
        item.assign_user = request.user
        item.save()
        messages.success(request, 'Registro adicionado com sucesso.')
        return redirect('/cong/list')
    form = AddCongForm()
    template = loader.get_template('cong/add.html')
    context = {
        'title': 'Adicionar Nova Congregação',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('register.change_cong')
def edit_cong(request, cong_id):
    cong = Cong.objects.get(id=cong_id)
    if request.POST:
        form = AddCongForm(request.POST, instance=cong)
        item = form.save(commit=False)
        item.assign_user = request.user
        item.save()
        messages.success(request, 'Registro alterado com sucesso.')
        return redirect('/cong/list')
    form = AddCongForm(instance=cong)
    template = loader.get_template('cong/edit.html')
    context = {
        'title': 'Dados da Congregação Selecionada',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('register.view_cong')
def list_cong(request):
    form = FindCongForm(request.GET)
    form.fields['nome'].required = False
    form.fields['numero'].required = False
    filter_search = {}
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            filter_search['id'] = crc_user.first().cong_id
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    for key, value in request.GET.items():
        if key in ['nome', 'numero'] and value:
            filter_search['%s__icontains' % key] = value
    list_cong = Cong.objects.filter(**filter_search)
    template = loader.get_template('cong/list.html')
    context = {
        'title': 'Relação de Congregações Cadastradas',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'list_cong': list_cong,
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('register.add_conguser')
def add_conguser(request):
    if request.POST:
        form = AddCongUserForm(request.POST)
        item = form.save(commit=False)
        item.create_user = request.user
        item.assign_user = request.user
        item.save()
        messages.success(request, 'Registro adicionado com sucesso.')
        return redirect('/conguser/list')
    form = AddCongUserForm()
    template = loader.get_template('conguser/add.html')
    context = {
        'title': 'Relacionar Usuário e Congregação',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('register.change_conguser')
def edit_conguser(request, conguser_id):
    conguser = CongUser.objects.get(id=conguser_id)
    if request.POST:
        form = AddCongUserForm(request.POST, instance=conguser)
        item = form.save(commit=False)
        item.assign_user = request.user
        item.save()
        messages.success(request, 'Registro alterado com sucesso.')
        return redirect('/conguser/list')
    form = AddCongUserForm(instance=conguser)
    template = loader.get_template('conguser/edit.html')
    context = {
        'title': 'Dados da Usuário Selecionado',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('register.view_conguser')
def list_conguser(request):
    form = FindCongUserForm(request.GET)
    form.fields['cong'].required = False
    form.fields['user'].required = False
    filter_search = {}
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            filter_search['cong_id'] = crc_user.first().cong_id
            print(filter_search['cong_id'])
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    for key, value in request.GET.items():
        if key in ['cong', 'user'] and value:
            filter_search['%s__icontains' % key] = value
    list_conguser = CongUser.objects.filter(**filter_search)
    template = loader.get_template('conguser/list.html')
    context = {
        'title': 'Relação de Usuários Cadastrados',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'list_conguser': list_conguser,
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('register.add_grupos')
def add_grupos(request):
    if request.POST:
        form = AddGruposForm(request.POST)
        item = form.save(commit=False)
        item.create_user = request.user
        item.assign_user = request.user
        item.save()
        messages.success(request, 'Registro adicionado com sucesso.')
        return redirect('/grupos/list')
    form = AddGruposForm()
    template = loader.get_template('grupos/add.html')
    context = {
        'title': 'Adicionar Novo Grupo de Serviço',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('register.change_grupos')
def edit_grupos(request, grupos_id):
    grupos = Grupos.objects.get(id=grupos_id)
    if request.POST:
        form = AddGruposForm(request.POST, instance=grupos)
        item = form.save(commit=False)
        item.assign_user = request.user
        item.save()
        messages.success(request, 'Registro alterado com sucesso.')
        return redirect('/grupos/list')
    form = AddGruposForm(instance=grupos)
    template = loader.get_template('grupos/edit.html')
    context = {
        'title': 'Dados do Grupo de Serviço Selecionado',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('register.view_grupos')
def list_grupos(request):
    form = FindGruposForm(request.GET)
    form.fields['grupo'].required = False
    form.fields['dirigente'].required = False
    form.fields['ajudante'].required = False
    filter_search = {}
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            filter_search['cong_id'] = crc_user.first().cong_id
            print(filter_search['cong_id'])
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    for key, value in request.GET.items():
        if key in ['grupo', 'dirigente', 'ajudante'] and value:
            filter_search['%s__icontains' % key] = value
    list_grupos = Grupos.objects.filter(**filter_search)
    template = loader.get_template('grupos/list.html')
    context = {
        'title': 'Relação dos Grupos de Serviço',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'list_grupos': list_grupos,
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('register.add_publicadores')
def add_publicadores(request):
    if request.POST:
        form = AddPublicadoresForm(request.POST)
        item = form.save(commit=False)
        item.create_user = request.user
        item.assign_user = request.user
        item.save()
        messages.success(request, 'Registro adicionado com sucesso.')
        return redirect('/publicadores/list')
    form = AddPublicadoresForm()
    template = loader.get_template('publicadores/add.html')
    context = {
        'title': 'Adicionar Novo Publicador',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('register.change_publicadores')
def edit_publicadores(request, publicadores_id):
    publicadores = Publicadores.objects.get(id=publicadores_id)
    if request.POST:
        form = AddPublicadoresForm(request.POST, instance=publicadores)
        item = form.save(commit=False)
        item.assign_user = request.user
        item.save()
        messages.success(request, 'Registro alterado com sucesso.')
        return redirect('/publicadores/list')
    form = AddPublicadoresForm(instance=publicadores)
    template = loader.get_template('publicadores/edit.html')
    context = {
        'title': 'Dados de Publicador Selecionado',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('register.view_publicadores')
def list_publicadores(request):
    form = FindPublicadoresForm(request.GET)
    form.fields['nome'].required = False
    form.fields['endereco'].required = False
    form.fields['esperanca'].required = False
    form.fields['privilegio'].required = False
    form.fields['tipo'].required = False
    form.fields['situacao'].required = False
    filter_search = {}
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            filter_search['cong_id'] = crc_user.first().cong_id
            print(filter_search['cong_id'])
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    for key, value in request.GET.items():
        if key in ['nome', 'numero'] and value:
            filter_search['%s__icontains' % key] = value
    list_publicadores = Publicadores.objects.filter(**filter_search)
    template = loader.get_template('publicadores/list.html')
    context = {
        'title': 'Relação de Publicadores',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'list_publicadores': list_publicadores,
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('register.add_pioneiros')
def add_pioneiros(request):
    if request.POST:
        form = AddPioneirosForm(request.POST)
        item = form.save(commit=False)
        item.create_user = request.user
        item.assign_user = request.user
        item.save()
        messages.success(request, 'Registro adicionado com sucesso.')
        return redirect('/pioneiros/list')
    form = AddPioneirosForm()
    template = loader.get_template('pioneiros/add.html')
    context = {
        'title': 'Adicionar Novo Publicador',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('register.change_pioneiros')
def edit_pioneiros(request, pioneiros_id):
    pioneiros = Pioneiros.objects.get(id=pioneiros_id)
    if request.POST:
        form = AddPioneirosForm(request.POST, instance=pioneiros)
        item = form.save(commit=False)
        item.assign_user = request.user
        item.save()
        messages.success(request, 'Registro alterado com sucesso.')
        return redirect('/pioneiros/list')
    form = AddPioneirosForm(instance=pioneiros)
    template = loader.get_template('pioneiros/edit.html')
    context = {
        'title': 'Dados de Publicador Selecionado',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('register.view_pioneiros')
def list_pioneiros(request):
    form = FindPioneirosForm(request.GET)
    form.fields['publicador'].required = False
    form.fields['mes'].required = False
    filter_search = {}
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            filter_search['publicador__cong_id'] = crc_user.first().cong_id
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    for key, value in request.GET.items():
        if key in ['publicador', 'mes'] and value:
            filter_search['%s__icontains' % key] = value
    list_pioneiros = Pioneiros.objects.filter(**filter_search)
    template = loader.get_template('pioneiros/list.html')
    context = {
        'title': 'Relação de Pioneiros',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'list_pioneiros': list_pioneiros,
        'form': form,
    }
    return HttpResponse(template.render(context, request))
