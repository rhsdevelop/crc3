from django.contrib import admin

from register.models import CongUser

from .models import VisitaGrupo, VisitaPastoreio


@admin.register(VisitaGrupo)
class VisitaGrupoAdmin(admin.ModelAdmin):
    list_display = ('grupo', 'cong', 'data_inicio', 'data_fim', 'confirmada', 'executada')
    list_filter = ('cong', 'confirmada', 'executada', 'data_inicio')
    search_fields = ('grupo__grupo', 'cong__nome')
    readonly_fields = ('data_fim', 'create_user', 'created', 'assign_user', 'modified')

    def _pode_gerenciar(self, request):
        return request.user.has_perm('ss_activities.manage_visitas_grupos')

    def has_module_permission(self, request):
        return self._pode_gerenciar(request)

    def has_view_permission(self, request, obj=None):
        return self._pode_gerenciar(request)

    def has_add_permission(self, request):
        return self._pode_gerenciar(request)

    def has_change_permission(self, request, obj=None):
        return self._pode_gerenciar(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        crc_user = CongUser.objects.filter(user=request.user).first()
        if not crc_user:
            return queryset.none()
        return queryset.filter(cong=crc_user.cong)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.create_user = request.user
        obj.assign_user = request.user
        super().save_model(request, obj, form, change)


@admin.register(VisitaPastoreio)
class VisitaPastoreioAdmin(admin.ModelAdmin):
    list_display = (
        'publicador',
        'data',
        'visita_grupo',
        'acompanhante',
        'confirmado',
    )
    list_filter = ('confirmado', 'data', 'visita_grupo__cong')
    search_fields = (
        'publicador__nome',
        'acompanhante__nome',
        'assuntos',
        'materia',
    )
    readonly_fields = ('create_user', 'created', 'assign_user', 'modified')

    def _pode_gerenciar(self, request):
        return request.user.has_perm('ss_activities.manage_visitas_grupos')

    def has_module_permission(self, request):
        return self._pode_gerenciar(request)

    def has_view_permission(self, request, obj=None):
        return self._pode_gerenciar(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return self._pode_gerenciar(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        crc_user = CongUser.objects.filter(user=request.user).first()
        if not crc_user:
            return queryset.none()
        return queryset.filter(visita_grupo__cong=crc_user.cong)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.create_user = request.user
        obj.assign_user = request.user
        super().save_model(request, obj, form, change)
