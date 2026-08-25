import datetime
import io
import re
import tempfile

from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from register.models import Cong, CongUser, Grupos, Publicadores

from .models import (
    ConfiguracaoCadernoPioneiro,
    TAMANHO_MAXIMO_IMAGEM_CAPA,
    validar_imagem_capa,
)
from .services import ano_servico_atual, dias_mes, meses_ano_servico, meta_acumulada


class CadernosPioneirosTests(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.media_override = override_settings(PRIVATE_MEDIA_ROOT=self.media.name)
        self.media_override.enable()

        self.cong_a = Cong.objects.create(nome='Congregação Caderno A', numero=501)
        self.cong_b = Cong.objects.create(nome='Congregação Caderno B', numero=502)
        self.grupo_a = Grupos.objects.create(
            grupo='Grupo A', dirigente='Dirigente A', cong=self.cong_a
        )
        self.grupo_b = Grupos.objects.create(
            grupo='Grupo B', dirigente='Dirigente B', cong=self.cong_b
        )
        self.pioneira = self.criar_publicador(
            'Ana Pioneira da Silva', self.grupo_a, tipo=2, sexo=1
        )
        self.pioneiro = self.criar_publicador(
            'Bruno Pioneiro Santos', self.grupo_a, tipo=2
        )
        self.pioneiro_inativo = self.criar_publicador(
            'Carlos Pioneiro Inativo', self.grupo_a, tipo=2, situacao=0
        )
        self.publicador = self.criar_publicador(
            'Daniel Publicador', self.grupo_a, tipo=0
        )
        self.pioneiro_outra = self.criar_publicador(
            'Eduardo Outra Congregação', self.grupo_b, tipo=2
        )

        self.usuario_a = User.objects.create_user('caderno_a', password='senha')
        self.usuario_b = User.objects.create_user('caderno_b', password='senha')
        self.usuario_sem = User.objects.create_user('caderno_sem', password='senha')
        self.usuario_sem_cong = User.objects.create_user(
            'caderno_sem_cong', password='senha'
        )
        self.superuser = User.objects.create_superuser(
            'caderno_admin', password='senha'
        )
        CongUser.objects.create(cong=self.cong_a, user=self.usuario_a)
        CongUser.objects.create(cong=self.cong_b, user=self.usuario_b)
        CongUser.objects.create(cong=self.cong_a, user=self.usuario_sem)
        permissao = Permission.objects.get(
            content_type__app_label='notebooks',
            codename='manage_pioneer_notebooks',
        )
        for usuario in [self.usuario_a, self.usuario_b, self.usuario_sem_cong]:
            usuario.user_permissions.add(permissao)

        self.ano = 2026
        self.configuracao = ConfiguracaoCadernoPioneiro.objects.create(
            cong=self.cong_a,
            ano_servico=self.ano,
            imagem=self.arquivo_imagem(),
            create_user=self.usuario_a,
            assign_user=self.usuario_a,
        )
        self.painel_url = reverse('notebooks:pioneiros_regulares')
        self.configuracao_url = reverse('notebooks:salvar_configuracao')
        self.capas_url = reverse('notebooks:pdf_capas')
        self.miolo_url = reverse('notebooks:pdf_miolo')

    def tearDown(self):
        self.media_override.disable()
        self.media.cleanup()

    def criar_publicador(self, nome, grupo, tipo=2, situacao=1, sexo=0):
        return Publicadores.objects.create(
            nome=nome,
            endereco='Rua dos Pioneiros',
            esperanca=0,
            privilegio=0,
            tipo=tipo,
            sexo=sexo,
            situacao=situacao,
            classe='0',
            grupo=grupo,
            cong=grupo.cong,
        )

    def arquivo_imagem(self, nome='capa.png', formato='PNG'):
        arquivo = io.BytesIO()
        Image.new('RGB', (300, 150), '#92b5d4').save(arquivo, formato)
        tipos = {
            'PNG': 'image/png',
            'JPEG': 'image/jpeg',
            'WEBP': 'image/webp',
        }
        return SimpleUploadedFile(
            nome,
            arquivo.getvalue(),
            content_type=tipos.get(formato, 'application/octet-stream'),
        )

    def quantidade_paginas(self, resposta):
        return len(re.findall(rb'/Type\s*/Page\b', resposta.content))

    def test_menu_e_rotas_exigem_permissao_propria(self):
        self.client.force_login(self.usuario_sem)
        self.assertNotContains(self.client.get('/'), 'Cadernos de atividade:')
        self.assertEqual(self.client.get(self.painel_url).status_code, 403)
        self.assertEqual(self.client.get(self.capas_url).status_code, 403)
        self.assertEqual(self.client.get(self.miolo_url).status_code, 403)
        self.assertEqual(self.client.post(self.configuracao_url).status_code, 403)
        self.assertEqual(
            self.client.get(
                reverse('notebooks:visualizar_imagem', args=[self.configuracao.id])
            ).status_code,
            403,
        )

        self.client.force_login(self.usuario_a)
        self.assertContains(self.client.get('/'), 'Cadernos de atividade:')
        self.assertEqual(self.client.get(self.painel_url).status_code, 200)

    def test_usuario_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(self.painel_url)
        self.assertEqual(resposta.status_code, 302)
        self.assertIn('/accounts/login/', resposta['Location'])

    def test_listagem_exibe_apenas_pioneiros_regulares_ativos_da_congregacao(self):
        self.client.force_login(self.usuario_a)
        resposta = self.client.get(self.painel_url, {'ano': self.ano})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, self.pioneira.nome)
        self.assertContains(resposta, self.pioneiro.nome)
        self.assertNotContains(resposta, self.pioneiro_inativo.nome)
        self.assertNotContains(resposta, self.publicador.nome)
        self.assertNotContains(resposta, self.pioneiro_outra.nome)
        self.assertEqual(resposta.context['total_pioneiros'], 2)
        self.assertEqual(
            list(resposta.context['pioneiros']),
            [self.pioneira, self.pioneiro],
        )

    def test_usuario_sem_congregacao_recebe_orientacao(self):
        self.client.force_login(self.usuario_sem_cong)
        resposta = self.client.get(self.painel_url, follow=True)
        self.assertContains(resposta, 'não está vinculado a nenhuma congregação')

    def test_superusuario_deve_selecionar_congregacao_e_respeita_filtro(self):
        self.client.force_login(self.superuser)
        sem_congregacao = self.client.get(self.painel_url)
        self.assertContains(sem_congregacao, 'Selecione uma congregação')

        resposta_a = self.client.get(
            self.painel_url, {'ano': self.ano, 'cong': self.cong_a.id}
        )
        self.assertContains(resposta_a, self.pioneira.nome)
        self.assertNotContains(resposta_a, self.pioneiro_outra.nome)

        resposta_b = self.client.get(
            self.painel_url, {'ano': self.ano, 'cong': self.cong_b.id}
        )
        self.assertContains(resposta_b, self.pioneiro_outra.nome)
        self.assertNotContains(resposta_b, self.pioneira.nome)
        self.assertEqual(self.client.get(self.miolo_url).status_code, 404)

    def test_configuracao_cria_ano_com_meta_imagem_e_auditoria(self):
        self.client.force_login(self.usuario_a)
        resposta = self.client.post(
            self.configuracao_url,
            {
                'cong': self.cong_b.id,
                'ano': 2027,
                'meta_horas': 60,
                'imagem': self.arquivo_imagem('capa-2027.jpg', 'JPEG'),
            },
        )
        self.assertEqual(resposta.status_code, 302)
        configuracao = ConfiguracaoCadernoPioneiro.objects.get(
            cong=self.cong_a,
            ano_servico=2027,
        )
        self.assertEqual(configuracao.meta_horas, 60)
        self.assertEqual(configuracao.create_user, self.usuario_a)
        self.assertEqual(configuracao.assign_user, self.usuario_a)
        self.assertTrue(configuracao.imagem.name.startswith(
            'cadernos/%s/2027/' % self.cong_a.id
        ))
        self.assertTrue(ConfiguracaoCadernoPioneiro.objects.filter(
            pk=self.configuracao.pk
        ).exists())
        self.assertFalse(ConfiguracaoCadernoPioneiro.objects.filter(
            cong=self.cong_b,
            ano_servico=2027,
        ).exists())

    def test_atualizacao_preserva_imagem_e_usuario_de_criacao(self):
        imagem_anterior = self.configuracao.imagem.name
        self.client.force_login(self.usuario_a)
        resposta = self.client.post(
            self.configuracao_url,
            {'ano': self.ano, 'meta_horas': 55},
        )
        self.assertEqual(resposta.status_code, 302)
        self.configuracao.refresh_from_db()
        self.assertEqual(self.configuracao.meta_horas, 55)
        self.assertEqual(self.configuracao.imagem.name, imagem_anterior)
        self.assertEqual(self.configuracao.create_user, self.usuario_a)
        self.assertEqual(self.configuracao.assign_user, self.usuario_a)

    def test_mesma_configuracao_nao_pode_ser_duplicada(self):
        with self.assertRaises(ValidationError):
            ConfiguracaoCadernoPioneiro.objects.create(
                cong=self.cong_a,
                ano_servico=self.ano,
                imagem=self.arquivo_imagem('duplicada.png'),
            )

    def test_upload_aceita_jpeg_png_e_webp(self):
        arquivos = [
            self.arquivo_imagem('imagem.jpg', 'JPEG'),
            self.arquivo_imagem('imagem.png', 'PNG'),
            self.arquivo_imagem('imagem.webp', 'WEBP'),
        ]
        for arquivo in arquivos:
            with self.subTest(arquivo=arquivo.name):
                validar_imagem_capa(arquivo)

    def test_upload_recusa_extensao_conteudo_e_tamanho_invalidos(self):
        invalidos = [
            SimpleUploadedFile('imagem.gif', b'invalido', 'image/gif'),
            SimpleUploadedFile('imagem.png', b'invalido', 'image/png'),
            self.arquivo_imagem('imagem.jpg', 'PNG'),
            SimpleUploadedFile(
                'grande.png',
                b'x' * (TAMANHO_MAXIMO_IMAGEM_CAPA + 1),
                'image/png',
            ),
        ]
        for arquivo in invalidos:
            with self.subTest(arquivo=arquivo.name):
                with self.assertRaises(ValidationError):
                    validar_imagem_capa(arquivo)

    def test_formulario_invalido_preserva_ano_e_mostra_erros(self):
        self.client.force_login(self.usuario_a)
        resposta = self.client.post(
            self.configuracao_url,
            {
                'ano': 2027,
                'meta_horas': 0,
                'imagem': SimpleUploadedFile('invalida.png', b'erro', 'image/png'),
            },
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context['ano'], 2027)
        self.assertTrue(resposta.context['form'].errors)

    def test_imagem_e_protegida_e_isolada_por_congregacao(self):
        url = reverse('notebooks:visualizar_imagem', args=[self.configuracao.id])
        self.client.force_login(self.usuario_a)
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta['Content-Type'], 'image/png')
        self.assertEqual(resposta['X-Content-Type-Options'], 'nosniff')

        self.client.force_login(self.usuario_b)
        self.assertEqual(self.client.get(url).status_code, 404)

        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get(url, {'cong': self.cong_b.id}).status_code, 404)
        self.assertEqual(self.client.get(url, {'cong': self.cong_a.id}).status_code, 200)

    def test_capa_individual_gera_pdf_com_nome_ano_e_imagem(self):
        self.client.force_login(self.usuario_a)
        resposta = self.client.get(
            reverse('notebooks:pdf_capa_individual', args=[self.pioneira.id]),
            {'ano': self.ano},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta['Content-Type'], 'application/pdf')
        self.assertTrue(resposta.content.startswith(b'%PDF-'))
        self.assertEqual(self.quantidade_paginas(resposta), 1)
        self.assertIn(b'Ana Pioneira da Silva', resposta.content)
        self.assertIn(b'2026/2027', resposta.content)
        self.assertIn(b'/Subtype /Image', resposta.content)
        self.assertIn('ana-pioneira-da-silva', resposta['Content-Disposition'])

    def test_capas_coletivas_geram_uma_pagina_por_pioneiro(self):
        self.client.force_login(self.usuario_a)
        resposta = self.client.get(self.capas_url, {'ano': self.ano})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.quantidade_paginas(resposta), 2)
        self.assertIn(b'Ana Pioneira da Silva', resposta.content)
        self.assertIn(b'Bruno Pioneiro Santos', resposta.content)
        self.assertNotIn(b'Daniel Publicador', resposta.content)
        self.assertNotIn(b'Carlos Pioneiro Inativo', resposta.content)

    def test_capas_sem_configuracao_sao_bloqueadas(self):
        self.client.force_login(self.usuario_a)
        resposta = self.client.get(self.capas_url, {'ano': 2028}, follow=True)
        self.assertContains(resposta, 'Configure a imagem da capa')
        self.assertEqual(resposta.context['ano'], 2028)

        individual = self.client.get(
            reverse('notebooks:pdf_capa_individual', args=[self.pioneira.id]),
            {'ano': 2028},
        )
        self.assertEqual(individual.status_code, 302)

    def test_capa_recusa_outra_congregacao_inativo_e_nao_pioneiro(self):
        self.client.force_login(self.usuario_a)
        for publicador in [self.pioneiro_outra, self.pioneiro_inativo, self.publicador]:
            with self.subTest(publicador=publicador.nome):
                resposta = self.client.get(
                    reverse('notebooks:pdf_capa_individual', args=[publicador.id]),
                    {'ano': self.ano},
                )
                self.assertEqual(resposta.status_code, 404)

    def test_miolo_gera_treze_paginas_a4_paisagem(self):
        self.client.force_login(self.usuario_a)
        resposta = self.client.get(self.miolo_url, {'ano': self.ano})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta['Content-Type'], 'application/pdf')
        self.assertTrue(resposta.content.startswith(b'%PDF-'))
        self.assertEqual(self.quantidade_paginas(resposta), 13)
        self.assertRegex(
            resposta.content.decode('latin-1'),
            r'/MediaBox\s*\[\s*0\s+0\s+841\.\d+\s+595\.\d+',
        )
        self.assertIn(b'Setembro', resposta.content)
        self.assertIn(b'Outubro', resposta.content)
        self.assertIn(b'Agosto', resposta.content)
        self.assertIn(b'50:00', resposta.content)
        self.assertIn('2026-2027-50h.pdf', resposta['Content-Disposition'])

    def test_miolo_usa_meta_configurada_e_padrao_sem_configuracao(self):
        self.configuracao.meta_horas = 60
        self.configuracao.save()
        self.client.force_login(self.usuario_a)
        configurado = self.client.get(self.miolo_url, {'ano': self.ano})
        self.assertIn(b'60:00', configurado.content)
        self.assertIn('60h.pdf', configurado['Content-Disposition'])

        padrao = self.client.get(self.miolo_url, {'ano': 2027})
        self.assertIn(b'50:00', padrao.content)
        self.assertIn('50h.pdf', padrao['Content-Disposition'])

    def test_contracapa_compensa_espacamento_da_fonte_caligrafica(self):
        self.client.force_login(self.usuario_a)
        resposta = self.client.get(self.miolo_url, {'ano': self.ano})
        self.assertIn(b'4.62 Tw', resposta.content)
        self.assertIn(b'5.94 Tw', resposta.content)

    def test_ano_de_servico_e_meses_consideram_setembro_a_agosto(self):
        self.assertEqual(ano_servico_atual(datetime.date(2026, 8, 31)), 2025)
        self.assertEqual(ano_servico_atual(datetime.date(2026, 9, 1)), 2026)
        meses = list(meses_ano_servico(2026))
        self.assertEqual(len(meses), 12)
        self.assertEqual(meses[0], datetime.date(2026, 9, 1))
        self.assertEqual(meses[3], datetime.date(2026, 12, 1))
        self.assertEqual(meses[4], datetime.date(2027, 1, 1))
        self.assertEqual(meses[-1], datetime.date(2027, 8, 1))

    def test_fevereiro_e_fins_de_semana_sao_identificados_corretamente(self):
        fevereiro_comum = list(dias_mes(datetime.date(2027, 2, 1), 50))
        fevereiro_bissexto = list(dias_mes(datetime.date(2028, 2, 1), 50))
        self.assertEqual(len(fevereiro_comum), 28)
        self.assertEqual(len(fevereiro_bissexto), 29)

        agosto = list(dias_mes(datetime.date(2026, 8, 1), 50))
        self.assertEqual(agosto[0]['dia_semana'], 'Sáb')
        self.assertTrue(agosto[0]['fim_semana'])
        self.assertEqual(agosto[1]['dia_semana'], 'Dom')
        self.assertTrue(agosto[1]['fim_semana'])
        self.assertFalse(agosto[2]['fim_semana'])

    def test_meta_acumulada_e_proporcional_e_termina_no_valor_configurado(self):
        self.assertEqual(meta_acumulada(50, 1, 30), '1:40')
        self.assertEqual(meta_acumulada(50, 15, 30), '25:00')
        self.assertEqual(meta_acumulada(50, 30, 30), '50:00')
        self.assertEqual(meta_acumulada(50, 1, 31), '1:37')
        self.assertEqual(meta_acumulada(70, 31, 31), '70:00')

    def test_metodos_http_sao_restritos(self):
        self.client.force_login(self.usuario_a)
        self.assertEqual(self.client.get(self.configuracao_url).status_code, 405)
        self.assertEqual(self.client.post(self.painel_url).status_code, 405)
        self.assertEqual(self.client.post(self.capas_url).status_code, 405)
        self.assertEqual(self.client.post(self.miolo_url).status_code, 405)

    def test_superusuario_gera_documentos_apenas_da_congregacao_escolhida(self):
        ConfiguracaoCadernoPioneiro.objects.create(
            cong=self.cong_b,
            ano_servico=self.ano,
            meta_horas=65,
            imagem=self.arquivo_imagem('capa-b.png'),
        )
        self.client.force_login(self.superuser)
        capas = self.client.get(
            self.capas_url,
            {'ano': self.ano, 'cong': self.cong_b.id},
        )
        self.assertEqual(self.quantidade_paginas(capas), 1)
        self.assertIn(b'Eduardo Outra', capas.content)
        self.assertNotIn(b'Ana Pioneira da Silva', capas.content)

        miolo = self.client.get(
            self.miolo_url,
            {'ano': self.ano, 'cong': self.cong_b.id},
        )
        self.assertIn(b'65:00', miolo.content)

    def test_admin_permite_edicao_sem_expor_imagem_ou_apagar_historico(self):
        self.client.force_login(self.superuser)
        url = reverse(
            'admin:notebooks_configuracaocadernopioneiro_change',
            args=[self.configuracao.id],
        )
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(resposta.context['has_delete_permission'])
