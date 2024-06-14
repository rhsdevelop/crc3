import django.contrib.auth.views
from django.urls import path

from . import views 

app_name = 'activities'

urlpatterns = [
    #path('', views.index, name='index'),
    #path('cong/add/', views.add_cong, name='add_cong'),
    #path('cong/list/', views.list_cong, name='list_cong'),
    #path('cong/<int:cong_id>/edit/', views.edit_cong, name='edit_cong'),
]
