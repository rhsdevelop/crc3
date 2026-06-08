import datetime

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.template import loader

from register.models import Cong, CongUser

from .forms import FindTarefaSecretarioForm, TarefaSecretarioForm
from .models import TarefaSecretario
from .services import carregar_tarefas_base


def get_cong_usuario(request):
    if request.user.is_staff:
        return None
    crc_user = CongUser.objects.filter(user=request.user)
    if crc_user:
        return crc_user.first().cong
    messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
    return False


def get_tarefa_usuario(request, tarefa_id):
    try:
        if request.user.is_staff:
            return TarefaSecretario.objects.get(id=tarefa_id)
        cong = get_cong_usuario(request)
        if not cong:
            raise Http404
        return TarefaSecretario.objects.get(id=tarefa_id, cong=cong)
    except TarefaSecretario.DoesNotExist:
        raise Http404


def aplicar_cong_form(request, form):
    if not request.user.is_staff:
        form.fields['cong'].widget = forms.HiddenInput()
        form.fields['cong'].required = False


@login_required
@permission_required('agenda.view_tarefasecretario')
def list_tarefas_secretario(request):
    form = FindTarefaSecretarioForm(request.GET)
    filter_search = {}
    cong = get_cong_usuario(request)
    if cong is False:
        return redirect('/')
    if cong:
        filter_search['cong'] = cong

    for key, value in request.GET.items():
        if key in ['status', 'categoria', 'tipo_recorrencia', 'mes_referencia', 'ano_referencia'] and value:
            filter_search[key] = value

    list_tarefas = TarefaSecretario.objects.filter(**filter_search).select_related('cong')
    busca = request.GET.get('busca')
    if busca:
        list_tarefas = list_tarefas.filter(Q(titulo__icontains=busca) | Q(descricao__icontains=busca))

    ordenacao = request.GET.get('ordenacao')
    if ordenacao == 'prioridade':
        list_tarefas = list_tarefas.order_by('prioridade', 'data_limite')
    else:
        list_tarefas = list_tarefas.order_by('data_limite', 'prioridade')

    template = loader.get_template('tarefas_secretario/list.html')
    context = {
        'title': 'Gestão de Tarefas',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'list_tarefas': list_tarefas,
        'form': form,
        'list_cong': Cong.objects.all().order_by('nome') if request.user.is_staff else None,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('agenda.add_tarefasecretario')
def add_tarefa_secretario(request):
    cong = get_cong_usuario(request)
    if cong is False:
        return redirect('/')
    if request.POST:
        form = TarefaSecretarioForm(request.POST)
        aplicar_cong_form(request, form)
        if form.is_valid():
            item = form.save(commit=False)
            item.create_user = request.user
            item.assign_user = request.user
            if cong:
                item.cong = cong
            item.save()
            messages.success(request, 'Registro adicionado com sucesso.')
            return redirect('/agenda/tarefas/')
    else:
        form = TarefaSecretarioForm()
        aplicar_cong_form(request, form)
    template = loader.get_template('tarefas_secretario/add.html')
    context = {
        'title': 'Adicionar Tarefa',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('agenda.change_tarefasecretario')
def edit_tarefa_secretario(request, tarefa_id):
    tarefa = get_tarefa_usuario(request, tarefa_id)
    cong_original = tarefa.cong
    if request.POST:
        form = TarefaSecretarioForm(request.POST, instance=tarefa)
        aplicar_cong_form(request, form)
        if form.is_valid():
            item = form.save(commit=False)
            item.assign_user = request.user
            if not request.user.is_staff:
                item.cong = cong_original
            item.save()
            messages.success(request, 'Registro alterado com sucesso.')
            return redirect('/agenda/tarefas/')
    else:
        form = TarefaSecretarioForm(instance=tarefa)
        aplicar_cong_form(request, form)
    template = loader.get_template('tarefas_secretario/edit.html')
    context = {
        'title': 'Editar Tarefa',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'form': form,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('agenda.view_tarefasecretario')
def view_tarefa_secretario(request, tarefa_id):
    tarefa = get_tarefa_usuario(request, tarefa_id)
    template = loader.get_template('tarefas_secretario/view.html')
    context = {
        'title': 'Detalhe da Tarefa',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'tarefa': tarefa,
    }
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('agenda.change_tarefasecretario')
def concluir_tarefa_secretario(request, tarefa_id):
    if request.method != 'POST':
        raise Http404
    tarefa = get_tarefa_usuario(request, tarefa_id)
    tarefa.status = 'concluida'
    tarefa.data_conclusao = datetime.date.today()
    tarefa.assign_user = request.user
    tarefa.save()
    messages.success(request, 'Tarefa concluída com sucesso.')
    return redirect('/agenda/tarefas/')


@login_required
@permission_required('agenda.add_tarefasecretario')
def carregar_tarefas_base_secretario(request):
    if request.method != 'POST':
        raise Http404
    cong = get_cong_usuario(request)
    if cong is False:
        return redirect('/')
    if request.user.is_staff:
        cong_id = request.POST.get('cong')
        if cong_id:
            cong = Cong.objects.get(id=cong_id)
        else:
            messages.warning(request, 'Selecione uma congregação para carregar as tarefas-base.')
            return redirect('/agenda/tarefas/')
    criadas = carregar_tarefas_base(cong, request.user)
    messages.success(request, '%s tarefa(s)-base carregada(s).' % criadas)
    return redirect('/agenda/tarefas/')
