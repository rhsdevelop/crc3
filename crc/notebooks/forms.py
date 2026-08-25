from django import forms

from .models import ConfiguracaoCadernoPioneiro


class ConfiguracaoCadernoPioneiroForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoCadernoPioneiro
        fields = ['imagem', 'meta_horas']
        widgets = {
            'imagem': forms.FileInput(
                attrs={'accept': 'image/jpeg,image/png,image/webp'}
            ),
            'meta_horas': forms.NumberInput(attrs={'min': 1, 'max': 744}),
        }

    def __init__(self, *args, cong=None, ano_servico=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cong = cong
        self.ano_servico = ano_servico
        self.instance.cong = cong
        self.instance.ano_servico = ano_servico
        if self.instance.pk:
            self.fields['imagem'].required = False

    def save(self, commit=True):
        configuracao = super().save(commit=False)
        configuracao.cong = self.cong
        configuracao.ano_servico = self.ano_servico
        if commit:
            configuracao.save()
        return configuracao
