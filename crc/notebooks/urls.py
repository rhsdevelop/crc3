from django.urls import path

from . import views


app_name = 'notebooks'

urlpatterns = [
    path(
        'pioneiros-regulares/',
        views.pioneiros_regulares,
        name='pioneiros_regulares',
    ),
    path(
        'pioneiros-regulares/configuracao/',
        views.salvar_configuracao,
        name='salvar_configuracao',
    ),
    path(
        'pioneiros-regulares/configuracoes/<int:configuracao_id>/imagem/',
        views.visualizar_imagem,
        name='visualizar_imagem',
    ),
    path(
        'pioneiros-regulares/capas/pdf/',
        views.pdf_capas,
        name='pdf_capas',
    ),
    path(
        'pioneiros-regulares/<int:publicador_id>/capa/pdf/',
        views.pdf_capa_individual,
        name='pdf_capa_individual',
    ),
    path(
        'pioneiros-regulares/miolo/pdf/',
        views.pdf_miolo,
        name='pdf_miolo',
    ),
]
