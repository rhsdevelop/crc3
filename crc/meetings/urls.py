import django.contrib.auth.views
from django.urls import path

from . import views 

app_name = 'meetings'

urlpatterns = [
    path('reunioes/list/', views.list_reunioes, name='list_reunioes'),
    path('reunioes/list/printcard/', views.printcard_reunioes, name='printcard_reunioes'),
    path('reunioes/add/', views.add_reunioes, name='add_reunioes'),
]
