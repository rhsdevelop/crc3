import mimetypes
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.http import require_GET, require_POST

from register.models import Cong, CongUser, Publicadores

from .forms import ConfiguracaoCadernoPioneiroForm
from .models import ConfiguracaoCadernoPioneiro
from .pdf import gerar_pdf_capas, gerar_pdf_miolo
from .services import ano_servico_atual


PERMISSAO_CADERNOS = 'notebooks.manage_pioneer_notebooks'


def _ano_selecionado(request):
    valor = request.POST.get('ano') or request.GET.get('ano')
    if valor:
        try:
            ano = int(valor)
            if 1900 <= ano <= 9998:
                return ano
        except (TypeError, ValueError):
            pass
    return ano_servico_atual()


def _congregacao_usuario(request, obrigatoria=True):
    if request.user.is_superuser:
        cong_id = request.POST.get('cong') or request.GET.get('cong')
        if not cong_id:
            if obrigatoria:
                raise Http404
            return None
        return get_object_or_404(Cong, pk=cong_id)

    vinculo = CongUser.objects.filter(user=request.user).select_related('cong').first()
    if not vinculo:
        if obrigatoria:
            raise Http404
        return False
    return vinculo.cong


def _url_painel(ano, cong=None):
    parametros = {'ano': ano}
    if cong:
        parametros['cong'] = cong.id
    return '%s?%s' % (
        reverse('notebooks:pioneiros_regulares'),
        urlencode(parametros),
    )


def _contexto(request, cong, ano, form=None):
    configuracao = None
    pioneiros = Publicadores.objects.none()
    anos_configurados = []

    if cong:
        configuracao = ConfiguracaoCadernoPioneiro.objects.filter(
            cong=cong,
            ano_servico=ano,
        ).first()
        pioneiros = Publicadores.objects.filter(
            cong=cong,
            tipo=2,
            situacao=1,
        ).select_related('grupo').order_by('nome')
        anos_configurados = ConfiguracaoCadernoPioneiro.objects.filter(
            cong=cong,
        ).values_list('ano_servico', flat=True)
        if form is None:
            form = ConfiguracaoCadernoPioneiroForm(
                instance=configuracao,
                initial={'meta_horas': 50},
                cong=cong,
                ano_servico=ano,
            )

    atual = ano_servico_atual()
    anos = sorted(
        set(range(atual - 3, atual + 5)) | set(anos_configurados) | {ano},
        reverse=True,
    )
    return {
        'title': 'Cadernos de Pioneiros Regulares',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
        'selected_cong': cong,
        'list_cong': (
            Cong.objects.all().order_by('nome')
            if request.user.is_superuser
            else None
        ),
        'ano': ano,
        'ano_exibicao': '%s/%s' % (ano, ano + 1),
        'anos': [
            {'valor': item, 'rotulo': '%s/%s' % (item, item + 1)}
            for item in anos
        ],
        'configuracao': configuracao,
        'form': form,
        'pioneiros': pioneiros,
        'total_pioneiros': pioneiros.count(),
    }


@login_required
@permission_required(PERMISSAO_CADERNOS, raise_exception=True)
@require_GET
def pioneiros_regulares(request):
    ano = _ano_selecionado(request)
    cong = _congregacao_usuario(request, obrigatoria=False)
    if cong is False:
        messages.warning(request, 'Seu usuário não está vinculado a nenhuma congregação.')
        return redirect('/')
    return render(
        request,
        'notebooks/pioneiros_regulares.html',
        _contexto(request, cong, ano),
    )


@login_required
@permission_required(PERMISSAO_CADERNOS, raise_exception=True)
@require_POST
def salvar_configuracao(request):
    cong = _congregacao_usuario(request)
    ano = _ano_selecionado(request)
    configuracao = ConfiguracaoCadernoPioneiro.objects.filter(
        cong=cong,
        ano_servico=ano,
    ).first()
    form = ConfiguracaoCadernoPioneiroForm(
        request.POST,
        request.FILES,
        instance=configuracao,
        cong=cong,
        ano_servico=ano,
    )
    if form.is_valid():
        item = form.save(commit=False)
        if not item.pk:
            item.create_user = request.user
        item.assign_user = request.user
        item.save()
        messages.success(request, 'Configuração anual salva com sucesso.')
        return redirect(_url_painel(ano, cong))

    return render(
        request,
        'notebooks/pioneiros_regulares.html',
        _contexto(request, cong, ano, form=form),
    )


@login_required
@permission_required(PERMISSAO_CADERNOS, raise_exception=True)
@require_GET
def visualizar_imagem(request, configuracao_id):
    cong = _congregacao_usuario(request)
    configuracao = get_object_or_404(
        ConfiguracaoCadernoPioneiro,
        pk=configuracao_id,
        cong=cong,
    )
    tipo, _ = mimetypes.guess_type(configuracao.imagem.name)
    resposta = FileResponse(
        configuracao.imagem.open('rb'),
        content_type=tipo or 'application/octet-stream',
    )
    resposta['Content-Disposition'] = 'inline'
    resposta['X-Content-Type-Options'] = 'nosniff'
    return resposta


def _configuracao_capa(request, cong, ano):
    configuracao = ConfiguracaoCadernoPioneiro.objects.filter(
        cong=cong,
        ano_servico=ano,
    ).first()
    if not configuracao or not configuracao.imagem:
        messages.error(
            request,
            'Configure a imagem da capa para o ano de serviço selecionado.',
        )
        return None
    return configuracao


def _resposta_pdf(arquivo, nome):
    resposta = HttpResponse(arquivo.getvalue(), content_type='application/pdf')
    resposta['Content-Disposition'] = 'inline; filename="%s"' % nome
    return resposta


@login_required
@permission_required(PERMISSAO_CADERNOS, raise_exception=True)
@require_GET
def pdf_capas(request):
    cong = _congregacao_usuario(request)
    ano = _ano_selecionado(request)
    configuracao = _configuracao_capa(request, cong, ano)
    if not configuracao:
        return redirect(_url_painel(ano, cong))

    pioneiros = list(Publicadores.objects.filter(
        cong=cong,
        tipo=2,
        situacao=1,
    ).order_by('nome'))
    if not pioneiros:
        messages.warning(request, 'Nenhum pioneiro regular ativo foi encontrado.')
        return redirect(_url_painel(ano, cong))

    arquivo = gerar_pdf_capas(configuracao, pioneiros)
    nome = 'capas-pioneiros-%s-%s-%s.pdf' % (
        slugify(cong.nome),
        ano,
        ano + 1,
    )
    return _resposta_pdf(arquivo, nome)


@login_required
@permission_required(PERMISSAO_CADERNOS, raise_exception=True)
@require_GET
def pdf_capa_individual(request, publicador_id):
    cong = _congregacao_usuario(request)
    ano = _ano_selecionado(request)
    publicador = get_object_or_404(
        Publicadores,
        pk=publicador_id,
        cong=cong,
        tipo=2,
        situacao=1,
    )
    configuracao = _configuracao_capa(request, cong, ano)
    if not configuracao:
        return redirect(_url_painel(ano, cong))

    arquivo = gerar_pdf_capas(configuracao, [publicador])
    nome = 'capa-pioneiro-%s-%s-%s.pdf' % (
        slugify(publicador.nome),
        ano,
        ano + 1,
    )
    return _resposta_pdf(arquivo, nome)


@login_required
@permission_required(PERMISSAO_CADERNOS, raise_exception=True)
@require_GET
def pdf_miolo(request):
    cong = _congregacao_usuario(request)
    ano = _ano_selecionado(request)
    configuracao = ConfiguracaoCadernoPioneiro.objects.filter(
        cong=cong,
        ano_servico=ano,
    ).first()
    meta_horas = configuracao.meta_horas if configuracao else 50
    arquivo = gerar_pdf_miolo(ano, meta_horas)
    return _resposta_pdf(
        arquivo,
        'miolo-pioneiros-%s-%s-%sh.pdf' % (ano, ano + 1, meta_horas),
    )
