from django.contrib import admin

from .models import TarefaSecretario


class TarefaSecretarioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'cong', 'categoria', 'tipo_recorrencia', 'data_limite', 'prioridade', 'status')
    list_filter = ('status', 'categoria', 'tipo_recorrencia', 'prioridade', 'cong')
    search_fields = ('titulo', 'descricao')


admin.site.register(TarefaSecretario, TarefaSecretarioAdmin)
