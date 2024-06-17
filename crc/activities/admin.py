from django.contrib import admin

# Register your models here.
from .models import Relatorios, Faltas

admin.site.register(Relatorios)
admin.site.register(Faltas)