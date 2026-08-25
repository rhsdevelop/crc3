import os
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from PIL import Image, UnidentifiedImageError

from register.models import Cong


FORMATOS_IMAGEM_CAPA = {
    '.jpg': 'JPEG',
    '.jpeg': 'JPEG',
    '.png': 'PNG',
    '.webp': 'WEBP',
}
TAMANHO_MAXIMO_IMAGEM_CAPA = 10 * 1024 * 1024


def validar_imagem_capa(arquivo):
    extensao = os.path.splitext(arquivo.name)[1].lower()
    if extensao not in FORMATOS_IMAGEM_CAPA:
        raise ValidationError('Envie uma imagem nos formatos JPEG, PNG ou WebP.')
    if arquivo.size > TAMANHO_MAXIMO_IMAGEM_CAPA:
        raise ValidationError('A imagem da capa deve ter no máximo 10 MB.')

    posicao = arquivo.tell() if hasattr(arquivo, 'tell') else None
    try:
        imagem = Image.open(arquivo)
        formato = imagem.format
        imagem.verify()
        if formato != FORMATOS_IMAGEM_CAPA[extensao]:
            raise ValidationError(
                'O conteúdo da imagem não corresponde ao formato informado.'
            )
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValidationError('O arquivo enviado não é uma imagem válida.')
    finally:
        if posicao is not None and hasattr(arquivo, 'seek'):
            arquivo.seek(posicao)


def caminho_imagem_caderno(instance, filename):
    extensao = os.path.splitext(filename)[1].lower()
    return 'cadernos/%s/%s/%s%s' % (
        instance.cong_id,
        instance.ano_servico,
        uuid.uuid4().hex,
        extensao,
    )


class PrivateNotebookStorage(FileSystemStorage):
    @property
    def base_location(self):
        return settings.PRIVATE_MEDIA_ROOT

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    @property
    def base_url(self):
        return None


private_notebook_storage = PrivateNotebookStorage()


class ConfiguracaoCadernoPioneiro(models.Model):
    cong = models.ForeignKey(
        Cong,
        db_column='Cong',
        on_delete=models.PROTECT,
        verbose_name='Congregação',
    )
    ano_servico = models.PositiveSmallIntegerField(
        db_column='Ano_Servico',
        verbose_name='Ano inicial do ano de serviço',
    )
    imagem = models.ImageField(
        db_column='Imagem',
        upload_to=caminho_imagem_caderno,
        storage=private_notebook_storage,
        validators=[validar_imagem_capa],
        verbose_name='Imagem da capa',
    )
    meta_horas = models.PositiveSmallIntegerField(
        db_column='Meta_Horas',
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(744)],
        verbose_name='Meta mensal de horas',
    )
    create_user = models.ForeignKey(
        User,
        db_column='User_Create',
        on_delete=models.PROTECT,
        related_name='caderno_pioneiro_user_create',
        blank=True,
        null=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    assign_user = models.ForeignKey(
        User,
        db_column='User_Modify',
        on_delete=models.PROTECT,
        related_name='caderno_pioneiro_user_assign',
        blank=True,
        null=True,
    )
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Caderno_Pioneiro_Configuracao'
        ordering = ['-ano_servico', 'cong__nome']
        default_permissions = ()
        permissions = [
            (
                'manage_pioneer_notebooks',
                'Pode gerenciar cadernos de pioneiros regulares',
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['cong', 'ano_servico'],
                name='unique_caderno_pioneiro_cong_ano',
            ),
        ]
        verbose_name = 'Configuração de caderno de pioneiro'
        verbose_name_plural = 'Configurações de cadernos de pioneiros'

    def __str__(self):
        return '%s - %s' % (self.cong, self.ano_servico_exibicao)

    @property
    def ano_servico_exibicao(self):
        return '%s/%s' % (self.ano_servico, self.ano_servico + 1)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
