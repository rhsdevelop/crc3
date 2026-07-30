import datetime
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template import loader
from django.urls import reverse
from django.views.decorators.http import require_POST

from register.models import Cong, CongUser, Grupos

from .forms import VisitaGrupoForm, VisitaPastoreioForm, limites_ano_servico
from .models import VisitaGrupo, VisitaPastoreio


def ano_servico_atual(data=None):
    data = data or datetime.date.today()
    return data.year if data.month >= 9 else data.year - 1


def get_ano_servico(request):
    valor = request.POST.get('ano') or request.GET.get('ano')
    try:
        return int(valor) if valor else ano_servico_atual()
    except (TypeError, ValueError):
        return ano_servico_atual()


def get_congregacao_usuario(request):
    if request.user.is_superuser:
        cong_id = request.POST.get('cong') or request.GET.get('cong')
        if not cong_id:
            return None
        return get_object_or_404(Cong, pk=cong_id)

    crc_user = CongUser.objects.filter(user=request.user).select_related('cong').first()
    if not crc_user:
        messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
        return False
    return crc_user.cong


def url_listagem(ano, cong=None):
    parametros = {'ano': ano}
    if cong:
        parametros['cong'] = cong.id
    return '/ss/visitas-grupos/?%s' % urlencode(parametros)


def contexto_listagem(
    request,
    ano,
    cong,
    form=None,
    modal_open=False,
    modal_mode='add',
    visita=None,
):
    inicio, fim = limites_ano_servico(ano)
    visitas = VisitaGrupo.objects.none()
    grupos = Grupos.objects.none()
    if cong:
        visitas = VisitaGrupo.objects.filter(
            cong=cong,
            data_inicio__gte=inicio,
            data_inicio__lte=fim,
        ).select_related('grupo', 'cong').annotate(
            total_visitas_pastoreio=Count('visitas_pastoreio'),
        )
        grupos = Grupos.objects.filter(cong=cong).order_by('grupo')

    grupos_programados = visitas.values_list('grupo_id', flat=True)
    grupos_sem_visita = grupos.exclude(id__in=grupos_programados)
    if form is None:
        form = VisitaGrupoForm(cong=cong, ano_inicio=ano)

    ano_atual = ano_servico_atual()
    anos = sorted(set(range(ano_atual - 2, ano_atual + 4)) | {ano})
    return {
        'title': 'Visitas aos Grupos',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'visitas': visitas,
        'grupos': grupos,
        'grupos_sem_visita': grupos_sem_visita,
        'total_grupos': grupos.count(),
        'total_programados': grupos.exclude(id__in=grupos_sem_visita).count(),
        'total_confirmados': visitas.filter(confirmada=True).values('grupo_id').distinct().count(),
        'total_executados': visitas.filter(executada=True).values('grupo_id').distinct().count(),
        'form': form,
        'ano': ano,
        'anos': anos,
        'periodo_inicio': inicio,
        'periodo_fim': fim,
        'selected_cong': cong,
        'list_cong': Cong.objects.all().order_by('nome') if request.user.is_superuser else None,
        'modal_open': modal_open,
        'modal_mode': modal_mode,
        'visita_edicao': visita,
    }


def render_listagem(request, ano, cong, **kwargs):
    template = loader.get_template('visitas_grupos/list.html')
    context = contexto_listagem(request, ano, cong, **kwargs)
    return HttpResponse(template.render(context, request))


def get_visita_grupo_acessivel(request, visita_id, for_update=False):
    visitas = VisitaGrupo.objects.select_related('grupo', 'cong')
    if for_update:
        visitas = visitas.select_for_update()
    if request.user.is_superuser:
        return get_object_or_404(visitas, pk=visita_id)

    cong = get_congregacao_usuario(request)
    if cong is False:
        return False
    return get_object_or_404(visitas, pk=visita_id, cong=cong)


def ano_da_visita(visita):
    return (
        visita.data_inicio.year
        if visita.data_inicio.month >= 9
        else visita.data_inicio.year - 1
    )


def contexto_visitas_pastoreio(
    request,
    visita,
    form=None,
    modal_open=False,
):
    pastoreios = VisitaPastoreio.objects.filter(
        visita_grupo=visita,
    ).select_related('publicador', 'acompanhante')
    if form is None:
        form = VisitaPastoreioForm(visita_grupo=visita)
    return {
        'title': 'Visitas de Pastoreio',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'visita_grupo': visita,
        'pastoreios': pastoreios,
        'form': form,
        'modal_open': modal_open,
        'back_url': url_listagem(ano_da_visita(visita), visita.cong),
    }


def render_visitas_pastoreio(request, visita, **kwargs):
    template = loader.get_template('visitas_pastoreio/list.html')
    context = contexto_visitas_pastoreio(request, visita, **kwargs)
    return HttpResponse(template.render(context, request))


@login_required
@permission_required('ss_activities.manage_visitas_grupos', raise_exception=True)
def list_visitas_grupos(request):
    ano = get_ano_servico(request)
    cong = get_congregacao_usuario(request)
    if cong is False:
        return redirect('/')
    return render_listagem(request, ano, cong)


@login_required
@permission_required('ss_activities.manage_visitas_grupos', raise_exception=True)
def list_visitas_pastoreio(request, visita_id):
    visita = get_visita_grupo_acessivel(request, visita_id)
    if visita is False:
        return redirect('/')
    return render_visitas_pastoreio(request, visita)


@login_required
@permission_required('ss_activities.manage_visitas_grupos', raise_exception=True)
@require_POST
def add_visita_pastoreio(request, visita_id):
    visita = get_visita_grupo_acessivel(request, visita_id)
    if visita is False:
        return redirect('/')

    form = VisitaPastoreioForm(request.POST, visita_grupo=visita)
    if form.is_valid():
        item = form.save(commit=False)
        item.create_user = request.user
        item.assign_user = request.user
        try:
            with transaction.atomic():
                item.save()
        except IntegrityError:
            form.add_error(
                'publicador',
                'Este publicador já possui uma visita de pastoreio nessa semana.',
            )
        else:
            messages.success(request, 'Visita de pastoreio adicionada com sucesso.')
            return redirect(
                reverse(
                    'ss_activities:list_visitas_pastoreio',
                    args=[visita.id],
                )
            )

    return render_visitas_pastoreio(
        request,
        visita,
        form=form,
        modal_open=True,
    )


@login_required
@permission_required('ss_activities.manage_visitas_grupos', raise_exception=True)
@require_POST
def delete_visita_pastoreio(request, visita_id, pastoreio_id):
    with transaction.atomic():
        visita = get_visita_grupo_acessivel(
            request,
            visita_id,
            for_update=True,
        )
        if visita is False:
            return redirect('/')
        pastoreio = get_object_or_404(
            VisitaPastoreio.objects.select_for_update(),
            pk=pastoreio_id,
            visita_grupo=visita,
        )
        pastoreio.delete()

    messages.success(request, 'Visita de pastoreio apagada com sucesso.')
    return redirect(
        reverse(
            'ss_activities:list_visitas_pastoreio',
            args=[visita.id],
        )
    )


@login_required
@permission_required('ss_activities.manage_visitas_grupos', raise_exception=True)
@require_POST
def add_visita_grupo(request):
    ano = get_ano_servico(request)
    cong = get_congregacao_usuario(request)
    if cong is False:
        return redirect('/')
    if not cong:
        messages.warning(request, 'Selecione uma congregação para programar a visita.')
        return redirect(url_listagem(ano))

    form = VisitaGrupoForm(request.POST, cong=cong, ano_inicio=ano)
    if form.is_valid():
        item = form.save(commit=False)
        item.create_user = request.user
        item.assign_user = request.user
        try:
            with transaction.atomic():
                item.save()
        except IntegrityError:
            form.add_error(
                'data_inicio',
                'Já existe uma visita programada para esta congregação nessa semana.',
            )
        else:
            messages.success(request, 'Visita programada com sucesso.')
            return redirect(url_listagem(ano, cong))

    return render_listagem(
        request,
        ano,
        cong,
        form=form,
        modal_open=True,
        modal_mode='add',
    )


@login_required
@permission_required('ss_activities.manage_visitas_grupos', raise_exception=True)
@require_POST
def edit_visita_grupo(request, visita_id):
    ano = get_ano_servico(request)
    cong = get_congregacao_usuario(request)
    if cong is False:
        return redirect('/')
    if request.user.is_superuser:
        visita = get_object_or_404(VisitaGrupo, pk=visita_id)
        cong = visita.cong
    elif cong:
        visita = get_object_or_404(VisitaGrupo, pk=visita_id, cong=cong)
    else:
        raise Http404

    form = VisitaGrupoForm(
        request.POST,
        instance=visita,
        cong=cong,
        ano_inicio=ano,
    )
    if form.is_valid():
        item = form.save(commit=False)
        item.assign_user = request.user
        try:
            with transaction.atomic():
                item.save()
        except IntegrityError:
            form.add_error(
                'data_inicio',
                'Já existe uma visita programada para esta congregação nessa semana.',
            )
        else:
            messages.success(request, 'Visita alterada com sucesso.')
            return redirect(url_listagem(ano, cong))

    return render_listagem(
        request,
        ano,
        cong,
        form=form,
        modal_open=True,
        modal_mode='edit',
        visita=visita,
    )


@login_required
@permission_required('ss_activities.manage_visitas_grupos', raise_exception=True)
@require_POST
def delete_visita_grupo(request, visita_id):
    ano = get_ano_servico(request)
    cong = get_congregacao_usuario(request)
    if cong is False:
        return redirect('/')

    with transaction.atomic():
        visitas = VisitaGrupo.objects.select_for_update()
        if request.user.is_superuser:
            visita = get_object_or_404(visitas, pk=visita_id)
            cong = visita.cong
        elif cong:
            visita = get_object_or_404(visitas, pk=visita_id, cong=cong)
        else:
            raise Http404

        if visita.visitas_pastoreio.exists():
            messages.warning(
                request,
                'Apague as visitas de pastoreio antes de apagar a visita ao grupo.',
            )
        elif visita.confirmada:
            messages.warning(request, 'Uma visita confirmada não pode ser apagada.')
        else:
            visita.delete()
            messages.success(request, 'Visita apagada com sucesso.')

    return redirect(url_listagem(ano, cong))
