import datetime
import os
import uuid

from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Q
from django.utils.text import slugify
from PIL import Image, UnidentifiedImageError

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


def resumir_nome(nome):
    partes = nome.split()
    if len(partes) <= 1:
        return nome
    return '%s %s' % (partes[0], partes[-1])


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

    @property
    def nomes_resumidos(self):
        return '%s / %s' % (
            resumir_nome(self.publicador_1.nome),
            resumir_nome(self.publicador_2.nome),
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


TIPOS_ATIVIDADE_CAMPO = [
    ('T', 'Território'),
    ('C', 'Cartas'),
    ('O', 'Outro'),
]

TIPOS_DIRIGENCIA_CAMPO = [
    ('P', 'Publicador habilitado'),
    ('G', 'Responsabilidade do grupo'),
]

STATUS_PROGRAMACAO_CAMPO = [
    ('A', 'A preparar'),
    ('P', 'Programada'),
    ('R', 'Retirada'),
    ('D', 'Devolvida'),
    ('C', 'Cancelada'),
]

RESULTADOS_TERRITORIO_CAMPO = [
    ('', 'Não informado'),
    ('C', 'Coberto'),
    ('P', 'Parcial'),
    ('N', 'Não trabalhado'),
]


def validar_arquivo_mapa(arquivo):
    extensao = os.path.splitext(arquivo.name)[1].lower()
    if extensao not in {'.jpg', '.jpeg', '.png', '.webp'}:
        raise ValidationError('Envie um mapa nos formatos JPEG, PNG ou WebP.')
    if arquivo.size > 10 * 1024 * 1024:
        raise ValidationError('O arquivo do mapa deve ter no máximo 10 MB.')
    posicao = arquivo.tell() if hasattr(arquivo, 'tell') else None
    try:
        imagem = Image.open(arquivo)
        imagem.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValidationError('O arquivo enviado não é uma imagem válida.')
    finally:
        if posicao is not None and hasattr(arquivo, 'seek'):
            arquivo.seek(posicao)


def caminho_mapa_territorio(instance, filename):
    extensao = os.path.splitext(filename)[1].lower()
    return 'territorios/%s/%s/%s%s' % (
        instance.territorio.cong_id,
        slugify(instance.territorio.codigo) or instance.territorio_id,
        uuid.uuid4().hex,
        extensao,
    )


class PrivateMapStorage(FileSystemStorage):
    @property
    def base_location(self):
        return settings.PRIVATE_MEDIA_ROOT

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    @property
    def base_url(self):
        return None


private_map_storage = PrivateMapStorage()


class DirigenteCampoHabilitado(AuditoriaTestemunhoPublico):
    cong = models.ForeignKey(Cong, db_column='Cong', on_delete=models.PROTECT)
    publicador = models.ForeignKey(
        Publicadores,
        db_column='Publicador',
        on_delete=models.PROTECT,
        related_name='habilitacoes_dirigente_campo',
    )
    ativo = models.BooleanField(db_column='Ativo', default=True)
    observacao = models.TextField(db_column='Observacao', blank=True)

    class Meta:
        db_table = 'Campo_Dirigente_Habilitado'
        ordering = ['publicador__nome']
        default_permissions = ()
        permissions = [
            ('manage_programacao_campo', 'Pode gerenciar a programação de campo'),
            ('manage_territorios', 'Pode gerenciar os territórios'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['cong', 'publicador'],
                name='unique_campo_dirigente_cong_publicador',
            ),
        ]

    def __str__(self):
        return str(self.publicador)

    def clean(self):
        super().clean()
        if not self.publicador_id:
            return
        errors = {}
        if self.publicador.cong_id != self.cong_id:
            errors['publicador'] = 'O publicador pertence a outra congregação.'
        elif self.publicador.situacao != 1:
            errors['publicador'] = 'O dirigente deve ser um publicador ativo.'
        elif self.publicador.sexo != 0:
            errors['publicador'] = 'O dirigente deve ser um homem ativo.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class LocalSaidaCampo(AuditoriaTestemunhoPublico):
    cong = models.ForeignKey(Cong, db_column='Cong', on_delete=models.PROTECT)
    nome = models.CharField(db_column='Nome', max_length=100)
    endereco_referencia = models.CharField(
        db_column='Endereco_Referencia', max_length=200, blank=True,
        verbose_name='Endereço ou referência',
    )
    ativo = models.BooleanField(db_column='Ativo', default=True)

    class Meta:
        db_table = 'Campo_Local_Saida'
        ordering = ['nome']
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(
                fields=['cong', 'nome'], name='unique_campo_local_cong_nome'
            ),
        ]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        self.nome = self.nome.strip()
        self.full_clean()
        return super().save(*args, **kwargs)


class ArranjoSaidaCampo(AuditoriaTestemunhoPublico):
    cong = models.ForeignKey(Cong, db_column='Cong', on_delete=models.PROTECT)
    dia_semana = models.IntegerField(
        db_column='Dia_Semana', choices=DIAS_SEMANA,
        verbose_name='Dia da semana',
    )
    horario = models.TimeField(db_column='Horario', verbose_name='Horário')
    local = models.ForeignKey(
        LocalSaidaCampo, db_column='Local', on_delete=models.PROTECT,
        related_name='arranjos',
    )
    grupo = models.ForeignKey(
        Grupos, db_column='Grupo', on_delete=models.PROTECT,
        related_name='arranjos_saida_campo', blank=True, null=True,
    )
    descricao = models.CharField(db_column='Descricao', max_length=80, blank=True)
    ativo = models.BooleanField(db_column='Ativo', default=True)

    class Meta:
        db_table = 'Campo_Arranjo_Saida'
        ordering = ['dia_semana', 'horario', 'local__nome', 'grupo__grupo']
        default_permissions = ()

    def __str__(self):
        complemento = ' - %s' % self.grupo if self.grupo_id else ''
        return '%s %s - %s%s' % (
            self.get_dia_semana_display(),
            self.horario.strftime('%H:%M'),
            self.local,
            complemento,
        )

    def clean(self):
        super().clean()
        errors = {}
        if self.local_id and self.local.cong_id != self.cong_id:
            errors['local'] = 'O local pertence a outra congregação.'
        if self.grupo_id and self.grupo.cong_id != self.cong_id:
            errors['grupo'] = 'O grupo pertence a outra congregação.'
        if self.cong_id and self.local_id and self.horario is not None:
            duplicados = ArranjoSaidaCampo.objects.filter(
                cong_id=self.cong_id,
                dia_semana=self.dia_semana,
                horario=self.horario,
                local_id=self.local_id,
                grupo_id=self.grupo_id,
            )
            if self.pk:
                duplicados = duplicados.exclude(pk=self.pk)
            if duplicados.exists():
                errors['horario'] = 'Já existe esse arranjo para o dia, local e grupo.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.descricao = self.descricao.strip()
        self.full_clean()
        return super().save(*args, **kwargs)


class TerritorioCampo(AuditoriaTestemunhoPublico):
    cong = models.ForeignKey(Cong, db_column='Cong', on_delete=models.PROTECT)
    codigo = models.CharField(db_column='Codigo', max_length=30, verbose_name='Código')
    localidade = models.CharField(db_column='Localidade', max_length=100)
    descricao = models.TextField(db_column='Descricao', blank=True, verbose_name='Descrição')
    observacao = models.TextField(db_column='Observacao', blank=True, verbose_name='Observações')
    ativo = models.BooleanField(db_column='Ativo', default=True)

    class Meta:
        db_table = 'Campo_Territorio'
        ordering = ['codigo']
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(
                fields=['cong', 'codigo'], name='unique_campo_territorio_cong_codigo'
            ),
        ]

    def __str__(self):
        return '%s - %s' % (self.codigo, self.localidade)

    @property
    def mapa_vigente(self):
        return self.mapas.filter(vigente=True).first()

    def save(self, *args, **kwargs):
        self.codigo = self.codigo.strip()
        self.localidade = self.localidade.strip()
        self.full_clean()
        return super().save(*args, **kwargs)


class MapaTerritorio(AuditoriaTestemunhoPublico):
    territorio = models.ForeignKey(
        TerritorioCampo, db_column='Territorio', on_delete=models.PROTECT,
        related_name='mapas',
    )
    arquivo = models.ImageField(
        db_column='Arquivo', upload_to=caminho_mapa_territorio,
        validators=[validar_arquivo_mapa], storage=private_map_storage,
    )
    versao = models.PositiveSmallIntegerField(db_column='Versao', editable=False)
    vigente = models.BooleanField(db_column='Vigente', default=True)

    class Meta:
        db_table = 'Campo_Mapa_Territorio'
        ordering = ['-versao']
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(
                fields=['territorio', 'versao'],
                name='unique_campo_mapa_territorio_versao',
            ),
            models.UniqueConstraint(
                fields=['territorio'], condition=Q(vigente=True),
                name='unique_campo_mapa_vigente',
            ),
        ]

    def __str__(self):
        return '%s - versão %s' % (self.territorio, self.versao)

    @property
    def cong(self):
        return self.territorio.cong

    def save(self, *args, **kwargs):
        with transaction.atomic():
            TerritorioCampo.objects.select_for_update().get(pk=self.territorio_id)
            if not self.pk and not self.versao:
                ultima = MapaTerritorio.objects.filter(
                    territorio_id=self.territorio_id,
                ).aggregate(models.Max('versao'))['versao__max'] or 0
                self.versao = ultima + 1
            if self.vigente:
                MapaTerritorio.objects.filter(
                    territorio_id=self.territorio_id, vigente=True,
                ).exclude(pk=self.pk).update(vigente=False)
            self.full_clean()
            return super().save(*args, **kwargs)


class ProgramacaoCampo(AuditoriaTestemunhoPublico):
    cong = models.ForeignKey(Cong, db_column='Cong', on_delete=models.PROTECT)
    data = models.DateField(db_column='Data')
    arranjo = models.ForeignKey(
        ArranjoSaidaCampo, db_column='Arranjo', on_delete=models.PROTECT,
        related_name='programacoes',
    )
    horario = models.TimeField(db_column='Horario', verbose_name='Horário')
    local = models.ForeignKey(
        LocalSaidaCampo, db_column='Local', on_delete=models.PROTECT,
        related_name='programacoes',
    )
    local_nome = models.CharField(db_column='Local_Nome', max_length=100, editable=False)
    grupo = models.ForeignKey(
        Grupos, db_column='Grupo', on_delete=models.PROTECT,
        related_name='programacoes_campo', blank=True, null=True,
    )
    grupo_nome = models.CharField(
        db_column='Grupo_Nome', max_length=50, blank=True, editable=False,
    )
    descricao = models.CharField(db_column='Descricao', max_length=80, blank=True)
    tipo_dirigencia = models.CharField(
        db_column='Tipo_Dirigencia', max_length=1,
        choices=TIPOS_DIRIGENCIA_CAMPO, default='P',
    )
    dirigente = models.ForeignKey(
        Publicadores, db_column='Dirigente', on_delete=models.PROTECT,
        related_name='programacoes_dirigidas', blank=True, null=True,
    )
    tipo_atividade = models.CharField(
        db_column='Tipo_Atividade', max_length=1,
        choices=TIPOS_ATIVIDADE_CAMPO, default='T',
    )
    descricao_atividade = models.CharField(
        db_column='Descricao_Atividade', max_length=100, blank=True,
        verbose_name='Descrição da atividade',
    )
    territorio = models.ForeignKey(
        TerritorioCampo, db_column='Territorio', on_delete=models.PROTECT,
        related_name='programacoes', blank=True, null=True,
    )
    mapa = models.ForeignKey(
        MapaTerritorio, db_column='Mapa', on_delete=models.PROTECT,
        related_name='programacoes', blank=True, null=True,
    )
    status = models.CharField(
        db_column='Status', max_length=1,
        choices=STATUS_PROGRAMACAO_CAMPO, default='A',
    )
    resultado = models.CharField(
        db_column='Resultado', max_length=1,
        choices=RESULTADOS_TERRITORIO_CAMPO, blank=True, default='',
    )
    retirada_em = models.DateTimeField(db_column='Retirada_Em', blank=True, null=True)
    retirada_por = models.ForeignKey(
        User, db_column='Retirada_Por', on_delete=models.PROTECT,
        related_name='programacoes_campo_retiradas', blank=True, null=True,
    )
    devolvida_em = models.DateTimeField(db_column='Devolvida_Em', blank=True, null=True)
    devolvida_por = models.ForeignKey(
        User, db_column='Devolvida_Por', on_delete=models.PROTECT,
        related_name='programacoes_campo_devolvidas', blank=True, null=True,
    )
    observacao_movimento = models.TextField(
        db_column='Observacao_Movimento', blank=True,
        verbose_name='Observação da movimentação',
    )
    motivo_cancelamento = models.TextField(
        db_column='Motivo_Cancelamento', blank=True,
        verbose_name='Motivo do cancelamento',
    )

    class Meta:
        db_table = 'Campo_Programacao'
        ordering = ['data', 'horario', 'local_nome', 'grupo_nome']
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(
                fields=['cong', 'data', 'arranjo'],
                name='unique_campo_programacao_cong_data_arranjo',
            ),
        ]

    def __str__(self):
        return '%s %s - %s' % (
            self.data.strftime('%d/%m/%Y'),
            self.horario.strftime('%H:%M'),
            self.local_nome,
        )

    @property
    def dirigente_exibicao(self):
        if self.tipo_dirigencia == 'G':
            return 'Responsabilidade do grupo'
        return str(self.dirigente) if self.dirigente_id else 'A definir'

    @property
    def atividade_exibicao(self):
        if self.tipo_atividade == 'T':
            return str(self.territorio) if self.territorio_id else 'Território a definir'
        if self.tipo_atividade == 'C':
            return 'Cartas'
        return self.descricao_atividade or 'Outra atividade'

    def clean(self):
        super().clean()
        errors = {}
        original = None
        if self.pk:
            original = ProgramacaoCampo.objects.filter(pk=self.pk).values(
                'status', 'data', 'arranjo_id', 'horario', 'local_id',
                'grupo_id', 'tipo_dirigencia', 'dirigente_id',
                'tipo_atividade', 'territorio_id', 'mapa_id',
            ).first()
            if original:
                transicoes = {
                    'A': {'A', 'P', 'C'},
                    'P': {'P', 'R', 'C'},
                    'R': {'R', 'D'},
                    'D': {'D'},
                    'C': {'C'},
                }
                if self.status not in transicoes[original['status']]:
                    errors['status'] = 'A transição de situação informada não é permitida.'
                if original['status'] in {'R', 'D', 'C'}:
                    protegidos = {
                        'data': self.data,
                        'arranjo_id': self.arranjo_id,
                        'horario': self.horario,
                        'local_id': self.local_id,
                        'grupo_id': self.grupo_id,
                        'tipo_dirigencia': self.tipo_dirigencia,
                        'dirigente_id': self.dirigente_id,
                        'tipo_atividade': self.tipo_atividade,
                        'territorio_id': self.territorio_id,
                        'mapa_id': self.mapa_id,
                    }
                    if any(original[campo] != valor for campo, valor in protegidos.items()):
                        errors['status'] = 'A programação movimentada não pode mais ser alterada.'
        elif self.status not in {'A', 'P'}:
            errors['status'] = 'Uma nova programação deve estar em preparação ou programada.'
        relacionados = {
            'arranjo': self.arranjo if self.arranjo_id else None,
            'local': self.local if self.local_id else None,
            'grupo': self.grupo if self.grupo_id else None,
            'dirigente': self.dirigente if self.dirigente_id else None,
            'territorio': self.territorio if self.territorio_id else None,
        }
        for campo, objeto in relacionados.items():
            if objeto and getattr(objeto, 'cong_id', None) != self.cong_id:
                errors[campo] = 'O item selecionado pertence a outra congregação.'
        if self.mapa_id and self.mapa.territorio.cong_id != self.cong_id:
            errors['mapa'] = 'O mapa pertence a outra congregação.'
        if self.data and self.arranjo_id and self.data.weekday() != self.arranjo.dia_semana:
            errors['data'] = 'A data não corresponde ao dia do arranjo.'

        if self.tipo_dirigencia == 'P':
            if not self.dirigente_id and self.status not in ['A', 'C']:
                errors['dirigente'] = 'Selecione o dirigente.'
            dirigente_historico = bool(
                original
                and original['status'] in {'P', 'R', 'D', 'C'}
                and original['dirigente_id'] == self.dirigente_id
            )
            if self.dirigente_id and not dirigente_historico and (
                self.dirigente.situacao != 1 or self.dirigente.sexo != 0
            ):
                errors['dirigente'] = 'O dirigente deve ser um homem ativo.'
            elif (
                self.dirigente_id
                and not dirigente_historico
                and not DirigenteCampoHabilitado.objects.filter(
                cong_id=self.cong_id, publicador_id=self.dirigente_id, ativo=True,
                ).exists()
            ):
                errors['dirigente'] = 'O publicador não está habilitado como dirigente.'
        elif self.tipo_dirigencia == 'G':
            self.dirigente = None
            if not self.grupo_id:
                errors['tipo_dirigencia'] = 'A responsabilidade do grupo exige um grupo.'

        if self.tipo_atividade == 'T':
            if not self.territorio_id and self.status not in ['A', 'C']:
                errors['territorio'] = 'Selecione o território.'
            if not self.mapa_id and self.status not in ['A', 'C']:
                errors['mapa'] = 'O território precisa possuir um mapa vigente.'
            elif (
                self.mapa_id
                and self.territorio_id
                and self.mapa.territorio_id != self.territorio_id
            ):
                errors['mapa'] = 'O mapa não pertence ao território selecionado.'
        else:
            self.territorio = None
            self.mapa = None
            if self.tipo_atividade == 'O' and not self.descricao_atividade.strip():
                errors['descricao_atividade'] = 'Informe a atividade.'

        if self.tipo_dirigencia == 'P' and self.dirigente_id and self.data and self.horario:
            conflitos = ProgramacaoCampo.objects.filter(
                cong_id=self.cong_id,
                data=self.data,
                horario=self.horario,
                dirigente_id=self.dirigente_id,
            ).exclude(status='C')
            if self.pk:
                conflitos = conflitos.exclude(pk=self.pk)
            if conflitos.exists():
                errors['dirigente'] = 'O dirigente já está escalado nesse horário.'

        if self.status == 'C' and not self.motivo_cancelamento.strip():
            errors['motivo_cancelamento'] = 'Informe o motivo do cancelamento.'
        if self.status in {'R', 'D'} and (not self.retirada_em or not self.retirada_por_id):
            errors['status'] = 'A retirada precisa estar registrada.'
        if self.status == 'D' and not self.resultado:
            errors['resultado'] = 'Informe o resultado da devolução.'
        if self.status == 'D' and (not self.devolvida_em or not self.devolvida_por_id):
            errors['status'] = 'A devolução precisa estar registrada.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.arranjo_id and not self.pk:
            self.horario = self.arranjo.horario
            self.local = self.arranjo.local
            self.grupo = self.arranjo.grupo
            self.descricao = self.arranjo.descricao
        original = None
        if self.pk:
            original = ProgramacaoCampo.objects.filter(pk=self.pk).values(
                'local_id', 'grupo_id'
            ).first()
        if self.local_id and (
            not self.local_nome
            or not self.pk
            or (original and original['local_id'] != self.local_id)
        ):
            self.local_nome = self.local.nome
        if self.grupo_id and (
            not self.grupo_nome
            or not self.pk
            or (original and original['grupo_id'] != self.grupo_id)
        ):
            self.grupo_nome = self.grupo.grupo
        elif not self.grupo_id:
            self.grupo_nome = ''
        self.full_clean()
        return super().save(*args, **kwargs)
