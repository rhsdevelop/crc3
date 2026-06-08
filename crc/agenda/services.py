import datetime

from .models import TarefaSecretario


TAREFAS_BASE_SECRETARIO = [
    {
        'titulo': 'Coletar relatórios de serviço de campo',
        'descricao': 'Coletar relatórios de serviço de campo dos publicadores por meio dos superintendentes de grupo.',
        'tipo_recorrencia': 'mensal',
        'categoria': 'relatorios',
        'prioridade': 'alta',
    },
    {
        'titulo': 'Consolidar e enviar relatório da congregação',
        'descricao': 'Consolidar e enviar o relatório da congregação à filial pelo site jw.org.',
        'tipo_recorrencia': 'mensal',
        'categoria': 'relatorios',
        'prioridade': 'alta',
    },
    {
        'titulo': 'Identificar publicadores sem relatório',
        'descricao': 'Identificar publicadores que não relataram atividade.',
        'tipo_recorrencia': 'mensal',
        'categoria': 'atividade_publicadores',
        'prioridade': 'media',
    },
    {
        'titulo': 'Informar superintendentes de grupo sobre atividade',
        'descricao': 'Informar os superintendentes de grupo sobre publicadores irregulares ou com redução de atividade.',
        'tipo_recorrencia': 'mensal',
        'categoria': 'atividade_publicadores',
        'prioridade': 'media',
    },
    {
        'titulo': 'Arquivar correspondências da filial',
        'descricao': 'Receber, repassar e arquivar correspondências da filial.',
        'tipo_recorrencia': 'mensal',
        'categoria': 'correspondencias',
        'prioridade': 'media',
    },
    {
        'titulo': 'Preparar fechamento do relatório anual',
        'descricao': 'Preparar fechamento do relatório anual da congregação.',
        'tipo_recorrencia': 'anual',
        'categoria': 'relatorios',
        'prioridade': 'alta',
    },
    {
        'titulo': 'Verificar atividade dos pioneiros regulares',
        'descricao': 'Verificar atividade dos pioneiros regulares.',
        'tipo_recorrencia': 'anual',
        'categoria': 'pioneiros',
        'prioridade': 'media',
    },
    {
        'titulo': 'Revisar e limpar arquivo da congregação',
        'descricao': 'Revisar e limpar o arquivo da congregação.',
        'tipo_recorrencia': 'anual',
        'categoria': 'arquivo',
        'prioridade': 'media',
    },
    {
        'titulo': 'Auxiliar na contagem da Celebração',
        'descricao': 'Auxiliar na contagem da assistência da Celebração.',
        'tipo_recorrencia': 'sazonal',
        'categoria': 'celebracao',
        'prioridade': 'alta',
    },
    {
        'titulo': 'Enviar relatório da Celebração',
        'descricao': 'Enviar relatório da assistência da Celebração e número de emblemas tomados.',
        'tipo_recorrencia': 'sazonal',
        'categoria': 'celebracao',
        'prioridade': 'alta',
    },
    {
        'titulo': 'Atualizar cartões S-21',
        'descricao': 'Atualizar cartões de Registro de Publicador de Congregação S-21.',
        'tipo_recorrencia': 'anual',
        'categoria': 'atividade_publicadores',
        'prioridade': 'media',
    },
    {
        'titulo': 'Preparar estatísticas para visita do superintendente',
        'descricao': 'Preparar estatísticas da congregação para visita do superintendente de circuito.',
        'tipo_recorrencia': 'sazonal',
        'categoria': 'visita_superintendente',
        'prioridade': 'alta',
    },
]


def carregar_tarefas_base(cong, user):
    ano = datetime.date.today().year
    criadas = 0
    for tarefa in TAREFAS_BASE_SECRETARIO:
        _, created = TarefaSecretario.objects.get_or_create(
            cong=cong,
            titulo=tarefa['titulo'],
            tipo_recorrencia=tarefa['tipo_recorrencia'],
            categoria=tarefa['categoria'],
            ano_referencia=ano,
            mes_referencia=None,
            defaults={
                'descricao': tarefa['descricao'],
                'status': 'pendente',
                'prioridade': tarefa['prioridade'],
                'create_user': user,
                'assign_user': user,
            },
        )
        if created:
            criadas += 1
    return criadas
