import datetime
import re
from unittest.mock import patch

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from register.models import Cong, CongUser, Grupos, Pioneiros, Publicadores
from .models import Relatorios
from .views import calcular_idade, data_nascimento_idade_minima, periodo_ano_servico, periodo_ultimos_seis_meses


class ResumoPioneirosRegularesTests(TestCase):
    def setUp(self):
        self.cong_a = Cong.objects.create(nome='Congregação A', numero=1)
        self.cong_b = Cong.objects.create(nome='Congregação B', numero=2)
        self.grupo_a = Grupos.objects.create(grupo='Grupo A', dirigente='Dirigente A', cong=self.cong_a)
        self.grupo_b = Grupos.objects.create(grupo='Grupo B', dirigente='Dirigente B', cong=self.cong_b)
        self.user = User.objects.create_user(username='usuario', password='senha')
        self.user.user_permissions.add(Permission.objects.get(codename='view_relatorios'))
        self.user.user_permissions.add(Permission.objects.get(codename='add_relatorios'))
        CongUser.objects.create(user=self.user, cong=self.cong_a)
        self.staff = User.objects.create_superuser(username='staff', password='senha')
        self.pioneiro_a = self.criar_publicador('Pioneiro A', self.cong_a, self.grupo_a)
        self.pioneiro_sem_horas = self.criar_publicador('Pioneiro Sem Horas', self.cong_a, self.grupo_a)
        self.pioneiro_b = self.criar_publicador('Pioneiro B', self.cong_b, self.grupo_b)
        self.criar_publicador('Pioneiro Inativo', self.cong_a, self.grupo_a, situacao=0)
        self.publicador_comum = self.criar_publicador('Publicador Comum', self.cong_a, self.grupo_a, tipo=0)
        self.pioneiro_auxiliar = self.criar_publicador('Pioneiro Auxiliar', self.cong_a, self.grupo_a, tipo=0)
        Pioneiros.objects.create(publicador=self.pioneiro_auxiliar, mes=datetime.date(2026, 1, 1))
        self.criar_relatorio(self.pioneiro_a, datetime.date(2025, 9, 1), 10, credito_horas=3)
        self.criar_relatorio(self.pioneiro_a, datetime.date(2025, 9, 1), 5, credito_horas=2)
        self.criar_relatorio(self.pioneiro_a, datetime.date(2025, 10, 1), 12)
        self.criar_relatorio(self.pioneiro_a, datetime.date(2025, 8, 1), 99)
        self.criar_relatorio(self.pioneiro_b, datetime.date(2025, 9, 1), 620, credito_horas=30)
        self.url = reverse('activities:resumo_pioneiros_regulares')
        self.add_url = reverse('activities:add_relatorios')

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

    def criar_relatorio(self, publicador, mes, horas, tipo=2, credito_horas=0):
        return Relatorios.objects.create(
            publicador=publicador,
            mes=mes,
            publicacoes=0,
            videos=0,
            horas=horas,
            credito_horas=credito_horas,
            revisitas=0,
            estudos=0,
            tipo=tipo,
        )

    def test_periodo_padrao_usa_ano_de_servico(self):
        self.assertEqual(periodo_ano_servico(datetime.date(2026, 6, 2)), ('2025-09', '2026-08'))
        self.assertEqual(periodo_ano_servico(datetime.date(2026, 9, 1)), ('2026-09', '2027-08'))

    def test_lancamento_exibe_salva_e_atualiza_credito_de_horas(self):
        self.client.login(username='usuario', password='senha')

        response = self.client.get(self.add_url)
        self.assertContains(response, 'Crédito (Horas)')

        dados = {
            'publicador': self.pioneiro_a.id,
            'tipo': 2,
            'mes': '2026-01',
            'presente': 'on',
            'horas': 40,
            'credito_horas': 10,
            'estudos': 1,
            'observacao': 'Crédito registrado na observação.',
            'atv_local': 'on',
        }
        response = self.client.post(self.add_url, dados)
        self.assertRedirects(response, self.add_url)
        relatorio = Relatorios.objects.get(publicador=self.pioneiro_a, mes=datetime.date(2026, 1, 1))
        self.assertEqual(relatorio.credito_horas, 10)

        dados['credito_horas'] = 15
        response = self.client.post(self.add_url, dados)
        self.assertRedirects(response, self.add_url)
        relatorio.refresh_from_db()
        self.assertEqual(relatorio.credito_horas, 15)

    def test_campos_e_gravacao_respeitam_tipo_do_publicador(self):
        self.client.login(username='usuario', password='senha')

        resposta_regular = self.client.get(self.add_url, {
            'publicador': self.pioneiro_a.id,
            'mes': '2026-01',
        })
        resposta_auxiliar = self.client.get(self.add_url, {
            'publicador': self.pioneiro_auxiliar.id,
            'mes': '2026-01',
        })
        resposta_publicador = self.client.get(self.add_url, {
            'publicador': self.publicador_comum.id,
            'mes': '2026-01',
        })
        self.assertEqual(resposta_regular.json(), [[2, 'Pioneiro Regular']])
        self.assertEqual(resposta_auxiliar.json(), [[1, 'Pioneiro Auxiliar']])
        self.assertEqual(resposta_publicador.json(), [[0, 'Publicador']])

        dados = {
            'publicador': self.pioneiro_auxiliar.id,
            'tipo': 2,
            'mes': '2026-01',
            'presente': 'on',
            'horas': 20,
            'credito_horas': 10,
            'estudos': 0,
            'observacao': '',
            'atv_local': 'on',
        }
        self.client.post(self.add_url, dados)
        relatorio_auxiliar = Relatorios.objects.get(
            publicador=self.pioneiro_auxiliar,
            mes=datetime.date(2026, 1, 1),
        )
        self.assertEqual(relatorio_auxiliar.tipo, 1)
        self.assertEqual(relatorio_auxiliar.horas, 20)
        self.assertEqual(relatorio_auxiliar.credito_horas, 0)

        dados.update({'publicador': self.publicador_comum.id, 'horas': 20, 'credito_horas': 10})
        self.client.post(self.add_url, dados)
        relatorio_publicador = Relatorios.objects.get(
            publicador=self.publicador_comum,
            mes=datetime.date(2026, 1, 1),
        )
        self.assertEqual(relatorio_publicador.tipo, 0)
        self.assertEqual(relatorio_publicador.horas, 0)
        self.assertEqual(relatorio_publicador.credito_horas, 0)

    def test_usuario_comum_ve_apenas_sua_congregacao_e_total_zero(self):
        self.client.login(username='usuario', password='senha')
        response = self.client.get(self.url, {
            'congregacao': self.cong_b.id,
            'mes_inicio': '2025-09',
            'mes_fim': '2026-08',
        })
        self.assertContains(response, 'Pioneiro A')
        self.assertContains(response, 'Pioneiro Sem Horas')
        self.assertNotContains(response, 'Pioneiro B')
        self.assertNotContains(response, 'Pioneiro Inativo')
        self.assertNotContains(response, 'Publicador Comum')
        self.assertNotContains(response, 'name="congregacao"')
        self.assertContains(response, '<td>27</td>', html=True)
        self.assertContains(response, '<td>5</td>', html=True)
        self.assertContains(response, '<td>2</td>', html=True)
        self.assertContains(response, '<td>16</td>', html=True)
        self.assertContains(response, '<td>568</td>', html=True)
        self.assertContains(response, '<td>0</td>', count=4, html=True)
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
        self.assertContains(response, '<td>30</td>', html=True)
        self.assertContains(response, '<td>1</td>', html=True)
        self.assertContains(response, '<td>650</td>', html=True)
        self.assertContains(response, '<td>-50</td>', html=True)
        self.assertNotContains(response, 'Pioneiro A')

    def test_considera_apenas_meses_como_pioneiro_regular(self):
        pioneiro_meio_periodo = self.criar_publicador('Pioneiro Meio Período', self.cong_a, self.grupo_a)
        self.criar_relatorio(pioneiro_meio_periodo, datetime.date(2025, 9, 1), 5, tipo=0, credito_horas=100)
        self.criar_relatorio(pioneiro_meio_periodo, datetime.date(2025, 10, 1), 20, tipo=1, credito_horas=100)
        self.criar_relatorio(pioneiro_meio_periodo, datetime.date(2025, 11, 1), 50, tipo=2, credito_horas=5)
        self.criar_relatorio(pioneiro_meio_periodo, datetime.date(2025, 12, 1), 60, tipo=2, credito_horas=5)

        self.client.login(username='usuario', password='senha')
        response = self.client.get(self.url, {
            'publicador': 'Pioneiro Meio Período',
            'mes_inicio': '2025-09',
            'mes_fim': '2026-08',
        })

        self.assertContains(response, 'Pioneiro Meio Período')
        self.assertContains(response, '<td>110</td>', html=True)
        self.assertContains(response, '<td>10</td>', html=True)
        self.assertContains(response, '<td>2</td>', html=True)
        self.assertContains(response, '<td>60</td>', html=True)
        self.assertContains(response, '<td>480</td>', html=True)

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
        self.assertIn('Publicador;Grupo de serviço;Congregação;Horas;Crédito;Meses;Média;Saldo', content)
        self.assertIn('Pioneiro B;Grupo B;Congregação B (2);620;30;1;650;-50', content)
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
        self.assertIn('Pioneiro A;Grupo A;Congregação A (1);27;5;2;16;568', content)
        self.assertNotIn('Pioneiro B', content)


class AnaliseTests(TestCase):
    def setUp(self):
        self.cong_a = Cong.objects.create(nome='Congregação A', numero=1)
        self.cong_b = Cong.objects.create(nome='Congregação B', numero=2)
        self.grupo_a = Grupos.objects.create(grupo='Grupo A', dirigente='Dirigente A', cong=self.cong_a)
        self.grupo_b = Grupos.objects.create(grupo='Grupo B', dirigente='Dirigente B', cong=self.cong_b)
        self.user = User.objects.create_user(username='usuario_analise', password='senha')
        self.user.user_permissions.add(Permission.objects.get(codename='view_relatorios'))
        CongUser.objects.create(user=self.user, cong=self.cong_a)
        self.staff = User.objects.create_superuser(username='staff_analise', password='senha')
        self.url = reverse('activities:analise')

    def criar_publicador(self, nome, congregacao, grupo, tipo=0, sexo=0, privilegio=0, situacao=1, nascimento=None):
        return Publicadores.objects.create(
            nome=nome,
            endereco='Endereço',
            nascimento=nascimento,
            esperanca=0,
            privilegio=privilegio,
            tipo=tipo,
            sexo=sexo,
            situacao=situacao,
            classe='0',
            grupo=grupo,
            cong=congregacao,
        )

    def criar_relatorio(self, publicador, mes, tipo=0, estudos=0, horas=0):
        return Relatorios.objects.create(
            publicador=publicador,
            mes=mes,
            publicacoes=0,
            videos=0,
            horas=horas,
            revisitas=0,
            estudos=estudos,
            tipo=tipo,
        )

    def assertLinha(self, response, nome, privilegio, pioneiro_regular, pioneiro_auxiliar, estudos, dirige_estudos):
        content = response.content.decode('utf-8')
        pattern = (
            r'<th scope="row">%s</th>\s*'
            r'<td>[^<]*</td>\s*'
            r'<td>%s</td>\s*'
            r'<td>%s</td>\s*'
            r'<td>%s</td>\s*'
            r'<td>%s</td>\s*'
            r'<td>%s</td>'
        ) % (
            re.escape(nome),
            re.escape(privilegio),
            re.escape(pioneiro_regular),
            re.escape(str(pioneiro_auxiliar)),
            re.escape(str(estudos)),
            re.escape(dirige_estudos),
        )
        self.assertRegex(content, pattern)

    def test_periodo_padrao_usa_seis_meses_encerrados(self):
        self.assertEqual(periodo_ultimos_seis_meses(datetime.date(2026, 6, 15)), ('2025-12', '2026-05'))
        self.assertEqual(periodo_ultimos_seis_meses(datetime.date(2026, 1, 10)), ('2025-07', '2025-12'))

    def test_calcula_idade(self):
        self.assertEqual(calcular_idade(datetime.date(2000, 6, 14), datetime.date(2026, 6, 15)), 26)
        self.assertEqual(calcular_idade(datetime.date(2000, 6, 16), datetime.date(2026, 6, 15)), 25)
        self.assertEqual(calcular_idade(None, datetime.date(2026, 6, 15)), '')
        self.assertEqual(data_nascimento_idade_minima(18, datetime.date(2026, 6, 15)), datetime.date(2008, 6, 15))

    @patch('activities.views.periodo_ultimos_seis_meses', return_value=('2025-12', '2026-05'))
    def test_staff_visualiza_todas_congregacoes_e_calculos(self, periodo_mock):
        regular = self.criar_publicador(
            'Regular Ana',
            self.cong_a,
            self.grupo_a,
            tipo=2,
            privilegio=2,
            nascimento=datetime.date(2000, 1, 1),
        )
        auxiliar = self.criar_publicador('Auxiliar Bia', self.cong_a, self.grupo_a, tipo=0, privilegio=1)
        publicador = self.criar_publicador('Publicador Carlos', self.cong_b, self.grupo_b, tipo=0)
        self.criar_publicador('Inativo Daniel', self.cong_a, self.grupo_a, situacao=0)

        self.criar_relatorio(regular, datetime.date(2026, 5, 1), tipo=1, estudos=2)
        self.criar_relatorio(auxiliar, datetime.date(2025, 12, 1), tipo=1, estudos=1)
        self.criar_relatorio(auxiliar, datetime.date(2025, 12, 1), tipo=1, estudos=3)
        self.criar_relatorio(auxiliar, datetime.date(2026, 1, 1), tipo=1, estudos=0)
        self.criar_relatorio(auxiliar, datetime.date(2026, 5, 1), tipo=0, estudos=4)
        self.criar_relatorio(auxiliar, datetime.date(2025, 11, 1), tipo=1, estudos=9)
        self.criar_relatorio(publicador, datetime.date(2026, 5, 1), tipo=0, estudos=0)

        self.client.login(username='staff_analise', password='senha')
        response = self.client.get(self.url)

        self.assertContains(response, 'Regular Ana')
        self.assertContains(response, 'Auxiliar Bia')
        self.assertContains(response, 'Publicador Carlos')
        self.assertNotContains(response, 'Inativo Daniel')
        self.assertContains(response, '<th scope="col">Idade</th>', html=True)
        self.assertContains(response, '<th scope="col">Privilégio</th>', html=True)
        self.assertContains(response, '<td>Ancião</td>', html=True)
        self.assertLinha(response, 'Regular Ana', 'Ancião', 'Sim', '-', 2, 'Sim')
        self.assertLinha(response, 'Auxiliar Bia', 'Servo Ministerial', 'Não', 2, 4, 'Sim')
        self.assertLinha(response, 'Publicador Carlos', 'Publicador', 'Não', 0, 0, 'Não')

    def test_usuario_comum_visualiza_apenas_sua_congregacao(self):
        publicador_a = self.criar_publicador('Publicador Local', self.cong_a, self.grupo_a)
        publicador_b = self.criar_publicador('Publicador Outra Congregação', self.cong_b, self.grupo_b)
        self.criar_relatorio(publicador_a, datetime.date(2026, 5, 1), estudos=1)
        self.criar_relatorio(publicador_b, datetime.date(2026, 5, 1), estudos=1)

        self.client.login(username='usuario_analise', password='senha')
        response = self.client.get(self.url, {'mes_inicio': '2025-12', 'mes_fim': '2026-05'})

        self.assertContains(response, 'Publicador Local')
        self.assertNotContains(response, 'Publicador Outra Congregação')

    def test_filtra_por_grupo_de_servico(self):
        grupo_extra = Grupos.objects.create(grupo='Grupo Extra', dirigente='Dirigente Extra', cong=self.cong_a)
        self.criar_publicador('Publicador Grupo A', self.cong_a, self.grupo_a)
        self.criar_publicador('Publicador Grupo Extra', self.cong_a, grupo_extra)

        self.client.login(username='staff_analise', password='senha')
        response = self.client.get(self.url, {
            'mes_inicio': '2025-12',
            'mes_fim': '2026-05',
            'grupo': grupo_extra.id,
        })

        self.assertContains(response, 'Publicador Grupo Extra')
        self.assertNotContains(response, 'Publicador Grupo A')

    def test_usuario_comum_nao_vaza_dados_ao_informar_grupo_de_outra_congregacao(self):
        self.criar_publicador('Publicador Local', self.cong_a, self.grupo_a)
        self.criar_publicador('Publicador Outra Congregação', self.cong_b, self.grupo_b)

        self.client.login(username='usuario_analise', password='senha')
        response = self.client.get(self.url, {
            'mes_inicio': '2025-12',
            'mes_fim': '2026-05',
            'grupo': self.grupo_b.id,
        })

        self.assertNotContains(response, 'Publicador Local')
        self.assertNotContains(response, 'Publicador Outra Congregação')

    @patch('activities.views.datetime')
    def test_filtra_por_idade_minima(self, datetime_mock):
        datetime_mock.date.today.return_value = datetime.date(2026, 6, 15)
        datetime_mock.date.side_effect = lambda *args, **kwargs: datetime.date(*args, **kwargs)
        datetime_mock.datetime = datetime.datetime
        datetime_mock.timedelta = datetime.timedelta
        self.criar_publicador(
            'Maior',
            self.cong_a,
            self.grupo_a,
            nascimento=datetime.date(2008, 6, 15),
        )
        self.criar_publicador(
            'Menor',
            self.cong_a,
            self.grupo_a,
            nascimento=datetime.date(2008, 6, 16),
        )
        self.criar_publicador('Sem Nascimento', self.cong_a, self.grupo_a)

        self.client.login(username='staff_analise', password='senha')
        response = self.client.get(self.url, {
            'mes_inicio': '2025-12',
            'mes_fim': '2026-05',
            'idade_minima': '18',
        })

        self.assertContains(response, 'Maior')
        self.assertNotContains(response, 'Menor')
        self.assertNotContains(response, 'Sem Nascimento')

    @patch('activities.views.datetime')
    def test_exportacao_csv_respeita_filtros_e_inclui_dados_da_tabela(self, datetime_mock):
        datetime_mock.date.today.return_value = datetime.date(2026, 6, 15)
        datetime_mock.date.side_effect = lambda *args, **kwargs: datetime.date(*args, **kwargs)
        datetime_mock.datetime = datetime.datetime
        datetime_mock.timedelta = datetime.timedelta
        incluido = self.criar_publicador(
            'CSV Incluído',
            self.cong_a,
            self.grupo_a,
            privilegio=1,
            nascimento=datetime.date(1990, 6, 15),
        )
        excluido = self.criar_publicador(
            'CSV Excluído',
            self.cong_a,
            self.grupo_a,
            nascimento=datetime.date(2010, 6, 15),
        )
        self.criar_relatorio(incluido, datetime.date(2026, 5, 1), tipo=1, estudos=2)
        self.criar_relatorio(excluido, datetime.date(2026, 5, 1), tipo=1, estudos=9)

        self.client.login(username='staff_analise', password='senha')
        response = self.client.get(self.url, {
            'mes_inicio': '2025-12',
            'mes_fim': '2026-05',
            'idade_minima': '18',
            'export': 'csv',
        })

        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename=analise-publicadores.csv')
        self.assertTrue(response.content.startswith(b'\xef\xbb\xbf'))
        content = response.content.decode('utf-8')
        self.assertIn('Publicador;Idade;Privilégio;Pioneiro Regular;Pioneiro Auxiliar;Estudos;Dirige estudos', content)
        self.assertIn('CSV Incluído;36;Servo Ministerial;Não;1;2;Sim', content)
        self.assertNotIn('CSV Excluído', content)

    def test_filtros_multiplos_de_sexo_tipo_privilegio(self):
        incluido = self.criar_publicador(
            'Incluído',
            self.cong_a,
            self.grupo_a,
            tipo=2,
            sexo=1,
            privilegio=2,
        )
        self.criar_publicador('Sexo Excluído', self.cong_a, self.grupo_a, tipo=2, sexo=0, privilegio=2)
        self.criar_publicador('Tipo Excluído', self.cong_a, self.grupo_a, tipo=1, sexo=1, privilegio=2)
        self.criar_publicador('Privilégio Excluído', self.cong_a, self.grupo_a, tipo=2, sexo=1, privilegio=0)
        self.criar_relatorio(incluido, datetime.date(2026, 5, 1), estudos=1)

        self.client.login(username='staff_analise', password='senha')
        response = self.client.get(self.url, {
            'mes_inicio': '2025-12',
            'mes_fim': '2026-05',
            'sexo': ['1'],
            'tipo': ['0', '2'],
            'privilegio': ['1', '2'],
        })

        self.assertContains(response, 'Incluído')
        self.assertContains(response, 'Pioneiro Regular')
        self.assertNotContains(response, '<option value="1">Pioneiro Auxiliar</option>', html=True)
        self.assertNotContains(response, 'Sexo Excluído')
        self.assertNotContains(response, 'Tipo Excluído')
        self.assertNotContains(response, 'Privilégio Excluído')
