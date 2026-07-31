import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Q

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


DIAS_SEMANA = [
    (0, 'Segunda-feira'),
    (1, 'Terça-feira'),
    (2, 'Quarta-feira'),
    (3, 'Quinta-feira'),
    (4, 'Sexta-feira'),
    (5, 'Sábado'),
    (6, 'Domingo'),
]

MODO_IDENTIFICACAO_CARRINHO = [
    ('N', 'Numérico'),
    ('A', 'Alfabético'),
]


def numero_para_letras(numero):
    resultado = ''
    while numero > 0:
        numero, resto = divmod(numero - 1, 26)
        resultado = chr(65 + resto) + resultado
    return resultado


class AuditoriaTestemunhoPublico(models.Model):
    create_user = models.ForeignKey(
        User,
        db_column='User_Create',
        on_delete=models.PROTECT,
        related_name='%(class)s_user_create',
        blank=True,
        null=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    assign_user = models.ForeignKey(
        User,
        db_column='User_Modify',
        on_delete=models.PROTECT,
        related_name='%(class)s_user_assign',
        blank=True,
        null=True,
    )
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class HabilitacaoTestemunhoPublico(AuditoriaTestemunhoPublico):
    cong = models.ForeignKey(Cong, db_column='Cong', on_delete=models.PROTECT)
    publicador = models.ForeignKey(
        Publicadores,
        db_column='Publicador',
        on_delete=models.PROTECT,
        related_name='habilitacoes_testemunho_publico',
    )
    data_treinamento = models.DateField(
        db_column='Data_Treinamento',
        verbose_name='Data do treinamento',
    )
    aprovado = models.BooleanField(db_column='Aprovado', default=True)
    observacao = models.TextField(db_column='Observacao', blank=True)

    class Meta:
        db_table = 'TP_Habilitacao'
        ordering = ['publicador__nome']
        default_permissions = ()
        permissions = [
            (
                'manage_testemunho_publico',
                'Pode gerenciar o testemunho público',
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['cong', 'publicador'],
                name='unique_tp_habilitacao_cong_publicador',
            ),
        ]

    def __str__(self):
        return str(self.publicador)

    def clean(self):
        super().clean()
        if self.publicador_id and self.cong_id != self.publicador.cong_id:
            raise ValidationError({
                'publicador': 'O publicador deve pertencer à congregação informada.',
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class PeriodoTestemunhoPublico(AuditoriaTestemunhoPublico):
    cong = models.ForeignKey(Cong, db_column='Cong', on_delete=models.PROTECT)
    dia_semana = models.IntegerField(
        db_column='Dia_Semana',
        choices=DIAS_SEMANA,
        verbose_name='Dia da semana',
    )
    descricao = models.CharField(
        db_column='Descricao',
        max_length=30,
        verbose_name='Descrição',
    )
    horario = models.TimeField(db_column='Horario', verbose_name='Horário')
    ativo = models.BooleanField(db_column='Ativo', default=True)

    class Meta:
        db_table = 'TP_Periodo'
        ordering = ['horario', 'descricao', 'dia_semana']
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(
                fields=['cong', 'dia_semana', 'horario'],
                name='unique_tp_periodo_cong_dia_horario',
            ),
        ]

    @property
    def rotulo(self):
        return '%s %s' % (self.descricao, self.horario.strftime('%H:%M'))

    def __str__(self):
        return '%s - %s' % (self.get_dia_semana_display(), self.rotulo)

    def save(self, *args, **kwargs):
        if self.descricao:
            self.descricao = self.descricao.strip()
        self.full_clean()
        return super().save(*args, **kwargs)


class LocalTestemunhoPublico(AuditoriaTestemunhoPublico):
    cong = models.ForeignKey(Cong, db_column='Cong', on_delete=models.PROTECT)
    nome = models.CharField(db_column='Nome', max_length=100)
    endereco_referencia = models.CharField(
        db_column='Endereco_Referencia',
        max_length=200,
        blank=True,
        verbose_name='Endereço ou referência',
    )
    observacao = models.TextField(db_column='Observacao', blank=True)
    ativo = models.BooleanField(db_column='Ativo', default=True)

    class Meta:
        db_table = 'TP_Local'
        ordering = ['nome']
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(
                fields=['cong', 'nome'],
                name='unique_tp_local_cong_nome',
            ),
        ]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if self.nome:
            self.nome = self.nome.strip()
        self.full_clean()
        return super().save(*args, **kwargs)


class ConfiguracaoTestemunhoPublico(AuditoriaTestemunhoPublico):
    cong = models.OneToOneField(
        Cong,
        db_column='Cong',
        on_delete=models.PROTECT,
        related_name='configuracao_testemunho_publico',
    )
    quantidade_carrinhos = models.PositiveSmallIntegerField(
        db_column='Quantidade_Carrinhos',
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Quantidade de carrinhos',
    )
    modo_identificacao = models.CharField(
        db_column='Modo_Identificacao',
        max_length=1,
        choices=MODO_IDENTIFICACAO_CARRINHO,
        default='N',
        verbose_name='Identificação automática',
    )

    class Meta:
        db_table = 'TP_Configuracao'
        default_permissions = ()

    def __str__(self):
        return 'Configuração - %s' % self.cong

    def clean(self):
        super().clean()
        if not self.cong_id or not self.pk:
            return
        carrinhos_excedentes = CarrinhoTestemunhoPublico.objects.filter(
            cong_id=self.cong_id,
            numero_ordem__gt=self.quantidade_carrinhos,
            designacoes__data__gte=datetime.date.today(),
        )
        if carrinhos_excedentes.exists():
            raise ValidationError({
                'quantidade_carrinhos': (
                    'Reatribua ou apague as designações futuras dos carrinhos '
                    'excedentes antes de reduzir a quantidade.'
                ),
            })

    def sincronizar_carrinhos(self):
        for numero in range(1, self.quantidade_carrinhos + 1):
            carrinho, criado = CarrinhoTestemunhoPublico.objects.get_or_create(
                cong=self.cong,
                numero_ordem=numero,
                defaults={
                    'ativo': True,
                    'create_user': self.assign_user or self.create_user,
                    'assign_user': self.assign_user or self.create_user,
                },
            )
            if not criado and not carrinho.ativo:
                carrinho.ativo = True
                carrinho.assign_user = self.assign_user
                carrinho.save()

        carrinhos_excedentes = CarrinhoTestemunhoPublico.objects.filter(
            cong=self.cong,
            numero_ordem__gt=self.quantidade_carrinhos,
            ativo=True,
        )
        for carrinho in carrinhos_excedentes:
            carrinho.ativo = False
            carrinho.assign_user = self.assign_user
            carrinho.save()

    def save(self, *args, **kwargs):
        with transaction.atomic():
            self.full_clean()
            resultado = super().save(*args, **kwargs)
            self.sincronizar_carrinhos()
            return resultado


class CarrinhoTestemunhoPublico(AuditoriaTestemunhoPublico):
    cong = models.ForeignKey(Cong, db_column='Cong', on_delete=models.PROTECT)
    numero_ordem = models.PositiveSmallIntegerField(
        db_column='Numero_Ordem',
        validators=[MinValueValidator(1)],
        verbose_name='Número de ordem',
    )
    nome_personalizado = models.CharField(
        db_column='Nome_Personalizado',
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Nome personalizado',
    )
    ativo = models.BooleanField(db_column='Ativo', default=True)

    class Meta:
        db_table = 'TP_Carrinho'
        ordering = ['numero_ordem']
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(
                fields=['cong', 'numero_ordem'],
                name='unique_tp_carrinho_cong_ordem',
            ),
            models.UniqueConstraint(
                fields=['cong', 'nome_personalizado'],
                name='unique_tp_carrinho_cong_nome',
            ),
        ]

    @property
    def identificacao(self):
        if self.nome_personalizado:
            return self.nome_personalizado
        try:
            modo = self.cong.configuracao_testemunho_publico.modo_identificacao
        except ConfiguracaoTestemunhoPublico.DoesNotExist:
            modo = 'N'
        codigo = (
            numero_para_letras(self.numero_ordem)
            if modo == 'A'
            else str(self.numero_ordem)
        )
        return 'Carrinho %s' % codigo

    def __str__(self):
        return self.identificacao

    def clean(self):
        super().clean()
        if self.nome_personalizado:
            self.nome_personalizado = self.nome_personalizado.strip() or None
        if self.ativo and self.cong_id and self.numero_ordem:
            try:
                quantidade = self.cong.configuracao_testemunho_publico.quantidade_carrinhos
            except ConfiguracaoTestemunhoPublico.DoesNotExist:
                quantidade = 0
            if self.numero_ordem > quantidade:
                raise ValidationError({
                    'numero_ordem': 'O carrinho excede a quantidade configurada.',
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class DesignacaoTestemunhoPublico(AuditoriaTestemunhoPublico):
    cong = models.ForeignKey(Cong, db_column='Cong', on_delete=models.PROTECT)
    data = models.DateField(db_column='Data')
    periodo = models.ForeignKey(
        PeriodoTestemunhoPublico,
        db_column='Periodo',
        on_delete=models.PROTECT,
        related_name='designacoes',
    )
    local = models.ForeignKey(
        LocalTestemunhoPublico,
        db_column='Local',
        on_delete=models.PROTECT,
        related_name='designacoes',
    )
    carrinho = models.ForeignKey(
        CarrinhoTestemunhoPublico,
        db_column='Carrinho',
        on_delete=models.PROTECT,
        related_name='designacoes',
    )
    publicador_1 = models.ForeignKey(
        Publicadores,
        db_column='Publicador_1',
        on_delete=models.PROTECT,
        related_name='designacoes_tp_publicador_1',
        verbose_name='Publicador 1',
    )
    publicador_2 = models.ForeignKey(
        Publicadores,
        db_column='Publicador_2',
        on_delete=models.PROTECT,
        related_name='designacoes_tp_publicador_2',
        verbose_name='Publicador 2',
    )

    class Meta:
        db_table = 'TP_Designacao'
        ordering = ['data', 'periodo__horario', 'local__nome']
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(
                fields=['data', 'periodo', 'carrinho'],
                name='unique_tp_designacao_data_periodo_carrinho',
            ),
            models.UniqueConstraint(
                fields=['data', 'periodo', 'local'],
                name='unique_tp_designacao_data_periodo_local',
            ),
        ]

    def __str__(self):
        return '%s / %s - %s' % (
            self.publicador_1,
            self.publicador_2,
            self.data.strftime('%d/%m/%Y'),
        )

    def clean(self):
        super().clean()
        errors = {}
        relacionados = {
            'periodo': self.periodo if self.periodo_id else None,
            'local': self.local if self.local_id else None,
            'carrinho': self.carrinho if self.carrinho_id else None,
            'publicador_1': self.publicador_1 if self.publicador_1_id else None,
            'publicador_2': self.publicador_2 if self.publicador_2_id else None,
        }
        for campo, objeto in relacionados.items():
            if objeto and objeto.cong_id != self.cong_id:
                errors[campo] = 'O item selecionado pertence a outra congregação.'

        if self.periodo_id:
            if not self.periodo.ativo:
                errors['periodo'] = 'O período selecionado está inativo.'
            elif self.data and self.data.weekday() != self.periodo.dia_semana:
                errors['data'] = 'A data não corresponde ao dia da semana do período.'
        if self.local_id and not self.local.ativo:
            errors['local'] = 'O local selecionado está inativo.'
        if self.carrinho_id and not self.carrinho.ativo:
            errors['carrinho'] = 'O carrinho selecionado está inativo.'

        publicadores = [
            ('publicador_1', self.publicador_1 if self.publicador_1_id else None),
            ('publicador_2', self.publicador_2 if self.publicador_2_id else None),
        ]
        for campo, publicador in publicadores:
            if not publicador:
                continue
            if publicador.situacao != 1:
                errors[campo] = 'O publicador deve estar ativo.'
            elif not HabilitacaoTestemunhoPublico.objects.filter(
                cong_id=self.cong_id,
                publicador=publicador,
                aprovado=True,
            ).exists():
                errors[campo] = (
                    'O publicador deve estar treinado e aprovado para o arranjo.'
                )

        if (
            self.publicador_1_id
            and self.publicador_1_id == self.publicador_2_id
        ):
            errors['publicador_2'] = 'Selecione dois publicadores diferentes.'

        if self.data and self.periodo_id:
            concorrentes = DesignacaoTestemunhoPublico.objects.filter(
                data=self.data,
                periodo_id=self.periodo_id,
            )
            if self.pk:
                concorrentes = concorrentes.exclude(pk=self.pk)
            if self.carrinho_id and concorrentes.filter(
                carrinho_id=self.carrinho_id,
            ).exists():
                errors['carrinho'] = 'O carrinho já está designado nesse período.'
            if self.local_id and concorrentes.filter(
                local_id=self.local_id,
            ).exists():
                errors['local'] = 'O local já está ocupado nesse período.'
            for campo, publicador in publicadores:
                if publicador and concorrentes.filter(
                    Q(publicador_1=publicador) | Q(publicador_2=publicador)
                ).exists():
                    errors[campo] = (
                        'O publicador já está designado nesse período.'
                    )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
