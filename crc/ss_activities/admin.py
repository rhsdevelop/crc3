from django.contrib import admin

from register.models import CongUser

from .models import (
    ArranjoSaidaCampo,
    CarrinhoTestemunhoPublico,
    ConfiguracaoTestemunhoPublico,
    DesignacaoTestemunhoPublico,
    HabilitacaoTestemunhoPublico,
    LocalTestemunhoPublico,
    PeriodoTestemunhoPublico,
    DirigenteCampoHabilitado,
    LocalSaidaCampo,
    MapaTerritorio,
    ProgramacaoCampo,
    TerritorioCampo,
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


class CampoAdminMixin:
    readonly_fields = ('create_user', 'created', 'assign_user', 'modified')

    def _pode_gerenciar(self, request):
        return (
            request.user.has_perm('ss_activities.manage_programacao_campo')
            or request.user.has_perm('ss_activities.manage_territorios')
        )

    def has_module_permission(self, request):
        return self._pode_gerenciar(request)

    def has_view_permission(self, request, obj=None):
        return self._pode_gerenciar(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

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


@admin.register(DirigenteCampoHabilitado)
class DirigenteCampoHabilitadoAdmin(CampoAdminMixin, admin.ModelAdmin):
    list_display = ('publicador', 'cong', 'ativo')
    list_filter = ('cong', 'ativo')
    search_fields = ('publicador__nome',)


@admin.register(LocalSaidaCampo)
class LocalSaidaCampoAdmin(CampoAdminMixin, admin.ModelAdmin):
    list_display = ('nome', 'cong', 'ativo')
    list_filter = ('cong', 'ativo')


@admin.register(ArranjoSaidaCampo)
class ArranjoSaidaCampoAdmin(CampoAdminMixin, admin.ModelAdmin):
    list_display = ('dia_semana', 'horario', 'local', 'grupo', 'cong', 'ativo')
    list_filter = ('cong', 'dia_semana', 'ativo')


@admin.register(TerritorioCampo)
class TerritorioCampoAdmin(CampoAdminMixin, admin.ModelAdmin):
    list_display = ('codigo', 'localidade', 'cong', 'ativo')
    list_filter = ('cong', 'ativo')
    search_fields = ('codigo', 'localidade')


@admin.register(ProgramacaoCampo)
class ProgramacaoCampoAdmin(CampoAdminMixin, admin.ModelAdmin):
    list_display = ('data', 'horario', 'local_nome', 'grupo_nome', 'dirigente', 'territorio', 'status', 'cong')
    list_filter = ('cong', 'status', 'resultado', 'data')
    search_fields = ('local_nome', 'grupo_nome', 'dirigente__nome', 'territorio__codigo')


@admin.register(MapaTerritorio)
class MapaTerritorioAdmin(CampoAdminMixin, admin.ModelAdmin):
    list_display = ('territorio', 'versao', 'vigente', 'created')
    list_filter = ('territorio__cong', 'vigente')

    def get_queryset(self, request):
        queryset = admin.ModelAdmin.get_queryset(self, request)
        if request.user.is_superuser:
            return queryset
        crc_user = CongUser.objects.filter(user=request.user).first()
        if not crc_user:
            return queryset.none()
        return queryset.filter(territorio__cong=crc_user.cong)


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
