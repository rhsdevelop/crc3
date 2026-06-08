import datetime

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from register.models import Cong, CongUser

from .models import TarefaSecretario


class TarefaSecretarioTests(TestCase):
    def setUp(self):
        self.cong_a = Cong.objects.create(nome='Congregação A', numero=1)
        self.cong_b = Cong.objects.create(nome='Congregação B', numero=2)
        self.user_a = User.objects.create_user(username='secretario_a', password='senha')
        self.user_b = User.objects.create_user(username='secretario_b', password='senha')
        self.staff = User.objects.create_superuser(username='staff_agenda', password='senha')
        CongUser.objects.create(cong=self.cong_a, user=self.user_a)
        CongUser.objects.create(cong=self.cong_b, user=self.user_b)
        perms = Permission.objects.filter(content_type__app_label='agenda')
        self.user_a.user_permissions.set(perms)
        self.user_b.user_permissions.set(perms)
        self.list_url = reverse('agenda:list_tarefas_secretario')

    def criar_tarefa(self, titulo, cong, **kwargs):
        dados = {
            'descricao': 'Descrição da tarefa',
            'tipo_recorrencia': 'mensal',
            'categoria': 'relatorios',
            'status': 'pendente',
            'prioridade': 'media',
            'ano_referencia': 2026,
            'mes_referencia': 6,
            'data_limite': datetime.date(2026, 6, 30),
            'cong': cong,
        }
        dados.update(kwargs)
        return TarefaSecretario.objects.create(titulo=titulo, **dados)

    def test_lista_carrega_para_usuario_com_permissao(self):
        self.client.login(username='secretario_a', password='senha')

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestão de Tarefas')

    def test_criacao_manual_vincula_congregacao_do_usuario(self):
        self.client.login(username='secretario_a', password='senha')

        response = self.client.post(reverse('agenda:add_tarefa_secretario'), {
            'titulo': 'Enviar relatório',
            'descricao': 'Enviar relatório mensal',
            'tipo_recorrencia': 'mensal',
            'categoria': 'relatorios',
            'mes_referencia': 6,
            'ano_referencia': 2026,
            'data_prevista': '2026-06-05',
            'data_limite': '2026-06-10',
            'status': 'pendente',
            'prioridade': 'alta',
            'observacoes': '',
            'data_conclusao': '',
        })

        self.assertRedirects(response, '/agenda/tarefas/', fetch_redirect_response=False)
        tarefa = TarefaSecretario.objects.get(titulo='Enviar relatório')
        self.assertEqual(tarefa.cong, self.cong_a)

    def test_filtros_por_status_categoria_recorrencia_referencia_e_busca(self):
        self.criar_tarefa('Relatório mensal', self.cong_a, categoria='relatorios', tipo_recorrencia='mensal', status='pendente', mes_referencia=6, ano_referencia=2026)
        self.criar_tarefa('Arquivo anual', self.cong_a, categoria='arquivo', tipo_recorrencia='anual', status='concluida', mes_referencia=None, ano_referencia=2026)
        self.client.login(username='secretario_a', password='senha')

        response = self.client.get(self.list_url, {
            'status': 'pendente',
            'categoria': 'relatorios',
            'tipo_recorrencia': 'mensal',
            'mes_referencia': 6,
            'ano_referencia': 2026,
            'busca': 'mensal',
            'ordenacao': 'data_limite',
        })

        self.assertContains(response, 'Relatório mensal')
        self.assertNotContains(response, 'Arquivo anual')

    def test_detalhe_e_edicao_respeitam_congregacao(self):
        tarefa_a = self.criar_tarefa('Tarefa A', self.cong_a)
        tarefa_b = self.criar_tarefa('Tarefa B', self.cong_b)
        self.client.login(username='secretario_a', password='senha')

        response = self.client.get(reverse('agenda:view_tarefa_secretario', args=[tarefa_a.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tarefa A')

        response = self.client.get(reverse('agenda:view_tarefa_secretario', args=[tarefa_b.id]))
        self.assertEqual(response.status_code, 404)

        response = self.client.post(reverse('agenda:edit_tarefa_secretario', args=[tarefa_a.id]), {
            'titulo': 'Tarefa A editada',
            'descricao': 'Descrição editada',
            'tipo_recorrencia': 'mensal',
            'categoria': 'relatorios',
            'mes_referencia': 6,
            'ano_referencia': 2026,
            'data_prevista': '',
            'data_limite': '2026-06-30',
            'status': 'em_andamento',
            'prioridade': 'alta',
            'observacoes': '',
            'data_conclusao': '',
        })
        self.assertRedirects(response, '/agenda/tarefas/', fetch_redirect_response=False)
        tarefa_a.refresh_from_db()
        self.assertEqual(tarefa_a.titulo, 'Tarefa A editada')
        self.assertEqual(tarefa_a.cong, self.cong_a)

    def test_concluir_tarefa_preenche_status_e_data(self):
        tarefa = self.criar_tarefa('Concluir tarefa', self.cong_a)
        self.client.login(username='secretario_a', password='senha')

        response = self.client.post(reverse('agenda:concluir_tarefa_secretario', args=[tarefa.id]))

        self.assertRedirects(response, '/agenda/tarefas/', fetch_redirect_response=False)
        tarefa.refresh_from_db()
        self.assertEqual(tarefa.status, 'concluida')
        self.assertEqual(tarefa.data_conclusao, datetime.date.today())

    def test_carregar_tarefas_base_nao_duplica(self):
        self.client.login(username='secretario_a', password='senha')
        url = reverse('agenda:carregar_tarefas_base_secretario')

        self.client.post(url)
        primeira_contagem = TarefaSecretario.objects.filter(cong=self.cong_a).count()
        self.client.post(url)

        self.assertGreater(primeira_contagem, 0)
        self.assertEqual(TarefaSecretario.objects.filter(cong=self.cong_a).count(), primeira_contagem)

    def test_staff_carrega_tarefas_base_para_congregacao_escolhida(self):
        self.client.login(username='staff_agenda', password='senha')

        response = self.client.post(reverse('agenda:carregar_tarefas_base_secretario'), {
            'cong': self.cong_b.id,
        })

        self.assertRedirects(response, '/agenda/tarefas/', fetch_redirect_response=False)
        self.assertEqual(TarefaSecretario.objects.filter(cong=self.cong_a).count(), 0)
        self.assertGreater(TarefaSecretario.objects.filter(cong=self.cong_b).count(), 0)
