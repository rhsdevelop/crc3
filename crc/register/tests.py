import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Cong, CongUser


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
