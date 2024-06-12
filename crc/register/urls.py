import django.contrib.auth.views
from django.urls import path

from . import views 

app_name = 'register'
urlpatterns = [
    path('', views.index, name='index'),
    #path('doctors/add/', views.add_doctor, name='add_doctor'),
    #path('doctors/list/', views.list_doctors, name='list_doctors'),
    #path('doctors/<int:doctor_id>/edit/', views.edit_doctor, name='edit_doctor'),
    #path('doctors/<int:doctor_id>/phone/<int:phone_id>/delete/', views.delete_phone, name='delete_phone'),
    #path('specialties/add/', views.add_specialty, name='add_specialties'),
    #path('specialties/list/', views.list_specialties, name='list_specialties'),
    #path('specialties/<int:specialty_id>/edit/', views.edit_specialty, name='edit_specialty'),
    #path('phones/list/', views.list_phones, name='list_phones'),
    #path('<int:doctor_id>/results/', views.results, name='results'),
    #path('<int:doctor_id>/vote/', views.vote, name='vote'),
]
