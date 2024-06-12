# Generated by Django 4.0 on 2024-06-11 20:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cong',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(db_column='Nome', max_length=50)),
                ('numero', models.IntegerField(db_column='Numero')),
            ],
            options={
                'db_table': 'Cong',
            },
        ),
        migrations.CreateModel(
            name='Drive',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('arquivo', models.CharField(db_column='Arquivo', max_length=30)),
                ('id_google', models.CharField(db_column='Id_Google', max_length=100)),
            ],
            options={
                'db_table': 'Drive',
            },
        ),
        migrations.CreateModel(
            name='Grupos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('grupo', models.CharField(db_column='Grupo', max_length=50)),
                ('dirigente', models.CharField(db_column='Dirigente', max_length=50)),
                ('ajudante', models.CharField(blank=True, db_column='Ajudante', max_length=50, null=True)),
            ],
            options={
                'db_table': 'Grupos',
            },
        ),
        migrations.CreateModel(
            name='Publicadores',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(db_column='Nome', max_length=50)),
                ('endereco', models.CharField(db_column='Endereco', max_length=100)),
                ('telefone_fixo', models.CharField(blank=True, db_column='Telefone_Fixo', max_length=16, null=True)),
                ('telefone_celular', models.CharField(blank=True, db_column='Telefone_Celular', max_length=16, null=True)),
                ('nascimento', models.DateField(blank=True, db_column='Nascimento', null=True)),
                ('batismo', models.DateField(blank=True, db_column='Batismo', null=True)),
                ('esperanca', models.IntegerField(choices=[(0, 'Outra Ovelha'), (1, 'Ungido')], db_column='Esperanca')),
                ('privilegio', models.IntegerField(choices=[(0, 'Publicador'), (1, 'Servo Ministerial'), (2, 'Ancião')], db_column='Privilegio')),
                ('tipo', models.IntegerField(choices=[(0, 'Publicador'), (1, 'Pioneiro Auxiliar'), (2, 'Pioneiro Regular'), (3, 'Irregular')], db_column='Tipo')),
                ('sexo', models.IntegerField(choices=[(0, 'Masculino'), (1, 'Feminino')], db_column='Sexo')),
                ('observacao', models.TextField(blank=True, db_column='Observacao', null=True)),
                ('situacao', models.IntegerField(choices=[(0, 'Inativo'), (1, 'Ativo'), (2, 'Desligado')], db_column='Situacao')),
                ('classe', models.CharField(choices=[('0', 'Normal'), ('1', 'Novo'), ('2', 'Mudou-se'), ('3', 'Pioneiro reg'), ('4', 'Reativado'), ('5', 'Sem atividade')], db_column='Classe', max_length=20)),
                ('data_classe', models.DateField(blank=True, db_column='Data_Classe', null=True)),
                ('data_visita', models.DateField(blank=True, db_column='Data_Visita', null=True)),
                ('nome_gdrive', models.CharField(blank=True, db_column='Nome_Gdrive', max_length=50, null=True)),
                ('grupo', models.ForeignKey(blank=True, db_column='Grupo', null=True, on_delete=django.db.models.deletion.PROTECT, to='register.grupos')),
            ],
            options={
                'db_table': 'Publicadores',
            },
        ),
        migrations.CreateModel(
            name='Reunioes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateField(db_column='Data')),
                ('tipo', models.IntegerField(choices=[(0, 'Meio de Semana'), (1, 'Fim de Semana'), (2, 'Outro Evento')], db_column='Tipo')),
                ('assistencia', models.IntegerField(db_column='Assistencia')),
                ('observacao', models.TextField(blank=True, db_column='Observacao', null=True)),
            ],
            options={
                'db_table': 'Reunioes',
            },
        ),
        migrations.CreateModel(
            name='Relatorios',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mes', models.DateField(db_column='Mes')),
                ('publicacoes', models.IntegerField(db_column='Publicacoes')),
                ('videos', models.IntegerField(db_column='Videos')),
                ('horas', models.IntegerField(db_column='Horas')),
                ('revisitas', models.IntegerField(db_column='Revisitas')),
                ('estudos', models.IntegerField(db_column='Estudos')),
                ('observacao', models.TextField(blank=True, db_column='Observacao', null=True)),
                ('tipo', models.IntegerField(choices=[(0, 'Publicador'), (1, 'Pioneiro Auxiliar'), (2, 'Pioneiro Regular'), (3, 'Irregular')], db_column='Tipo')),
                ('reuniao_meio', models.IntegerField(blank=True, db_column='Reuniao_Meio', null=True)),
                ('reuniao_fim', models.IntegerField(blank=True, db_column='Reuniao_Fim', null=True)),
                ('atv_local', models.IntegerField(blank=True, db_column='Atv_Local', null=True)),
                ('publicador', models.ForeignKey(blank=True, db_column='Publicador', null=True, on_delete=django.db.models.deletion.PROTECT, to='register.publicadores')),
            ],
            options={
                'db_table': 'Relatorios',
            },
        ),
        migrations.CreateModel(
            name='Pioneiros',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mes', models.DateField(db_column='Mes')),
                ('observacao', models.TextField(blank=True, db_column='Observacao', null=True)),
                ('publicador', models.ForeignKey(blank=True, db_column='Publicador', null=True, on_delete=django.db.models.deletion.PROTECT, to='register.publicadores')),
            ],
            options={
                'db_table': 'Pioneiros',
            },
        ),
        migrations.CreateModel(
            name='Faltas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateField(db_column='Data')),
                ('reuniao', models.IntegerField(blank=True, db_column='Reuniao', null=True)),
                ('publicador', models.ForeignKey(blank=True, db_column='Publicador', null=True, on_delete=django.db.models.deletion.PROTECT, to='register.publicadores')),
            ],
            options={
                'db_table': 'Faltas',
            },
        ),
    ]