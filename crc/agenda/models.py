from django.contrib.auth.models import User
from django.db import models

from register.models import Cong


TIPO_RECORRENCIA = [
    ('mensal', 'Mensal'),
    ('anual', 'Anual'),
    ('sazonal', 'Sazonal'),
    ('eventual', 'Eventual'),
]

CATEGORIA_TAREFA = [
    ('relatorios', 'Relatórios'),
    ('atividade_publicadores', 'Atividade dos publicadores'),
    ('correspondencias', 'Correspondências'),
    ('pioneiros', 'Pioneiros'),
    ('celebracao', 'Celebração'),
    ('visita_superintendente', 'Visita do superintendente'),
    ('arquivo', 'Arquivo'),
    ('outros', 'Outros'),
]

STATUS_TAREFA = [
    ('pendente', 'Pendente'),
    ('em_andamento', 'Em andamento'),
    ('concluida', 'Concluída'),
    ('cancelada', 'Cancelada'),
]

PRIORIDADE_TAREFA = [
    ('baixa', 'Baixa'),
    ('media', 'Média'),
    ('alta', 'Alta'),
]

MESES_REFERENCIA = [
    (1, 'Janeiro'),
    (2, 'Fevereiro'),
    (3, 'Março'),
    (4, 'Abril'),
    (5, 'Maio'),
    (6, 'Junho'),
    (7, 'Julho'),
    (8, 'Agosto'),
    (9, 'Setembro'),
    (10, 'Outubro'),
    (11, 'Novembro'),
    (12, 'Dezembro'),
]


class TarefaSecretario(models.Model):
    cong = models.ForeignKey(Cong, db_column='Cong', on_delete=models.PROTECT, blank=True, null=True)
    titulo = models.CharField(db_column='Titulo', max_length=120)
    descricao = models.TextField(db_column='Descricao', blank=True, null=True)
    tipo_recorrencia = models.CharField(db_column='Tipo_Recorrencia', max_length=20, choices=TIPO_RECORRENCIA)
    categoria = models.CharField(db_column='Categoria', max_length=40, choices=CATEGORIA_TAREFA)
    mes_referencia = models.IntegerField(db_column='Mes_Referencia', choices=MESES_REFERENCIA, blank=True, null=True)
    ano_referencia = models.IntegerField(db_column='Ano_Referencia', blank=True, null=True)
    data_prevista = models.DateField(db_column='Data_Prevista', blank=True, null=True)
    data_limite = models.DateField(db_column='Data_Limite', blank=True, null=True)
    status = models.CharField(db_column='Status', max_length=20, choices=STATUS_TAREFA, default='pendente')
    prioridade = models.CharField(db_column='Prioridade', max_length=20, choices=PRIORIDADE_TAREFA, default='media')
    observacoes = models.TextField(db_column='Observacoes', blank=True, null=True)
    data_conclusao = models.DateField(db_column='Data_Conclusao', blank=True, null=True)
    create_user = models.ForeignKey(User, db_column='User_Create', on_delete=models.PROTECT, related_name='tarefa_secretario_user_create', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    assign_user = models.ForeignKey(User, db_column='User_Modify', on_delete=models.PROTECT, related_name='tarefa_secretario_user_assign', blank=True, null=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'TarefaSecretario'
        ordering = ['status', 'data_limite', 'prioridade']

    def __str__(self) -> str:
        return self.titulo
