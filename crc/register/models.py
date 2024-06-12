from django.db import models

# Base cadastral.
ESPERANCA = [
    (0, 'Outra Ovelha'),
    (1, 'Ungido')
]
PRIVILEGIO = [
    (0, 'Publicador'),
    (1, 'Servo Ministerial'),
    (2, 'Ancião')
]
TIPO = [
    (0, 'Publicador'),
    (1, 'Pioneiro Auxiliar'),
    (2, 'Pioneiro Regular'),
    (3, 'Irregular')
]
SEXO = [
    (0, 'Masculino'),
    (1, 'Feminino')
]
SITUACAO = [
    (0, 'Inativo'),
    (1, 'Ativo'),
    (2, 'Desligado')
]
CLASSE_PUB = [
    ('0', 'Normal'),
    ('1', 'Novo'),
    ('2', 'Mudou-se'),
    ('3', 'Pioneiro reg'),
    ('4', 'Reativado'),
    ('5', 'Sem atividade')
]
TIPO_REUNIAO = [
    (0, 'Meio de Semana'),
    (1, 'Fim de Semana'),
    (2, 'Outro Evento')
]

class Cong(models.Model):
    nome = models.CharField(db_column='Nome', max_length=50)
    numero = models.IntegerField(db_column='Numero')

    class Meta:
        db_table = 'Cong'


class Drive(models.Model):
    arquivo = models.CharField(db_column='Arquivo', max_length=30)
    id_google = models.CharField(db_column='Id_Google', max_length=100)

    class Meta:
        db_table = 'Drive'


class Grupos(models.Model):
    grupo = models.CharField(db_column='Grupo', max_length=50)
    dirigente = models.CharField(db_column='Dirigente', max_length=50)
    ajudante = models.CharField(db_column='Ajudante', max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'Grupos'


class Publicadores(models.Model):
    nome = models.CharField(db_column='Nome', max_length=50)
    endereco = models.CharField(db_column='Endereco', max_length=100)
    telefone_fixo = models.CharField(db_column='Telefone_Fixo', max_length=16, blank=True, null=True)
    telefone_celular = models.CharField(db_column='Telefone_Celular', max_length=16, blank=True, null=True)
    nascimento = models.DateField(db_column='Nascimento', blank=True, null=True)
    batismo = models.DateField(db_column='Batismo', blank=True, null=True)
    esperanca = models.IntegerField(db_column='Esperanca', choices=ESPERANCA)
    privilegio = models.IntegerField(db_column='Privilegio', choices=PRIVILEGIO)
    tipo = models.IntegerField(db_column='Tipo', choices=TIPO)
    sexo = models.IntegerField(db_column='Sexo', choices=SEXO)
    observacao = models.TextField(db_column='Observacao', blank=True, null=True)
    situacao = models.IntegerField(db_column='Situacao', choices=SITUACAO)
    classe = models.CharField(db_column='Classe', choices=CLASSE_PUB, max_length=20)
    data_classe = models.DateField(db_column='Data_Classe', blank=True, null=True)
    data_visita = models.DateField(db_column='Data_Visita', blank=True, null=True)
    grupo = models.ForeignKey(Grupos, db_column='Grupo', on_delete=models.PROTECT, blank=True, null=True)
    nome_gdrive = models.CharField(db_column='Nome_Gdrive', blank=True, null=True, max_length=50)

    class Meta:
        db_table = 'Publicadores'


class Pioneiros(models.Model):
    publicador = models.ForeignKey(Publicadores, db_column='Publicador', on_delete=models.PROTECT, blank=True, null=True)
    mes = models.DateField(db_column='Mes')
    observacao = models.TextField(db_column='Observacao', blank=True, null=True)

    class Meta:
        db_table = 'Pioneiros'

# Movimentos.


class Faltas(models.Model):
    data = models.DateField(db_column='Data')
    publicador = models.ForeignKey(Publicadores, db_column='Publicador', on_delete=models.PROTECT, blank=True, null=True)
    reuniao = models.IntegerField(db_column='Reuniao', blank=True, null=True)

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
    atv_local = models.IntegerField(db_column='Atv_Local', blank=True, null=True)

    class Meta:
        db_table = 'Relatorios'


class Reunioes(models.Model):
    data = models.DateField(db_column='Data')
    tipo = models.IntegerField(db_column='Tipo', choices=TIPO_REUNIAO)
    assistencia = models.IntegerField(db_column='Assistencia')
    observacao = models.TextField(db_column='Observacao', blank=True, null=True)

    class Meta:
        db_table = 'Reunioes'