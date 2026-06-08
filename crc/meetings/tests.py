import datetime
from io import BytesIO

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import S3ReunioesForm
from .helpers import dias_meio_semana_por_coluna, dias_reuniao_no_mes, imprime_s3_reunioes


class S3ReunioesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='s3_user', password='senha')
        self.client.login(username='s3_user', password='senha')
        self.url = reverse('meetings:s3_reunioes')

    def test_tela_s3_carrega(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gerar relatório')
        self.assertContains(response, 'Nome da congregação')

    def test_parametros_validos_retornam_pdf(self):
        response = self.client.get(self.url, {
            'congregacao': 'Congregação Central',
            'mes_inicial': '2026-06',
            'dia_meio_semana': 2,
            'dia_fim_semana': 6,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="S-3-T-Reunioes.pdf"')
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_exemplo_de_junho_2026_calcula_tres_meses(self):
        meses = [datetime.date(2026, 6, 1), datetime.date(2026, 7, 1), datetime.date(2026, 8, 1)]

        self.assertEqual(dias_reuniao_no_mes(meses[0], 2), [3, 10, 17, 24])
        self.assertEqual(dias_reuniao_no_mes(meses[1], 2), [1, 8, 15, 22, 29])
        self.assertEqual(dias_reuniao_no_mes(meses[2], 2), [5, 12, 19, 26])

    def test_mes_com_quatro_ocorrencias_deixa_quinta_semana_sem_dia(self):
        self.assertEqual(dias_reuniao_no_mes(datetime.date(2026, 6, 1), 2), [3, 10, 17, 24])

    def test_mes_com_cinco_ocorrencias_preenche_quinta_semana(self):
        self.assertEqual(dias_reuniao_no_mes(datetime.date(2026, 7, 1), 2), [1, 8, 15, 22, 29])

    def test_meio_semana_antes_do_fim_semana_comeca_na_primeira_coluna(self):
        dias_meio = [3, 10, 17, 24]
        dias_fim = [7, 14, 21, 28]

        self.assertEqual(dias_meio_semana_por_coluna(dias_meio, dias_fim), [(0, 3), (1, 10), (2, 17), (3, 24)])

    def test_meio_semana_depois_do_fim_semana_comeca_na_segunda_coluna(self):
        dias_meio = [6, 13, 20, 27]
        dias_fim = [3, 10, 17, 24, 31]

        self.assertEqual(dias_meio_semana_por_coluna(dias_meio, dias_fim), [(1, 6), (2, 13), (3, 20), (4, 27)])

    def test_meio_semana_deslocado_com_cinco_ocorrencias_ignora_excedente(self):
        dias_meio = [6, 13, 20, 27, 30]
        dias_fim = [3, 10, 17, 24]

        self.assertEqual(dias_meio_semana_por_coluna(dias_meio, dias_fim), [(1, 6), (2, 13), (3, 20), (4, 27)])

    def test_form_nao_aceita_dias_iguais(self):
        form = S3ReunioesForm({
            'congregacao': 'Congregação Central',
            'mes_inicial': '2026-06',
            'dia_meio_semana': 2,
            'dia_fim_semana': 2,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('Os dias das reuniões não podem ser iguais.', form.non_field_errors())

    def test_helper_gera_pdf_em_memoria(self):
        arquivo = BytesIO()
        imprime_s3_reunioes(arquivo, 'Congregação Central', datetime.date(2026, 6, 1), 2, 6)

        self.assertTrue(arquivo.getvalue().startswith(b'%PDF'))
