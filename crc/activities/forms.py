from django import forms
from .models import Relatorios
from register.models import Cong, Grupos, Publicadores, PRIVILEGIO, SEXO, TIPO


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


class FindResumoPioneirosRegularesForm(forms.Form):
    congregacao = forms.ModelChoiceField(queryset=Cong.objects.all(), label='Congregação', required=False)
    grupo = forms.ModelChoiceField(queryset=Grupos.objects.all(), label='Grupo de serviço', required=False)
    publicador = forms.CharField(label='Publicador', required=False)
    mes_inicio = forms.DateField(
        label='Período inicial',
        widget=forms.widgets.TextInput(
            attrs={'type': "month"}
        ),
        required=False
    )
    mes_fim = forms.DateField(
        label='Período final',
        widget=forms.widgets.TextInput(
            attrs={'type': "month"}
        ),
        required=False
    )


class FindAnaliseForm(forms.Form):
    sexo = forms.MultipleChoiceField(
        choices=SEXO,
        label='Sexo',
        required=False,
        widget=forms.SelectMultiple(attrs={'size': 2})
    )
    tipo = forms.MultipleChoiceField(
        choices=TIPO[0:3],
        label='Tipo',
        required=False,
        widget=forms.SelectMultiple(attrs={'size': 3})
    )
    privilegio = forms.MultipleChoiceField(
        choices=PRIVILEGIO,
        label='Privilégio',
        required=False,
        widget=forms.SelectMultiple(attrs={'size': 3})
    )
    idade_minima = forms.IntegerField(
        label='Idade mínima',
        min_value=0,
        required=False
    )
    mes_inicio = forms.DateField(
        label='Período inicial',
        widget=forms.widgets.TextInput(
            attrs={'type': "month"}
        ),
        required=False
    )
    mes_fim = forms.DateField(
        label='Período final',
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
