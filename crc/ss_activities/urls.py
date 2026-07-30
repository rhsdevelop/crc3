from django.urls import path

from . import views

app_name = 'ss_activities'

urlpatterns = [
    path('visitas-grupos/', views.list_visitas_grupos, name='list_visitas_grupos'),
    path(
        'visitas-grupos/adicionar/',
        views.add_visita_grupo,
        name='add_visita_grupo',
    ),
    path(
        'visitas-grupos/<int:visita_id>/editar/',
        views.edit_visita_grupo,
        name='edit_visita_grupo',
    ),
    path(
        'visitas-grupos/<int:visita_id>/apagar/',
        views.delete_visita_grupo,
        name='delete_visita_grupo',
    ),
    path(
        'visitas-grupos/<int:visita_id>/pastoreio/',
        views.list_visitas_pastoreio,
        name='list_visitas_pastoreio',
    ),
    path(
        'visitas-grupos/<int:visita_id>/pastoreio/adicionar/',
        views.add_visita_pastoreio,
        name='add_visita_pastoreio',
    ),
    path(
        'visitas-grupos/<int:visita_id>/pastoreio/<int:pastoreio_id>/confirmar/',
        views.confirm_visita_pastoreio,
        name='confirm_visita_pastoreio',
    ),
    path(
        'visitas-grupos/<int:visita_id>/pastoreio/<int:pastoreio_id>/apagar/',
        views.delete_visita_pastoreio,
        name='delete_visita_pastoreio',
    ),
]
