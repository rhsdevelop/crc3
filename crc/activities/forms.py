from django import forms
from .models import Relatorios
from register.models import Grupos, Publicadores, PRIVILEGIO, TIPO


class AddRelatoriosForm(forms.ModelForm):
    mes = forms.DateField(
        label='Mês',
        widget=forms.widgets.TextInput(
            attrs={'type': "month"}
        ),
        required=False
    )
    presente = forms.BooleanField(label='Participou no ministério', initial=True, required=False)
    class Meta:
        model = Relatorios
        exclude = ['id', 'create_user', 'created', 'assign_user', 'modified']


class FindRelatoriosForm(forms.ModelForm):
    grupo = forms.ModelChoiceField(queryset=Grupos.objects.all())
    tipo = forms.ChoiceField(choices=[(None, '------')] + TIPO, required=False)
    privilegio = forms.ChoiceField(choices=[(None, '------')] + PRIVILEGIO, required=False)
    mes_inicio = forms.DateField(
        label='Mês inicial',
        widget=forms.widgets.TextInput(
            attrs={'type': "month"}
        ),
        required=False
    )
    mes_fim = forms.DateField(
        label='Mês final',
        widget=forms.widgets.TextInput(
            attrs={'type': "month"}
        ),
        required=False
    )

    class Meta:
        model = Relatorios
        fields = ['publicador', 'tipo']


class FindResumoForm(forms.Form):
    grupo = forms.ModelChoiceField(queryset=Grupos.objects.all(), required=False)
    somente_ativos = forms.BooleanField(initial=True, required=False)
    mes_inicio = forms.DateField(
        label='Mês inicial',
        widget=forms.widgets.TextInput(
            attrs={'type': "month"}
        ),
        required=False
    )
    mes_fim = forms.DateField(
        label='Mês final',
        widget=forms.widgets.TextInput(
            attrs={'type': "month"}
        ),
        required=False
    )


class FindCartoesForm(forms.Form):
    publicador = forms.ModelChoiceField(queryset=Publicadores.objects.all(), required=False)
    grupo = forms.ModelChoiceField(queryset=Grupos.objects.all(), required=False)
    mes_inicio = forms.DateField(
        label='Mês inicial',
        widget=forms.widgets.TextInput(
            attrs={'type': "month"}
        ),
        required=False
    )
    mes_fim = forms.DateField(
        label='Mês final',
        widget=forms.widgets.TextInput(
            attrs={'type': "month"}
        ),
        required=False
    )
    somente_resumo = forms.BooleanField(initial=False, required=False)
