import datetime
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template import loader
from django.urls import reverse
from django.views.decorators.http import require_POST

from register.models import Cong, CongUser, Grupos, Publicadores

from .forms import (
    CarrinhoTestemunhoPublicoForm,
    ConfiguracaoTestemunhoPublicoForm,
    DesignacaoTestemunhoPublicoForm,
    HabilitacaoTestemunhoPublicoForm,
    LocalTestemunhoPublicoForm,
    PeriodoTestemunhoPublicoForm,
    VisitaGrupoForm,
    VisitaPastoreioForm,
    limites_ano_servico,
)
from .models import (
    CarrinhoTestemunhoPublico,
    ConfiguracaoTestemunhoPublico,
    DesignacaoTestemunhoPublico,
    HabilitacaoTestemunhoPublico,
    LocalTestemunhoPublico,
    PeriodoTestemunhoPublico,
    VisitaGrupo,
    VisitaPastoreio,
)


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
def confirm_visita_pastoreio(request, visita_id, pastoreio_id):
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
        if not pastoreio.confirmado:
            pastoreio.confirmado = True
            pastoreio.assign_user = request.user
            pastoreio.save()
            messages.success(
                request,
                'Visita de pastoreio confirmada com sucesso.',
            )
        else:
            messages.info(
                request,
                'A visita de pastoreio já estava confirmada.',
            )

    return redirect(
        reverse(
            'ss_activities:list_visitas_pastoreio',
            args=[visita.id],
        )
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


PERMISSAO_TESTEMUNHO_PUBLICO = 'ss_activities.manage_testemunho_publico'


def semana_testemunho_publico(request):
    valor = request.POST.get('semana') or request.GET.get('semana')
    try:
        data = datetime.date.fromisoformat(valor) if valor else datetime.date.today()
    except (TypeError, ValueError):
        data = datetime.date.today()
    return data - datetime.timedelta(days=data.weekday())


def url_testemunho_publico(nome_rota, semana, cong=None):
    parametros = {'semana': semana.isoformat()}
    if cong:
        parametros['cong'] = cong.id
    return '%s?%s' % (
        reverse('ss_activities:%s' % nome_rota),
        urlencode(parametros),
    )


def get_objeto_testemunho_publico(request, model, objeto_id, for_update=False):
    cong = get_congregacao_usuario(request)
    if cong is False:
        return False, None
    if not cong:
        raise Http404
    queryset = model.objects.all()
    if for_update:
        queryset = queryset.select_for_update()
    return get_object_or_404(queryset, pk=objeto_id, cong=cong), cong


def contexto_painel_testemunho_publico(
    request,
    semana,
    cong,
    form=None,
    modal_open=False,
    modal_mode='add',
    designacao=None,
):
    fim_semana = semana + datetime.timedelta(days=6)
    dias = [
        {
            'data': semana + datetime.timedelta(days=indice),
            'nome': nome,
        }
        for indice, nome in enumerate([
            'Segunda-feira',
            'Terça-feira',
            'Quarta-feira',
            'Quinta-feira',
            'Sexta-feira',
            'Sábado',
            'Domingo',
        ])
    ]
    designacoes = DesignacaoTestemunhoPublico.objects.none()
    periodos = PeriodoTestemunhoPublico.objects.none()
    configuracao = None
    carrinhos_ativos = 0
    if cong:
        designacoes = DesignacaoTestemunhoPublico.objects.filter(
            cong=cong,
            data__range=(semana, fim_semana),
        ).select_related(
            'periodo',
            'local',
            'carrinho__cong__configuracao_testemunho_publico',
            'publicador_1',
            'publicador_2',
        )
        periodos = PeriodoTestemunhoPublico.objects.filter(cong=cong).filter(
            Q(ativo=True)
            | Q(designacoes__data__range=(semana, fim_semana))
        ).distinct()
        configuracao = ConfiguracaoTestemunhoPublico.objects.filter(
            cong=cong,
        ).first()
        carrinhos_ativos = CarrinhoTestemunhoPublico.objects.filter(
            cong=cong,
            ativo=True,
        ).count()

    designacoes_por_periodo = {}
    for item in designacoes:
        designacoes_por_periodo.setdefault(
            (item.periodo_id, item.data),
            [],
        ).append(item)

    periodos_por_linha = {}
    for periodo in periodos:
        chave = (periodo.horario, periodo.descricao)
        periodos_por_linha.setdefault(chave, {})[periodo.dia_semana] = periodo

    linhas = []
    for (horario, descricao), periodos_dia in sorted(
        periodos_por_linha.items(),
        key=lambda item: (item[0][0], item[0][1]),
    ):
        celulas = []
        for indice, dia in enumerate(dias):
            periodo = periodos_dia.get(indice)
            celulas.append({
                'data': dia['data'],
                'periodo': periodo,
                'designacoes': (
                    designacoes_por_periodo.get((periodo.id, dia['data']), [])
                    if periodo
                    else []
                ),
                'pode_adicionar': bool(
                    periodo and periodo.ativo and carrinhos_ativos
                ),
            })
        linhas.append({
            'rotulo': '%s %s' % (descricao, horario.strftime('%H:%M')),
            'celulas': celulas,
        })

    if form is None:
        form = DesignacaoTestemunhoPublicoForm(cong=cong)
    return {
        'title': 'Testemunho Público',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'selected_cong': cong,
        'list_cong': (
            Cong.objects.all().order_by('nome')
            if request.user.is_superuser
            else None
        ),
        'semana': semana,
        'fim_semana': fim_semana,
        'semana_anterior_url': url_testemunho_publico(
            'painel_testemunho_publico',
            semana - datetime.timedelta(days=7),
            cong,
        ),
        'semana_atual_url': url_testemunho_publico(
            'painel_testemunho_publico',
            datetime.date.today()
            - datetime.timedelta(days=datetime.date.today().weekday()),
            cong,
        ),
        'proxima_semana_url': url_testemunho_publico(
            'painel_testemunho_publico',
            semana + datetime.timedelta(days=7),
            cong,
        ),
        'dias': dias,
        'linhas': linhas,
        'designacoes': designacoes,
        'configuracao': configuracao,
        'carrinhos_ativos': carrinhos_ativos,
        'form': form,
        'modal_open': modal_open,
        'modal_mode': modal_mode,
        'designacao_edicao': designacao,
    }


def render_painel_testemunho_publico(request, semana, cong, **kwargs):
    template = loader.get_template('testemunho_publico/painel.html')
    context = contexto_painel_testemunho_publico(
        request,
        semana,
        cong,
        **kwargs,
    )
    return HttpResponse(template.render(context, request))


@login_required
@permission_required(PERMISSAO_TESTEMUNHO_PUBLICO, raise_exception=True)
def painel_testemunho_publico(request):
    semana = semana_testemunho_publico(request)
    cong = get_congregacao_usuario(request)
    if cong is False:
        return redirect('/')
    return render_painel_testemunho_publico(request, semana, cong)


def salvar_designacao_testemunho_publico(request, designacao=None):
    semana = semana_testemunho_publico(request)
    cong = get_congregacao_usuario(request)
    if cong is False:
        return redirect('/')
    if not cong:
        raise Http404
    form = DesignacaoTestemunhoPublicoForm(
        request.POST,
        instance=designacao,
        cong=cong,
    )
    if form.is_valid():
        item = form.save(commit=False)
        if not item.pk:
            item.create_user = request.user
        item.assign_user = request.user
        try:
            with transaction.atomic():
                list(
                    HabilitacaoTestemunhoPublico.objects.select_for_update()
                    .filter(
                        cong=cong,
                        publicador_id__in=[
                            item.publicador_1_id,
                            item.publicador_2_id,
                        ],
                    )
                    .values_list('id', flat=True)
                )
                CarrinhoTestemunhoPublico.objects.select_for_update().get(
                    pk=item.carrinho_id,
                    cong=cong,
                )
                LocalTestemunhoPublico.objects.select_for_update().get(
                    pk=item.local_id,
                    cong=cong,
                )
                item.save()
        except (IntegrityError, ValidationError):
            form.add_error(
                None,
                'A designação conflita com outra programação. Atualize os dados e tente novamente.',
            )
        else:
            messages.success(request, 'Designação salva com sucesso.')
            return redirect(
                url_testemunho_publico(
                    'painel_testemunho_publico',
                    semana,
                    cong,
                )
            )
    return render_painel_testemunho_publico(
        request,
        semana,
        cong,
        form=form,
        modal_open=True,
        modal_mode='edit' if designacao else 'add',
        designacao=designacao,
    )


@login_required
@permission_required(PERMISSAO_TESTEMUNHO_PUBLICO, raise_exception=True)
@require_POST
def add_designacao_testemunho_publico(request):
    return salvar_designacao_testemunho_publico(request)


@login_required
@permission_required(PERMISSAO_TESTEMUNHO_PUBLICO, raise_exception=True)
@require_POST
def edit_designacao_testemunho_publico(request, designacao_id):
    designacao, cong = get_objeto_testemunho_publico(
        request,
        DesignacaoTestemunhoPublico,
        designacao_id,
    )
    if designacao is False:
        return redirect('/')
    return salvar_designacao_testemunho_publico(request, designacao)


@login_required
@permission_required(PERMISSAO_TESTEMUNHO_PUBLICO, raise_exception=True)
@require_POST
def delete_designacao_testemunho_publico(request, designacao_id):
    semana = semana_testemunho_publico(request)
    with transaction.atomic():
        designacao, cong = get_objeto_testemunho_publico(
            request,
            DesignacaoTestemunhoPublico,
            designacao_id,
            for_update=True,
        )
        if designacao is False:
            return redirect('/')
        designacao.delete()
    messages.success(request, 'Designação apagada com sucesso.')
    return redirect(
        url_testemunho_publico('painel_testemunho_publico', semana, cong)
    )


@login_required
@permission_required(PERMISSAO_TESTEMUNHO_PUBLICO, raise_exception=True)
def disponibilidade_testemunho_publico(request):
    cong = get_congregacao_usuario(request)
    if cong is False:
        return JsonResponse({'detail': 'Usuário sem congregação.'}, status=400)
    if not cong:
        raise Http404
    try:
        data = datetime.date.fromisoformat(request.GET.get('data', ''))
        periodo = PeriodoTestemunhoPublico.objects.get(
            pk=request.GET.get('periodo'),
            cong=cong,
            ativo=True,
        )
    except (TypeError, ValueError, PeriodoTestemunhoPublico.DoesNotExist):
        return JsonResponse({'detail': 'Data ou período inválido.'}, status=400)
    if data.weekday() != periodo.dia_semana:
        return JsonResponse(
            {'detail': 'A data não corresponde ao período.'},
            status=400,
        )
    ocupadas = DesignacaoTestemunhoPublico.objects.filter(
        cong=cong,
        data=data,
        periodo=periodo,
    )
    designacao_id = request.GET.get('designacao')
    if designacao_id:
        designacao = get_object_or_404(
            DesignacaoTestemunhoPublico,
            pk=designacao_id,
            cong=cong,
        )
        ocupadas = ocupadas.exclude(pk=designacao.pk)
    publicadores_ocupados = set(
        ocupadas.values_list('publicador_1_id', flat=True)
    ) | set(ocupadas.values_list('publicador_2_id', flat=True))
    publicadores = Publicadores.objects.filter(
        cong=cong,
        situacao=1,
        habilitacoes_testemunho_publico__cong=cong,
        habilitacoes_testemunho_publico__aprovado=True,
    ).exclude(pk__in=publicadores_ocupados).distinct()
    carrinhos = CarrinhoTestemunhoPublico.objects.filter(
        cong=cong,
        ativo=True,
    ).exclude(pk__in=ocupadas.values('carrinho_id'))
    locais = LocalTestemunhoPublico.objects.filter(
        cong=cong,
        ativo=True,
    ).exclude(pk__in=ocupadas.values('local_id'))
    return JsonResponse({
        'publicadores': list(publicadores.values_list('id', flat=True)),
        'carrinhos': list(carrinhos.values_list('id', flat=True)),
        'locais': list(locais.values_list('id', flat=True)),
    })


CADASTROS_TESTEMUNHO_PUBLICO = {
    'habilitados': {
        'model': HabilitacaoTestemunhoPublico,
        'form': HabilitacaoTestemunhoPublicoForm,
        'title': 'Publicadores habilitados',
    },
    'periodos': {
        'model': PeriodoTestemunhoPublico,
        'form': PeriodoTestemunhoPublicoForm,
        'title': 'Horários do testemunho público',
    },
    'locais': {
        'model': LocalTestemunhoPublico,
        'form': LocalTestemunhoPublicoForm,
        'title': 'Locais do testemunho público',
    },
}


def contexto_cadastro_testemunho_publico(
    request,
    tipo,
    semana,
    cong,
    form=None,
    modal_open=False,
    item=None,
):
    definicao = CADASTROS_TESTEMUNHO_PUBLICO[tipo]
    itens = definicao['model'].objects.none()
    if cong:
        itens = definicao['model'].objects.filter(cong=cong)
        if tipo == 'habilitados':
            itens = itens.select_related('publicador')
    if form is None:
        form = definicao['form'](cong=cong)
    return {
        'title': definicao['title'],
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'tipo': tipo,
        'itens': itens,
        'form': form,
        'modal_open': modal_open,
        'item_edicao': item,
        'selected_cong': cong,
        'list_cong': (
            Cong.objects.all().order_by('nome')
            if request.user.is_superuser
            else None
        ),
        'semana': semana,
        'back_url': url_testemunho_publico(
            'painel_testemunho_publico',
            semana,
            cong,
        ),
    }


def render_cadastro_testemunho_publico(request, tipo, semana, cong, **kwargs):
    template = loader.get_template('testemunho_publico/cadastro.html')
    context = contexto_cadastro_testemunho_publico(
        request,
        tipo,
        semana,
        cong,
        **kwargs,
    )
    return HttpResponse(template.render(context, request))


def listar_cadastro_testemunho_publico(request, tipo):
    semana = semana_testemunho_publico(request)
    cong = get_congregacao_usuario(request)
    if cong is False:
        return redirect('/')
    return render_cadastro_testemunho_publico(request, tipo, semana, cong)


def salvar_cadastro_testemunho_publico(request, tipo, item=None):
    semana = semana_testemunho_publico(request)
    cong = get_congregacao_usuario(request)
    if cong is False:
        return redirect('/')
    if not cong:
        raise Http404
    definicao = CADASTROS_TESTEMUNHO_PUBLICO[tipo]
    form = definicao['form'](
        request.POST,
        instance=item,
        cong=cong,
    )
    if form.is_valid():
        objeto = form.save(commit=False)
        if not objeto.pk:
            objeto.create_user = request.user
        objeto.assign_user = request.user
        try:
            with transaction.atomic():
                objeto.save()
        except (IntegrityError, ValidationError):
            form.add_error(None, 'Já existe um cadastro com esses dados.')
        else:
            messages.success(request, 'Cadastro salvo com sucesso.')
            return redirect(
                url_testemunho_publico(
                    'list_%s_testemunho_publico' % tipo,
                    semana,
                    cong,
                )
            )
    return render_cadastro_testemunho_publico(
        request,
        tipo,
        semana,
        cong,
        form=form,
        modal_open=True,
        item=item,
    )


@login_required
@permission_required(PERMISSAO_TESTEMUNHO_PUBLICO, raise_exception=True)
def list_habilitados_testemunho_publico(request):
    return listar_cadastro_testemunho_publico(request, 'habilitados')


@login_required
@permission_required(PERMISSAO_TESTEMUNHO_PUBLICO, raise_exception=True)
@require_POST
def add_habilitado_testemunho_publico(request):
    return salvar_cadastro_testemunho_publico(request, 'habilitados')


@login_required
@permission_required(PERMISSAO_TESTEMUNHO_PUBLICO, raise_exception=True)
@require_POST
def edit_habilitado_testemunho_publico(request, item_id):
    item, cong = get_objeto_testemunho_publico(
        request,
        HabilitacaoTestemunhoPublico,
        item_id,
    )
    if item is False:
        return redirect('/')
    return salvar_cadastro_testemunho_publico(request, 'habilitados', item)


@login_required
@permission_required(PERMISSAO_TESTEMUNHO_PUBLICO, raise_exception=True)
def list_periodos_testemunho_publico(request):
    return listar_cadastro_testemunho_publico(request, 'periodos')


@login_required
@permission_required(PERMISSAO_TESTEMUNHO_PUBLICO, raise_exception=True)
@require_POST
def add_periodo_testemunho_publico(request):
    return salvar_cadastro_testemunho_publico(request, 'periodos')


@login_required
@permission_required(PERMISSAO_TESTEMUNHO_PUBLICO, raise_exception=True)
@require_POST
def edit_periodo_testemunho_publico(request, item_id):
    item, cong = get_objeto_testemunho_publico(
        request,
        PeriodoTestemunhoPublico,
        item_id,
    )
    if item is False:
        return redirect('/')
    return salvar_cadastro_testemunho_publico(request, 'periodos', item)


@login_required
@permission_required(PERMISSAO_TESTEMUNHO_PUBLICO, raise_exception=True)
def list_locais_testemunho_publico(request):
    return listar_cadastro_testemunho_publico(request, 'locais')


@login_required
@permission_required(PERMISSAO_TESTEMUNHO_PUBLICO, raise_exception=True)
@require_POST
def add_local_testemunho_publico(request):
    return salvar_cadastro_testemunho_publico(request, 'locais')


@login_required
@permission_required(PERMISSAO_TESTEMUNHO_PUBLICO, raise_exception=True)
@require_POST
def edit_local_testemunho_publico(request, item_id):
    item, cong = get_objeto_testemunho_publico(
        request,
        LocalTestemunhoPublico,
        item_id,
    )
    if item is False:
        return redirect('/')
    return salvar_cadastro_testemunho_publico(request, 'locais', item)


def contexto_carrinhos_testemunho_publico(
    request,
    semana,
    cong,
    configuracao_form=None,
    carrinho_form=None,
    modal_open=False,
    carrinho=None,
):
    configuracao = None
    carrinhos = CarrinhoTestemunhoPublico.objects.none()
    if cong:
        configuracao = ConfiguracaoTestemunhoPublico.objects.filter(
            cong=cong,
        ).first()
        carrinhos = CarrinhoTestemunhoPublico.objects.filter(
            cong=cong,
        ).select_related('cong__configuracao_testemunho_publico')
    if configuracao_form is None:
        configuracao_form = ConfiguracaoTestemunhoPublicoForm(
            instance=configuracao,
            cong=cong,
        )
    if carrinho_form is None:
        carrinho_form = CarrinhoTestemunhoPublicoForm(
            instance=carrinho,
            cong=cong,
        )
    return {
        'title': 'Carrinhos do testemunho público',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'selected_cong': cong,
        'list_cong': (
            Cong.objects.all().order_by('nome')
            if request.user.is_superuser
            else None
        ),
        'semana': semana,
        'configuracao': configuracao,
        'configuracao_form': configuracao_form,
        'carrinhos': carrinhos,
        'carrinho_form': carrinho_form,
        'modal_open': modal_open,
        'carrinho_edicao': carrinho,
        'back_url': url_testemunho_publico(
            'painel_testemunho_publico',
            semana,
            cong,
        ),
    }


def render_carrinhos_testemunho_publico(request, semana, cong, **kwargs):
    template = loader.get_template('testemunho_publico/carrinhos.html')
    context = contexto_carrinhos_testemunho_publico(
        request,
        semana,
        cong,
        **kwargs,
    )
    return HttpResponse(template.render(context, request))


@login_required
@permission_required(PERMISSAO_TESTEMUNHO_PUBLICO, raise_exception=True)
def list_carrinhos_testemunho_publico(request):
    semana = semana_testemunho_publico(request)
    cong = get_congregacao_usuario(request)
    if cong is False:
        return redirect('/')
    return render_carrinhos_testemunho_publico(request, semana, cong)


@login_required
@permission_required(PERMISSAO_TESTEMUNHO_PUBLICO, raise_exception=True)
@require_POST
def save_configuracao_testemunho_publico(request):
    semana = semana_testemunho_publico(request)
    cong = get_congregacao_usuario(request)
    if cong is False:
        return redirect('/')
    if not cong:
        raise Http404
    configuracao = ConfiguracaoTestemunhoPublico.objects.filter(cong=cong).first()
    form = ConfiguracaoTestemunhoPublicoForm(
        request.POST,
        instance=configuracao,
        cong=cong,
    )
    if form.is_valid():
        item = form.save(commit=False)
        if not item.pk:
            item.create_user = request.user
        item.assign_user = request.user
        try:
            with transaction.atomic():
                Cong.objects.select_for_update().get(pk=cong.pk)
                item.save()
        except (IntegrityError, ValidationError) as erro:
            mensagem = getattr(erro, 'message_dict', {}).get(
                'quantidade_carrinhos',
                ['Não foi possível atualizar a configuração.'],
            )[0]
            form.add_error('quantidade_carrinhos', mensagem)
        else:
            messages.success(request, 'Configuração de carrinhos salva com sucesso.')
            return redirect(
                url_testemunho_publico(
                    'list_carrinhos_testemunho_publico',
                    semana,
                    cong,
                )
            )
    return render_carrinhos_testemunho_publico(
        request,
        semana,
        cong,
        configuracao_form=form,
    )


@login_required
@permission_required(PERMISSAO_TESTEMUNHO_PUBLICO, raise_exception=True)
@require_POST
def edit_carrinho_testemunho_publico(request, carrinho_id):
    semana = semana_testemunho_publico(request)
    carrinho, cong = get_objeto_testemunho_publico(
        request,
        CarrinhoTestemunhoPublico,
        carrinho_id,
    )
    if carrinho is False:
        return redirect('/')
    form = CarrinhoTestemunhoPublicoForm(
        request.POST,
        instance=carrinho,
        cong=cong,
    )
    if form.is_valid():
        item = form.save(commit=False)
        item.assign_user = request.user
        try:
            with transaction.atomic():
                item.save()
        except (IntegrityError, ValidationError):
            form.add_error(
                'nome_personalizado',
                'Já existe um carrinho com esse nome.',
            )
        else:
            messages.success(request, 'Identificação do carrinho salva com sucesso.')
            return redirect(
                url_testemunho_publico(
                    'list_carrinhos_testemunho_publico',
                    semana,
                    cong,
                )
            )
    return render_carrinhos_testemunho_publico(
        request,
        semana,
        cong,
        carrinho_form=form,
        modal_open=True,
        carrinho=carrinho,
    )
