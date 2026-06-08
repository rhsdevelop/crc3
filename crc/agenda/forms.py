from django import forms

from .models import (
    CATEGORIA_TAREFA,
    MESES_REFERENCIA,
    PRIORIDADE_TAREFA,
    STATUS_TAREFA,
    TIPO_RECORRENCIA,
    TarefaSecretario,
)


class TarefaSecretarioForm(forms.ModelForm):
    data_prevista = forms.DateField(
        label='Data prevista',
        widget=forms.widgets.DateInput(attrs={'type': 'date'}),
        required=False,
    )
    data_limite = forms.DateField(
        label='Data limite',
        widget=forms.widgets.DateInput(attrs={'type': 'date'}),
        required=False,
    )
    data_conclusao = forms.DateField(
        label='Data de conclusão',
        widget=forms.widgets.DateInput(attrs={'type': 'date'}),
        required=False,
    )

    class Meta:
        model = TarefaSecretario
        exclude = ['id', 'create_user', 'created', 'assign_user', 'modified']


class FindTarefaSecretarioForm(forms.Form):
    status = forms.ChoiceField(choices=[('', '------')] + STATUS_TAREFA, required=False)
    categoria = forms.ChoiceField(choices=[('', '------')] + CATEGORIA_TAREFA, required=False)
    tipo_recorrencia = forms.ChoiceField(choices=[('', '------')] + TIPO_RECORRENCIA, required=False)
    mes_referencia = forms.ChoiceField(choices=[('', '------')] + MESES_REFERENCIA, required=False)
    ano_referencia = forms.IntegerField(label='Ano de referência', required=False)
    busca = forms.CharField(label='Busca', required=False)
    ordenacao = forms.ChoiceField(
        label='Ordenação',
        choices=[
            ('data_limite', 'Data limite'),
            ('prioridade', 'Prioridade'),
        ],
        required=False,
    )
