from django import forms
from django.db.models import Q

from register.models import Grupos, Publicadores

from .models import (
    ArranjoSaidaCampo,
    DirigenteCampoHabilitado,
    LocalSaidaCampo,
    MapaTerritorio,
    ProgramacaoCampo,
    TerritorioCampo,
)


class DirigenteCampoHabilitadoForm(forms.ModelForm):
    class Meta:
        model = DirigenteCampoHabilitado
        fields = ['publicador', 'ativo', 'observacao']
        widgets = {'observacao': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, cong=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cong = cong
        self.instance.cong = cong
        publicadores = Publicadores.objects.none()
        if cong:
            publicadores = Publicadores.objects.filter(
                cong=cong, situacao=1, sexo=0
            )
            if self.instance.pk:
                publicadores = Publicadores.objects.filter(cong=cong).filter(
                    Q(situacao=1, sexo=0)
                    | Q(pk=self.instance.publicador_id)
                )
        self.fields['publicador'].queryset = publicadores.order_by('nome')

    def save(self, commit=True):
        item = super().save(commit=False)
        item.cong = self.cong
        if commit:
            item.save()
        return item


class LocalSaidaCampoForm(forms.ModelForm):
    class Meta:
        model = LocalSaidaCampo
        fields = ['nome', 'endereco_referencia', 'ativo']

    def __init__(self, *args, cong=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cong = cong
        self.instance.cong = cong

    def save(self, commit=True):
        item = super().save(commit=False)
        item.cong = self.cong
        if commit:
            item.save()
        return item


class ArranjoSaidaCampoForm(forms.ModelForm):
    class Meta:
        model = ArranjoSaidaCampo
        fields = ['dia_semana', 'horario', 'local', 'grupo', 'descricao', 'ativo']
        widgets = {'horario': forms.TimeInput(attrs={'type': 'time'})}

    def __init__(self, *args, cong=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cong = cong
        self.instance.cong = cong
        self.fields['local'].queryset = LocalSaidaCampo.objects.none()
        self.fields['grupo'].queryset = Grupos.objects.none()
        if cong:
            locais = LocalSaidaCampo.objects.filter(cong=cong)
            if self.instance.pk:
                locais = locais.filter(Q(ativo=True) | Q(pk=self.instance.local_id))
            else:
                locais = locais.filter(ativo=True)
            self.fields['local'].queryset = locais.order_by('nome')
            self.fields['grupo'].queryset = Grupos.objects.filter(
                cong=cong
            ).order_by('grupo')

    def save(self, commit=True):
        item = super().save(commit=False)
        item.cong = self.cong
        if commit:
            item.save()
        return item


class TerritorioCampoForm(forms.ModelForm):
    class Meta:
        model = TerritorioCampo
        fields = ['codigo', 'localidade', 'descricao', 'observacao', 'ativo']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 2}),
            'observacao': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, cong=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cong = cong
        self.instance.cong = cong

    def save(self, commit=True):
        item = super().save(commit=False)
        item.cong = self.cong
        if commit:
            item.save()
        return item


class MapaTerritorioForm(forms.ModelForm):
    class Meta:
        model = MapaTerritorio
        fields = ['arquivo']
        widgets = {'arquivo': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'})}

    def __init__(self, *args, territorio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.territorio = territorio
        if territorio:
            self.instance.territorio = territorio

    def save(self, commit=True):
        item = super().save(commit=False)
        item.territorio = self.territorio
        item.vigente = True
        if commit:
            item.save()
        return item


class ProgramacaoCampoForm(forms.ModelForm):
    class Meta:
        model = ProgramacaoCampo
        fields = [
            'horario', 'local', 'grupo', 'descricao',
            'tipo_dirigencia', 'dirigente', 'tipo_atividade',
            'descricao_atividade', 'territorio',
        ]
        widgets = {'horario': forms.TimeInput(attrs={'type': 'time'})}

    def __init__(self, *args, cong=None, somente_territorio=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.cong = cong
        self.somente_territorio = somente_territorio
        self.fields['dirigente'].queryset = Publicadores.objects.none()
        self.fields['territorio'].queryset = TerritorioCampo.objects.none()
        self.fields['local'].queryset = LocalSaidaCampo.objects.none()
        self.fields['grupo'].queryset = Grupos.objects.none()
        if cong:
            habilitados = DirigenteCampoHabilitado.objects.filter(
                cong=cong, ativo=True
            ).values_list('publicador_id', flat=True)
            dirigentes = Publicadores.objects.filter(
                pk__in=habilitados, situacao=1, sexo=0
            )
            if self.instance.pk and self.instance.dirigente_id:
                dirigentes = Publicadores.objects.filter(cong=cong).filter(
                    Q(pk__in=dirigentes.values_list('pk', flat=True))
                    | Q(pk=self.instance.dirigente_id)
                )
            self.fields['dirigente'].queryset = dirigentes.order_by('nome')
            locais = LocalSaidaCampo.objects.filter(cong=cong)
            if self.instance.pk:
                locais = locais.filter(Q(ativo=True) | Q(pk=self.instance.local_id))
            else:
                locais = locais.filter(ativo=True)
            self.fields['local'].queryset = locais.order_by('nome')
            self.fields['grupo'].queryset = Grupos.objects.filter(
                cong=cong
            ).order_by('grupo')
            territorios = TerritorioCampo.objects.filter(cong=cong)
            if self.instance.pk and self.instance.territorio_id:
                territorios = territorios.filter(
                    Q(ativo=True) | Q(pk=self.instance.territorio_id)
                )
            else:
                territorios = territorios.filter(ativo=True)
            self.fields['territorio'].queryset = territorios.order_by('codigo')
        if somente_territorio:
            for campo in [
                'horario', 'local', 'grupo', 'descricao',
                'tipo_dirigencia', 'dirigente',
            ]:
                del self.fields[campo]

    def clean(self):
        dados = super().clean()
        tipo = dados.get('tipo_atividade')
        territorio = dados.get('territorio')
        if tipo == 'T' and territorio:
            mapa = territorio.mapas.filter(vigente=True).first()
            if not mapa:
                self.add_error('territorio', 'O território selecionado não possui mapa vigente.')
            else:
                self.instance.mapa = mapa
        elif tipo != 'T':
            self.instance.mapa = None
        self.instance.cong = self.cong
        tipo_dirigencia = dados.get(
            'tipo_dirigencia', self.instance.tipo_dirigencia
        )
        dirigente = dados.get('dirigente', self.instance.dirigente)
        dirigente_pronto = tipo_dirigencia == 'G' or bool(dirigente)
        atividade_pronta = (
            tipo != 'T' or bool(territorio and self.instance.mapa_id)
        )
        self.instance.status = 'P' if dirigente_pronto and atividade_pronta else 'A'
        return dados

    def save(self, commit=True):
        item = super().save(commit=False)
        item.cong = self.cong
        if commit:
            item.save()
        return item


class MovimentoProgramacaoCampoForm(forms.Form):
    ACAO = [
        ('retirar', 'Registrar retirada'),
        ('devolver', 'Registrar devolução'),
        ('cancelar', 'Cancelar programação'),
    ]
    acao = forms.ChoiceField(choices=ACAO, widget=forms.HiddenInput())
    resultado = forms.ChoiceField(
        choices=ProgramacaoCampo._meta.get_field('resultado').choices,
        required=False,
    )
    observacao = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'rows': 3})
    )

    def clean(self):
        dados = super().clean()
        acao = dados.get('acao')
        if acao == 'devolver' and not dados.get('resultado'):
            self.add_error('resultado', 'Informe o resultado da devolução.')
        if acao == 'cancelar' and not dados.get('observacao', '').strip():
            self.add_error('observacao', 'Informe o motivo do cancelamento.')
        return dados
