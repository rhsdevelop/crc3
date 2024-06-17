from register.models import Cong, CongUser, Drive, Grupos, Publicadores, Pioneiros, TIPO

from django.contrib.auth.models import User
from django.db import models

class Faltas(models.Model):
    data = models.DateField(db_column='Data')
    publicador = models.ForeignKey(Publicadores, db_column='Publicador', on_delete=models.PROTECT, blank=True, null=True)
    reuniao = models.IntegerField(db_column='Reuniao', blank=True, null=True)
    create_user = models.ForeignKey(User, db_column='User_Create', on_delete=models.PROTECT, related_name='falta_user_create', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    assign_user = models.ForeignKey(User, db_column='User_Modify', on_delete=models.PROTECT, related_name='falta_user_assign', blank=True, null=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Faltas'


class Relatorios(models.Model):
    publicador = models.ForeignKey(Publicadores, db_column='Publicador', on_delete=models.PROTECT, blank=True, null=True)
    mes = models.DateField(db_column='Mes')
    publicacoes = models.IntegerField(db_column='Publicacoes')
    videos = models.IntegerField(db_column='Videos')
    horas = models.IntegerField(db_column='Horas')
    revisitas = models.IntegerField(db_column='Revisitas')
    estudos = models.IntegerField(db_column='Estudos')
    observacao = models.TextField(db_column='Observacao', blank=True, null=True)
    tipo = models.IntegerField(db_column='Tipo', choices=TIPO)  # Usuário não edita.
    reuniao_meio = models.IntegerField(db_column='Reuniao_Meio', blank=True, null=True)
    reuniao_fim = models.IntegerField(db_column='Reuniao_Fim', blank=True, null=True)
    atv_local = models.BooleanField(db_column='Atv_Local', verbose_name='Atividade na congregação', default=True)
    create_user = models.ForeignKey(User, db_column='User_Create', on_delete=models.PROTECT, related_name='relatorio_user_create', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    assign_user = models.ForeignKey(User, db_column='User_Modify', on_delete=models.PROTECT, related_name='relatorio_user_assign', blank=True, null=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Relatorios'
