from django import forms
from .models import Cong, CongUser, Drive, Grupos, Publicadores, Pioneiros


class AddCongForm(forms.ModelForm):
    class Meta:
        model = Cong
        exclude = ['id', 'create_user', 'created', 'assign_user', 'modified']


class FindCongForm(forms.ModelForm):
    class Meta:
        model = Cong
        exclude = ['id', 'create_user', 'created', 'assign_user', 'modified']


class AddCongUserForm(forms.ModelForm):
    class Meta:
        model = CongUser
        exclude = ['id', 'create_user', 'created', 'assign_user', 'modified']


class FindCongUserForm(forms.ModelForm):
    class Meta:
        model = CongUser
        exclude = ['id', 'create_user', 'created', 'assign_user', 'modified']


class AddGruposForm(forms.ModelForm):
    class Meta:
        model = Grupos
        exclude = ['id', 'create_user', 'created', 'assign_user', 'modified']


class FindGruposForm(forms.ModelForm):
    class Meta:
        model = Grupos
        exclude = ['id', 'create_user', 'created', 'assign_user', 'modified']


class AddPioneirosForm(forms.ModelForm):
    mes = forms.DateField(
        label='Mês',
        widget=forms.widgets.TextInput(
            attrs={'type': "month"}
        ),
        required=False
    )
    class Meta:
        model = Pioneiros
        exclude = ['id', 'create_user', 'created', 'assign_user', 'modified']


class FindPioneirosForm(forms.ModelForm):
    mes = forms.DateField(
        label='Mês',
        widget=forms.widgets.TextInput(
            attrs={'type': "month"}
        ),
        required=False
    )
    class Meta:
        model = Pioneiros
        exclude = ['id', 'create_user', 'created', 'assign_user', 'modified']


class AddPublicadoresForm(forms.ModelForm):
    nascimento = forms.DateField(
        label='Nascimento',
        widget=forms.widgets.DateInput(
            attrs={'type': "date"}
        ),
        required=False
    )
    batismo = forms.DateField(
        label='Batismo',
        widget=forms.widgets.DateInput(
            attrs={'type': "date"}
        ),
        required=False
    )
    data_classe = forms.DateField(
        label='Data classe',
        widget=forms.widgets.DateInput(
            attrs={'type': "date"}
        ),
        required=False
    )
    data_visita = forms.DateField(
        label='Data classe',
        widget=forms.widgets.DateInput(
            attrs={'type': "date"}
        ),
        required=False
    )

    class Meta:
        model = Publicadores
        exclude = ['id', 'create_user', 'created', 'assign_user', 'modified']


class FindPublicadoresForm(forms.ModelForm):
    class Meta:
        model = Publicadores
        fields = ['nome', 'endereco', 'esperanca', 'privilegio', 'tipo', 'situacao', 'grupo']
