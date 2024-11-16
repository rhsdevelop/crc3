import django.contrib.auth.views
from django.urls import path

from . import views 

app_name = 'register'
urlpatterns = [
    path('', views.index, name='index'),
    path('cong/add/', views.add_cong, name='add_cong'),
    path('cong/list/', views.list_cong, name='list_cong'),
    path('cong/<int:cong_id>/edit/', views.edit_cong, name='edit_cong'),
    path('conguser/add/', views.add_conguser, name='add_conguser'),
    path('conguser/list/', views.list_conguser, name='list_conguser'),
    path('conguser/<int:conguser_id>/edit/', views.edit_conguser, name='edit_conguser'),
    path('grupos/add/', views.add_grupos, name='add_grupos'),
    path('grupos/list/', views.list_grupos, name='list_grupos'),
    path('grupos/<int:grupos_id>/edit/', views.edit_grupos, name='edit_grupos'),
    path('publicadores/add/', views.add_publicadores, name='add_publicadores'),
    path('publicadores/list/', views.list_publicadores, name='list_publicadores'),
    path('publicadores/sheet/', views.sheet_publicadores, name='sheet_publicadores'),
    path('publicadores/<int:publicadores_id>/edit/', views.edit_publicadores, name='edit_publicadores'),
    path('pioneiros/add/', views.add_pioneiros, name='add_pioneiros'),
    path('pioneiros/list/', views.list_pioneiros, name='list_pioneiros'),
    path('pioneiros/<int:pioneiros_id>/delete/', views.delete_pioneiros, name='delete_pioneiros'),
    path('profile/', views.edit_profile, name='edit_profile'),
    #path('doctors/<int:doctor_id>/phone/<int:phone_id>/delete/', views.delete_phone, name='delete_phone'),
    #path('specialties/add/', views.add_specialty, name='add_specialties'),
    #path('specialties/list/', views.list_specialties, name='list_specialties'),
    #path('specialties/<int:specialty_id>/edit/', views.edit_specialty, name='edit_specialty'),
    #path('phones/list/', views.list_phones, name='list_phones'),
    #path('<int:doctor_id>/results/', views.results, name='results'),
    #path('<int:doctor_id>/vote/', views.vote, name='vote'),
]
