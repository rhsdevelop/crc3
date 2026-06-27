import datetime
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from activities.models import Relatorios
from .models import ComissaoServico, Cong, CongUser, Pioneiros, Publicadores


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


class ComissaoServicoTests(TestCase):
    def setUp(self):
        self.cong_a = Cong.objects.create(nome='Congregação A', numero=1)
        self.cong_b = Cong.objects.create(nome='Congregação B', numero=2)
        self.staff = User.objects.create_superuser(username='staff_comissao', password='senha')
        self.user = User.objects.create_user(username='user_comissao', password='senha')
        self.user.user_permissions.add(
            Permission.objects.get(codename='view_publicadores'),
            Permission.objects.get(codename='view_comissaoservico'),
            Permission.objects.get(codename='change_comissaoservico'),
        )
        CongUser.objects.create(cong=self.cong_a, user=self.user)
        self.url = reverse('register:list_comissao_servico')

    def test_usuario_comum_ve_menu_e_apenas_comissao_da_sua_congregacao(self):
        ComissaoServico.objects.create(cong=self.cong_b, coordenador='Outra Congregação')
        self.client.login(username='user_comissao', password='senha')

        response = self.client.get(self.url)

        self.assertContains(response, 'Comissão de Serviço')
        self.assertContains(response, 'Congregação A')
        self.assertNotContains(response, 'Congregação B')
        self.assertTrue(ComissaoServico.objects.filter(cong=self.cong_a).exists())

    def test_edita_assinaturas_da_comissao(self):
        comissao = ComissaoServico.objects.create(cong=self.cong_a)
        self.client.login(username='staff_comissao', password='senha')

        response = self.client.post(reverse('register:edit_comissao_servico', args=[comissao.id]), {
            'cong': self.cong_a.id,
            'coordenador': 'Coordenador Atual',
            'superintendente_servico': 'Superintendente Atual',
            'secretario': 'Secretário Atual',
        })

        self.assertRedirects(response, '/comissao-servico/list/')
        comissao.refresh_from_db()
        self.assertEqual(comissao.coordenador, 'Coordenador Atual')
        self.assertEqual(comissao.superintendente_servico, 'Superintendente Atual')
        self.assertEqual(comissao.secretario, 'Secretário Atual')


class PioneirosReturnUrlTests(TestCase):
    def setUp(self):
        self.cong = Cong.objects.create(nome='Congregação', numero=1)
        self.outra_cong = Cong.objects.create(nome='Outra Congregação', numero=2)
        self.user = User.objects.create_superuser(username='staff_pioneiros', password='senha')
        self.publicador = Publicadores.objects.create(
            nome='Joao',
            endereco='Endereço',
            esperanca=0,
            privilegio=0,
            tipo=0,
            sexo=0,
            situacao=1,
            classe='0',
            cong=self.cong,
        )
        self.pioneiro = Pioneiros.objects.create(
            publicador=self.publicador,
            mes=datetime.date(2026, 5, 1),
            observacao='Teste',
            create_user=self.user,
            assign_user=self.user,
        )
        self.client.login(username='staff_pioneiros', password='senha')

    def test_listagem_envia_url_atual_como_next_nos_links(self):
        response = self.client.get(reverse('register:list_pioneiros'), {
            'publicador': self.publicador.id,
            'mes': '2026-05',
            'foo': 'bar',
        })

        next_url = '/pioneiros/list/%%3Fpublicador%%3D%s%%26mes%%3D2026-05%%26foo%%3Dbar' % self.publicador.id
        self.assertContains(response, '/pioneiros/add/?next=%s' % next_url)
        self.assertContains(response, '/pioneiros/%s/delete/?next=%s' % (self.pioneiro.id, next_url))
        self.assertContains(response, '/pioneiros/%s/peticao/' % self.pioneiro.id)

    def test_tela_de_add_mantem_next_no_formulario(self):
        next_url = '/pioneiros/list/?publicador=%s&mes=2026-05&foo=bar' % self.publicador.id
        response = self.client.get(reverse('register:add_pioneiros'), {'next': next_url})

        self.assertContains(response, '<input type="hidden" name="next" value="%s">' % next_url, html=True)

    def test_add_pioneiro_redireciona_para_next_interno_com_filtros(self):
        next_url = '/pioneiros/list/?publicador=%s&mes=2026-05&foo=bar' % self.publicador.id
        response = self.client.post(reverse('register:add_pioneiros'), {
            'publicador': self.publicador.id,
            'mes': '2026-06',
            'observacao': 'Novo',
            'next': next_url,
        })

        self.assertRedirects(response, next_url, fetch_redirect_response=False)

    def test_delete_pioneiro_redireciona_para_next_interno_com_filtros(self):
        next_url = '/pioneiros/list/?publicador=%s&mes=2026-05&foo=bar' % self.publicador.id
        response = self.client.get(
            reverse('register:delete_pioneiros', args=[self.pioneiro.id]),
            {'next': next_url},
        )

        self.assertRedirects(response, next_url, fetch_redirect_response=False)

    def test_next_externo_e_ignorado(self):
        response = self.client.post(reverse('register:add_pioneiros'), {
            'publicador': self.publicador.id,
            'mes': '2026-06',
            'observacao': 'Novo',
            'next': 'https://example.com/pioneiros/list/',
        })

        self.assertRedirects(response, '/pioneiros/list/', fetch_redirect_response=False)

    def test_pdf_da_peticao_inclui_dados_do_publicador_mes_e_comissao(self):
        ComissaoServico.objects.create(
            cong=self.cong,
            coordenador='Coordenador Teste',
            superintendente_servico='Superintendente Teste',
            secretario='Secretario Teste',
        )

        response = self.client.get(reverse('register:peticao_pioneiro_auxiliar', args=[self.pioneiro.id]))

        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(
            response['Content-Disposition'],
            'inline; filename=peticao-pioneiro-auxiliar-%s.pdf' % self.pioneiro.id,
        )
        self.assertTrue(response.content.startswith(b'%PDF'))
        self.assertIn(b'05/2026', response.content)
        self.assertIn(b'Teste', response.content)
        self.assertIn(b'Joao', response.content)
        self.assertIn(b'Coordenador Teste', response.content)
        self.assertIn(b'Secretario Teste', response.content)

    def test_pdf_da_peticao_funciona_sem_comissao_cadastrada(self):
        response = self.client.get(reverse('register:peticao_pioneiro_auxiliar', args=[self.pioneiro.id]))

        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_usuario_comum_nao_imprime_peticao_de_outra_congregacao(self):
        usuario = User.objects.create_user(username='usuario_pioneiros', password='senha')
        usuario.user_permissions.add(Permission.objects.get(codename='view_pioneiros'))
        CongUser.objects.create(user=usuario, cong=self.cong)
        publicador_outra = Publicadores.objects.create(
            nome='Publicador Outra',
            endereco='Endereço',
            esperanca=0,
            privilegio=0,
            tipo=0,
            sexo=0,
            situacao=1,
            classe='0',
            cong=self.outra_cong,
        )
        pioneiro_outra = Pioneiros.objects.create(
            publicador=publicador_outra,
            mes=datetime.date(2026, 5, 1),
            observacao='Outra',
            create_user=self.user,
            assign_user=self.user,
        )

        self.client.login(username='usuario_pioneiros', password='senha')
        response = self.client.get(reverse('register:peticao_pioneiro_auxiliar', args=[pioneiro_outra.id]))

        self.assertEqual(response.status_code, 404)
