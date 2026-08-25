import calendar
import datetime
from decimal import Decimal, ROUND_HALF_UP


MESES_PORTUGUES = [
    'Janeiro',
    'Fevereiro',
    'Março',
    'Abril',
    'Maio',
    'Junho',
    'Julho',
    'Agosto',
    'Setembro',
    'Outubro',
    'Novembro',
    'Dezembro',
]

DIAS_SEMANA = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']


def ano_servico_atual(data=None):
    data = data or datetime.date.today()
    return data.year if data.month >= 9 else data.year - 1


def meses_ano_servico(ano_servico):
    for indice in range(12):
        mes = ((8 + indice) % 12) + 1
        ano = ano_servico if mes >= 9 else ano_servico + 1
        yield datetime.date(ano, mes, 1)


def meta_acumulada(meta_horas, dia, quantidade_dias):
    minutos = (
        Decimal(meta_horas * 60) * Decimal(dia) / Decimal(quantidade_dias)
    ).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    horas, minutos_restantes = divmod(int(minutos), 60)
    return '%s:%02d' % (horas, minutos_restantes)


def dias_mes(data, meta_horas):
    quantidade = calendar.monthrange(data.year, data.month)[1]
    for dia in range(1, quantidade + 1):
        data_dia = datetime.date(data.year, data.month, dia)
        yield {
            'data': data_dia,
            'dia': dia,
            'dia_semana': DIAS_SEMANA[data_dia.weekday()],
            'fim_semana': data_dia.weekday() >= 5,
            'meta': meta_acumulada(meta_horas, dia, quantidade),
        }
