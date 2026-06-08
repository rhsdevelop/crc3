from django import forms
from .models import Reunioes, TIPO_REUNIAO


DIAS_SEMANA = [
    (0, 'Segunda-feira'),
    (1, 'Terça-feira'),
    (2, 'Quarta-feira'),
    (3, 'Quinta-feira'),
    (4, 'Sexta-feira'),
    (5, 'Sábado'),
    (6, 'Domingo'),
]


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
    somente_resumo = forms.BooleanField(initial=False, required=False)

    class Meta:
        model = Reunioes
        fields = ['tipo']


class S3ReunioesForm(forms.Form):
    congregacao = forms.CharField(label='Nome da congregação', max_length=120)
    mes_inicial = forms.DateField(
        label='Mês inicial',
        widget=forms.widgets.TextInput(
            attrs={'type': "month"}
        ),
        input_formats=['%Y-%m']
    )
    dia_meio_semana = forms.ChoiceField(label='Reunião do meio da semana', choices=DIAS_SEMANA)
    dia_fim_semana = forms.ChoiceField(label='Reunião do fim de semana', choices=DIAS_SEMANA)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('dia_meio_semana') == cleaned_data.get('dia_fim_semana'):
            raise forms.ValidationError('Os dias das reuniões não podem ser iguais.')
        return cleaned_data
