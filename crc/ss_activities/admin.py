from django.contrib import admin

from register.models import CongUser

from .models import (
    CarrinhoTestemunhoPublico,
    ConfiguracaoTestemunhoPublico,
    DesignacaoTestemunhoPublico,
    HabilitacaoTestemunhoPublico,
    LocalTestemunhoPublico,
    PeriodoTestemunhoPublico,
    VisitaGrupo,
    VisitaPastoreio,
)


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


class TestemunhoPublicoAdminMixin:
    readonly_fields = ('create_user', 'created', 'assign_user', 'modified')

    def _pode_gerenciar(self, request):
        return request.user.has_perm(
            'ss_activities.manage_testemunho_publico'
        )

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
        if not request.user.is_superuser:
            crc_user = CongUser.objects.filter(user=request.user).first()
            if crc_user:
                obj.cong = crc_user.cong
        if not change:
            obj.create_user = request.user
        obj.assign_user = request.user
        super().save_model(request, obj, form, change)


@admin.register(HabilitacaoTestemunhoPublico)
class HabilitacaoTestemunhoPublicoAdmin(
    TestemunhoPublicoAdminMixin,
    admin.ModelAdmin,
):
    list_display = ('publicador', 'cong', 'data_treinamento', 'aprovado')
    list_filter = ('cong', 'aprovado', 'data_treinamento')
    search_fields = ('publicador__nome', 'observacao')


@admin.register(PeriodoTestemunhoPublico)
class PeriodoTestemunhoPublicoAdmin(
    TestemunhoPublicoAdminMixin,
    admin.ModelAdmin,
):
    list_display = ('descricao', 'dia_semana', 'horario', 'cong', 'ativo')
    list_filter = ('cong', 'dia_semana', 'ativo')


@admin.register(LocalTestemunhoPublico)
class LocalTestemunhoPublicoAdmin(
    TestemunhoPublicoAdminMixin,
    admin.ModelAdmin,
):
    list_display = ('nome', 'cong', 'endereco_referencia', 'ativo')
    list_filter = ('cong', 'ativo')
    search_fields = ('nome', 'endereco_referencia', 'observacao')


@admin.register(ConfiguracaoTestemunhoPublico)
class ConfiguracaoTestemunhoPublicoAdmin(
    TestemunhoPublicoAdminMixin,
    admin.ModelAdmin,
):
    list_display = ('cong', 'quantidade_carrinhos', 'modo_identificacao')


@admin.register(CarrinhoTestemunhoPublico)
class CarrinhoTestemunhoPublicoAdmin(
    TestemunhoPublicoAdminMixin,
    admin.ModelAdmin,
):
    list_display = ('identificacao', 'numero_ordem', 'cong', 'ativo')
    list_filter = ('cong', 'ativo')

    def has_add_permission(self, request):
        return False


@admin.register(DesignacaoTestemunhoPublico)
class DesignacaoTestemunhoPublicoAdmin(
    TestemunhoPublicoAdminMixin,
    admin.ModelAdmin,
):
    list_display = (
        'data',
        'periodo',
        'carrinho',
        'local',
        'publicador_1',
        'publicador_2',
        'cong',
    )
    list_filter = ('cong', 'data', 'periodo')
    search_fields = (
        'publicador_1__nome',
        'publicador_2__nome',
        'local__nome',
    )
