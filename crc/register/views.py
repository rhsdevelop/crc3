from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.template import loader

from .models import Cong, Drive, Grupos, Publicadores, Reunioes, Relatorios, Pioneiros, Faltas

# Create your views here.


@login_required
def index(request):
    template = loader.get_template('index.html')
    context = {
        'title': 'CRC - Controle de Registros de Congregação - V.3.0',
        'username': '%s %s' % (request.user.first_name, request.user.last_name),
    }
    return HttpResponse(template.render(context, request))
