import csv
import datetime
from io import StringIO

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.template import loader

from .forms import (AddCongForm, FindCongForm, AddGruposForm, FindGruposForm,
                    AddCongUserForm, FindCongUserForm,
                    AddPublicadoresForm, FindPublicadoresForm, AddPioneirosForm,
                    FindPioneirosForm, AddProfileForm)
from .models import Cong, CongUser, Drive, Grupos, Publicadores, Pioneiros
from .schedule import atualiza_pioneiros

# Create your views here.


@login_required
def index(request):
    # Atualiza pioneiros
    if datetime.datetime.now().hour in [8, 12, 16, 20]:
        atualiza_pioneiros()
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
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            if cong_id == crc_user.first().cong_id:
                cong = Cong.objects.get(id=cong_id)
            else:
                raise Http404('Congregação indisponível!')
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    else:
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
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            conguser = CongUser.objects.get(id=conguser_id, cong_id=crc_user.first().cong_id)
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    else:
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
        if not request.user.is_staff:
            form.fields['cong'].widget = forms.HiddenInput()
        item = form.save(commit=False)
        item.create_user = request.user
        item.assign_user = request.user
        if not request.user.is_staff:
            crc_user = CongUser.objects.filter(user=request.user)
            if crc_user:
                item.cong_id = crc_user.first().cong_id
            else:
                messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
                return redirect('/')
        item.save()
        messages.success(request, 'Registro adicionado com sucesso.')
        return redirect('/grupos/list')
    form = AddGruposForm()
    if not request.user.is_staff:
        form.fields['cong'].widget = forms.HiddenInput()
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
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            grupos = Grupos.objects.get(id=grupos_id, cong_id=crc_user.first().cong_id)
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    else:
        grupos = Grupos.objects.get(id=grupos_id)
    if request.POST:
        form = AddGruposForm(request.POST, instance=grupos)
        if not request.user.is_staff:
            form.fields['cong'].widget = forms.HiddenInput()
        item = form.save(commit=False)
        item.assign_user = request.user
        item.save()
        messages.success(request, 'Registro alterado com sucesso.')
        return redirect('/grupos/list')
    form = AddGruposForm(instance=grupos)
    if not request.user.is_staff:
        form.fields['cong'].widget = forms.HiddenInput()
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
        if not request.user.is_staff:
            form.fields['cong'].widget = forms.HiddenInput()
        item = form.save(commit=False)
        item.create_user = request.user
        item.assign_user = request.user
        if not request.user.is_staff:
            crc_user = CongUser.objects.filter(user=request.user)
            if crc_user:
                item.cong_id = crc_user.first().cong_id
            else:
                messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
                return redirect('/')
        item.save()
        messages.success(request, 'Registro adicionado com sucesso.')
        return redirect('/publicadores/list')
    form = AddPublicadoresForm()
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            form.fields['cong'].widget = forms.HiddenInput()
            form.fields['grupo'].queryset = Grupos.objects.filter(cong_id=crc_user.first().cong_id).order_by('grupo')
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
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
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            publicadores = Publicadores.objects.get(id=publicadores_id, cong_id=crc_user.first().cong_id)
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    else:
        publicadores = Publicadores.objects.get(id=publicadores_id)
    if request.POST:
        form = AddPublicadoresForm(request.POST, instance=publicadores)
        if not request.user.is_staff:
            form.fields['cong'].widget = forms.HiddenInput()
        item = form.save(commit=False)
        item.assign_user = request.user
        item.save()
        messages.success(request, 'Registro alterado com sucesso.')
        return redirect('/publicadores/list')
    publicadores.nascimento = str(publicadores.nascimento)
    publicadores.batismo = str(publicadores.batismo)
    publicadores.data_classe = str(publicadores.data_classe)
    publicadores.data_visita = str(publicadores.data_visita)
    form = AddPublicadoresForm(instance=publicadores)
    if not request.user.is_staff:
        form.fields['cong'].widget = forms.HiddenInput()
        form.fields['grupo'].queryset = Grupos.objects.filter(cong_id=crc_user.first().cong_id).order_by('grupo')
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
    filter_search = {}
    if request.GET:
        form = FindPublicadoresForm(request.GET)
    else:
        form = FindPublicadoresForm()
        form.fields['situacao'].initial = 1
        filter_search['situacao'] = 1
    form.fields['nome'].required = False
    form.fields['endereco'].required = False
    form.fields['esperanca'].required = False
    form.fields['privilegio'].required = False
    form.fields['tipo'].required = False
    form.fields['situacao'].required = False
    form.fields['grupo'].required = False
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            filter_search['cong_id'] = crc_user.first().cong_id
            form.fields['grupo'].queryset = Grupos.objects.filter(cong_id=crc_user.first().cong_id).order_by('grupo')
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    for key, value in request.GET.items():
        if key in ['nome', 'endereco'] and value:
            filter_search['%s__icontains' % key] = value
        elif key in ['esperanca', 'privilegio', 'tipo', 'situacao', 'grupo'] and value:
            filter_search[key] = value
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
        request_post = request.POST.copy()
        new_item = {
            'publicador_id': request_post['publicador'],
            'mes': request_post['mes'] + '-01',
            'observacao': request_post['observacao'],
            'create_user_id': request.user.id,
            'assign_user_id': request.user.id,
        }
        Pioneiros.objects.create(**new_item)
        messages.success(request, 'Registro adicionado com sucesso.')
        messages.warning(request, 'Se você já digitou o relatório do publicador, favor atualize os dados.')
        return redirect('/pioneiros/list')
    form = AddPioneirosForm()
    form.fields['mes'].initial = str(datetime.date.today().replace(day=1))[0:7]
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            form.fields['publicador'].queryset = Publicadores.objects.filter(cong_id=crc_user.first().cong_id, situacao=1).order_by('nome')
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    template = loader.get_template('pioneiros/add.html')
    context = {
        'title': 'Incluir Petição de Pioneiro Auxiliar',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('register.view_publicadores')
def sheet_publicadores(request):
    filter_search = {'situacao': 1}
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            filter_search['cong_id'] = crc_user.first().cong_id
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    list_publicadores = Publicadores.objects.filter(**filter_search)
    fieldnames = ['nome', 'endereco', 'telefone_fixo', 'telefone_celular', 'nascimento', 'idade', 'batismo', 'tempo_batismo', 'esperanca', 'privilegio', 'tipo', 'sexo', 'observacao', 'situacao', 'grupo']
    data = []
    for i in list_publicadores:
        new_pub = {
            'nome': i.nome,
            'endereco': i.endereco,
            'telefone_fixo': '' if not i.telefone_fixo else i.telefone_fixo,
            'telefone_celular': '' if not i.telefone_celular else i.telefone_celular,
            'nascimento': '' if not i.nascimento else i.nascimento.strftime('%d/%m/%Y'),
            'idade': '0' if not i.nascimento else datetime.date.today().year - i.nascimento.year,
            'batismo': ''if not i.batismo else i.batismo,
            'tempo_batismo': '0' if not i.batismo else datetime.date.today().year - i.batismo.year,
            'esperanca': i.get_esperanca_display(),
            'privilegio': i.get_privilegio_display(),
            'tipo': i.get_tipo_display(),
            'sexo': i.get_sexo_display(),
            'observacao': '' if not i.observacao else i.observacao,
            'situacao': i.get_situacao_display(),
            'grupo': '' if not i.grupo else i.grupo.grupo,
        }
        data.append(new_pub)
    io_report = StringIO()
    writerio = csv.DictWriter(io_report, fieldnames=fieldnames, delimiter=';')
    writerio.writeheader()
    writerio.writerows(data)
    response = HttpResponse(io_report.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=publicadores.csv'
    messages.success(request, 'Relatório gerado com sucesso.')
    return response


@login_required
@permission_required('register.delete_pioneiros')
def delete_pioneiros(request, pioneiros_id):
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            pioneiros = Pioneiros.objects.get(id=pioneiros_id, publicador__cong_id=crc_user.first().cong_id)
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    else:
        pioneiros = Pioneiros.objects.get(id=pioneiros_id)
    pioneiros.delete()
    messages.success(request, 'Registro removido com sucesso.')
    return redirect('/pioneiros/list/')


@login_required
@permission_required('register.view_pioneiros')
def list_pioneiros(request):
    filter_search = {}
    form = FindPioneirosForm()
    if request.GET:
        request_get = request.GET.copy()
        form.fields['mes'].initial = request_get['mes']
        form.fields['publicador'].initial = request_get['publicador']
    else:
        form.fields['mes'].initial = str(datetime.date.today().replace(day=1))[0:7]
        filter_search['mes'] = datetime.date.today().replace(day=1)
    form.fields['publicador'].required = False
    form.fields['mes'].required = False
    if not request.user.is_staff:
        crc_user = CongUser.objects.filter(user=request.user)
        if crc_user:
            filter_search['publicador__cong_id'] = crc_user.first().cong_id
            form.fields['publicador'].queryset = Publicadores.objects.filter(cong_id=crc_user.first().cong_id, situacao=1).order_by('nome')
        else:
            messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
            return redirect('/')
    for key, value in request.GET.items():
        if key in ['publicador'] and value:
            filter_search[key] = value
        elif key in ['mes'] and value:
            filter_search[key] = value + '-01'
    list_pioneiros = Pioneiros.objects.filter(**filter_search)
    template = loader.get_template('pioneiros/list.html')
    context = {
        'title': 'Relação de Pioneiros',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'list_pioneiros': list_pioneiros,
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def edit_profile(request):
    if request.POST:
        if request.POST['senha'] != request.POST['senha_repete']:
            messages.error(request, 'As senhas digitadas são diferentes. Por favor digite a senha e repita para confirmar a alteração.')
        else:
            user = User.objects.get(pk=request.user.id)
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.email = request.POST['email']
            user.set_password(request.POST['senha'])
            user.save()
            messages.success(request, 'Dados editados com sucesso.')
            return redirect('/')
    form = AddProfileForm()
    form.fields['first_name'].initial = request.user.first_name
    form.fields['last_name'].initial = request.user.last_name
    form.fields['email'].initial = request.user.email
    
    template = loader.get_template('profile/edit.html')
    context = {
        'title': 'Dados pessoais do usuário',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'form': form,
    }
    return HttpResponse(template.render(context, request))
