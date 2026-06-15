import django.contrib.auth.views
from django.urls import path

from . import views 

app_name = 'activities'

urlpatterns = [
    #path('', views.index, name='index'),
    path('relatorios/add/', views.add_relatorios, name='add_relatorios'),
    path('relatorios/list/', views.list_relatorios, name='list_relatorios'),
    path('resumo/list/', views.list_resumo, name='list_resumo'),
    path('analise/list/', views.analise, name='analise'),
    path('resumo-pioneiros-regulares/list/', views.resumo_pioneiros_regulares, name='resumo_pioneiros_regulares'),
    path('cartoes/list/', views.list_cartoes, name='list_cartoes'),
    path('cartoes/<int:publicadores_id>/generate/', views.generate_cartoes, name='generate_cartoes'),
    path('pendentes/list/', views.relatorios_pendentes, name='list_pendentes'),
]
