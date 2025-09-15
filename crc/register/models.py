from django.contrib.auth.models import User
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
    (2, 'Mudou-se'),
    (3, 'Removido'),
    (4, 'Falecido'),
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
    create_user = models.ForeignKey(User, db_column='User_Create', on_delete=models.PROTECT, related_name='cong_user_create', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    assign_user = models.ForeignKey(User, db_column='User_Modify', on_delete=models.PROTECT, related_name='cong_user_assign', blank=True, null=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Cong'

    def __str__(self) -> str:
        return self.nome + ' (%s)' % self.numero


class CongUser(models.Model):
    cong = models.ForeignKey(Cong, db_column='Cong', on_delete=models.PROTECT)
    user = models.ForeignKey(User, db_column='Usuario', on_delete=models.PROTECT, related_name='cong_user')
    admin = models.BooleanField(db_column='Administrador', default=False)
    create_user = models.ForeignKey(User, db_column='User_Create', on_delete=models.PROTECT, related_name='conguser_user_create', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    assign_user = models.ForeignKey(User, db_column='User_Modify', on_delete=models.PROTECT, related_name='conguser_user_assign', blank=True, null=True)
    modified = models.DateTimeField(auto_now=True)


class Drive(models.Model):
    arquivo = models.CharField(db_column='Arquivo', max_length=30)
    id_google = models.CharField(db_column='Id_Google', max_length=100)

    class Meta:
        db_table = 'Drive'


class Grupos(models.Model):
    grupo = models.CharField(db_column='Grupo', max_length=50)
    dirigente = models.CharField(db_column='Dirigente', max_length=50)
    ajudante = models.CharField(db_column='Ajudante', max_length=50, blank=True, null=True)
    cong = models.ForeignKey(Cong, db_column='Cong', on_delete=models.PROTECT, blank=True, null=True)
    create_user = models.ForeignKey(User, db_column='User_Create', on_delete=models.PROTECT, related_name='grupo_user_create', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    assign_user = models.ForeignKey(User, db_column='User_Modify', on_delete=models.PROTECT, related_name='grupo_user_assign', blank=True, null=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Grupos'

    def __str__(self) -> str:
        return self.grupo


class Publicadores(models.Model):
    nome = models.CharField(db_column='Nome', max_length=50)
    endereco = models.CharField(db_column='Endereco', max_length=100)
    telefone_fixo = models.CharField(db_column='Telefone_Fixo', max_length=16, blank=True, null=True)
    telefone_celular = models.CharField(db_column='Telefone_Celular', max_length=16, blank=True, null=True)
    email = models.EmailField(db_column='Email', max_length=254, blank=True, null=True)
    nascimento = models.DateField(db_column='Nascimento', blank=True, null=True)
    batismo = models.DateField(db_column='Batismo', blank=True, null=True)
    esperanca = models.IntegerField(db_column='Esperanca', choices=ESPERANCA)
    privilegio = models.IntegerField(db_column='Privilegio', choices=PRIVILEGIO)
    tipo = models.IntegerField(db_column='Tipo', choices=TIPO[0:3])
    sexo = models.IntegerField(db_column='Sexo', choices=SEXO)
    observacao = models.TextField(db_column='Observacao', blank=True, null=True)
    situacao = models.IntegerField(db_column='Situacao', choices=SITUACAO)
    classe = models.CharField(db_column='Classe', choices=CLASSE_PUB, max_length=20)
    data_classe = models.DateField(db_column='Data_Classe', blank=True, null=True)
    data_visita = models.DateField(db_column='Data_Visita', blank=True, null=True)
    grupo = models.ForeignKey(Grupos, db_column='Grupo', on_delete=models.PROTECT, blank=True, null=True)
    nome_gdrive = models.CharField(db_column='Nome_Gdrive', blank=True, null=True, max_length=50)
    cong = models.ForeignKey(Cong, db_column='Cong', on_delete=models.PROTECT, blank=True, null=True)
    create_user = models.ForeignKey(User, db_column='User_Create', on_delete=models.PROTECT, related_name='publicador_user_create', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    assign_user = models.ForeignKey(User, db_column='User_Modify', on_delete=models.PROTECT, related_name='publicador_user_assign', blank=True, null=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Publicadores'

    def __str__(self) -> str:
        return self.nome


class Pioneiros(models.Model):
    publicador = models.ForeignKey(Publicadores, db_column='Publicador', on_delete=models.PROTECT, blank=True, null=True)
    mes = models.DateField(db_column='Mes')
    observacao = models.TextField(db_column='Observacao', blank=True, null=True)
    create_user = models.ForeignKey(User, db_column='User_Create', on_delete=models.PROTECT, related_name='pioneiro_user_create', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    assign_user = models.ForeignKey(User, db_column='User_Modify', on_delete=models.PROTECT, related_name='pioneiro_user_assign', blank=True, null=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Pioneiros'
