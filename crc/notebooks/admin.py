from django import forms
from django.contrib import admin
from django.db import models

from register.models import CongUser

from .models import ConfiguracaoCadernoPioneiro


@admin.register(ConfiguracaoCadernoPioneiro)
class ConfiguracaoCadernoPioneiroAdmin(admin.ModelAdmin):
    list_display = ('cong', 'ano_servico', 'meta_horas', 'modified')
    list_filter = ('cong', 'ano_servico')
    search_fields = ('cong__nome',)
    readonly_fields = ('create_user', 'created', 'assign_user', 'modified')
    formfield_overrides = {models.ImageField: {'widget': forms.FileInput}}

    def _pode_gerenciar(self, request):
        return request.user.has_perm('notebooks.manage_pioneer_notebooks')

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
        vinculo = CongUser.objects.filter(user=request.user).first()
        if not vinculo:
            return queryset.none()
        return queryset.filter(cong=vinculo.cong)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'cong' and not request.user.is_superuser:
            vinculo = CongUser.objects.filter(user=request.user).first()
            kwargs['queryset'] = db_field.remote_field.model.objects.filter(
                pk=vinculo.cong_id if vinculo else None
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            vinculo = CongUser.objects.filter(user=request.user).first()
            if vinculo:
                obj.cong = vinculo.cong
        if not change:
            obj.create_user = request.user
        obj.assign_user = request.user
        super().save_model(request, obj, form, change)
