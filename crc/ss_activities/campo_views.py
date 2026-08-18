import datetime
import mimetypes
from functools import wraps
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from register.models import Cong, Publicadores

from .campo_forms import (
    ArranjoSaidaCampoForm,
    DirigenteCampoHabilitadoForm,
    LocalSaidaCampoForm,
    MapaTerritorioForm,
    MovimentoProgramacaoCampoForm,
    ProgramacaoCampoForm,
    TerritorioCampoForm,
)
from .campo_services import (
    gerar_programacao_semana,
    movimentar_programacao,
    normalizar_semana,
)
from .campo_pdf import gerar_pdf_programacao_campo
from .models import (
    ArranjoSaidaCampo,
    DirigenteCampoHabilitado,
    LocalSaidaCampo,
    MapaTerritorio,
    ProgramacaoCampo,
    TerritorioCampo,
)
from .views import get_congregacao_usuario


PERMISSAO_PROGRAMACAO = 'ss_activities.manage_programacao_campo'
PERMISSAO_TERRITORIOS = 'ss_activities.manage_territorios'


def _decorador_permissao(*permissoes):
    def decorar(view):
        @login_required
        @wraps(view)
        def executar(request, *args, **kwargs):
            if not any(request.user.has_perm(permissao) for permissao in permissoes):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return executar
    return decorar


acesso_campo = _decorador_permissao(PERMISSAO_PROGRAMACAO, PERMISSAO_TERRITORIOS)
acesso_programacao = _decorador_permissao(PERMISSAO_PROGRAMACAO)


def _congregacao(request, obrigatoria=True):
    cong = get_congregacao_usuario(request)
    if cong is False:
        return None
    if obrigatoria and not cong:
        raise Http404
    return cong


def _url(nome, semana=None, cong=None, **parametros):
    if semana:
        parametros['semana'] = semana.isoformat()
    if cong:
        parametros['cong'] = cong.id
    url = reverse('ss_activities:%s' % nome)
    return '%s?%s' % (url, urlencode(parametros)) if parametros else url


def _contexto_base(request, cong, title):
    return {
        'title': title,
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'selected_cong': cong,
        'list_cong': Cong.objects.all().order_by('nome') if request.user.is_superuser else None,
        'pode_programar': request.user.has_perm(PERMISSAO_PROGRAMACAO),
        'pode_territorios': request.user.has_perm(PERMISSAO_TERRITORIOS),
    }


def _contexto_painel(request, cong, semana, form=None, modal_open=False, programacao=None):
    fim = semana + datetime.timedelta(days=6)
    programas = ProgramacaoCampo.objects.none()
    if cong:
        programas = ProgramacaoCampo.objects.filter(
            cong=cong, data__range=(semana, fim)
        ).select_related(
            'arranjo', 'local', 'grupo', 'dirigente', 'territorio', 'mapa'
        )
    programas = list(programas)
    dias = []
    nomes = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    for indice, nome in enumerate(nomes):
        data = semana + datetime.timedelta(days=indice)
        dias.append({
            'nome': nome,
            'data': data,
            'programacoes': [item for item in programas if item.data == data],
        })
    if form is None:
        form = ProgramacaoCampoForm(
            cong=cong,
            somente_territorio=(
                request.user.has_perm(PERMISSAO_TERRITORIOS)
                and not request.user.has_perm(PERMISSAO_PROGRAMACAO)
            ),
        )
    contexto = _contexto_base(request, cong, 'Serviço de Campo')
    contexto.update({
        'semana': semana,
        'fim_semana': fim,
        'dias': dias,
        'total_programacoes': len(programas),
        'form': form,
        'modal_open': modal_open,
        'programacao_edicao': programacao,
        'semana_anterior_url': _url('painel_servico_campo', semana - datetime.timedelta(days=7), cong),
        'semana_atual_url': _url('painel_servico_campo', normalizar_semana(), cong),
        'proxima_semana_url': _url('painel_servico_campo', semana + datetime.timedelta(days=7), cong),
    })
    return contexto


@acesso_campo
@require_GET
def painel_servico_campo(request):
    semana = normalizar_semana(request.GET.get('semana'))
    cong = _congregacao(request, obrigatoria=False)
    return render(
        request,
        'servico_campo/painel.html',
        _contexto_painel(request, cong, semana),
    )


@acesso_programacao
@require_POST
def gerar_semana_servico_campo(request):
    semana = normalizar_semana(request.POST.get('semana'))
    cong = _congregacao(request)
    criadas = gerar_programacao_semana(cong, semana, request.user)
    if criadas:
        messages.success(request, '%s saída(s) adicionada(s) à semana.' % criadas)
    else:
        messages.info(request, 'A semana já contém todos os arranjos ativos.')
    return redirect(_url('painel_servico_campo', semana, cong))


@acesso_campo
@require_POST
def editar_programacao_campo(request, programacao_id):
    semana = normalizar_semana(request.POST.get('semana'))
    cong = _congregacao(request)
    item = get_object_or_404(ProgramacaoCampo, pk=programacao_id, cong=cong)
    if item.status not in {'A', 'P'}:
        messages.error(request, 'Somente programações em preparação ou programadas podem ser editadas.')
        return redirect(_url('painel_servico_campo', semana, cong))
    somente_territorio = (
        request.user.has_perm(PERMISSAO_TERRITORIOS)
        and not request.user.has_perm(PERMISSAO_PROGRAMACAO)
    )
    form = ProgramacaoCampoForm(
        request.POST,
        instance=item,
        cong=cong,
        somente_territorio=somente_territorio,
    )
    if form.is_valid():
        objeto = form.save(commit=False)
        objeto.assign_user = request.user
        objeto.save()
        messages.success(request, 'Programação atualizada com sucesso.')
        return redirect(_url('painel_servico_campo', semana, cong))
    return render(
        request,
        'servico_campo/painel.html',
        _contexto_painel(
            request, cong, semana, form=form, modal_open=True, programacao=item
        ),
        status=200,
    )


@acesso_campo
@require_POST
def movimentar_programacao_campo(request, programacao_id):
    semana = normalizar_semana(request.POST.get('semana'))
    cong = _congregacao(request)
    form = MovimentoProgramacaoCampoForm(request.POST)
    if form.is_valid():
        acao = form.cleaned_data['acao']
        if acao == 'cancelar' and not request.user.has_perm(PERMISSAO_PROGRAMACAO):
            raise PermissionDenied
        try:
            movimentar_programacao(
                programacao_id,
                cong,
                request.user,
                acao,
                form.cleaned_data.get('resultado', ''),
                form.cleaned_data.get('observacao', ''),
            )
            messages.success(request, 'Movimentação registrada com sucesso.')
        except ProgramacaoCampo.DoesNotExist:
            raise Http404
        except ValidationError as exc:
            messages.error(request, '; '.join(exc.messages))
    else:
        messages.error(request, '; '.join(
            mensagem for erros in form.errors.values() for mensagem in erros
        ))
    return redirect(_url('painel_servico_campo', semana, cong))


CADASTROS = {
    'dirigentes': {
        'model': DirigenteCampoHabilitado,
        'form': DirigenteCampoHabilitadoForm,
        'title': 'Dirigentes habilitados',
        'permission': PERMISSAO_PROGRAMACAO,
    },
    'locais': {
        'model': LocalSaidaCampo,
        'form': LocalSaidaCampoForm,
        'title': 'Locais de saída',
        'permission': PERMISSAO_PROGRAMACAO,
    },
    'arranjos': {
        'model': ArranjoSaidaCampo,
        'form': ArranjoSaidaCampoForm,
        'title': 'Arranjos recorrentes',
        'permission': PERMISSAO_PROGRAMACAO,
    },
    'territorios': {
        'model': TerritorioCampo,
        'form': TerritorioCampoForm,
        'title': 'Territórios',
        'permission': None,
    },
}


def _cadastro(request, tipo, item_id=None):
    config = CADASTROS[tipo]
    if config['permission'] and not request.user.has_perm(config['permission']):
        raise PermissionDenied
    cong = _congregacao(request, obrigatoria=False)
    if request.method == 'POST' and not cong:
        raise Http404
    item = None
    if item_id:
        item = get_object_or_404(config['model'], pk=item_id, cong=cong)
    form = config['form'](
        request.POST or None,
        instance=item,
        cong=cong,
    )
    if request.method == 'POST' and form.is_valid():
        objeto = form.save(commit=False)
        if not objeto.pk:
            objeto.create_user = request.user
        objeto.assign_user = request.user
        objeto.save()
        messages.success(request, 'Cadastro salvo com sucesso.')
        return redirect(_url('list_%s_campo' % tipo, cong=cong))
    itens = config['model'].objects.none()
    if cong:
        itens = config['model'].objects.filter(cong=cong)
        if tipo == 'dirigentes':
            itens = itens.select_related('publicador')
        elif tipo == 'arranjos':
            itens = itens.select_related('local', 'grupo')
        elif tipo == 'territorios':
            itens = itens.prefetch_related('mapas')
    contexto = _contexto_base(request, cong, config['title'])
    contexto.update({
        'tipo': tipo,
        'itens': itens,
        'form': form,
        'item_edicao': item,
        'mapa_form': MapaTerritorioForm(),
    })
    return render(request, 'servico_campo/cadastro.html', contexto)


@acesso_programacao
def list_dirigentes_campo(request):
    return _cadastro(request, 'dirigentes')


@acesso_programacao
def edit_dirigente_campo(request, item_id):
    return _cadastro(request, 'dirigentes', item_id)


@acesso_programacao
def list_locais_campo(request):
    return _cadastro(request, 'locais')


@acesso_programacao
def edit_local_campo(request, item_id):
    return _cadastro(request, 'locais', item_id)


@acesso_programacao
def list_arranjos_campo(request):
    return _cadastro(request, 'arranjos')


@acesso_programacao
def edit_arranjo_campo(request, item_id):
    return _cadastro(request, 'arranjos', item_id)


@acesso_campo
def list_territorios_campo(request):
    return _cadastro(request, 'territorios')


@acesso_campo
def edit_territorio_campo(request, item_id):
    return _cadastro(request, 'territorios', item_id)


@acesso_campo
@require_POST
def upload_mapa_territorio(request, territorio_id):
    cong = _congregacao(request)
    territorio = get_object_or_404(TerritorioCampo, pk=territorio_id, cong=cong)
    form = MapaTerritorioForm(request.POST, request.FILES, territorio=territorio)
    if form.is_valid():
        mapa = form.save(commit=False)
        mapa.create_user = request.user
        mapa.assign_user = request.user
        mapa.save()
        messages.success(request, 'Nova versão do mapa enviada com sucesso.')
    else:
        messages.error(request, '; '.join(
            mensagem for erros in form.errors.values() for mensagem in erros
        ))
    return redirect(_url('list_territorios_campo', cong=cong))


@acesso_campo
@require_GET
def baixar_mapa_territorio(request, mapa_id):
    cong = _congregacao(request)
    mapa = get_object_or_404(
        MapaTerritorio.objects.select_related('territorio'),
        pk=mapa_id,
        territorio__cong=cong,
    )
    tipo, _ = mimetypes.guess_type(mapa.arquivo.name)
    resposta = FileResponse(
        mapa.arquivo.open('rb'),
        content_type=tipo or 'application/octet-stream',
    )
    disposicao = 'attachment' if request.GET.get('download') == '1' else 'inline'
    nome = 'territorio-%s-v%s%s' % (
        mapa.territorio.codigo,
        mapa.versao,
        mimetypes.guess_extension(tipo or '') or '',
    )
    resposta['Content-Disposition'] = '%s; filename="%s"' % (disposicao, nome)
    resposta['X-Content-Type-Options'] = 'nosniff'
    return resposta


@acesso_campo
@require_GET
def distribuicao_territorios(request):
    cong = _congregacao(request, obrigatoria=False)
    itens = ProgramacaoCampo.objects.none()
    if cong:
        itens = ProgramacaoCampo.objects.filter(cong=cong).select_related(
            'territorio', 'grupo', 'dirigente', 'local', 'mapa'
        )
        inicio = request.GET.get('inicio')
        fim = request.GET.get('fim')
        if inicio:
            itens = itens.filter(data__gte=inicio)
        if fim:
            itens = itens.filter(data__lte=fim)
        for campo in ['territorio', 'grupo', 'dirigente', 'local']:
            valor = request.GET.get(campo)
            if valor:
                itens = itens.filter(**{'%s_id' % campo: valor})
        if request.GET.get('status'):
            itens = itens.filter(status=request.GET['status'])
        if request.GET.get('resultado'):
            itens = itens.filter(resultado=request.GET['resultado'])
    contexto = _contexto_base(request, cong, 'Distribuição de territórios')
    contexto.update({
        'itens': itens,
        'territorios': TerritorioCampo.objects.filter(cong=cong).order_by('codigo') if cong else [],
        'grupos': cong.grupos_set.all().order_by('grupo') if cong else [],
        'dirigentes': Publicadores.objects.filter(
            programacoes_dirigidas__cong=cong
        ).distinct().order_by('nome') if cong else [],
        'locais': LocalSaidaCampo.objects.filter(cong=cong).order_by('nome') if cong else [],
        'filtros': request.GET,
        'status_choices': ProgramacaoCampo._meta.get_field('status').choices,
        'resultado_choices': ProgramacaoCampo._meta.get_field('resultado').choices,
    })
    return render(request, 'servico_campo/distribuicao.html', contexto)


@acesso_campo
@require_GET
def pdf_servico_campo(request):
    semana = normalizar_semana(request.GET.get('semana'))
    cong = _congregacao(request)
    arquivo = gerar_pdf_programacao_campo(cong, semana)
    resposta = HttpResponse(arquivo.getvalue(), content_type='application/pdf')
    resposta['Content-Disposition'] = (
        'inline; filename="servico-campo-%s.pdf"' % semana.isoformat()
    )
    return resposta
