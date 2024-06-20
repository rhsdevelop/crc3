from django import forms
from .models import Reunioes, TIPO_REUNIAO


class AddReunioesForm(forms.ModelForm):
    data = forms.DateField(
        label='Mês',
        widget=forms.widgets.TextInput(
            attrs={'type': "date"}
        ),
        required=False
    )
    class Meta:
        model = Reunioes
        exclude = ['id', 'create_user', 'created', 'assign_user', 'modified']


class FindReunioesForm(forms.ModelForm):
    tipo = forms.ChoiceField(choices=[(None, '------')] + TIPO_REUNIAO, required=False)
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
        model = Reunioes
        fields = ['tipo']
