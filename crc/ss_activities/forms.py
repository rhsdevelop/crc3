import datetime

from django import forms
from django.db.models import Q

from register.models import Grupos, Publicadores

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


class HabilitacaoTestemunhoPublicoForm(forms.ModelForm):
    data_treinamento = forms.DateField(
        label='Data do treinamento',
        widget=forms.widgets.DateInput(attrs={'type': 'date'}),
    )

    class Meta:
        model = HabilitacaoTestemunhoPublico
        fields = ['publicador', 'data_treinamento', 'aprovado', 'observacao']
        widgets = {'observacao': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, cong=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cong = cong
        if cong:
            self.instance.cong = cong
        publicadores = Publicadores.objects.none()
        if cong:
            publicadores = Publicadores.objects.filter(cong=cong)
            if self.instance.pk:
                publicadores = publicadores.filter(
                    Q(situacao=1) | Q(pk=self.instance.publicador_id)
                )
            else:
                publicadores = publicadores.filter(situacao=1)
        self.fields['publicador'].queryset = publicadores.order_by('nome')

    def save(self, commit=True):
        item = super().save(commit=False)
        item.cong = self.cong
        if commit:
            item.save()
        return item


class PeriodoTestemunhoPublicoForm(forms.ModelForm):
    class Meta:
        model = PeriodoTestemunhoPublico
        fields = ['dia_semana', 'descricao', 'horario', 'ativo']
        widgets = {'horario': forms.widgets.TimeInput(attrs={'type': 'time'})}

    def __init__(self, *args, cong=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cong = cong
        if cong:
            self.instance.cong = cong

    def save(self, commit=True):
        item = super().save(commit=False)
        item.cong = self.cong
        if commit:
            item.save()
        return item


class LocalTestemunhoPublicoForm(forms.ModelForm):
    class Meta:
        model = LocalTestemunhoPublico
        fields = ['nome', 'endereco_referencia', 'observacao', 'ativo']
        widgets = {'observacao': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, cong=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cong = cong
        if cong:
            self.instance.cong = cong

    def save(self, commit=True):
        item = super().save(commit=False)
        item.cong = self.cong
        if commit:
            item.save()
        return item


class ConfiguracaoTestemunhoPublicoForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoTestemunhoPublico
        fields = ['quantidade_carrinhos', 'modo_identificacao']

    def __init__(self, *args, cong=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cong = cong
        if cong:
            self.instance.cong = cong

    def save(self, commit=True):
        item = super().save(commit=False)
        item.cong = self.cong
        if commit:
            item.save()
        return item


class CarrinhoTestemunhoPublicoForm(forms.ModelForm):
    class Meta:
        model = CarrinhoTestemunhoPublico
        fields = ['nome_personalizado']

    def __init__(self, *args, cong=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cong = cong
        if cong:
            self.instance.cong = cong

    def save(self, commit=True):
        item = super().save(commit=False)
        item.cong = self.cong
        if commit:
            item.save()
        return item


class DesignacaoTestemunhoPublicoForm(forms.ModelForm):
    data = forms.DateField(
        widget=forms.widgets.DateInput(attrs={'type': 'date'}),
    )

    class Meta:
        model = DesignacaoTestemunhoPublico
        fields = [
            'data',
            'periodo',
            'local',
            'carrinho',
            'publicador_1',
            'publicador_2',
        ]

    def __init__(self, *args, cong=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cong = cong
        if cong:
            self.instance.cong = cong
        periodos = PeriodoTestemunhoPublico.objects.none()
        locais = LocalTestemunhoPublico.objects.none()
        carrinhos = CarrinhoTestemunhoPublico.objects.none()
        publicadores = Publicadores.objects.none()
        if cong:
            periodos = PeriodoTestemunhoPublico.objects.filter(
                cong=cong,
                ativo=True,
            )
            locais = LocalTestemunhoPublico.objects.filter(cong=cong, ativo=True)
            carrinhos = CarrinhoTestemunhoPublico.objects.filter(
                cong=cong,
                ativo=True,
            ).select_related('cong__configuracao_testemunho_publico')
            publicadores = Publicadores.objects.filter(
                cong=cong,
                situacao=1,
                habilitacoes_testemunho_publico__cong=cong,
                habilitacoes_testemunho_publico__aprovado=True,
            ).distinct()
            if self.instance.pk:
                periodos = PeriodoTestemunhoPublico.objects.filter(
                    Q(cong=cong, ativo=True) | Q(pk=self.instance.periodo_id)
                )
                locais = LocalTestemunhoPublico.objects.filter(
                    Q(cong=cong, ativo=True) | Q(pk=self.instance.local_id)
                )
                carrinhos = CarrinhoTestemunhoPublico.objects.filter(
                    Q(cong=cong, ativo=True) | Q(pk=self.instance.carrinho_id)
                ).select_related('cong__configuracao_testemunho_publico')
                publicadores = Publicadores.objects.filter(
                    Q(
                        cong=cong,
                        situacao=1,
                        habilitacoes_testemunho_publico__cong=cong,
                        habilitacoes_testemunho_publico__aprovado=True,
                    )
                    | Q(
                        pk__in=[
                            self.instance.publicador_1_id,
                            self.instance.publicador_2_id,
                        ]
                    )
                ).distinct()
        self.fields['periodo'].queryset = periodos.order_by(
            'dia_semana',
            'horario',
        )
        self.fields['local'].queryset = locais.order_by('nome')
        self.fields['carrinho'].queryset = carrinhos.order_by('numero_ordem')
        self.fields['publicador_1'].queryset = publicadores.order_by('nome')
        self.fields['publicador_2'].queryset = publicadores.order_by('nome')

    def save(self, commit=True):
        item = super().save(commit=False)
        item.cong = self.cong
        if commit:
            item.save()
        return item
