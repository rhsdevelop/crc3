import datetime

from django import forms

from register.models import Grupos, Publicadores

from .models import VisitaGrupo, VisitaPastoreio


def limites_ano_servico(ano_inicio):
    return (
        datetime.date(ano_inicio, 9, 1),
        datetime.date(ano_inicio + 1, 8, 31),
    )


class VisitaGrupoForm(forms.ModelForm):
    data_inicio = forms.DateField(
        label='Início (segunda-feira)',
        widget=forms.widgets.DateInput(attrs={'type': 'date'}),
    )

    class Meta:
        model = VisitaGrupo
        fields = ['grupo', 'data_inicio', 'confirmada', 'executada']
        labels = {'grupo': 'Grupo de serviço'}

    def __init__(self, *args, cong=None, ano_inicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cong = cong
        self.ano_inicio = ano_inicio
        self.fields['grupo'].queryset = Grupos.objects.none()
        if cong:
            self.fields['grupo'].queryset = Grupos.objects.filter(
                cong=cong,
            ).order_by('grupo')
        if ano_inicio is not None:
            inicio, fim = limites_ano_servico(ano_inicio)
            self.fields['data_inicio'].widget.attrs.update({
                'min': inicio.isoformat(),
                'max': fim.isoformat(),
            })

    def clean_data_inicio(self):
        data_inicio = self.cleaned_data['data_inicio']
        if data_inicio.weekday() != 0:
            raise forms.ValidationError('A visita deve começar em uma segunda-feira.')
        if self.ano_inicio is not None:
            inicio, fim = limites_ano_servico(self.ano_inicio)
            if not inicio <= data_inicio <= fim:
                raise forms.ValidationError(
                    'A data deve pertencer ao ano de serviço selecionado.'
                )
        return data_inicio

    def clean(self):
        cleaned_data = super().clean()
        grupo = cleaned_data.get('grupo')
        if grupo and (not self.cong or grupo.cong_id != self.cong.id):
            self.add_error(
                'grupo',
                'O grupo selecionado não pertence à congregação informada.',
            )
        if cleaned_data.get('executada'):
            cleaned_data['confirmada'] = True
        return cleaned_data

    def save(self, commit=True):
        item = super().save(commit=False)
        item.cong = self.cong
        if item.data_inicio:
            item.data_fim = item.data_inicio + datetime.timedelta(days=6)
        if item.executada:
            item.confirmada = True
        if commit:
            item.save()
        return item


class VisitaPastoreioForm(forms.ModelForm):
    data = forms.DateField(
        label='Data',
        widget=forms.widgets.DateInput(attrs={'type': 'date'}),
    )

    class Meta:
        model = VisitaPastoreio
        fields = [
            'publicador',
            'data',
            'assuntos',
            'materia',
            'acompanhante',
            'confirmado',
        ]
        widgets = {
            'assuntos': forms.Textarea(attrs={'rows': 3}),
            'materia': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, visita_grupo=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.visita_grupo = visita_grupo
        self.fields['publicador'].queryset = Publicadores.objects.none()
        self.fields['acompanhante'].queryset = Publicadores.objects.none()
        if visita_grupo:
            self.instance.visita_grupo = visita_grupo
            self.fields['publicador'].queryset = Publicadores.objects.filter(
                grupo=visita_grupo.grupo,
                situacao__in=[0, 1],
            ).order_by('nome')
            self.fields['acompanhante'].queryset = Publicadores.objects.filter(
                cong=visita_grupo.cong,
                situacao=1,
                privilegio__in=[1, 2],
            ).order_by('nome')
            self.fields['data'].widget.attrs.update({
                'min': visita_grupo.data_inicio.isoformat(),
                'max': visita_grupo.data_fim.isoformat(),
            })

    def save(self, commit=True):
        item = super().save(commit=False)
        item.visita_grupo = self.visita_grupo
        if commit:
            item.save()
        return item
