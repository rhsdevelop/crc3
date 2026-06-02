import datetime

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from register.models import Cong, CongUser, Grupos, Publicadores
from .models import Relatorios
from .views import periodo_ano_servico


class ResumoPioneirosRegularesTests(TestCase):
    def setUp(self):
        self.cong_a = Cong.objects.create(nome='Congregação A', numero=1)
        self.cong_b = Cong.objects.create(nome='Congregação B', numero=2)
        self.grupo_a = Grupos.objects.create(grupo='Grupo A', dirigente='Dirigente A', cong=self.cong_a)
        self.grupo_b = Grupos.objects.create(grupo='Grupo B', dirigente='Dirigente B', cong=self.cong_b)
        self.user = User.objects.create_user(username='usuario', password='senha')
        self.user.user_permissions.add(Permission.objects.get(codename='view_relatorios'))
        CongUser.objects.create(user=self.user, cong=self.cong_a)
        self.staff = User.objects.create_superuser(username='staff', password='senha')
        self.pioneiro_a = self.criar_publicador('Pioneiro A', self.cong_a, self.grupo_a)
        self.pioneiro_sem_horas = self.criar_publicador('Pioneiro Sem Horas', self.cong_a, self.grupo_a)
        self.pioneiro_b = self.criar_publicador('Pioneiro B', self.cong_b, self.grupo_b)
        self.criar_publicador('Pioneiro Inativo', self.cong_a, self.grupo_a, situacao=0)
        self.criar_publicador('Publicador Comum', self.cong_a, self.grupo_a, tipo=0)
        self.criar_relatorio(self.pioneiro_a, datetime.date(2025, 9, 1), 10)
        self.criar_relatorio(self.pioneiro_a, datetime.date(2025, 9, 1), 5)
        self.criar_relatorio(self.pioneiro_a, datetime.date(2025, 10, 1), 12)
        self.criar_relatorio(self.pioneiro_a, datetime.date(2025, 8, 1), 99)
        self.criar_relatorio(self.pioneiro_b, datetime.date(2025, 9, 1), 620)
        self.url = reverse('activities:resumo_pioneiros_regulares')

    def criar_publicador(self, nome, congregacao, grupo, tipo=2, situacao=1):
        return Publicadores.objects.create(
            nome=nome,
            endereco='Endereço',
            esperanca=0,
            privilegio=0,
            tipo=tipo,
            sexo=0,
            situacao=situacao,
            classe='0',
            grupo=grupo,
            cong=congregacao,
        )

    def criar_relatorio(self, publicador, mes, horas):
        return Relatorios.objects.create(
            publicador=publicador,
            mes=mes,
            publicacoes=0,
            videos=0,
            horas=horas,
            revisitas=0,
            estudos=0,
            tipo=2,
        )

    def test_periodo_padrao_usa_ano_de_servico(self):
        self.assertEqual(periodo_ano_servico(datetime.date(2026, 6, 2)), ('2025-09', '2026-08'))
        self.assertEqual(periodo_ano_servico(datetime.date(2026, 9, 1)), ('2026-09', '2027-08'))

    def test_usuario_comum_ve_apenas_sua_congregacao_e_total_zero(self):
        self.client.login(username='usuario', password='senha')
        response = self.client.get(self.url, {'congregacao': self.cong_b.id})
        self.assertContains(response, 'Pioneiro A')
        self.assertContains(response, 'Pioneiro Sem Horas')
        self.assertNotContains(response, 'Pioneiro B')
        self.assertNotContains(response, 'Pioneiro Inativo')
        self.assertNotContains(response, 'Publicador Comum')
        self.assertNotContains(response, 'name="congregacao"')
        self.assertContains(response, '<td>27</td>', html=True)
        self.assertContains(response, '<td>2</td>', html=True)
        self.assertContains(response, '<td>14</td>', html=True)
        self.assertContains(response, '<td>573</td>', html=True)
        self.assertContains(response, '<td>0</td>', count=3, html=True)
        self.assertContains(response, '<td>600</td>', html=True)

    def test_staff_filtra_congregacao_grupo_publicador_e_periodo(self):
        self.client.login(username='staff', password='senha')
        response = self.client.get(self.url, {
            'congregacao': self.cong_b.id,
            'grupo': self.grupo_b.id,
            'publicador': 'Pioneiro B',
            'mes_inicio': '2025-09',
            'mes_fim': '2026-08',
        })
        self.assertContains(response, 'name="congregacao"')
        self.assertContains(response, 'Pioneiro B')
        self.assertContains(response, '<td>620</td>', html=True)
        self.assertContains(response, '<td>1</td>', html=True)
        self.assertContains(response, '<td>-20</td>', html=True)
        self.assertNotContains(response, 'Pioneiro A')

    def test_usuario_comum_nao_vaza_dados_ao_informar_grupo_de_outra_congregacao(self):
        self.client.login(username='usuario', password='senha')
        response = self.client.get(self.url, {'grupo': self.grupo_b.id})
        self.assertNotContains(response, 'Pioneiro B')

    def test_exportacao_csv_respeita_filtros_e_inclui_metricas(self):
        self.client.login(username='staff', password='senha')
        response = self.client.get(self.url, {
            'congregacao': self.cong_b.id,
            'mes_inicio': '2025-09',
            'mes_fim': '2026-08',
            'export': 'csv',
        })
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename=resumo-pioneiros-regulares.csv')
        content = response.content.decode('utf-8')
        self.assertIn('Publicador;Grupo de serviço;Congregação;Horas;Meses;Média;Saldo', content)
        self.assertIn('Pioneiro B;Grupo B;Congregação B (2);620;1;620;-20', content)
        self.assertNotIn('Pioneiro A', content)

    def test_exportacao_csv_de_usuario_comum_nao_vaza_outra_congregacao(self):
        self.client.login(username='usuario', password='senha')
        response = self.client.get(self.url, {
            'congregacao': self.cong_b.id,
            'mes_inicio': '2025-09',
            'mes_fim': '2026-08',
            'export': 'csv',
        })
        content = response.content.decode('utf-8')
        self.assertIn('Pioneiro A;Grupo A;Congregação A (1);27;2;14;573', content)
        self.assertNotIn('Pioneiro B', content)
