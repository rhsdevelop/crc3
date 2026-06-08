from django.urls import path

from . import views

app_name = 'agenda'

urlpatterns = [
    path('tarefas/', views.list_tarefas_secretario, name='list_tarefas_secretario'),
    path('tarefas/add/', views.add_tarefa_secretario, name='add_tarefa_secretario'),
    path('tarefas/base/', views.carregar_tarefas_base_secretario, name='carregar_tarefas_base_secretario'),
    path('tarefas/<int:tarefa_id>/edit/', views.edit_tarefa_secretario, name='edit_tarefa_secretario'),
    path('tarefas/<int:tarefa_id>/view/', views.view_tarefa_secretario, name='view_tarefa_secretario'),
    path('tarefas/<int:tarefa_id>/concluir/', views.concluir_tarefa_secretario, name='concluir_tarefa_secretario'),
]
