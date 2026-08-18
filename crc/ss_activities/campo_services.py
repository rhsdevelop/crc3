import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import ArranjoSaidaCampo, ProgramacaoCampo


def normalizar_semana(valor=None):
    try:
        data = datetime.date.fromisoformat(valor) if valor else datetime.date.today()
    except (TypeError, ValueError):
        data = datetime.date.today()
    return data - datetime.timedelta(days=data.weekday())


def gerar_programacao_semana(cong, semana, usuario):
    criadas = 0
    with transaction.atomic():
        arranjos = ArranjoSaidaCampo.objects.filter(
            cong=cong, ativo=True
        ).select_related('local', 'grupo')
        for arranjo in arranjos:
            data = semana + datetime.timedelta(days=arranjo.dia_semana)
            try:
                _, criado = ProgramacaoCampo.objects.get_or_create(
                    cong=cong,
                    data=data,
                    arranjo=arranjo,
                    defaults={
                        'horario': arranjo.horario,
                        'local': arranjo.local,
                        'local_nome': arranjo.local.nome,
                        'grupo': arranjo.grupo,
                        'grupo_nome': arranjo.grupo.grupo if arranjo.grupo else '',
                        'descricao': arranjo.descricao,
                        'status': 'A',
                        'create_user': usuario,
                        'assign_user': usuario,
                    },
                )
            except IntegrityError:
                criado = False
            criadas += int(criado)
    return criadas


def movimentar_programacao(programacao_id, cong, usuario, acao, resultado='', observacao=''):
    with transaction.atomic():
        item = ProgramacaoCampo.objects.select_for_update().get(
            pk=programacao_id, cong=cong
        )
        agora = timezone.now()
        if acao == 'retirar':
            if item.status != 'P':
                raise ValidationError('Somente uma programação pronta pode ser retirada.')
            if item.tipo_atividade != 'T':
                raise ValidationError('A retirada se aplica apenas a atividades com território.')
            item.status = 'R'
            item.retirada_em = agora
            item.retirada_por = usuario
        elif acao == 'devolver':
            if item.status != 'R':
                raise ValidationError('Somente um território retirado pode ser devolvido.')
            if resultado not in {'C', 'P', 'N'}:
                raise ValidationError('Informe o resultado da devolução.')
            item.status = 'D'
            item.resultado = resultado
            item.devolvida_em = agora
            item.devolvida_por = usuario
            item.observacao_movimento = observacao.strip()
        elif acao == 'cancelar':
            if item.status not in {'A', 'P'}:
                raise ValidationError('Essa programação não pode mais ser cancelada.')
            if not observacao.strip():
                raise ValidationError('Informe o motivo do cancelamento.')
            item.status = 'C'
            item.motivo_cancelamento = observacao.strip()
        else:
            raise ValidationError('Ação inválida.')
        item.assign_user = usuario
        item.save()
        return item
