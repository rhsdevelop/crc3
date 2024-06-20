import datetime
from .models import Pioneiros, Publicadores

# Rotinas para agendamento em horários.

def atualiza_pioneiros():
    pio = Pioneiros.objects.filter(mes=datetime.date.today().replace(day=1))
    pioneiros_vinculados = [x.publicador_id for x in pio]
    pub = Publicadores.objects.filter(tipo=1).exclude(id__in=pioneiros_vinculados)
    for i in pub:
        Pioneiros.objects.create(publicador_id=i.id, mes=datetime.date.today().replace(day=1), observacao='Tempo Indeterminado', create_user_id=1, assign_user_id=1)

if __name__=='__main__':
    atualiza_pioneiros()