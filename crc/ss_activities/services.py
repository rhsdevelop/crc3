import datetime

from django.db.models import Q

from .models import (
    CarrinhoTestemunhoPublico,
    DesignacaoTestemunhoPublico,
    PeriodoTestemunhoPublico,
)


NOMES_DIAS_SEMANA = [
    'Segunda-feira',
    'Terça-feira',
    'Quarta-feira',
    'Quinta-feira',
    'Sexta-feira',
    'Sábado',
    'Domingo',
]


def montar_grade_testemunho_publico(cong, semana, carrinho=None):
    """Monta a mesma grade semanal usada pelo painel e pelo PDF."""
    fim_semana = semana + datetime.timedelta(days=6)
    dias = [
        {
            'data': semana + datetime.timedelta(days=indice),
            'nome': nome,
        }
        for indice, nome in enumerate(NOMES_DIAS_SEMANA)
    ]

    designacoes = DesignacaoTestemunhoPublico.objects.none()
    periodos = PeriodoTestemunhoPublico.objects.none()
    if cong:
        designacoes = DesignacaoTestemunhoPublico.objects.filter(
            cong=cong,
            data__range=(semana, fim_semana),
        )
        if carrinho is not None:
            designacoes = designacoes.filter(carrinho=carrinho)
        designacoes = designacoes.select_related(
            'periodo',
            'local',
            'carrinho__cong__configuracao_testemunho_publico',
            'publicador_1',
            'publicador_2',
        ).order_by('data', 'periodo__horario', 'carrinho__ordem', 'id')

        periodos_usados = designacoes.values_list('periodo_id', flat=True)
        periodos = PeriodoTestemunhoPublico.objects.filter(cong=cong).filter(
            Q(ativo=True) | Q(pk__in=periodos_usados)
        ).distinct()

    designacoes_queryset = designacoes
    designacoes = list(designacoes_queryset)
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
            })
        linhas.append({
            'rotulo': '%s %s' % (descricao, horario.strftime('%H:%M')),
            'celulas': celulas,
        })

    return {
        'semana': semana,
        'fim_semana': fim_semana,
        'dias': dias,
        'linhas': linhas,
        'designacoes': designacoes_queryset,
    }


def carrinhos_disponiveis_para_impressao(cong, semana):
    if not cong:
        return CarrinhoTestemunhoPublico.objects.none()
    fim_semana = semana + datetime.timedelta(days=6)
    return CarrinhoTestemunhoPublico.objects.filter(cong=cong).filter(
        Q(ativo=True) | Q(designacoes__data__range=(semana, fim_semana))
    ).select_related(
        'cong__configuracao_testemunho_publico'
    ).distinct().order_by('numero_ordem')
