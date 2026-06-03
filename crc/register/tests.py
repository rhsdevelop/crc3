import datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from activities.models import Relatorios
from .models import Cong, CongUser, Publicadores


class CongUserListTests(TestCase):
    def setUp(self):
        self.cong_a = Cong.objects.create(nome='Congregação A', numero=1)
        self.cong_b = Cong.objects.create(nome='Congregação B', numero=2)
        self.admin = User.objects.create_superuser(username='admin', password='senha', first_name='Admin')
        self.user_com_login = User.objects.create_user(
            username='usuario_login',
            password='senha',
            last_login=datetime.datetime(2026, 6, 2, 10, 30),
        )
        self.user_sem_login = User.objects.create_user(username='usuario_sem_login', password='senha')
        CongUser.objects.create(cong=self.cong_a, user=self.user_com_login, create_user=self.admin)
        CongUser.objects.create(cong=self.cong_b, user=self.user_sem_login, create_user=self.admin)
        self.url = reverse('register:list_conguser')

    def test_lista_mostra_ultimo_acesso_no_lugar_de_data_de_criacao(self):
        self.client.login(username='admin', password='senha')
        response = self.client.get(self.url)
        self.assertContains(response, 'Último acesso')
        self.assertNotContains(response, 'Data de criação')
        self.assertContains(response, '2 de Junho de 2026')

    def test_usuario_sem_ultimo_acesso_mostra_celula_em_branco(self):
        self.client.login(username='admin', password='senha')
        response = self.client.get(self.url, {'user': self.user_sem_login.id})
        content = response.content.decode('utf-8')
        self.assertIn('<td>usuario_sem_login</td>', content)
        self.assertIn('<td></td>', content)

    def test_filtros_de_congregacao_e_usuario_continuam_funcionando(self):
        self.client.login(username='admin', password='senha')
        response = self.client.get(self.url, {'cong': self.cong_a.id, 'user': self.user_com_login.id})
        self.assertContains(response, 'usuario_login')
        self.assertNotIn('<td>usuario_sem_login</td>', response.content.decode('utf-8'))


class DashboardTests(TestCase):
    def setUp(self):
        self.cong_a = Cong.objects.create(nome='Congregação A', numero=1)
        self.cong_b = Cong.objects.create(nome='Congregação B', numero=2)
        self.staff = User.objects.create_superuser(username='staff_dashboard', password='senha')
        self.user = User.objects.create_user(username='user_dashboard', password='senha')
        CongUser.objects.create(cong=self.cong_a, user=self.user)
        self.meses = [datetime.date(2025, 12, 1), datetime.date(2026, 1, 1), datetime.date(2026, 2, 1), datetime.date(2026, 3, 1), datetime.date(2026, 4, 1), datetime.date(2026, 5, 1)]
        self.url = reverse('register:index')

    def criar_publicador(self, nome, congregacao, tipo=0, situacao=1):
        return Publicadores.objects.create(
            nome=nome,
            endereco='Endereço',
            esperanca=0,
            privilegio=0,
            tipo=tipo,
            sexo=0,
            situacao=situacao,
            classe='0',
            cong=congregacao,
        )

    def criar_relatorio(self, publicador, mes, tipo=0):
        return Relatorios.objects.create(
            publicador=publicador,
            mes=mes,
            publicacoes=0,
            videos=0,
            horas=1,
            revisitas=0,
            estudos=0,
            tipo=tipo,
        )

    def criar_relatorios_todos_meses(self, publicador, tipo=0):
        for mes in self.meses:
            self.criar_relatorio(publicador, mes, tipo)

    def test_staff_ve_todas_as_congregacoes_com_prioridade_de_classificacao(self):
        regular = self.criar_publicador('Regular', self.cong_a, tipo=2)
        auxiliar = self.criar_publicador('Auxiliar', self.cong_a)
        publicador = self.criar_publicador('Publicador', self.cong_a)
        irregular = self.criar_publicador('Irregular', self.cong_a)
        sem_relatorio = self.criar_publicador('Sem Relatório', self.cong_a)
        outra_cong = self.criar_publicador('Outra Congregação', self.cong_b)
        inativo = self.criar_publicador('Inativo', self.cong_a, situacao=0)
        self.criar_relatorios_todos_meses(regular, tipo=1)
        self.criar_relatorio(auxiliar, self.meses[0], tipo=1)
        self.criar_relatorios_todos_meses(publicador)
        self.criar_relatorio(irregular, self.meses[0], tipo=3)
        self.criar_relatorios_todos_meses(outra_cong)
        self.criar_relatorios_todos_meses(inativo)
        self.client.login(username='staff_dashboard', password='senha')
        with patch('register.views.ultimos_seis_meses_encerrados', return_value=self.meses):
            response = self.client.get(self.url)
        self.assertContains(response, 'Resumo dos últimos 6 meses')
        self.assertContains(response, '12/2025 a 05/2026')
        self.assertEqual(response.context['dashboard_values'], [1, 1, 3, 1])

    def test_usuario_comum_ve_apenas_sua_congregacao(self):
        publicador_a = self.criar_publicador('Publicador A', self.cong_a)
        publicador_b = self.criar_publicador('Publicador B', self.cong_b)
        self.criar_relatorios_todos_meses(publicador_a)
        self.criar_relatorios_todos_meses(publicador_b)
        self.client.login(username='user_dashboard', password='senha')
        with patch('register.views.ultimos_seis_meses_encerrados', return_value=self.meses):
            response = self.client.get(self.url)
        self.assertEqual(response.context['dashboard_values'], [0, 0, 1, 0])
