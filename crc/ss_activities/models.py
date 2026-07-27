import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from register.models import Cong, Grupos


class VisitaGrupo(models.Model):
    cong = models.ForeignKey(Cong, db_column='Cong', on_delete=models.PROTECT)
    grupo = models.ForeignKey(Grupos, db_column='Grupo', on_delete=models.PROTECT)
    data_inicio = models.DateField(db_column='Data_Inicio', verbose_name='Início')
    data_fim = models.DateField(db_column='Data_Fim', verbose_name='Fim', editable=False)
    confirmada = models.BooleanField(db_column='Confirmada', default=False)
    executada = models.BooleanField(db_column='Executada', default=False)
    create_user = models.ForeignKey(
        User,
        db_column='User_Create',
        on_delete=models.PROTECT,
        related_name='visita_grupo_user_create',
        blank=True,
        null=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    assign_user = models.ForeignKey(
        User,
        db_column='User_Modify',
        on_delete=models.PROTECT,
        related_name='visita_grupo_user_assign',
        blank=True,
        null=True,
    )
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Visita_Grupo'
        ordering = ['data_inicio', 'grupo__grupo']
        default_permissions = ()
        permissions = [
            ('manage_visitas_grupos', 'Pode gerenciar visitas aos grupos'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['cong', 'data_inicio'],
                name='unique_visita_cong_semana',
            ),
        ]

    def __str__(self):
        return '%s - %s a %s' % (
            self.grupo,
            self.data_inicio.strftime('%d/%m/%Y'),
            self.data_fim.strftime('%d/%m/%Y'),
        )

    def clean(self):
        super().clean()
        errors = {}

        if self.grupo_id:
            if not self.grupo.cong_id:
                errors['grupo'] = 'O grupo selecionado não está vinculado a uma congregação.'
            elif self.cong_id and self.cong_id != self.grupo.cong_id:
                errors['grupo'] = 'O grupo selecionado não pertence à congregação informada.'
            else:
                self.cong_id = self.grupo.cong_id

        if self.data_inicio:
            if self.data_inicio.weekday() != 0:
                errors['data_inicio'] = 'A visita deve começar em uma segunda-feira.'
            self.data_fim = self.data_inicio + datetime.timedelta(days=6)

        if self.executada:
            self.confirmada = True

        if self.cong_id and self.data_inicio:
            visitas_na_semana = VisitaGrupo.objects.filter(
                cong_id=self.cong_id,
                data_inicio=self.data_inicio,
            )
            if self.pk:
                visitas_na_semana = visitas_na_semana.exclude(pk=self.pk)
            if visitas_na_semana.exists():
                errors['data_inicio'] = (
                    'Já existe uma visita programada para esta congregação nessa semana.'
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.grupo_id:
            self.cong_id = self.grupo.cong_id
        if self.data_inicio:
            self.data_fim = self.data_inicio + datetime.timedelta(days=6)
        if self.executada:
            self.confirmada = True
        self.full_clean()
        return super().save(*args, **kwargs)
