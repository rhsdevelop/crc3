import django.contrib.auth.views
from django.urls import path

from . import views 

app_name = 'activities'

urlpatterns = [
    #path('', views.index, name='index'),
    path('relatorios/add/', views.add_relatorios, name='add_relatorios'),
    path('relatorios/list/', views.list_relatorios, name='list_relatorios'),
]
