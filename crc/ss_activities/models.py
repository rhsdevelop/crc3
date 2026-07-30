import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from register.models import Cong, Grupos, Publicadores


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

        if self.pk:
            original = VisitaGrupo.objects.filter(pk=self.pk).values(
                'grupo_id',
                'data_inicio',
            ).first()
            if original and self.visitas_pastoreio.exists():
                if self.grupo_id != original['grupo_id']:
                    errors['grupo'] = (
                        'Apague as visitas de pastoreio antes de alterar o grupo.'
                    )
                if self.data_inicio != original['data_inicio']:
                    errors['data_inicio'] = (
                        'Apague as visitas de pastoreio antes de alterar a semana.'
                    )

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


class VisitaPastoreio(models.Model):
    visita_grupo = models.ForeignKey(
        VisitaGrupo,
        db_column='Visita_Grupo',
        on_delete=models.PROTECT,
        related_name='visitas_pastoreio',
    )
    publicador = models.ForeignKey(
        Publicadores,
        db_column='Publicador',
        on_delete=models.PROTECT,
        related_name='visitas_pastoreio_recebidas',
    )
    data = models.DateField(db_column='Data')
    assuntos = models.TextField(db_column='Assuntos')
    materia = models.TextField(db_column='Materia', verbose_name='Matéria')
    acompanhante = models.ForeignKey(
        Publicadores,
        db_column='Acompanhante',
        on_delete=models.PROTECT,
        related_name='visitas_pastoreio_acompanhadas',
        verbose_name='Quem acompanha',
    )
    confirmado = models.BooleanField(db_column='Confirmado', default=False)
    create_user = models.ForeignKey(
        User,
        db_column='User_Create',
        on_delete=models.PROTECT,
        related_name='visita_pastoreio_user_create',
        blank=True,
        null=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    assign_user = models.ForeignKey(
        User,
        db_column='User_Modify',
        on_delete=models.PROTECT,
        related_name='visita_pastoreio_user_assign',
        blank=True,
        null=True,
    )
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Visita_Pastoreio'
        ordering = ['data', 'publicador__nome']
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(
                fields=['visita_grupo', 'publicador'],
                name='unique_pastoreio_visita_publicador',
            ),
        ]

    def __str__(self):
        return '%s - %s' % (
            self.publicador,
            self.data.strftime('%d/%m/%Y'),
        )

    def clean(self):
        super().clean()
        errors = {}

        if self.visita_grupo_id:
            visita = self.visita_grupo
            if self.publicador_id:
                if self.publicador.grupo_id != visita.grupo_id:
                    errors['publicador'] = (
                        'O publicador deve pertencer ao grupo visitado.'
                    )
                elif self.publicador.situacao not in [0, 1]:
                    errors['publicador'] = (
                        'Selecione um publicador ativo ou inativo.'
                    )

            if self.data and not visita.data_inicio <= self.data <= visita.data_fim:
                errors['data'] = (
                    'A data deve estar dentro da semana da visita ao grupo.'
                )

            if self.acompanhante_id:
                if self.acompanhante.cong_id != visita.cong_id:
                    errors['acompanhante'] = (
                        'O acompanhante deve pertencer à mesma congregação.'
                    )
                elif self.acompanhante.situacao != 1:
                    errors['acompanhante'] = 'O acompanhante deve estar ativo.'
                elif self.acompanhante.privilegio not in [1, 2]:
                    errors['acompanhante'] = (
                        'O acompanhante deve ser servo ministerial ou ancião.'
                    )

        if (
            self.publicador_id
            and self.acompanhante_id
            and self.publicador_id == self.acompanhante_id
        ):
            errors['acompanhante'] = (
                'O acompanhante deve ser diferente do publicador visitado.'
            )

        if self.visita_grupo_id and self.publicador_id:
            duplicadas = VisitaPastoreio.objects.filter(
                visita_grupo_id=self.visita_grupo_id,
                publicador_id=self.publicador_id,
            )
            if self.pk:
                duplicadas = duplicadas.exclude(pk=self.pk)
            if duplicadas.exists():
                errors['publicador'] = (
                    'Este publicador já possui uma visita de pastoreio nessa semana.'
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
