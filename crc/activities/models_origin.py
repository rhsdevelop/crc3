# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Cong(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True, blank=True, null=True)  # Field name made lowercase.
    nome = models.CharField(db_column='Nome')  # Field name made lowercase.
    numero = models.IntegerField(db_column='Numero')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Cong'


class Drive(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True, blank=True, null=True)  # Field name made lowercase.
    arquivo = models.CharField(db_column='Arquivo')  # Field name made lowercase.
    id_google = models.CharField(db_column='Id_Google')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Drive'


'''
class Faltas(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True, blank=True, null=True)  # Field name made lowercase.
    data = models.CharField(db_column='Data')  # Field name made lowercase.
    publicador = models.ForeignKey('Publicadores', models.DO_NOTHING, db_column='Publicador', blank=True, null=True)  # Field name made lowercase.
    reuniao = models.IntegerField(db_column='Reuniao', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Faltas'
'''


class Grupos(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True, blank=True, null=True)  # Field name made lowercase.
    grupo = models.CharField(db_column='Grupo')  # Field name made lowercase.
    dirigente = models.CharField(db_column='Dirigente')  # Field name made lowercase.
    ajudante = models.CharField(db_column='Ajudante', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Grupos'


class Pioneiros(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True, blank=True, null=True)  # Field name made lowercase.
    publicador = models.ForeignKey('Publicadores', models.DO_NOTHING, db_column='Publicador', blank=True, null=True)  # Field name made lowercase.
    mes = models.CharField(db_column='Mes')  # Field name made lowercase.
    observacao = models.CharField(db_column='Observacao', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Pioneiros'


class Publicadores(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True, blank=True, null=True)  # Field name made lowercase.
    nome = models.CharField(db_column='Nome')  # Field name made lowercase.
    endereco = models.CharField(db_column='Endereco')  # Field name made lowercase.
    telefone_fixo = models.CharField(db_column='Telefone_Fixo', blank=True, null=True)  # Field name made lowercase.
    telefone_celular = models.CharField(db_column='Telefone_Celular', blank=True, null=True)  # Field name made lowercase.
    nascimento = models.CharField(db_column='Nascimento', blank=True, null=True)  # Field name made lowercase.
    batismo = models.CharField(db_column='Batismo', blank=True, null=True)  # Field name made lowercase.
    esperanca = models.IntegerField(db_column='Esperanca')  # Field name made lowercase.
    privilegio = models.IntegerField(db_column='Privilegio')  # Field name made lowercase.
    tipo = models.IntegerField(db_column='Tipo')  # Field name made lowercase.
    sexo = models.IntegerField(db_column='Sexo')  # Field name made lowercase.
    observacao = models.CharField(db_column='Observacao', blank=True, null=True)  # Field name made lowercase.
    situacao = models.IntegerField(db_column='Situacao')  # Field name made lowercase.
    classe = models.CharField(db_column='Classe')  # Field name made lowercase.
    data_classe = models.CharField(db_column='Data_Classe', blank=True, null=True)  # Field name made lowercase.
    data_visita = models.CharField(db_column='Data_Visita', blank=True, null=True)  # Field name made lowercase.
    grupo = models.ForeignKey(Grupos, models.DO_NOTHING, db_column='Grupo', blank=True, null=True)  # Field name made lowercase.
    nome_gdrive = models.CharField(db_column='Nome_Gdrive', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Publicadores'


'''
class Relatorios(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True, blank=True, null=True)  # Field name made lowercase.
    publicador = models.ForeignKey(Publicadores, models.DO_NOTHING, db_column='Publicador', blank=True, null=True)  # Field name made lowercase.
    mes = models.CharField(db_column='Mes')  # Field name made lowercase.
    publicacoes = models.IntegerField(db_column='Publicacoes')  # Field name made lowercase.
    videos = models.IntegerField(db_column='Videos')  # Field name made lowercase.
    horas = models.IntegerField(db_column='Horas')  # Field name made lowercase.
    revisitas = models.IntegerField(db_column='Revisitas')  # Field name made lowercase.
    estudos = models.IntegerField(db_column='Estudos')  # Field name made lowercase.
    observacao = models.CharField(db_column='Observacao', blank=True, null=True)  # Field name made lowercase.
    tipo = models.IntegerField(db_column='Tipo')  # Field name made lowercase.
    reuniao_meio = models.IntegerField(db_column='Reuniao_Meio', blank=True, null=True)  # Field name made lowercase.
    reuniao_fim = models.IntegerField(db_column='Reuniao_Fim', blank=True, null=True)  # Field name made lowercase.
    atv_local = models.IntegerField(db_column='Atv_Local', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Relatorios'


class Reunioes(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True, blank=True, null=True)  # Field name made lowercase.
    data = models.CharField(db_column='Data')  # Field name made lowercase.
    tipo = models.IntegerField(db_column='Tipo')  # Field name made lowercase.
    assistencia = models.IntegerField(db_column='Assistencia')  # Field name made lowercase.
    observacao = models.CharField(db_column='Observacao', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Reunioes'


class Security(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True, blank=True, null=True)  # Field name made lowercase.
    nome = models.CharField(db_column='Nome')  # Field name made lowercase.
    senha = models.CharField(db_column='Senha')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Security'
'''