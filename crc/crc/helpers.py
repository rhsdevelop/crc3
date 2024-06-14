# Importação
from activities.models_origin import Pioneiros, Publicadores
from register.models import Pioneiros as NewPio
from register.models import Publicadores as NewPub

pub = Publicadores.objects.using('origin').all()
for i in pub.values():
    new_item = i.copy()
    new_item['cong_id'] = 1
    new_item['create_user_id'] = 1
    new_item['assign_user_id'] = 1
    if not new_item['data_classe']: del new_item['data_classe']
    if not new_item['data_visita']: del new_item['data_visita']
    if not new_item['nascimento']: del new_item['nascimento']
    if not new_item['batismo']: del new_item['batismo']
    if not new_item['grupo_id']: del new_item['grupo_id']
    NewPio.objects.create(**new_item)


pio = Pioneiros.objects.using('origin').all().order_by('id')
for i in pio.values():
    new_item = i.copy()
    new_item['mes'] = new_item['mes'].replace('/', '-')
    new_item['mes'] += '-01'
    new_item['create_user_id'] = 1
    new_item['assign_user_id'] = 1
    try:
        NewPio.objects.create(**new_item)
    except Exception as e:
        print(new_item)
        print(e)
