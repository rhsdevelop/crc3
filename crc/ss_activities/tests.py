import datetime

from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from register.models import Cong, CongUser, Grupos, Publicadores

from .forms import limites_ano_servico
from .models import (
    CarrinhoTestemunhoPublico,
    ConfiguracaoTestemunhoPublico,
    DesignacaoTestemunhoPublico,
    HabilitacaoTestemunhoPublico,
    LocalTestemunhoPublico,
    PeriodoTestemunhoPublico,
    VisitaGrupo,
    VisitaPastoreio,
    numero_para_letras,
)
from .views import ano_servico_atual, semana_testemunho_publico


class VisitaGrupoTests(TestCase):
    def setUp(self):
        self.cong_a = Cong.objects.create(nome='Congregação A', numero=1)
        self.cong_b = Cong.objects.create(nome='Congregação B', numero=2)
        self.grupo_a1 = Grupos.objects.create(
            grupo='Grupo A1',
            dirigente='Dirigente A1',
            cong=self.cong_a,
        )
        self.grupo_a2 = Grupos.objects.create(
            grupo='Grupo A2',
            dirigente='Dirigente A2',
            cong=self.cong_a,
        )
        self.grupo_b1 = Grupos.objects.create(
            grupo='Grupo B1',
            dirigente='Dirigente B1',
            cong=self.cong_b,
        )
        self.publicador_a1 = self.criar_publicador(
            'Publicador A1',
            self.grupo_a1,
        )
        self.publicador_inativo_a1 = self.criar_publicador(
            'Publicador Inativo A1',
            self.grupo_a1,
            situacao=0,
        )
        self.publicador_mudou_a1 = self.criar_publicador(
            'Publicador Mudou A1',
            self.grupo_a1,
            situacao=2,
        )
        self.publicador_a2 = self.criar_publicador(
            'Publicador A2',
            self.grupo_a2,
        )
        self.servo_a1 = self.criar_publicador(
            'Servo A1',
            self.grupo_a1,
            privilegio=1,
        )
        self.anciao_a2 = self.criar_publicador(
            'Ancião A2',
            self.grupo_a2,
            privilegio=2,
        )
        self.publicador_comum_a2 = self.criar_publicador(
            'Publicador Comum A2',
            self.grupo_a2,
        )
        self.anciao_inativo_a2 = self.criar_publicador(
            'Ancião Inativo A2',
            self.grupo_a2,
            privilegio=2,
            situacao=0,
        )
        self.anciao_b1 = self.criar_publicador(
            'Ancião B1',
            self.grupo_b1,
            privilegio=2,
        )
        self.publicador_b1 = self.criar_publicador(
            'Publicador B1',
            self.grupo_b1,
        )
        self.usuario_a = User.objects.create_user(username='ss_a', password='senha')
        self.usuario_b = User.objects.create_user(username='ss_b', password='senha')
        self.sem_permissao = User.objects.create_user(username='publicador', password='senha')
        self.superuser = User.objects.create_superuser(username='admin_ss', password='senha')
        CongUser.objects.create(cong=self.cong_a, user=self.usuario_a)
        CongUser.objects.create(cong=self.cong_b, user=self.usuario_b)
        CongUser.objects.create(cong=self.cong_a, user=self.sem_permissao)
        permissao = Permission.objects.get(
            content_type__app_label='ss_activities',
            codename='manage_visitas_grupos',
        )
        self.usuario_a.user_permissions.add(permissao)
        self.usuario_b.user_permissions.add(permissao)
        self.list_url = reverse('ss_activities:list_visitas_grupos')
        self.add_url = reverse('ss_activities:add_visita_grupo')

    def criar_publicador(
        self,
        nome,
        grupo,
        privilegio=0,
        situacao=1,
    ):
        return Publicadores.objects.create(
            nome=nome,
            endereco='Endereço de teste',
            esperanca=0,
            privilegio=privilegio,
            tipo=0,
            sexo=0,
            situacao=situacao,
            classe='0',
            grupo=grupo,
            cong=grupo.cong,
        )

    def criar_visita(self, grupo, data_inicio, **kwargs):
        dados = {
            'cong': grupo.cong,
            'grupo': grupo,
            'data_inicio': data_inicio,
            'data_fim': data_inicio + datetime.timedelta(days=6),
        }
        dados.update(kwargs)
        return VisitaGrupo.objects.create(**dados)

    def criar_pastoreio(self, visita, publicador=None, **kwargs):
        dados = {
            'visita_grupo': visita,
            'publicador': publicador or self.publicador_a1,
            'data': visita.data_inicio,
            'assuntos': 'Assuntos de teste',
            'materia': 'Matéria de teste',
            'acompanhante': self.anciao_a2,
        }
        dados.update(kwargs)
        return VisitaPastoreio.objects.create(**dados)

    def post_visita(self, grupo, data_inicio, **kwargs):
        dados = {
            'grupo': grupo.id,
            'data_inicio': data_inicio.isoformat(),
            'ano': 2026,
        }
        dados.update(kwargs)
        return self.client.post(self.add_url, dados)

    def test_permissao_controla_rotas_e_menu(self):
        self.client.force_login(self.sem_permissao)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.get('/')
        self.assertNotContains(response, 'Atividades SS')

        self.client.force_login(self.usuario_a)
        response = self.client.get('/')
        self.assertContains(response, 'Atividades SS')
        self.assertContains(response, 'Visita aos Grupos')

    def test_criacao_calcula_domingo_e_registra_auditoria(self):
        self.client.force_login(self.usuario_a)
        segunda = datetime.date(2026, 9, 7)

        response = self.post_visita(self.grupo_a1, segunda)

        self.assertRedirects(
            response,
            '/ss/visitas-grupos/?ano=2026&cong=%s' % self.cong_a.id,
            fetch_redirect_response=False,
        )
        visita = VisitaGrupo.objects.get()
        self.assertEqual(visita.cong, self.cong_a)
        self.assertEqual(visita.data_fim, datetime.date(2026, 9, 13))
        self.assertEqual(visita.create_user, self.usuario_a)
        self.assertEqual(visita.assign_user, self.usuario_a)
        self.assertFalse(visita.confirmada)
        self.assertFalse(visita.executada)

    def test_data_que_nao_e_segunda_feira_e_recusada_e_modal_reabre(self):
        self.client.force_login(self.usuario_a)

        response = self.post_visita(self.grupo_a1, datetime.date(2026, 9, 8))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A visita deve começar em uma segunda-feira.')
        self.assertContains(response, "$('#visitaModal').modal('show')")
        self.assertEqual(VisitaGrupo.objects.count(), 0)

    def test_modelo_tambem_recusa_inicio_fora_da_segunda_feira(self):
        visita = VisitaGrupo(
            cong=self.cong_a,
            grupo=self.grupo_a1,
            data_inicio=datetime.date(2026, 9, 8),
            data_fim=datetime.date(2026, 9, 14),
        )

        with self.assertRaises(ValidationError):
            visita.save()

    def test_mesma_semana_na_congregacao_e_bloqueada_com_mensagem(self):
        self.client.force_login(self.usuario_a)
        segunda = datetime.date(2026, 9, 7)
        self.post_visita(self.grupo_a1, segunda)

        response = self.post_visita(self.grupo_a2, segunda)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'Já existe uma visita programada para esta congregação nessa semana.',
        )
        self.assertEqual(VisitaGrupo.objects.count(), 1)

    def test_restricao_do_banco_protege_contra_duplicidade_concorrente(self):
        segunda = datetime.date(2026, 9, 7)
        self.criar_visita(self.grupo_a1, segunda)
        duplicada = VisitaGrupo(
            cong=self.cong_a,
            grupo=self.grupo_a2,
            data_inicio=segunda,
            data_fim=segunda + datetime.timedelta(days=6),
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                VisitaGrupo.objects.bulk_create([duplicada])

    def test_congregacoes_diferentes_podem_usar_a_mesma_semana(self):
        segunda = datetime.date(2026, 9, 7)
        self.client.force_login(self.usuario_a)
        self.post_visita(self.grupo_a1, segunda)
        self.client.force_login(self.usuario_b)

        response = self.post_visita(self.grupo_b1, segunda)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(VisitaGrupo.objects.count(), 2)

    def test_mesmo_grupo_pode_receber_visitas_em_semanas_diferentes(self):
        self.client.force_login(self.usuario_a)

        self.post_visita(self.grupo_a1, datetime.date(2026, 9, 7))
        response = self.post_visita(self.grupo_a1, datetime.date(2026, 9, 14))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(VisitaGrupo.objects.filter(grupo=self.grupo_a1).count(), 2)

    def test_executada_confirma_visita_automaticamente(self):
        self.client.force_login(self.usuario_a)

        self.post_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
            executada='on',
        )

        visita = VisitaGrupo.objects.get()
        self.assertTrue(visita.executada)
        self.assertTrue(visita.confirmada)

    def test_listagem_e_cobertura_respeitam_congregacao_e_ano_servico(self):
        visita_ano_anterior = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 8, 31),
        )
        visita_atual = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
            confirmada=True,
        )
        self.criar_visita(
            self.grupo_b1,
            datetime.date(2026, 9, 7),
        )
        self.client.force_login(self.usuario_a)

        response = self.client.get(self.list_url, {'ano': 2026})

        self.assertEqual(response.status_code, 200)
        self.assertIn(visita_atual, response.context['visitas'])
        self.assertNotIn(visita_ano_anterior, response.context['visitas'])
        self.assertNotContains(response, 'Grupo B1')
        self.assertEqual(list(response.context['grupos_sem_visita']), [self.grupo_a2])
        self.assertEqual(response.context['total_programados'], 1)
        self.assertEqual(response.context['total_confirmados'], 1)
        self.assertEqual(response.context['total_executados'], 0)

    def test_edicao_preserva_criador_e_atualiza_responsavel(self):
        criador = User.objects.create_user(username='criador', password='senha')
        visita = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
            create_user=criador,
            assign_user=criador,
        )
        self.client.force_login(self.usuario_a)

        response = self.client.post(
            reverse('ss_activities:edit_visita_grupo', args=[visita.id]),
            {
                'grupo': self.grupo_a2.id,
                'data_inicio': '2026-09-14',
                'confirmada': 'on',
                'ano': 2026,
            },
        )

        self.assertEqual(response.status_code, 302)
        visita.refresh_from_db()
        self.assertEqual(visita.grupo, self.grupo_a2)
        self.assertEqual(visita.data_inicio, datetime.date(2026, 9, 14))
        self.assertEqual(visita.data_fim, datetime.date(2026, 9, 20))
        self.assertEqual(visita.create_user, criador)
        self.assertEqual(visita.assign_user, self.usuario_a)
        self.assertTrue(visita.confirmada)

    def test_usuario_nao_edita_visita_de_outra_congregacao(self):
        visita = self.criar_visita(
            self.grupo_b1,
            datetime.date(2026, 9, 7),
        )
        self.client.force_login(self.usuario_a)

        response = self.client.post(
            reverse('ss_activities:edit_visita_grupo', args=[visita.id]),
            {
                'grupo': self.grupo_a1.id,
                'data_inicio': '2026-09-14',
                'ano': 2026,
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_visita_nao_confirmada_pode_ser_apagada_e_atualiza_cobertura(self):
        visita = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        self.client.force_login(self.usuario_a)

        response = self.client.post(
            reverse('ss_activities:delete_visita_grupo', args=[visita.id]),
            {'ano': 2026},
            follow=True,
        )

        self.assertFalse(VisitaGrupo.objects.filter(pk=visita.id).exists())
        self.assertContains(response, 'Visita apagada com sucesso.')
        self.assertIn(self.grupo_a1, response.context['grupos_sem_visita'])

    def test_visita_confirmada_nao_pode_ser_apagada(self):
        visita = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
            confirmada=True,
        )
        self.client.force_login(self.usuario_a)

        response = self.client.post(
            reverse('ss_activities:delete_visita_grupo', args=[visita.id]),
            {'ano': 2026},
            follow=True,
        )

        self.assertTrue(VisitaGrupo.objects.filter(pk=visita.id).exists())
        self.assertContains(response, 'Uma visita confirmada não pode ser apagada.')

    def test_visita_executada_nao_pode_ser_apagada(self):
        visita = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
            executada=True,
        )
        self.client.force_login(self.usuario_a)

        self.client.post(
            reverse('ss_activities:delete_visita_grupo', args=[visita.id]),
            {'ano': 2026},
        )

        visita.refresh_from_db()
        self.assertTrue(visita.confirmada)
        self.assertTrue(visita.executada)

    def test_botao_apagar_aparece_somente_para_visita_nao_confirmada(self):
        visita_aberta = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        visita_confirmada = self.criar_visita(
            self.grupo_a2,
            datetime.date(2026, 9, 14),
            confirmada=True,
        )
        self.client.force_login(self.usuario_a)

        response = self.client.get(self.list_url, {'ano': 2026})

        self.assertContains(
            response,
            reverse('ss_activities:delete_visita_grupo', args=[visita_aberta.id]),
        )
        self.assertNotContains(
            response,
            reverse('ss_activities:delete_visita_grupo', args=[visita_confirmada.id]),
        )

    def test_endpoint_apagar_exige_post_e_permissao(self):
        visita = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        url = reverse('ss_activities:delete_visita_grupo', args=[visita.id])
        self.client.force_login(self.usuario_a)
        self.assertEqual(self.client.get(url).status_code, 405)

        self.client.force_login(self.sem_permissao)
        self.assertEqual(
            self.client.post(url, {'ano': 2026}).status_code,
            403,
        )
        self.assertTrue(VisitaGrupo.objects.filter(pk=visita.id).exists())

    def test_usuario_nao_apaga_visita_de_outra_congregacao(self):
        visita = self.criar_visita(
            self.grupo_b1,
            datetime.date(2026, 9, 7),
        )
        self.client.force_login(self.usuario_a)

        response = self.client.post(
            reverse('ss_activities:delete_visita_grupo', args=[visita.id]),
            {'ano': 2026},
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(VisitaGrupo.objects.filter(pk=visita.id).exists())

    def test_superusuario_apaga_e_retorna_para_congregacao_da_visita(self):
        visita = self.criar_visita(
            self.grupo_b1,
            datetime.date(2026, 9, 7),
        )
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse('ss_activities:delete_visita_grupo', args=[visita.id]),
            {
                'ano': 2026,
                'cong': self.cong_a.id,
            },
        )

        self.assertRedirects(
            response,
            '/ss/visitas-grupos/?ano=2026&cong=%s' % self.cong_b.id,
            fetch_redirect_response=False,
        )
        self.assertFalse(VisitaGrupo.objects.filter(pk=visita.id).exists())

    def test_grupo_de_outra_congregacao_nao_pode_ser_enviado(self):
        self.client.force_login(self.usuario_a)

        response = self.post_visita(
            self.grupo_b1,
            datetime.date(2026, 9, 7),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('grupo', response.context['form'].errors)
        self.assertEqual(VisitaGrupo.objects.count(), 0)

    def test_superusuario_seleciona_congregacao_e_popup_limita_grupos(self):
        self.client.force_login(self.superuser)

        response = self.client.get(self.list_url)
        self.assertContains(
            response,
            'Selecione uma congregação para visualizar e programar visitas.',
        )

        response = self.client.get(
            self.list_url,
            {'ano': 2026, 'cong': self.cong_a.id},
        )
        self.assertContains(response, 'Grupo A1')
        self.assertContains(response, 'Grupo A2')
        self.assertNotContains(response, 'Grupo B1')

    def test_tela_pastoreio_isola_visita_e_congregacao(self):
        visita_a = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        visita_b = self.criar_visita(
            self.grupo_b1,
            datetime.date(2026, 9, 7),
        )
        self.criar_pastoreio(visita_a, assuntos='Assunto Congregação A')
        self.criar_pastoreio(
            visita_b,
            publicador=self.publicador_b1,
            acompanhante=self.anciao_b1,
            assuntos='Assunto Congregação B',
        )
        self.client.force_login(self.usuario_a)

        response = self.client.get(
            reverse('ss_activities:list_visitas_pastoreio', args=[visita_a.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Assunto Congregação A')
        self.assertNotContains(response, 'Assunto Congregação B')
        self.assertEqual(
            self.client.get(
                reverse(
                    'ss_activities:list_visitas_pastoreio',
                    args=[visita_b.id],
                )
            ).status_code,
            404,
        )

    def test_formulario_pastoreio_filtra_publicadores_e_acompanhantes(self):
        visita = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        self.client.force_login(self.usuario_a)

        response = self.client.get(
            reverse('ss_activities:list_visitas_pastoreio', args=[visita.id])
        )
        form = response.context['form']

        self.assertIn(self.publicador_a1, form.fields['publicador'].queryset)
        self.assertIn(
            self.publicador_inativo_a1,
            form.fields['publicador'].queryset,
        )
        self.assertNotIn(
            self.publicador_mudou_a1,
            form.fields['publicador'].queryset,
        )
        self.assertNotIn(self.publicador_a2, form.fields['publicador'].queryset)
        self.assertIn(self.servo_a1, form.fields['acompanhante'].queryset)
        self.assertIn(self.anciao_a2, form.fields['acompanhante'].queryset)
        self.assertNotIn(
            self.publicador_comum_a2,
            form.fields['acompanhante'].queryset,
        )
        self.assertNotIn(
            self.anciao_inativo_a2,
            form.fields['acompanhante'].queryset,
        )
        self.assertNotIn(self.anciao_b1, form.fields['acompanhante'].queryset)
        self.assertEqual(
            form.fields['data'].widget.attrs['min'],
            '2026-09-07',
        )
        self.assertEqual(
            form.fields['data'].widget.attrs['max'],
            '2026-09-13',
        )

    def test_adiciona_pastoreio_com_auditoria(self):
        visita = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        self.client.force_login(self.usuario_a)

        response = self.client.post(
            reverse('ss_activities:add_visita_pastoreio', args=[visita.id]),
            {
                'publicador': self.publicador_a1.id,
                'data': '2026-09-10',
                'assuntos': 'Encorajamento',
                'materia': 'Texto bíblico',
                'acompanhante': self.anciao_a2.id,
                'confirmado': 'on',
            },
        )

        self.assertRedirects(
            response,
            '/ss/visitas-grupos/%s/pastoreio/' % visita.id,
            fetch_redirect_response=False,
        )
        pastoreio = VisitaPastoreio.objects.get()
        self.assertEqual(pastoreio.visita_grupo, visita)
        self.assertEqual(pastoreio.publicador, self.publicador_a1)
        self.assertEqual(pastoreio.acompanhante, self.anciao_a2)
        self.assertEqual(pastoreio.create_user, self.usuario_a)
        self.assertEqual(pastoreio.assign_user, self.usuario_a)
        self.assertTrue(pastoreio.confirmado)

    def test_pastoreio_recusa_data_fora_da_semana_e_campos_obrigatorios(self):
        visita = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        self.client.force_login(self.usuario_a)

        response = self.client.post(
            reverse('ss_activities:add_visita_pastoreio', args=[visita.id]),
            {
                'publicador': self.publicador_a1.id,
                'data': '2026-09-14',
                'assuntos': '',
                'materia': '',
                'acompanhante': '',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('data', response.context['form'].errors)
        self.assertIn('assuntos', response.context['form'].errors)
        self.assertIn('materia', response.context['form'].errors)
        self.assertIn('acompanhante', response.context['form'].errors)
        self.assertContains(response, "$('#pastoreioModal').modal('show')")
        self.assertEqual(VisitaPastoreio.objects.count(), 0)

    def test_pastoreio_recusa_publicador_e_acompanhante_invalidos(self):
        visita = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        self.client.force_login(self.usuario_a)
        url = reverse('ss_activities:add_visita_pastoreio', args=[visita.id])

        response = self.client.post(
            url,
            {
                'publicador': self.publicador_mudou_a1.id,
                'data': '2026-09-08',
                'assuntos': 'Assunto',
                'materia': 'Matéria',
                'acompanhante': self.anciao_b1.id,
            },
        )

        self.assertIn('publicador', response.context['form'].errors)
        self.assertIn('acompanhante', response.context['form'].errors)
        self.assertEqual(VisitaPastoreio.objects.count(), 0)

    def test_acompanhante_deve_ser_diferente_do_publicador(self):
        visita = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        self.client.force_login(self.usuario_a)

        response = self.client.post(
            reverse('ss_activities:add_visita_pastoreio', args=[visita.id]),
            {
                'publicador': self.servo_a1.id,
                'data': '2026-09-08',
                'assuntos': 'Assunto',
                'materia': 'Matéria',
                'acompanhante': self.servo_a1.id,
            },
        )

        self.assertIn('acompanhante', response.context['form'].errors)
        self.assertEqual(VisitaPastoreio.objects.count(), 0)

    def test_publicador_so_pode_ter_um_pastoreio_na_semana(self):
        visita = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        self.criar_pastoreio(visita)
        self.client.force_login(self.usuario_a)

        response = self.client.post(
            reverse('ss_activities:add_visita_pastoreio', args=[visita.id]),
            {
                'publicador': self.publicador_a1.id,
                'data': '2026-09-09',
                'assuntos': 'Outro assunto',
                'materia': 'Outra matéria',
                'acompanhante': self.servo_a1.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('publicador', response.context['form'].errors)
        self.assertEqual(VisitaPastoreio.objects.count(), 1)

    def test_confirma_pastoreio_com_auditoria(self):
        visita = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        pastoreio = self.criar_pastoreio(visita)
        self.client.force_login(self.usuario_a)

        response = self.client.post(
            reverse(
                'ss_activities:confirm_visita_pastoreio',
                args=[visita.id, pastoreio.id],
            )
        )

        self.assertRedirects(
            response,
            '/ss/visitas-grupos/%s/pastoreio/' % visita.id,
            fetch_redirect_response=False,
        )
        pastoreio.refresh_from_db()
        self.assertTrue(pastoreio.confirmado)
        self.assertEqual(pastoreio.assign_user, self.usuario_a)

    def test_confirmacao_de_pastoreio_e_idempotente(self):
        visita = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        pastoreio = self.criar_pastoreio(
            visita,
            confirmado=True,
            assign_user=self.usuario_b,
        )
        modified = pastoreio.modified
        self.client.force_login(self.usuario_a)

        response = self.client.post(
            reverse(
                'ss_activities:confirm_visita_pastoreio',
                args=[visita.id, pastoreio.id],
            ),
            follow=True,
        )

        self.assertContains(
            response,
            'A visita de pastoreio já estava confirmada.',
        )
        pastoreio.refresh_from_db()
        self.assertTrue(pastoreio.confirmado)
        self.assertEqual(pastoreio.assign_user, self.usuario_b)
        self.assertEqual(pastoreio.modified, modified)

    def test_tela_pastoreio_oferece_confirmacao_so_para_nao_confirmado(self):
        visita = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        nao_confirmado = self.criar_pastoreio(visita)
        confirmado = self.criar_pastoreio(
            visita,
            publicador=self.publicador_inativo_a1,
            confirmado=True,
        )
        self.client.force_login(self.usuario_a)

        response = self.client.get(
            reverse('ss_activities:list_visitas_pastoreio', args=[visita.id])
        )

        self.assertContains(response, 'id="confirmPastoreioModal"')
        self.assertContains(response, str(nao_confirmado.publicador))
        self.assertContains(response, nao_confirmado.data.strftime('%d/%m/%Y'))
        self.assertContains(
            response,
            reverse(
                'ss_activities:confirm_visita_pastoreio',
                args=[visita.id, nao_confirmado.id],
            ),
        )
        self.assertNotContains(
            response,
            reverse(
                'ss_activities:confirm_visita_pastoreio',
                args=[visita.id, confirmado.id],
            ),
        )

    def test_endpoint_confirmacao_exige_metodo_permissao_e_congregacao(self):
        visita_a = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        visita_b = self.criar_visita(
            self.grupo_b1,
            datetime.date(2026, 9, 7),
        )
        pastoreio_a = self.criar_pastoreio(visita_a)
        pastoreio_b = self.criar_pastoreio(
            visita_b,
            publicador=self.publicador_b1,
            acompanhante=self.anciao_b1,
        )
        confirm_url = reverse(
            'ss_activities:confirm_visita_pastoreio',
            args=[visita_a.id, pastoreio_a.id],
        )

        self.client.force_login(self.usuario_a)
        self.assertEqual(self.client.get(confirm_url).status_code, 405)
        self.assertEqual(
            self.client.post(
                reverse(
                    'ss_activities:confirm_visita_pastoreio',
                    args=[visita_b.id, pastoreio_b.id],
                )
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                reverse(
                    'ss_activities:confirm_visita_pastoreio',
                    args=[visita_a.id, pastoreio_b.id],
                )
            ).status_code,
            404,
        )

        self.client.force_login(self.sem_permissao)
        self.assertEqual(self.client.post(confirm_url).status_code, 403)
        pastoreio_a.refresh_from_db()
        pastoreio_b.refresh_from_db()
        self.assertFalse(pastoreio_a.confirmado)
        self.assertFalse(pastoreio_b.confirmado)

    def test_apaga_pastoreio_confirmado(self):
        visita = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        pastoreio = self.criar_pastoreio(visita, confirmado=True)
        self.client.force_login(self.usuario_a)

        response = self.client.post(
            reverse(
                'ss_activities:delete_visita_pastoreio',
                args=[visita.id, pastoreio.id],
            )
        )

        self.assertRedirects(
            response,
            '/ss/visitas-grupos/%s/pastoreio/' % visita.id,
            fetch_redirect_response=False,
        )
        self.assertFalse(
            VisitaPastoreio.objects.filter(pk=pastoreio.id).exists()
        )

    def test_endpoints_pastoreio_exigem_permissao_metodo_e_congregacao(self):
        visita_a = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        visita_b = self.criar_visita(
            self.grupo_b1,
            datetime.date(2026, 9, 7),
        )
        pastoreio_b = self.criar_pastoreio(
            visita_b,
            publicador=self.publicador_b1,
            acompanhante=self.anciao_b1,
        )
        delete_url = reverse(
            'ss_activities:delete_visita_pastoreio',
            args=[visita_b.id, pastoreio_b.id],
        )

        self.client.force_login(self.usuario_a)
        self.assertEqual(self.client.get(delete_url).status_code, 405)
        self.assertEqual(self.client.post(delete_url).status_code, 404)

        self.client.force_login(self.sem_permissao)
        add_url = reverse(
            'ss_activities:add_visita_pastoreio',
            args=[visita_a.id],
        )
        self.assertEqual(self.client.post(add_url, {}).status_code, 403)
        self.assertTrue(
            VisitaPastoreio.objects.filter(pk=pastoreio_b.id).exists()
        )

    def test_pastoreios_bloqueiam_reagendamento_e_exclusao_da_visita(self):
        visita = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        self.criar_pastoreio(visita)
        self.client.force_login(self.usuario_a)

        response = self.client.post(
            reverse('ss_activities:edit_visita_grupo', args=[visita.id]),
            {
                'grupo': self.grupo_a2.id,
                'data_inicio': '2026-09-14',
                'ano': 2026,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('grupo', response.context['form'].errors)
        self.assertIn('data_inicio', response.context['form'].errors)

        response = self.client.post(
            reverse('ss_activities:delete_visita_grupo', args=[visita.id]),
            {'ano': 2026},
            follow=True,
        )
        self.assertContains(
            response,
            'Apague as visitas de pastoreio antes de apagar a visita ao grupo.',
        )
        self.assertTrue(VisitaGrupo.objects.filter(pk=visita.id).exists())

    def test_pastoreios_nao_bloqueiam_alteracao_das_flags_da_visita(self):
        visita = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        self.criar_pastoreio(visita)
        self.client.force_login(self.usuario_a)

        response = self.client.post(
            reverse('ss_activities:edit_visita_grupo', args=[visita.id]),
            {
                'grupo': self.grupo_a1.id,
                'data_inicio': '2026-09-07',
                'confirmada': 'on',
                'ano': 2026,
            },
        )

        self.assertEqual(response.status_code, 302)
        visita.refresh_from_db()
        self.assertTrue(visita.confirmada)

    def test_programacao_anual_mostra_botao_e_quantidade_de_pastoreios(self):
        visita = self.criar_visita(
            self.grupo_a1,
            datetime.date(2026, 9, 7),
        )
        self.criar_pastoreio(visita)
        self.client.force_login(self.usuario_a)

        response = self.client.get(self.list_url, {'ano': 2026})
        visita_listada = response.context['visitas'].get(pk=visita.id)

        self.assertEqual(visita_listada.total_visitas_pastoreio, 1)
        self.assertContains(response, 'Pastoreio')
        self.assertContains(
            response,
            reverse(
                'ss_activities:list_visitas_pastoreio',
                args=[visita.id],
            ),
        )

    def test_helpers_definem_ano_de_servico_de_setembro_a_agosto(self):
        self.assertEqual(
            limites_ano_servico(2026),
            (datetime.date(2026, 9, 1), datetime.date(2027, 8, 31)),
        )
        self.assertEqual(ano_servico_atual(datetime.date(2026, 8, 31)), 2025)
        self.assertEqual(ano_servico_atual(datetime.date(2026, 9, 1)), 2026)


class TestemunhoPublicoTests(TestCase):
    def setUp(self):
        self.cong_a = Cong.objects.create(nome='Congregação A', numero=10)
        self.cong_b = Cong.objects.create(nome='Congregação B', numero=20)
        self.grupo_a = Grupos.objects.create(
            grupo='Grupo A',
            dirigente='Dirigente A',
            cong=self.cong_a,
        )
        self.grupo_b = Grupos.objects.create(
            grupo='Grupo B',
            dirigente='Dirigente B',
            cong=self.cong_b,
        )
        self.publicadores_a = [
            self.criar_publicador('Ana', self.grupo_a),
            self.criar_publicador('Beatriz', self.grupo_a),
            self.criar_publicador('Carlos', self.grupo_a),
            self.criar_publicador('Daniel', self.grupo_a),
        ]
        self.publicador_b = self.criar_publicador('Eduardo', self.grupo_b)
        self.inativo_a = self.criar_publicador(
            'Inativo',
            self.grupo_a,
            situacao=0,
        )
        self.usuario_a = User.objects.create_user(username='tp_a', password='senha')
        self.usuario_b = User.objects.create_user(username='tp_b', password='senha')
        self.sem_permissao = User.objects.create_user(
            username='sem_tp',
            password='senha',
        )
        self.superuser = User.objects.create_superuser(
            username='admin_tp',
            password='senha',
        )
        CongUser.objects.create(cong=self.cong_a, user=self.usuario_a)
        CongUser.objects.create(cong=self.cong_b, user=self.usuario_b)
        CongUser.objects.create(cong=self.cong_a, user=self.sem_permissao)
        permissao = Permission.objects.get(
            content_type__app_label='ss_activities',
            codename='manage_testemunho_publico',
        )
        self.usuario_a.user_permissions.add(permissao)
        self.usuario_b.user_permissions.add(permissao)
        self.semana = datetime.date(2026, 8, 3)
        self.periodo = PeriodoTestemunhoPublico.objects.create(
            cong=self.cong_a,
            dia_semana=0,
            descricao='Manhã',
            horario=datetime.time(6, 40),
        )
        self.periodo_b = PeriodoTestemunhoPublico.objects.create(
            cong=self.cong_b,
            dia_semana=0,
            descricao='Manhã',
            horario=datetime.time(6, 40),
        )
        self.local_1 = LocalTestemunhoPublico.objects.create(
            cong=self.cong_a,
            nome='Praça Central',
        )
        self.local_2 = LocalTestemunhoPublico.objects.create(
            cong=self.cong_a,
            nome='Terminal',
        )
        self.local_b = LocalTestemunhoPublico.objects.create(
            cong=self.cong_b,
            nome='Praça B',
        )
        for publicador in self.publicadores_a:
            HabilitacaoTestemunhoPublico.objects.create(
                cong=self.cong_a,
                publicador=publicador,
                data_treinamento=datetime.date(2026, 7, 1),
            )
        HabilitacaoTestemunhoPublico.objects.create(
            cong=self.cong_b,
            publicador=self.publicador_b,
            data_treinamento=datetime.date(2026, 7, 1),
        )
        self.configuracao = ConfiguracaoTestemunhoPublico.objects.create(
            cong=self.cong_a,
            quantidade_carrinhos=2,
            modo_identificacao='N',
        )
        self.configuracao_b = ConfiguracaoTestemunhoPublico.objects.create(
            cong=self.cong_b,
            quantidade_carrinhos=1,
            modo_identificacao='N',
        )
        self.carrinho_1, self.carrinho_2 = list(
            CarrinhoTestemunhoPublico.objects.filter(cong=self.cong_a)
        )
        self.carrinho_b = CarrinhoTestemunhoPublico.objects.get(cong=self.cong_b)
        self.painel_url = reverse('ss_activities:painel_testemunho_publico')

    def criar_publicador(self, nome, grupo, situacao=1):
        return Publicadores.objects.create(
            nome=nome,
            endereco='Endereço',
            esperanca=0,
            privilegio=0,
            tipo=0,
            sexo=0,
            situacao=situacao,
            classe='0',
            grupo=grupo,
            cong=grupo.cong,
        )

    def criar_designacao(self, **kwargs):
        dados = {
            'cong': self.cong_a,
            'data': self.semana,
            'periodo': self.periodo,
            'local': self.local_1,
            'carrinho': self.carrinho_1,
            'publicador_1': self.publicadores_a[0],
            'publicador_2': self.publicadores_a[1],
        }
        dados.update(kwargs)
        return DesignacaoTestemunhoPublico.objects.create(**dados)

    def test_configuracao_gera_carrinhos_numericos_alfabeticos_e_customizados(self):
        self.assertEqual(str(self.carrinho_1), 'Carrinho 1')
        self.assertEqual(str(self.carrinho_2), 'Carrinho 2')
        self.assertEqual(numero_para_letras(26), 'Z')
        self.assertEqual(numero_para_letras(27), 'AA')
        self.assertEqual(numero_para_letras(28), 'AB')

        self.carrinho_1.nome_personalizado = 'Carrinho Principal'
        self.carrinho_1.save()
        self.configuracao.modo_identificacao = 'A'
        self.configuracao.save()
        self.carrinho_1.refresh_from_db()
        self.carrinho_2.refresh_from_db()

        self.assertEqual(str(self.carrinho_1), 'Carrinho Principal')
        self.assertEqual(str(self.carrinho_2), 'Carrinho B')

        self.configuracao.quantidade_carrinhos = 28
        self.configuracao.save()
        self.assertEqual(
            str(
                CarrinhoTestemunhoPublico.objects.get(
                    cong=self.cong_a,
                    numero_ordem=27,
                )
            ),
            'Carrinho AA',
        )
        self.assertEqual(
            str(
                CarrinhoTestemunhoPublico.objects.get(
                    cong=self.cong_a,
                    numero_ordem=28,
                )
            ),
            'Carrinho AB',
        )

        self.carrinho_1.nome_personalizado = ''
        self.carrinho_1.save()
        self.assertEqual(str(self.carrinho_1), 'Carrinho A')

    def test_aumento_reducao_e_reativacao_de_carrinhos(self):
        self.configuracao.quantidade_carrinhos = 3
        self.configuracao.save()
        self.assertEqual(
            CarrinhoTestemunhoPublico.objects.filter(
                cong=self.cong_a,
                ativo=True,
            ).count(),
            3,
        )

        self.configuracao.quantidade_carrinhos = 1
        self.configuracao.save()
        self.assertEqual(
            CarrinhoTestemunhoPublico.objects.filter(
                cong=self.cong_a,
                ativo=True,
            ).count(),
            1,
        )

        self.configuracao.quantidade_carrinhos = 2
        self.configuracao.save()
        self.carrinho_2.refresh_from_db()
        self.assertTrue(self.carrinho_2.ativo)

    def test_reducao_bloqueia_carrinho_com_designacao_futura(self):
        proxima_segunda = datetime.date.today() + datetime.timedelta(
            days=(7 - datetime.date.today().weekday()) % 7,
        )
        if proxima_segunda == datetime.date.today():
            proxima_segunda += datetime.timedelta(days=7)
        self.criar_designacao(
            data=proxima_segunda,
            local=self.local_2,
            carrinho=self.carrinho_2,
        )
        self.configuracao.quantidade_carrinhos = 1

        with self.assertRaises(ValidationError):
            self.configuracao.save()

        self.configuracao.refresh_from_db()
        self.carrinho_2.refresh_from_db()
        self.assertEqual(self.configuracao.quantidade_carrinhos, 2)
        self.assertTrue(self.carrinho_2.ativo)

    def test_designacao_valida_habilitacao_congregacao_e_conflitos(self):
        self.criar_designacao()
        with self.assertRaises(ValidationError):
            self.criar_designacao(
                local=self.local_2,
                carrinho=self.carrinho_1,
                publicador_1=self.publicadores_a[2],
                publicador_2=self.publicadores_a[3],
            )
        with self.assertRaises(ValidationError):
            self.criar_designacao(
                local=self.local_1,
                carrinho=self.carrinho_2,
                publicador_1=self.publicadores_a[2],
                publicador_2=self.publicadores_a[3],
            )
        with self.assertRaises(ValidationError):
            self.criar_designacao(
                local=self.local_2,
                carrinho=self.carrinho_2,
                publicador_1=self.publicadores_a[0],
                publicador_2=self.publicadores_a[2],
            )
        with self.assertRaises(ValidationError):
            self.criar_designacao(
                data=self.semana + datetime.timedelta(days=1),
                local=self.local_2,
                carrinho=self.carrinho_2,
                publicador_1=self.publicadores_a[2],
                publicador_2=self.publicadores_a[3],
            )
        with self.assertRaises(ValidationError):
            self.criar_designacao(
                local=self.local_2,
                carrinho=self.carrinho_2,
                publicador_1=self.inativo_a,
                publicador_2=self.publicadores_a[3],
            )
        with self.assertRaises(ValidationError):
            self.criar_designacao(
                periodo=self.periodo_b,
                local=self.local_b,
                carrinho=self.carrinho_b,
                publicador_1=self.publicador_b,
                publicador_2=self.publicadores_a[3],
            )

    def test_permite_duplas_no_mesmo_periodo_com_local_e_carrinho_diferentes(self):
        self.criar_designacao()
        segunda = self.criar_designacao(
            local=self.local_2,
            carrinho=self.carrinho_2,
            publicador_1=self.publicadores_a[2],
            publicador_2=self.publicadores_a[3],
        )
        self.assertIsNotNone(segunda.pk)
        self.assertEqual(DesignacaoTestemunhoPublico.objects.count(), 2)

    def test_permissao_controla_menu_e_rotas(self):
        self.client.force_login(self.sem_permissao)
        self.assertEqual(self.client.get(self.painel_url).status_code, 403)
        self.assertNotContains(self.client.get('/'), 'Testemunho Público')

        self.client.force_login(self.usuario_a)
        self.assertContains(self.client.get('/'), 'Testemunho Público')
        response = self.client.get(
            self.painel_url,
            {'semana': self.semana.isoformat()},
        )
        self.assertEqual(response.status_code, 200)

    def test_painel_semanal_mostra_dupla_carrinho_local_e_navegacao(self):
        self.publicadores_a[0].nome = 'Ana Maria da Silva'
        self.publicadores_a[0].save()
        self.publicadores_a[1].nome = 'Beatriz dos Santos Oliveira'
        self.publicadores_a[1].save()
        self.criar_designacao()
        self.client.force_login(self.usuario_a)

        response = self.client.get(
            self.painel_url,
            {'semana': '2026-08-05'},
        )

        self.assertEqual(response.context['semana'], self.semana)
        self.assertContains(response, 'Ana Silva / Beatriz Oliveira')
        self.assertEqual(
            response.context['designacoes'].get().nomes_resumidos,
            'Ana Silva / Beatriz Oliveira',
        )
        self.assertContains(response, 'Carrinho 1')
        self.assertContains(response, 'Praça Central')
        self.assertContains(response, 'Segunda-feira')
        self.assertContains(response, 'Domingo')
        self.assertContains(response, 'Semana atual')

    def test_inclusao_por_rota_registra_auditoria_e_isola_congregacao(self):
        self.client.force_login(self.usuario_a)
        response = self.client.post(
            reverse('ss_activities:add_designacao_testemunho_publico'),
            {
                'semana': self.semana.isoformat(),
                'data': self.semana.isoformat(),
                'periodo': self.periodo.id,
                'local': self.local_1.id,
                'carrinho': self.carrinho_1.id,
                'publicador_1': self.publicadores_a[0].id,
                'publicador_2': self.publicadores_a[1].id,
            },
        )
        self.assertEqual(response.status_code, 302)
        designacao = DesignacaoTestemunhoPublico.objects.get()
        self.assertEqual(designacao.create_user, self.usuario_a)
        self.assertEqual(designacao.assign_user, self.usuario_a)

        response = self.client.post(
            reverse('ss_activities:add_designacao_testemunho_publico'),
            {
                'semana': self.semana.isoformat(),
                'data': self.semana.isoformat(),
                'periodo': self.periodo_b.id,
                'local': self.local_b.id,
                'carrinho': self.carrinho_b.id,
                'publicador_1': self.publicador_b.id,
                'publicador_2': self.publicadores_a[2].id,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('periodo', response.context['form'].errors)
        self.assertEqual(DesignacaoTestemunhoPublico.objects.count(), 1)

    def test_disponibilidade_remove_recursos_ocupados(self):
        self.criar_designacao()
        self.client.force_login(self.usuario_a)

        response = self.client.get(
            reverse('ss_activities:disponibilidade_testemunho_publico'),
            {
                'data': self.semana.isoformat(),
                'periodo': self.periodo.id,
            },
        )
        dados = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.carrinho_1.id, dados['carrinhos'])
        self.assertIn(self.carrinho_2.id, dados['carrinhos'])
        self.assertNotIn(self.local_1.id, dados['locais'])
        self.assertIn(self.local_2.id, dados['locais'])
        self.assertNotIn(self.publicadores_a[0].id, dados['publicadores'])
        self.assertIn(self.publicadores_a[2].id, dados['publicadores'])

    def test_cadastros_e_designacoes_de_outra_congregacao_retornam_404(self):
        publicador_b_2 = self.criar_publicador('Fernanda', self.grupo_b)
        HabilitacaoTestemunhoPublico.objects.create(
            cong=self.cong_b,
            publicador=publicador_b_2,
            data_treinamento=datetime.date(2026, 7, 1),
        )
        designacao_b = DesignacaoTestemunhoPublico.objects.create(
            cong=self.cong_b,
            data=self.semana,
            periodo=self.periodo_b,
            local=self.local_b,
            carrinho=self.carrinho_b,
            publicador_1=self.publicador_b,
            publicador_2=publicador_b_2,
        )
        self.client.force_login(self.usuario_a)

        self.assertEqual(
            self.client.post(
                reverse(
                    'ss_activities:delete_designacao_testemunho_publico',
                    args=[designacao_b.id],
                ),
                {'semana': self.semana.isoformat()},
            ).status_code,
            404,
        )

    def test_helper_semana_normaliza_para_segunda_feira(self):
        class Request:
            POST = {}
            GET = {'semana': '2026-08-09'}

        self.assertEqual(semana_testemunho_publico(Request()), self.semana)
