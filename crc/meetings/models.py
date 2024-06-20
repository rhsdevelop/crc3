from django.contrib.auth.models import User
from django.db import models

from register.models import Cong

TIPO_REUNIAO = [
    (0, 'Meio de Semana'),
    (1, 'Fim de Semana'),
    (2, 'Outro Evento')
]

class Reunioes(models.Model):
    data = models.DateField(db_column='Data')
    tipo = models.IntegerField(db_column='Tipo', choices=TIPO_REUNIAO)
    assistencia = models.IntegerField(db_column='Assistencia')
    observacao = models.TextField(db_column='Observacao', blank=True, null=True)
    cong = models.ForeignKey(Cong, db_column='Cong', on_delete=models.PROTECT, blank=True, null=True)
    create_user = models.ForeignKey(User, db_column='User_Create', on_delete=models.PROTECT, related_name='reuniao_user_create', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    assign_user = models.ForeignKey(User, db_column='User_Modify', on_delete=models.PROTECT, related_name='reuniao_user_assign', blank=True, null=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Reunioes'
