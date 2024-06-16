from django import forms
from .models import Relatorios
from register.models import Grupos


class AddRelatoriosForm(forms.ModelForm):
    class Meta:
        model = Relatorios
        exclude = ['id', 'create_user', 'created', 'assign_user', 'modified']


class FindRelatoriosForm(forms.ModelForm):
    grupo = forms.ModelChoiceField(queryset=Grupos.objects.all())
    class Meta:
        model = Relatorios
        fields = ['publicador']
